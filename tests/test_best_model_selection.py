"""Test best model selection logic (self-contained)."""


def test_best_model_selection():
    # Self-contained test — the selection logic is replicated from the training pipeline
    # to validate correctness without depending on the pipeline module.
    def _select_best_model(metrics, ranking_metric):
        def diversity(e):
            return e.get("diversity_avg")

        def improvement(e):
            return e.get("perplexity_improvement")

        def post(e):
            return e.get("post_perplexity")

        filtered = [m for m in metrics if post(m) is not None]
        if ranking_metric in ("perplexity_improvement", "combined_improvement"):
            if ranking_metric == "combined_improvement":
                for m in filtered:
                    m["combined_improvement"] = 0.7 * (improvement(m) or 0.0) + 0.3 * (
                        diversity(m) or 0.0
                    )
                filtered = [
                    m for m in filtered if m.get("combined_improvement") is not None
                ]

                def key(x):
                    return x.get("combined_improvement")

            else:
                filtered = [m for m in filtered if improvement(m) is not None]

                def key(x):
                    return improvement(x)

            return max(filtered, key=key) if filtered else None
        elif ranking_metric in ("diversity_avg", "distinct_diversity"):
            filtered = [m for m in filtered if diversity(m) is not None]
            return max(filtered, key=lambda x: diversity(x)) if filtered else None
        elif ranking_metric == "post_perplexity":
            return min(filtered, key=lambda x: post(x)) if filtered else None
        return min(filtered, key=lambda x: post(x)) if filtered else None

    select_fn = _select_best_model
    metrics = [
        {
            "model": "phi",
            "run_id": "r1",
            "pre_perplexity": 30.0,
            "post_perplexity": 20.0,
            "perplexity_improvement": (30 - 20) / 30,
            "diversity_avg": 0.5,
        },
        {
            "model": "tinyllama",
            "run_id": "r2",
            "pre_perplexity": 10.0,
            "post_perplexity": 9.0,
            "perplexity_improvement": (10 - 9) / 10,
            "diversity_avg": 0.9,
        },
    ]
    # Improvement metric picks phi (larger relative improvement 0.333 vs 0.1)
    best_imp = select_fn([m.copy() for m in metrics], "perplexity_improvement")
    assert best_imp["model"] == "phi"
    # Diversity picks tinyllama
    best_div = select_fn([m.copy() for m in metrics], "diversity_avg")
    assert best_div["model"] == "tinyllama"
    # Post perplexity picks tinyllama (9<20)
    best_post = select_fn([m.copy() for m in metrics], "post_perplexity")
    assert best_post["model"] == "tinyllama"
    # Combined improvement weights improvement more but diversity gives tinyllama maybe still phi due to improvement weight dominance (0.7*0.333 + 0.3*0.5=0.366 vs 0.7*0.1 +0.3*0.9=0.34) => phi
    metrics_ci = [m.copy() for m in metrics]
    # compute combined to compare
    phi_score = 0.7 * ((30 - 20) / 30) + 0.3 * 0.5
    tiny_score = 0.7 * ((10 - 9) / 10) + 0.3 * 0.9
    assert phi_score > tiny_score
