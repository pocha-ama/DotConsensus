from otree.api import *
import string, json, random
from time import time
import numpy as np
from dot_consensus.experiment_settings import DOT2_CONSTANTS
from dot_consensus.task_config import PILOT_TASKS
from dot_consensus import stimulus_gen

doc = 'Dot Consensus Experiment (Kuroda et al. 2025 stimulus x consensus loop)'

# constants
class C(BaseConstants):
    NAME_IN_URL = 'dot_consensus'
    PLAYERS_PER_GROUP = 5
    NUM_ROUNDS = 1000

    NUM_PRACTICE_TASKS = 1
    NUM_NORMAL_TASKS = len(PILOT_TASKS)        # 12問のパイロット構成
    NUM_ATTENTION_CHECKS = 0                    # パイロットではアテンションチェックなし
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

# ── 刺激生成: 課題タイプ別にディスパッチ（stimulus_gen.py に委譲） ──────────────
def _generate_stimulus(task: dict) -> dict:
    """task（task_type を含む dict）に応じた刺激パラメータ dict を返す。"""
    return stimulus_gen.generate_stimulus(task, C)


# ── 練習問題の定義 ──────────────────────────────────────────────────────────
#  パイロットでは練習をドット課題1問とする（参加者が操作に慣れるため）。
PRACTICE_TASKS = [
    dict(task_type='dot', choice_type='redblue', can_review=False, answer='red'),
]


# ── 出題順の生成: 練習 + 本番12問（PILOT_TASKS） ──────────────────────────────
#  PILOT_TASKS は「ドット2→ガボール2→RDK4→avg4」という課題ブロック順序を
#  そのまま用いる（課題タイプを比較する目的なのでブロック提示が自然）。
#  セッション内で固定の順序を使う。
def _generate_answer_sequence() -> list:
    tasks = []
    # 練習問題
    for i, pt in enumerate(PRACTICE_TASKS[:C.NUM_PRACTICE_TASKS]):
        tasks.append({
            **pt,
            'question_id': 0,
            'task_index': i,
            'is_practice': True,
            'is_attention': False,
        })
    # 本番問題
    if len(PILOT_TASKS) > 0:
        tasks_with_qid = []
        for j, pt in enumerate(PILOT_TASKS):
            tasks_with_qid.append({
                **pt,
                'question_id': j + 1,
                'task_index': C.NUM_PRACTICE_TASKS + j,
                'is_practice': False,
                'is_attention': False,
            })
        grouped_by_type = {}
        for task in tasks_with_qid:
            task_type = task['task_type']
            if task_type not in grouped_by_type:
                grouped_by_type[task_type] = []
            grouped_by_type[task_type].append(task)
        for task_type in grouped_by_type:
            random.shuffle(grouped_by_type[task_type])
        task_types = list(grouped_by_type.keys())
        random.shuffle(task_types)
        for task_type in task_types:
            tasks.extend(grouped_by_type[task_type])
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
                stim = _generate_stimulus(info)
                group_tasks.append({**info, **stim})
            for order_id, task in enumerate(group_tasks, start=1):
                task['order_id'] = order_id
            gkey = f'group_{g.id_in_subsession}_tasks'
            subsession.session.vars[gkey] = group_tasks
            ## nickname map for chat (rank-based, shuffled each round)
            nickname_maps = [{} for _ in players]
            for task_idx in range(len(group_tasks)):
                perm = list(range(len(players)))
                random.shuffle(perm)
                for rank, pidx in enumerate(perm):
                    nickname_maps[pidx][task_idx] = f'{rank + 1}番さん'
            for i, p in enumerate(players):
                p.participant.vars['group_task_key'] = gkey
                p.participant.vars['num_tasks'] = len(group_tasks)
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
# get the list of all tasks for the player's group
def _get_tasks(player: Player) -> list:
    key = player.participant.vars.get('group_task_key', '')
    return player.session.vars.get(key, [])

