import json
from pathlib import Path

from scripts.parallel_train import ParallelTrainer
from scripts.auto_data_train import create_training_config


def _make_temp_config(tmp_path: Path) -> Path:
    p = tmp_path / "config.yaml"
    p.write_text("jobs: []\n", encoding="utf-8")
    return p


def test_distinct_diversity_alias(tmp_path):
    """distinct_diversity should behave identically to diversity_avg regarding score & ordering."""
    cfg = _make_temp_config(tmp_path)
    trainer_div = ParallelTrainer(str(cfg), ranking_metric="diversity_avg")
    trainer_alias = ParallelTrainer(str(cfg), ranking_metric="distinct_diversity")
    mock_results = [
        {"name": "jobA", "status": "succeeded", "evaluation": {"diversity": {"distinct_1": 0.5, "distinct_2": 0.7}}},
        {"name": "jobB", "status": "succeeded", "evaluation": {"diversity": {"distinct_1": 0.6, "distinct_2": 0.8}}},
    ]
    rank_div = trainer_div._compute_ranking(mock_results)
    rank_alias = trainer_alias._compute_ranking(mock_results)
    assert rank_div and rank_alias, "Ranking lists should not be empty"
    # Both should sort with jobB first due to higher diversity avg (0.7 vs 0.6)
    assert rank_div[0]["name"] == rank_alias[0]["name"] == "jobB"
    assert rank_div[0]["score"] == rank_alias[0]["score"]
    assert rank_alias[0]["metric"] == "distinct_diversity"


def test_unknown_metric_fallback(tmp_path):
    """Unknown metric should fallback to post perplexity (negative for sorting)."""
    cfg = _make_temp_config(tmp_path)
    trainer = ParallelTrainer(str(cfg), ranking_metric="totally_unknown_metric")
    mock_results = [
        {"name": "jobLowPPL", "status": "succeeded", "evaluation": {"pre_eval_perplexity": 10.0, "post_eval_perplexity": 5.0}},
        {"name": "jobHighPPL", "status": "succeeded", "evaluation": {"pre_eval_perplexity": 10.0, "post_eval_perplexity": 7.0}},
    ]
    ranking = trainer._compute_ranking(mock_results)
    assert ranking[0]["name"] == "jobLowPPL", "Lower post perplexity should rank higher via fallback"
    # Score comparison (stored negative)
    assert ranking[0]["score"] > ranking[1]["score"]


def test_tinyllama_config_generation(tmp_path):
    """Ensure tinyllama branch populates correct HF model id in config file."""
    ds_dir = tmp_path / "dataset"
    ds_dir.mkdir()
    config_path, job_name = create_training_config(ds_dir, "testtoken", "tinyllama")
    text = Path(config_path).read_text(encoding="utf-8")
    assert "TinyLlama/TinyLlama-1.1B-Chat-v1.0" in text
    assert "job_name" not in text  # ensure raw YAML style remains identical to other configs
    assert job_name.startswith("tinyllama_ultra")
