from pathlib import Path

from scripts.eval.evaluator import evaluate_tags, evaluate_actions


def test_evaluate_tags_fallback():
    ds = Path('tests/evaluation/data/tags_test.jsonl')
    # prefer server implementation when available but fall back to local one
    try:
        from aria_web.server import generate_tags_fallback as server_tags
    except (ImportError, SyntaxError):
        server_tags = None

    from scripts.eval.evaluator import fallback_tags_predictor

    predictor = server_tags or fallback_tags_predictor

    res = evaluate_tags(ds, predictor)
    assert res['samples'] == 3
    # fallback should match expected tags in our small dataset
    assert res['f1'] == 1.0


def test_evaluate_actions_fallback():
    ds = Path('tests/evaluation/data/actions_test.jsonl')
    try:
        from aria_web.server import AriaActionParser as ServerParser
    except (ImportError, SyntaxError):
        ServerParser = None

    from scripts.eval.evaluator import fallback_action_parser

    if ServerParser is not None:
        parser = ServerParser()
        parse_fn = parser.parse
    else:
        parse_fn = fallback_action_parser

    res = evaluate_actions(ds, parse_fn)
    assert res['samples'] == 1
    assert res['accuracy'] == 1.0