# check if the current task is active, practice, and to get the current task info
def _active(player: Player) -> bool:
    idx = player.participant.vars.get('current_task_index', 0)
    return idx < player.participant.vars.get('num_tasks', 0)

# check if the current task is an attention check
def _is_practice(player: Player) -> bool:
    idx   = player.participant.vars.get('current_task_index', 0)
    tasks = _get_tasks(player)
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
    tasks = _get_tasks(player)
    return tasks[idx]

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
            next_task_idx = idx + 1
            tasks = _get_tasks(player)
            next_task = tasks[next_task_idx] if next_task_idx < len(tasks) else {}
            task_type = next_task.get('task_type', 'unknown')
        else:
            next_real_num = idx - C.NUM_PRACTICE_TASKS + 1
            task = _current_task(player)
            task_type = task.get('task_type', 'unknown')
        return dict(
            task_num           = next_real_num,
            num_real           = C.NUM_REAL_TASKS,
            is_practice_ending = _is_practice(player),
            task_type          = task_type,
        )

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        if _is_practice(player):
            idx = player.participant.vars['current_task_index']
            player.participant.vars['current_task_index'] = idx + 1
            player.participant.vars[f'task{idx}_iter'] = 1
            player.participant.vars[f'is_finished_round_{player.round_number}'] = True


# ITI + trial
# 刺激描画用 js_vars を課題タイプ別に組み立てる共通ヘルパー
#  Task ページと（参照可能な課題の）Chat ポップアップの両方で使う。
def _stim_js_vars(player: Player, task: dict) -> dict:
    base = dict(
        task_type   = task['task_type'],
        choice_type = task['choice_type'],
        color_pos   = player.participant.color_pos,
        seed        = task.get('seed', ''),
        fps         = C.FPS,
        time_limit  = C.TIME_LIMIT,
    )
    t = task['task_type']
    if t == 'dot':
        base.update(
            n_dots = C.N_DOTS,
            n_red  = task.get('n_red', '[]'),
            n_blue = task.get('n_blue', '[]'),
        )
    elif t == 'gabor':
        base.update(
            oddball_interval = task.get('oddball_interval', 1),
            oddball_position = task.get('oddball_position', 0),
            oddball_contrast = task.get('oddball_contrast', 3.5),
            base_contrast    = task.get('base_contrast', 10.0),
            n_patches        = task.get('n_patches', 6),
        )
    elif t == 'rdk':
        base.update(
            direction  = task.get('direction', 'right'),
            coherence  = task.get('coherence', 10.0),
            n_dots     = task.get('n_dots', 200),
            dot_radius = task.get('dot_radius', 2),
            dot_speed  = task.get('dot_speed', 2),
        )
    elif t == 'avg':
        base.update(
            colors     = task.get('colors', '[]'),
            n_elements = task.get('n_elements', 8),
        )
    return base


