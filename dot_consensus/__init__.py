from otree.api import *
import string, json, random
from time import time
import numpy as np
from dot_consensus.experiment_settings import DOT2_CONSTANTS

doc = 'Dot Consensus Experiment (Kuroda et al. 2025 stimulus x consensus loop)'

# constants
class C(BaseConstants):
    NAME_IN_URL = 'dot_consensus'
    PLAYERS_PER_GROUP = 5
    NUM_ROUNDS = 1000

    NUM_PRACTICE_TASKS = 1
    NUM_NORMAL_TASKS = DOT2_CONSTANTS['NUM_ROUNDS']
    NUM_ATTENTION_CHECKS = max(0, min(4, NUM_NORMAL_TASKS // 14))
    NUM_REAL_TASKS = NUM_ATTENTION_CHECKS + NUM_NORMAL_TASKS
    TOTAL_TASKS = NUM_PRACTICE_TASKS + NUM_REAL_TASKS

    CHAT_TIMEOUT = 120
    MAIN_TEMPLATE = 'dot_consensus/MyPage.html'
    ## Kuroda et al. (2025) stimulus parameters
    SIGMA = DOT2_CONSTANTS['SIGMA']
    N_DOTS = DOT2_CONSTANTS['N_DOTS']
    MEAN = DOT2_CONSTANTS['MEAN']
    FPS = DOT2_CONSTANTS['FPS']
    TIME_LIMIT = DOT2_CONSTANTS['TIME_LIMIT']
    REDIRECT_URL = DOT2_CONSTANTS.get('REDIRECT_URL', '')

# models
class Subsession(BaseSubsession):
    pass

class Group(BaseGroup):
    pass

class Player(BasePlayer):
    taskdata = models.StringField(blank=True)
    time_start = models.StringField(blank=True)
    ## decision 1 (before chat)
    decision1_choice = models.StringField(blank=True)
    decision1_confidence = models.IntegerField(blank=True)
    decision1_rt_ms = models.IntegerField(blank=True)
    ## decision 2 (after chat)
    decision2_choice = models.StringField(blank=True)
    decision2_confidence = models.IntegerField(blank=True)
    decision2_rt_ms = models.IntegerField(blank=True)
    ## consensus check
    is_consensus = models.BooleanField(initial=False)

# create stimulus
def _generate_stimulus(answer: str, is_attention: bool = False) -> tuple:
    if is_attention:
        mean = 30 if answer == 'red' else -30
    else:
        mean = C.MEAN if answer == 'red' else -C.MEAN
    diff_dots = np.random.normal(mean, C.SIGMA, C.FPS * C.TIME_LIMIT)
    for i in range(len(diff_dots)):
        if diff_dots[i] % 2 < 1:
            diff_dots[i] = (diff_dots[i] // 2) * 2
        else:
            diff_dots[i] = (diff_dots[i] // 2) * 2 + 2
    red_dots = (C.N_DOTS + diff_dots) / 2
    n_red = json.dumps(list(red_dots.astype(np.float64)))
    n_blue = json.dumps(list(C.N_DOTS - np.array(json.loads(n_red))))
    seed = ''.join(random.sample(string.ascii_letters, 20))
    return n_red, n_blue, seed

def _generate_answer_sequence() -> list:
    task_parameters = np.array([-1, -1, 1, 1])
    tasks = []
    ## practice task
    practice_answers = ['red', 'blue', 'red', 'blue']
    for i in range(C.NUM_PRACTICE_TASKS):
        tasks.append({
            'question_id': i,
            'task_index': i,
            'is_practice': True,
            'is_attention': False,
            'answer': practice_answers[i % len(practice_answers)],
        })
    ## real task
    num_block = (C.NUM_NORMAL_TASKS + 3) // 4
    rng_list = []
    for _ in range(num_block):
        rng_list += random.sample(range(4), 4)
    rng_list = rng_list[:C.NUM_NORMAL_TASKS]
    for i in range(C.NUM_ATTENTION_CHECKS):
        rng_list.insert(13 + i * 14, 99)
    attn_count = 0
    for i in range(C.NUM_REAL_TASKS):
        val = rng_list[i]
        is_attention = (val == 99)
        if is_attention:
            answer = 'red' if attn_count % 2 == 0 else 'blue'
            attn_count += 1
        else:
            answer = 'red' if task_parameters[val] == -1 else 'blue'
        tasks.append({
            'question_id': C.NUM_PRACTICE_TASKS + i,
            'task_index': C.NUM_PRACTICE_TASKS + i,
            'is_practice': False,
            'is_attention': is_attention,
            'answer': answer,
        })
    return tasks

# session initialization
def creating_session(subsession):
    if subsession.round_number == 1:
        subsession.group_randomly(fixed_id_in_group=True)
        ## Generate the stimulus parameters for all tasks and store them in session.vars
        if 'answer_sequence' not in subsession.session.vars:
            subsession.session.vars['answer_sequence'] = _generate_answer_sequence()
        answer_sequence = subsession.session.vars['answer_sequence']
        ## Generate the stimulus parameters for each group and store them in group.vars
        for g in subsession.get_groups():
            players = g.get_players()
            group_tasks = []
            for info in answer_sequence:
                n_red, n_blue, seed = _generate_stimulus(info['answer'], info.get('is_attention', False))
                group_tasks.append({**info, 'n_red': n_red, 'n_blue': n_blue, 'seed': seed})
            ## nickname map for chat (rank-based, shuffled each round)
            nickname_maps = [{} for _ in players]
            for task_idx in range(len(group_tasks)):
                perm = list(range(len(players)))
                random.shuffle(perm)
                for rank, pidx in enumerate(perm):
                    nickname_maps[pidx][task_idx] = f'{rank + 1}番さん'
            for order_id, task in enumerate(group_tasks, start=1):
                task['order_id'] = order_id
            for i, p in enumerate(players):
                p.participant.vars['all_tasks'] = group_tasks
                p.participant.vars['current_task_index'] = 0
                p.participant.vars['correct_count'] = 0
                p.participant.vars['task_correct'] = []
                p.participant.vars['nickname_map'] = nickname_maps[i]
                p.participant.vars['latest_choice'] = None
                p.participant.vars['last_confidence'] = None
                p.participant.color_pos = 'redblue' if i % 2 == 0 else 'bluered'
    else:
        subsession.group_like_round(1)

# helper functions
# check if the current task is active, practice, and to get the current task info
def _active(player: Player) -> bool:
    idx   = player.participant.vars.get('current_task_index', 0)
    tasks = player.participant.vars.get('all_tasks', [])
    return idx < len(tasks)

# check if the current task is an attention check
def _is_practice(player: Player) -> bool:
    idx   = player.participant.vars.get('current_task_index', 0)
    tasks = player.participant.vars.get('all_tasks', [])
    return idx < len(tasks) and tasks[idx].get('is_practice', False)

# check if the current task is a new task (not repeated due to lack of consensus in the previous iteration)
def _is_new_task(player: Player) -> bool:
    if not _active(player):
        return False
    if player.round_number == 1:
        return True
    prev = player.round_number - 1
    return player.participant.vars.get(f'is_finished_round_{prev}') is True

# get the current task info as a dict
def _current_task(player: Player) -> dict:
    idx = player.participant.vars['current_task_index']
    return player.participant.vars['all_tasks'][idx]

# get the current iteration number for the current task (1, 2, 3, ...)
def _iteration_num(player: Player) -> int:
    idx = player.participant.vars['current_task_index']
    return player.participant.vars.get(f'task{idx}_iter', 1)


# Page
# Welcome to the experiment: You need to enter the full-screen mode
class Fullscreen(Page):
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 1

# Instructions: Google slide is embedded in the page
class Instruction(Page):
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 1
    @staticmethod
    def js_vars(player: Player):
        return dict(color_pos = player.participant.color_pos)

class Wait_Instruction(WaitPage):
    title_text = '他の参加者を待っています...'
    body_text  = '全員が揃い次第、実験を開始します。'
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 1


# stimulus presentation
# Are you ready for the practice?
class StartPractice(Page):
    @staticmethod
    def is_displayed(player):
        return player.round_number == 1

# Are you ready for the real task?
class StartReal(Page):
    @staticmethod
    def is_displayed(player: Player):
        if _active(player) and _is_practice(player):
            return True
        if _active(player) and not _is_practice(player):
            return player.participant.vars.get(f'is_finished_round_{player.round_number}', False)
        return False

    @staticmethod
    def vars_for_template(player: Player):
        idx = player.participant.vars['current_task_index']
        if _is_practice(player):
            next_real_num = 1
        else:
            next_real_num = idx - C.NUM_PRACTICE_TASKS + 1
        return dict(
            task_num           = next_real_num,
            num_real           = C.NUM_REAL_TASKS,
            is_practice_ending = _is_practice(player),
        )

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        if _is_practice(player):
            idx = player.participant.vars['current_task_index']
            player.participant.vars['current_task_index'] = idx + 1
            player.participant.vars[f'task{idx}_iter'] = 1
            player.participant.vars[f'is_finished_round_{player.round_number}'] = True


# ITI + trial
class Task(Page):
    form_model = 'player'
    form_fields = ['taskdata']
    timeout_seconds = C.TIME_LIMIT
    ## Pass the coherence and answer to the JavaScript file
    @staticmethod
    def is_displayed(player: Player):
        return _is_new_task(player)
    @staticmethod
    def js_vars(player: Player):
        task = _current_task(player)
        return dict(
            fps = C.FPS,
            color_pos = player.participant.color_pos,
            n_dots = C.N_DOTS,
            n_red = task['n_red'],
            n_blue = task['n_blue'],
            seed = task['seed']
        )
    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        if player.taskdata:
            try:
                player.time_start = json.loads(player.taskdata).get('time_start', '')
            except Exception:
                pass
        player.participant.vars['page_start_time'] = time()

# Decision 1 (before chat)
class Decision1(Page):
    form_model  = 'player'
    form_fields = ['decision1_choice', 'decision1_confidence', 'decision1_rt_ms']
    @staticmethod
    def is_displayed(player):
        return _is_new_task(player)
    @staticmethod
    def vars_for_template(player):
        idx  = player.participant.vars['current_task_index']
        task = _current_task(player)
        real_no = idx - C.NUM_PRACTICE_TASKS + 1 if not task['is_practice'] else 0
        return dict(
            is_practice  = task['is_practice'],
            task_num     = max(0, real_no),
            num_real     = C.NUM_REAL_TASKS,
            color_pos    = player.participant.color_pos,
            iteration    = _iteration_num(player),
        )
    @staticmethod
    def error_message(player: Player, values):
        if not values.get('decision1_choice'):
            return 'どちらかの色を選択してください。'
        if values.get('decision1_confidence') is None:
            return '自信の程度を選択してください。'
    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        t0 = player.participant.vars.get('page_start_time')
        if t0:
            player.decision1_rt_ms = int((time() - t0) * 1000)
        player.participant.vars['latest_choice'] = player.decision1_choice or 'miss'
        player.participant.vars['last_confidence'] = player.decision1_confidence
        player.participant.vars[f'decision_making_round_{player.round_number}'] = (
            player.decision1_choice or 'miss'
        )
        idx = player.participant.vars['current_task_index']
        task = _current_task(player)
        choice = player.decision1_choice or 'miss'
        true_false = (1 if choice == task['answer'] else 0) if choice != 'miss' else None
        elapsed_ms = int((time() - t0) * 1000) if t0 else None
        player.participant.vars[f'choice_task{idx}'] = [{
            'time_step': 0,
            'choice': choice,
            'true_false': true_false,
            'confidence': player.decision1_confidence,
            'time_spent_ms': elapsed_ms,
        }]
        player.participant.vars['page_start_time'] = time()


# Wait for everyone to finish Decision 1
class Wait_Chat(WaitPage):
    title_text = '他の参加者を待っています...'
    body_text = '全員が最初の判断を入力するまでお待ちください。'
    @staticmethod
    def is_displayed(player: Player):
        return _is_new_task(player)

# Chat
class Chat(Page):
    timeout_seconds = C.CHAT_TIMEOUT

    @staticmethod
    def is_displayed(player: Player):
        return _active(player)

    @staticmethod
    def vars_for_template(player: Player):
        idx = player.participant.vars['current_task_index']
        nickname = player.participant.vars['nickname_map'].get(idx, '匿名')
        decisions = []
        for p in player.group.get_players():
            decisions.append({
                'id': p.id_in_group,
                'nickname': p.participant.vars['nickname_map'].get(idx, '匿名'),
                'choice': p.participant.vars.get('latest_choice', 'miss'),
                'confidence': p.participant.vars.get('last_confidence'),
                'is_me': p.id_in_group == player.id_in_group,
            })
        count_red = sum(1 for d in decisions if d['choice'] == 'red')
        count_blue = sum(1 for d in decisions if d['choice'] == 'blue')
        return dict(
            nickname = nickname,
            my_choice = player.participant.vars.get('latest_choice', ''),
            decisions = decisions,
            decisions_json = json.dumps(decisions),
            count_red = count_red,
            count_blue = count_blue,
            chat_timeout = C.CHAT_TIMEOUT,
            is_practice = _is_practice(player),
            iteration = _iteration_num(player),
        )
    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        player.participant.vars['page_start_time'] = time()

# Decision 2 (after chat)
class Decision2(Page):
    form_model  = 'player'
    form_fields = ['decision2_choice', 'decision2_confidence', 'decision2_rt_ms']
    @staticmethod
    def is_displayed(player: Player):
        return _active(player) and not _is_practice(player)
    @staticmethod
    def vars_for_template(player: Player):
        return dict(
            color_pos = player.participant.color_pos,
            iteration = _iteration_num(player),
        )
    @staticmethod
    def error_message(player: Player, values):
        if not values.get('decision2_choice'):
            return 'どちらかの色を選択してください。'
        if values.get('decision2_confidence') is None:
            return '自信の程度を選択してください。'
    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        t0 = player.participant.vars.get('page_start_time')
        if t0:
            player.decision2_rt_ms = int((time() - t0) * 1000)
        player.participant.vars['latest_choice'] = player.decision2_choice or 'miss'
        player.participant.vars['last_confidence'] = player.decision2_confidence
        player.participant.vars[f'decision_making_round_{player.round_number}'] = (
            player.decision2_choice or 'miss'
        )
        idx = player.participant.vars['current_task_index']
        task = _current_task(player)
        choice = player.decision2_choice or 'miss'
        true_false = (1 if choice == task['answer'] else 0) if choice != 'miss' else None
        elapsed_ms = int((time() - t0) * 1000) if t0 else None
        player.participant.vars.setdefault(f'choice_task{idx}', [])
        player.participant.vars[f'choice_task{idx}'].append({
            'time_step':     _iteration_num(player),
            'choice':        choice,
            'true_false':    true_false,
            'confidence':    player.decision2_confidence,
            'time_spent_ms': elapsed_ms,
        })
        player.participant.vars['page_start_time'] = time()

# Wait for everyone to finish Decision 2 and check consensus
class Wait_Decision(WaitPage):
    title_text = '集計中...'
    body_text  = '全員の最終回答を集計しています。'
    @staticmethod
    def is_displayed(player: Player):
        return _active(player) and not _is_practice(player)
    @staticmethod
    def after_all_players_arrive(group: Group):
        players = group.get_players()
        round_n = players[0].round_number
        decisions = [
            p.participant.vars.get(f'decision_making_round_{round_n}', 'miss')
            for p in players
        ]
        consensus = (len(set(decisions)) == 1 and decisions[0] != 'miss')
        for p in players:
            p.participant.vars[f'is_finished_round_{round_n}'] = consensus
            p.is_consensus = consensus
        if not consensus:
            idx = players[0].participant.vars['current_task_index']
            for p in players:
                p.participant.vars[f'task{idx}_iter'] = (
                    p.participant.vars.get(f'task{idx}_iter', 1) + 1
                )

# Consensus result and feedback, and prepare for the next iteration or next task
class Consensus(Page):
    @staticmethod
    def is_displayed(player: Player):
        return (
            _active(player)
            and not _is_practice(player)
            and player.participant.vars.get(f'is_finished_round_{player.round_number}', False)
        )
    @staticmethod
    def vars_for_template(player: Player):
        task = _current_task(player)
        decision = player.participant.vars.get(f'decision_making_round_{player.round_number}', '')
        is_correct = decision == task['answer']
        return dict(
            decision = decision,
            answer = task['answer'],
            is_correct = is_correct,
            n_iters = _iteration_num(player),
        )
    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        idx = player.participant.vars['current_task_index']
        task = _current_task(player)
        decision = player.participant.vars.get(f'decision_making_round_{player.round_number}', '')
        is_correct = int(decision == task['answer'])
        player.participant.vars['correct_count'] += is_correct
        player.participant.vars['task_correct'].append(is_correct)
        player.participant.vars['current_task_index'] = idx + 1
        player.participant.vars[f'task{idx}_iter'] = 1
        player.participant.vars[f'is_finished_round_{player.round_number + 1}'] = False

# Result
class Results(Page):
    @staticmethod
    def is_displayed(player: Player):
        return not _active(player) and player.round_number > 1
    @staticmethod
    def vars_for_template(player: Player):
        return dict(
            total_questions = C.NUM_REAL_TASKS,
            correct_count = player.participant.vars.get('correct_count', 0),
            reward = player.participant.vars.get('correct_count', 0) * 100,
        )

# End of the experiment
class Finish(Page):
    @staticmethod
    def is_displayed(player: Player):
        return not _active(player) and player.round_number > 1

# This is the entire app
page_sequence = [
    Fullscreen,
    # Instruction,
    StartPractice,
    Task,
    Decision1,
    Wait_Chat,
    Chat,
    Decision2,
    Wait_Decision,
    Consensus,
    StartReal,
    Results,
    Finish,
]

# Custom export
def custom_export(players):
    yield [
        'participant_code', 'session_code', 'time_started_utc',
        'question_id',
        'order_id',
        'answer',
        'is_practice',
        'is_attention',
        'time_step',
        'choice',
        'true_false',
        'confidence',
        'time_spent_ms',
    ]
    for p in players:
        if p.round_number != C.NUM_ROUNDS:
            continue
        tasks = p.participant.vars.get('all_tasks', [])
        for idx, task in enumerate(tasks):
            choices = p.participant.vars.get(f'choice_task{idx}', [])
            for entry in choices:
                yield [
                    p.participant.code,
                    p.session.code,
                    p.participant.time_started_utc,
                    task.get('question_id', idx),
                    task.get('order_id',    idx + 1),
                    task.get('answer', ''),
                    task.get('is_practice',  False),
                    task.get('is_attention', False),
                    entry['time_step'],
                    entry['choice'],
                    entry['true_false'],
                    entry['confidence'],
                    entry.get('time_spent_ms', ''),
                ]
