PILOT_TASKS = [
    dict(task_type='dot', choice_type='redblue', can_review=False, answer='red',  mean_diff=4),
    dict(task_type='dot', choice_type='redblue', can_review=False, answer='blue', mean_diff=3),
    dict(task_type='dot', choice_type='redblue', can_review=False, answer='red',  mean_diff=2),

    dict(task_type='gabor', choice_type='interval', can_review=False, answer='first',  difficulty=5.0),
    dict(task_type='gabor', choice_type='interval', can_review=False, answer='second', difficulty=3.5),
    dict(task_type='gabor', choice_type='interval', can_review=False, answer='first',  difficulty=2.0),

    dict(task_type='rdk', choice_type='leftright', can_review=False, answer='right', coherence=7.0),
    dict(task_type='rdk', choice_type='leftright', can_review=False, answer='left',  coherence=5.0),
    dict(task_type='rdk', choice_type='leftright', can_review=False, answer='right', coherence=3.0),

    dict(task_type='avg', choice_type='redblue', can_review=False, answer='red',  mean_shift=0.16, sigma=0.45),
    dict(task_type='avg', choice_type='redblue', can_review=False, answer='blue', mean_shift=0.12, sigma=0.50),
    dict(task_type='avg', choice_type='redblue', can_review=False, answer='red',  mean_shift=0.08, sigma=0.55),
]