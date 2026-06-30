import string, json, random
import numpy as np

def _rand_seed(n: int = 20) -> str:
    return ''.join(random.sample(string.ascii_letters, n))

def gen_dot(answer: str, is_attention: bool, C, mean_diff: float = None) -> dict:
    if is_attention:
        mean = 30 if answer == 'red' else -30
    else:
        base = mean_diff if mean_diff is not None else C.MEAN
        mean = base if answer == 'red' else -base
    diff_dots = np.random.normal(mean, C.SIGMA, C.FPS*C.TIME_LIMIT)
    for i in range(len(diff_dots)):
        if diff_dots[i] % 2 < 1:
            diff_dots[i] = (diff_dots[i] // 2) * 2
        else:
            diff_dots[i] = (diff_dots[i] // 2) * 2 + 2
    red_dots = (C.N_DOTS + diff_dots) / 2
    n_red = json.dumps(list(red_dots.astype(np.float64)))
    n_blue = json.dumps(list(C.N_DOTS - np.array(json.loads(n_red))))
    return dict(n_red=n_red, n_blue=n_blue, seed=_rand_seed())

def gen_gabor(answer: str, difficulty: float = 5.0) -> dict:
    oddball_interval = 1 if answer == 'first' else 2
    oddball_position = random.randint(0, 5)
    return dict(
        oddball_interval=oddball_interval,
        oddball_position=oddball_position,
        oddball_contrast=difficulty,
        base_contrast=10,
        n_patches=6,
        seed=_rand_seed(),
    )

def gen_rdk(answer: str, coherence: float = 20.0) -> dict:
    return dict(
        direction=answer, coherence=coherence,
        n_dots=200, dot_radius=2, dot_speed=3, seed=_rand_seed(),
    )

def gen_avg(answer: str, mean_shift: float = 0.16, sigma: float = 0.45, n_elements: int = 8) -> dict:
    mu = mean_shift if answer == 'red' else -mean_shift
    vals = np.random.normal(mu, sigma, n_elements)
    vals = np.clip(vals, -1.0, 1.0)
    if (answer == 'red' and vals.mean() <= 0) or (answer == 'blue' and vals.mean() >= 0):
        vals[0] = mu * 2
        vals = np.clip(vals, -1.0, 1.0)
    return dict(
        colors=json.dumps(list(vals.astype(np.float64))),
        mean_color=answer, n_elements=n_elements, seed=_rand_seed(),
    )

def generate_stimulus(task: dict, C) -> dict:
    t = task['task_type']
    ans = task['answer']
    is_attn = task.get('is_attention', False)
    if t == 'dot':
        return gen_dot(ans, is_attn, C, task.get('mean_diff'))
    elif t == 'gabor':
        return gen_gabor(ans, task.get('difficulty', 5.0))
    elif t == 'rdk':
        return gen_rdk(ans, task.get('coherence', 20.0))
    elif t == 'avg':
        return gen_avg(ans, task.get('mean_shift', 0.16), task.get('sigma', 0.45))
    else:
        raise ValueError(f'unknown task_type: {t}')