class Task(Page):
    form_model = 'player'
    form_fields = ['taskdata']
    ## Pass the coherence and answer to the JavaScript file
    @staticmethod
    def is_displayed(player: Player):
        return _is_new_task(player)
    @staticmethod
    def js_vars(player: Player):
        return _stim_js_vars(player, _current_task(player))
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
            choice_type  = task['choice_type'],
            task_type    = task['task_type'],
        )
    @staticmethod
    def error_message(player: Player, values):
        if not values.get('decision1_choice'):
            return '選択肢のいずれかを選んでください。'
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
        task = _current_task(player)
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
        # choice_type に応じた2択ラベルと集計
        ctype = task['choice_type']
        if ctype == 'redblue':
            opt_a, opt_b = 'red', 'blue'
        elif ctype == 'leftright':
            opt_a, opt_b = 'left', 'right'
        else:  # interval
            opt_a, opt_b = 'first', 'second'
        count_a = sum(1 for d in decisions if d['choice'] == opt_a)
        count_b = sum(1 for d in decisions if d['choice'] == opt_b)
        # 表示ラベル（choice_type ごと）
        label_map = {
            'red': 'RED', 'blue': 'BLUE',
            'left': 'LEFT', 'right': 'RIGHT',
            'first': 'FIRST', 'second': 'SECOND',
        }
        my_choice_raw = player.participant.vars.get('latest_choice', '')
        return dict(
            nickname = nickname,
            my_choice = my_choice_raw,
            my_choice_label = label_map.get(my_choice_raw, '—'),
            decisions = decisions,
            decisions_json = json.dumps(decisions),
            choice_type = ctype,
            opt_a = opt_a, opt_b = opt_b,
            opt_a_label = label_map.get(opt_a, opt_a),
            opt_b_label = label_map.get(opt_b, opt_b),
            count_a = count_a, count_b = count_b,
            # 後方互換（テンプレートが count_red/count_blue を参照している場合）
            count_red = count_a if ctype == 'redblue' else 0,
            count_blue = count_b if ctype == 'redblue' else 0,
            can_review = task.get('can_review', False),
            task_type = task['task_type'],
            chat_timeout = C.CHAT_TIMEOUT,
            is_practice = _is_practice(player),
            iteration = _iteration_num(player),
        )
    @staticmethod
    def js_vars(player: Player):
        task = _current_task(player)
        # 参照可能な課題のみ刺激パラメータを渡す（参照不可なら最小限）
        if task.get('can_review', False):
            v = _stim_js_vars(player, task)
            v['can_review'] = True
            return v
        return dict(can_review=False, task_type=task['task_type'])
    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        player.participant.vars['page_start_time'] = time()

class PreTask2(Page):
    @staticmethod
    def is_displayed(player: Player):
        return _active(player) and not _is_practice(player)

class Task2(Page):
    form_model = 'player'
    form_fields = ['taskdata']
    @staticmethod
    def is_displayed(player: Player):
        return _active(player) and not _is_practice(player)
    @staticmethod
    def js_vars(player: Player):
        return _stim_js_vars(player, _current_task(player))
    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        player.participant.vars['page_start_time'] = time()

class Decision2(Page):
    form_model  = 'player'
    form_fields = ['decision2_choice', 'decision2_confidence', 'decision2_rt_ms']
    @staticmethod
    def is_displayed(player: Player):
        return _active(player) and not _is_practice(player)
    @staticmethod
    def vars_for_template(player: Player):
        task = _current_task(player)
        return dict(
            color_pos   = player.participant.color_pos,
            iteration   = _iteration_num(player),
            choice_type = task['choice_type'],
            task_type   = task['task_type'],
        )
    @staticmethod
    def error_message(player: Player, values):
        if not values.get('decision2_choice'):
            return '選択肢のいずれかを選んでください。'
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
            decision    = decision,
            answer      = task['answer'],
            is_correct  = is_correct,
            n_iters     = _iteration_num(player),
            choice_type = task['choice_type'],   # ← 追加
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
    Instruction,
    Wait_Instruction,
    StartPractice,
    Task,
    Decision1,
    Wait_Chat,
    Chat,
    PreTask2,
    Task2,
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
        'task_type',
        'can_review',
        'answer',
        'is_attention',
        'time_step',
        'choice',
        'true_false',
        'confidence',
        'time_spent_ms',
    ]
    for p in players:
        if p.round_number == 1:
            key = p.participant.vars.get('group_task_key', '')
            tasks = p.session.vars.get(key, [])
            for idx, task in enumerate(tasks):
                choices = p.participant.vars.get(f'choice_task{idx}', [])
                for entry in choices:
                    yield [
                        p.participant.code,
                        p.session.code,
                        p.participant.time_started_utc,
                        task.get('question_id', idx),
                        task.get('order_id',    idx + 1),
                        task.get('task_type', ''),
                        task.get('can_review', False),
                        task.get('answer', ''),
                        task.get('is_attention', False),
                        entry['time_step'],
                        entry['choice'],
                        entry['true_false'],
                        entry['confidence'],
                        entry.get('time_spent_ms', ''),
                    ]