from __future__ import annotations

import json
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Optional


def load_jsonl(path: Path, max_samples: Optional[int] = None) -> List[Dict]:
    if not path.exists():
        raise FileNotFoundError(path)
    out = []
    with path.open("r", encoding="utf-8") as fh:
        for i, line in enumerate(fh):
            if max_samples is not None and i >= max_samples:
                break
            s = line.strip()
            if not s:
                continue
            out.append(json.loads(s))
    return out


def normalize_tag(t: str) -> str:
    # tags like [aria:gesture:wave] -> normalized lowercased
    return t.strip().lower()


def evaluate_tags(
    dataset: Path,
    predictor: Callable[[str], Iterable[str]],
    max_samples: Optional[int] = None,
    top_k: Optional[int] = None,
) -> Dict:
    """Evaluate tag generation on a JSONL dataset.

    Each example must contain `'command'` and `'expected_tags'` (list).

    predictor should accept the natural-language command and return
    iterable of tags.
    """
    data = load_jsonl(dataset, max_samples=max_samples)

    tp = 0
    fp = 0
    fn = 0
    per_example = []

    for ex in data:
        cmd = ex.get("command", "")
        expected = ex.get("expected_tags", []) or ex.get("expected", [])
        expected_norm = {normalize_tag(t) for t in expected}

        preds_raw = list(predictor(cmd) or [])
        if top_k is not None:
            preds_raw = preds_raw[:top_k]
        preds = {normalize_tag(t) for t in preds_raw}

        tp_set = preds & expected_norm
        tp += len(tp_set)
        fp_set = preds - expected_norm
        fn_set = expected_norm - preds
        fp += len(fp_set)
        fn += len(fn_set)

        per_example.append({
            "command": cmd,
            "expected": list(sorted(expected_norm)),
            "predicted": list(sorted(preds)),
            "tp": list(sorted(tp_set)),
            "fp": list(sorted(fp_set)),
            "fn": list(sorted(fn_set)),
        })

    precision = tp / (tp + fp) if tp + fp > 0 else 0.0
    recall = tp / (tp + fn) if tp + fn > 0 else 0.0
    # f1 with guard against division by zero
    if precision + recall > 0:
        f1 = 2 * precision * recall / (precision + recall)
    else:
        f1 = 0.0

    return {
        "samples": len(data),
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "per_example": per_example,
    }


def compare_actions(expected: List[Dict], predicted: List[Dict]) -> bool:
    """Basic comparator for action sequences.

    This is strict equality in shape and order for now.
    """
    if not isinstance(expected, list) or not isinstance(predicted, list):
        return False
    if len(expected) != len(predicted):
        return False
    # Compare each action dict as JSON-serialized with sorted keys so
    # ordering of keys doesn't affect equality
    for e, p in zip(expected, predicted):
        try:
            if json.dumps(e, sort_keys=True) != json.dumps(p, sort_keys=True):
                return False
        except Exception:
            return False
    return True


def evaluate_actions(
    dataset: Path,
    parser: Callable[[str], List[Dict]],
    max_samples: Optional[int] = None,
) -> Dict:
    data = load_jsonl(dataset, max_samples=max_samples)
    total = len(data)
    exact_matches = 0
    per_example = []

    for ex in data:
        cmd = ex.get("command", "")
        expected = ex.get("expected_actions", [])
        predicted = parser(cmd)
        ok = compare_actions(expected, predicted)
        if ok:
            exact_matches += 1
        per_example.append({
            "command": cmd,
            "expected": expected,
            "predicted": predicted,
            "match": ok,
        })

    accuracy = exact_matches / total if total else 0.0
    return {
        "samples": total,
        "exact_matches": exact_matches,
        "accuracy": accuracy,
        "per_example": per_example,
    }


def fallback_tags_predictor(cmd: str):
    """Basic fallback predictor used when aria_web.server is not importable.

    This mirrors a small subset of generate_tags_fallback rules used in the
    server: detect wave/jump/say and return tags.
    """
    c = cmd.lower()
    tags = []
    if 'wave' in c:
        tags.append('[aria:gesture:wave]')
    if 'jump' in c:
        tags.append('[aria:animate:jump]')
    # say detection
    m = __import__('re').search(
        r'(?:say|announce|speak)[:\s]+(.+)$', cmd, flags=__import__('re').I
    )
    if m:
        text = m.group(1).strip()[:200]
        tags.append(f'[aria:say:{text}]')
        if any(w in text.lower() for w in ['hello', 'hi', '!']):
            tags.append('[aria:expression:happy]')
    return tags


def fallback_action_parser(cmd: str) -> List[Dict]:
    """Small action parser used in tests when server parser is not available.

    Currently supports move->pickup pattern for known objects.
    """
    c = cmd.lower()
    actions: List[Dict] = []
    objects = {
        'apple': {'position': {'x': 55, 'y': 35}},
        'book': {'position': {'x': 48, 'y': 35}},
        'cup': {'position': {'x': 62, 'y': 35}},
        'ball': {'position': {'x': 70, 'y': 35}},
        'flower': {'position': {'x': 52, 'y': 35}},
    }

    if any(k in c for k in ['pick', 'grab', 'take', 'get']):
        for obj in objects:
            if obj in c:
                actions.append(
                    {
                        'action': 'move',
                        'target': objects[obj]['position'],
                        'speed': 'normal',
                    }
                )
                actions.append({'action': 'pickup', 'object_id': obj})
                break
    return actions
