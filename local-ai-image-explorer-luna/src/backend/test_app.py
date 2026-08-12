from app import prompt_variation, resolve_seed, validate


def test_empty_seed_is_random_and_explicit_seed_is_preserved():
    first = resolve_seed(None)
    second = resolve_seed(None)
    assert first != 0 and second != 0 and first != second
    assert resolve_seed('') != 0
    assert validate({'prompt': 'x', 'seed': 42})[3] == 42

def test_creativity_is_ordered():
    base='a tree'; remixes=['glass cathedral']
    values=[prompt_variation(base, remixes, x, 1) for x in ('mild','normal','wild')]
    assert values[0] != values[1] != values[2]

def test_validation_defaults_and_rejects_empty():
    assert validate({'prompt':'x'})[1:3] == (512,512)
    try: validate({'prompt':' '})
    except ValueError: pass
    else: assert False
