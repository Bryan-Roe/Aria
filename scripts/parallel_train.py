"""
Parallel training launcher - runs multiple training jobs concurrently
Optimized for maximum throughput on multi-GPU or multi-CPU systems
"""
import argparse
import asyncio
import json
import math
import shutil
import os
import subprocess
import sys
import yaml
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

###############################################
# Parallel Training Orchestrator Enhancements #
# - Historical run append mode for status.json #
# - Min train samples safety guard             #
# - Post-training evaluation (perplexity + gen)#
# - Qwen compatibility via config HF id        #
###############################################

class ParallelTrainer:
    """Manages parallel execution of training jobs with evaluation & safety guards."""

    def __init__(
        self,
        config_path: str,
        max_parallel: int = 3,
        min_train_samples: Optional[int] = None,
        generate_samples: int = 3,
        perform_evaluation: bool = True,
        cleanup: bool = False,
        ranking_metric: str = "perplexity_improvement",
    ):
        """Initialize parallel trainer.

        Args:
            config_path: Path to autotrain YAML config
            max_parallel: Maximum concurrent jobs (default: 3)
            min_train_samples: Skip training if counted train samples below this threshold
            generate_samples: Number of sample generations for post-training evaluation
        """
        self.config_path = Path(config_path)
        self.max_parallel = max_parallel
        self.min_train_samples = min_train_samples
        self.generate_samples = generate_samples
        self.root = Path(__file__).parent.parent
        self.venv_python = self.root / "AI/microsoft_phi-silica-3.6_v1/venv/Scripts/python.exe"
        self.train_script = self.root / "AI/microsoft_phi-silica-3.6_v1/scripts/train_lora.py"
        self.perform_evaluation = perform_evaluation
        self.cleanup = cleanup
        self.ranking_metric = ranking_metric

        # Load config
        with open(self.config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f) or {}

        self.jobs = self.config.get('jobs', [])
        self.results: List[Dict[str, Any]] = []
    
    async def run_job(self, job: Dict[str, Any], device_id: int) -> Dict[str, Any]:
        """
        Run a single training job.
        
        Args:
            job: Job configuration
            device_id: GPU/CPU device ID for this job
            
        Returns:
            Job result with status and timing
        """
        job_name = job['name']
        start_time = datetime.now()
        
        print(f"\n[{job_name}] Starting on device {device_id}")
        
        # Resolve dataset path & gather dataset stats (best effort)
        raw_dataset_path = job['dataset']
        ds_path = Path(raw_dataset_path)
        if not ds_path.is_absolute():
            ds_path = self.root / ds_path

        train_count = None
        test_count = None
        try:
            if ds_path.is_dir():
                # Look for train/test files - use efficient binary read for line counting
                for candidate, attr in [("train.json", "train"), ("train.jsonl", "train"),
                                        ("test.json", "test"), ("test.jsonl", "test")]:
                    fpath = ds_path / candidate
                    if fpath.exists():
                        # Efficient line counting using binary mode and buffer
                        line_count = 0
                        with open(fpath, 'rb') as f:
                            # Read in 64KB chunks for better I/O performance
                            buf_size = 65536
                            read_f = f.read
                            buf = read_f(buf_size)
                            while buf:
                                # Count non-empty lines by checking for content
                                line_count += buf.count(b'\n')
                                buf = read_f(buf_size)
                        if attr == "train":
                            train_count = (train_count or 0) + line_count
                        else:
                            test_count = (test_count or 0) + line_count
            elif ds_path.is_file():
                # Efficient line counting for single files
                line_count = 0
                with open(ds_path, 'rb') as f:
                    buf_size = 65536
                    read_f = f.read
                    buf = read_f(buf_size)
                    while buf:
                        line_count += buf.count(b'\n')
                        buf = read_f(buf_size)
                train_count = line_count
        except Exception as ds_err:
            print(f"[{job_name}] Warning: failed counting dataset samples: {ds_err}")

        # Safety guard: skip if insufficient train samples
        if self.min_train_samples is not None and train_count is not None and train_count < self.min_train_samples:
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            result = {
                'name': job_name,
                'status': 'skipped',
                'reason': f'insufficient_train_samples (<{self.min_train_samples})',
                'device': device_id,
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'duration_seconds': duration,
                'log_file': None,
                'output_dir': job['save_dir'],
                'dataset_path': str(ds_path),
                'dataset_train_samples': train_count,
                'dataset_test_samples': test_count,
            }
            print(f"[{job_name}] ⚠ Skipping training: train_samples={train_count} < {self.min_train_samples}")
            return result

        # Build command for actual training
        cmd = [
            str(self.venv_python),
            str(self.train_script),
            "--config", job.get('config', 'AI/microsoft_phi-silica-3.6_v1/lora/lora.yaml'),
            "--dataset", job['dataset'],
            "--save-dir", job['save_dir'],
            "--epochs", str(job.get('epochs', 1)),
            "--learning-rate", str(job.get('learning_rate', 0.0002)),
            "--lora-dropout", str(job.get('lora_dropout', 0.1)),
            "--hf-model-id", job['hf_model_id'],
            "--device", "auto"  # Use auto device selection
        ]
        
        # Set CUDA_VISIBLE_DEVICES for device isolation
        env = dict(os.environ)
        if device_id >= 0:
            env['CUDA_VISIBLE_DEVICES'] = str(device_id)
        
        if job.get('max_train_samples'):
            cmd.extend(["--max-train-samples", str(job['max_train_samples'])])
        if job.get('max_eval_samples'):
            cmd.extend(["--max-eval-samples", str(job['max_eval_samples'])])
        # Note: lora_rank should be set in config YAML, not via CLI
        if job.get('no_stream'):
            cmd.append("--no-stream")
        
        # Create output directory
        output_dir = self.root / "data_out/parallel_training" / job_name / start_time.strftime("%Y%m%dT%H%M%SZ")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        log_file = output_dir / "stdout.log"
        
        # Run job
        try:
            with open(log_file, 'w', encoding='utf-8') as f:
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=f,
                    stderr=asyncio.subprocess.STDOUT,
                    cwd=str(self.root),
                    env=env
                )
                returncode = await process.wait()

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            result: Dict[str, Any] = {
                'name': job_name,
                'status': 'succeeded' if returncode == 0 else 'failed',
                'return_code': returncode,
                'device': device_id,
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'duration_seconds': duration,
                'log_file': str(log_file),
                'output_dir': job['save_dir'],
                'dataset_path': str(ds_path),
                'dataset_train_samples': train_count,
                'dataset_test_samples': test_count,
            }

            print(f"[{job_name}] {'✓' if returncode == 0 else '✗'} Completed in {duration:.1f}s")

            # Post-training evaluation (only if succeeded)
            if returncode == 0:
                # Artifact paths
                adapter_dir = self.root / job['save_dir'] / 'lora_adapter'
                tokenizer_dir = self.root / job['save_dir'] / 'tokenizer'
                result['adapter_dir'] = str(adapter_dir)
                result['tokenizer_dir'] = str(tokenizer_dir)
                if self.perform_evaluation:
                    eval_data = self._perform_evaluation(job, result)
                    if eval_data:
                        result['evaluation'] = eval_data
                else:
                    result['evaluation'] = None
                if self.cleanup:
                    self._perform_cleanup(job, result)

        except Exception as e:
            result = {
                'name': job_name,
                'status': 'error',
                'error': str(e),
                'device': device_id,
                'start_time': start_time.isoformat(),
                'log_file': str(log_file),
                'dataset_path': str(ds_path),
                'dataset_train_samples': train_count,
                'dataset_test_samples': test_count,
            }
            print(f"[{job_name}] ✗ Error: {e}")

        return result

    def _perform_evaluation(self, job: Dict[str, Any], result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Quick evaluation: parse metrics.jsonl & generate sample outputs.

        Returns evaluation dict or None if unavailable.
        """
        save_dir = self.root / job['save_dir']
        metrics_file = save_dir / 'metrics.jsonl'
        eval_info: Dict[str, Any] = {}

        # Parse metrics file for pre/post perplexity
        try:
            if metrics_file.exists():
                pre_ppl = post_ppl = None
                pre_loss = post_loss = None
                with metrics_file.open('r', encoding='utf-8') as mf:
                    for line in mf:
                        line = line.strip()
                        if not line:
                            continue
                        rec = json.loads(line)
                        phase = rec.get('phase')
                        if phase == 'pre':
                            pre_loss = rec.get('eval_loss')
                            pre_ppl = rec.get('eval_perplexity') or (math.e ** rec.get('eval_loss', 0))
                        elif phase == 'post':
                            post_loss = rec.get('eval_loss')
                            post_ppl = rec.get('eval_perplexity') or (math.e ** rec.get('eval_loss', 0))
                if pre_loss is not None:
                    eval_info['pre_eval_loss'] = pre_loss
                if pre_ppl is not None:
                    eval_info['pre_eval_perplexity'] = pre_ppl
                if post_loss is not None:
                    eval_info['post_eval_loss'] = post_loss
                if post_ppl is not None:
                    eval_info['post_eval_perplexity'] = post_ppl
        except Exception as m_err:
            eval_info['metrics_error'] = f"metrics_parse_failed: {m_err}"

        # Sample generations (best effort)
        prompts = [
            "Hello! Provide a concise helpful assistant greeting.",
            "Explain one optimization used in ultrafast fine-tuning.",
            "Summarize the purpose of this training run in one sentence.",
            "List two potential risks in rapid fine-tuning.",
            "Give one improvement suggestion for dataset quality.",
        ]
        samples: List[Dict[str, Any]] = []
        if self.generate_samples > 0:
            try:
                from transformers import AutoTokenizer, AutoModelForCausalLM  # type: ignore
                from peft import PeftModel  # type: ignore
                base_model_id = job.get('hf_model_id')
                adapter_dir = save_dir / 'lora_adapter'
                if adapter_dir.exists():
                    tokenizer = AutoTokenizer.from_pretrained(base_model_id, use_fast=True)
                    if tokenizer.pad_token is None:
                        tokenizer.pad_token = tokenizer.eos_token
                    base_model = AutoModelForCausalLM.from_pretrained(base_model_id)
                    model = PeftModel.from_pretrained(base_model, str(adapter_dir))
                    model.eval()
                    import torch
                    for p in prompts[: self.generate_samples]:
                        try:
                            inputs = tokenizer(p, return_tensors='pt')
                            with torch.no_grad():
                                output_ids = model.generate(**inputs, max_new_tokens=80, do_sample=True, temperature=0.8, top_p=0.9)
                            gen_text = tokenizer.decode(output_ids[0], skip_special_tokens=True)
                            samples.append({'prompt': p, 'response': gen_text})
                        except Exception as gen_err:
                            samples.append({'prompt': p, 'error': str(gen_err)})
                else:
                    eval_info['generation_note'] = 'adapter_dir_missing; skipping sample generation'
            except Exception as g_err:
                eval_info['generation_error'] = f"generation_failed: {g_err}"
        if samples:
            # Diversity metrics (Distinct-1/2) & echo ratio
            def _distinct_1_2(texts: List[str]) -> Dict[str, float]:
                unigrams_total = 0
                unigrams_set = set()
                bigrams_total = 0
                bigrams_set = set()
                for t in texts:
                    toks = t.split()
                    unigrams_total += len(toks)
                    unigrams_set.update(toks)
                    bgs = list(zip(toks, toks[1:]))
                    bigrams_total += len(bgs)
                    bigrams_set.update(bgs)
                d1 = len(unigrams_set) / unigrams_total if unigrams_total else 0.0
                d2 = len(bigrams_set) / bigrams_total if bigrams_total else 0.0
                return {'distinct_1': d1, 'distinct_2': d2}

            def _echo_ratio(prompt: str, response: str) -> float:
                p_tokens = prompt.lower().split()
                r_tokens = response.lower().split()
                if not r_tokens:
                    return 0.0
                overlap = sum(1 for t in r_tokens if t in p_tokens)
                return overlap / len(r_tokens)

            responses = [s.get('response', '') for s in samples]
            diversity = _distinct_1_2(responses)
            avg_len = sum(len(r.split()) for r in responses) / len(responses) if responses else 0.0
            echo_scores = [ _echo_ratio(s['prompt'], s.get('response','')) for s in samples ]
            eval_info['samples'] = samples
            eval_info['diversity'] = {
                'distinct_1': diversity['distinct_1'],
                'distinct_2': diversity['distinct_2'],
                'avg_response_tokens': avg_len,
                'avg_echo_ratio': sum(echo_scores)/len(echo_scores) if echo_scores else 0.0,
            }
        return eval_info or None

    def _perform_cleanup(self, job: Dict[str, Any], result: Dict[str, Any]) -> None:
        """Remove intermediate checkpoints to slim output directory."""
        save_dir = self.root / job['save_dir']
        if not save_dir.exists():
            return
        preserved = {'lora_adapter', 'tokenizer', 'metrics.jsonl'}
        try:
            for item in save_dir.iterdir():
                name = item.name
                if item.is_dir():
                    if name not in preserved and name.startswith('checkpoint'):
                        shutil.rmtree(item, ignore_errors=True)
                elif item.is_file() and name.startswith('checkpoint'):
                    try:
                        item.unlink()
                    except Exception:
                        pass
            result['cleanup'] = 'completed'
        except Exception as c_err:
            result['cleanup'] = f'error: {c_err}'
    
    def _compute_ranking(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Compute ranking of jobs based on selected metric.

        Supported metrics:
            - perplexity_improvement: relative reduction (higher better)
            - post_perplexity: final perplexity (lower better; stored negative for sorting)
            - diversity_avg: average of distinct-1 and distinct-2 (higher better)
            - distinct_diversity: alias of diversity_avg
            - combined_improvement: weighted combo of perplexity_improvement (70%) + diversity_avg (30%)
        """
        ranked: List[Dict[str, Any]] = []
        for r in results:
            ev = r.get('evaluation') or {}
            pre_ppl = ev.get('pre_eval_perplexity')
            post_ppl = ev.get('post_eval_perplexity')
            diversity = (ev.get('diversity') or {})
            d1 = diversity.get('distinct_1')
            d2 = diversity.get('distinct_2')
            diversity_avg = (d1 + d2) / 2 if (d1 is not None and d2 is not None) else None
            # Skip jobs without post perplexity for metrics relying on perplexity
            if self.ranking_metric in ('perplexity_improvement', 'post_perplexity', 'combined_improvement') and post_ppl is None:
                continue
            if self.ranking_metric == 'perplexity_improvement' and pre_ppl is not None and post_ppl is not None:
                ppl_improvement = (pre_ppl - post_ppl) / pre_ppl if pre_ppl and pre_ppl > 0 else 0.0
                score = ppl_improvement
            elif self.ranking_metric == 'post_perplexity' and post_ppl is not None:
                ppl_improvement = (pre_ppl - post_ppl) / pre_ppl if (pre_ppl and post_ppl and pre_ppl > 0) else None
                score = -post_ppl  # lower is better
            elif self.ranking_metric in ('diversity_avg', 'distinct_diversity'):
                if diversity_avg is None:
                    # Cannot rank this job on diversity; skip it
                    continue
                ppl_improvement = (pre_ppl - post_ppl) / pre_ppl if (pre_ppl and post_ppl and pre_ppl > 0) else None
                score = diversity_avg
            elif self.ranking_metric == 'combined_improvement':
                ppl_improvement = (pre_ppl - post_ppl) / pre_ppl if (pre_ppl and post_ppl and pre_ppl > 0) else 0.0
                div_component = diversity_avg if diversity_avg is not None else 0.0
                score = 0.7 * ppl_improvement + 0.3 * div_component
            else:
                # Fallback to post perplexity if unknown metric
                ppl_improvement = (pre_ppl - post_ppl) / pre_ppl if (pre_ppl and post_ppl and pre_ppl > 0) else None
                score = -post_ppl if post_ppl is not None else 0.0
            ranked.append({
                'name': r.get('name'),
                'score': score,
                'metric': self.ranking_metric,
                'pre_perplexity': pre_ppl,
                'post_perplexity': post_ppl,
                'perplexity_improvement': ppl_improvement,
                'distinct_1': d1,
                'distinct_2': d2,
                'diversity_avg': diversity_avg,
                'status': r.get('status')
            })
        ranked.sort(key=lambda x: x['score'], reverse=True)
        return ranked

    async def run_all_parallel(self, job_filter: str = "*"):
        """
        Run all jobs in parallel with concurrency limit.
        
        Args:
            job_filter: Glob pattern to filter job names
        """
        import fnmatch
        
        # Filter jobs
        filtered_jobs = [j for j in self.jobs if fnmatch.fnmatch(j['name'], job_filter)]
        
        if not filtered_jobs:
            print(f"No jobs match filter: {job_filter}")
            return
        
        print(f"Running {len(filtered_jobs)} jobs with max {self.max_parallel} parallel")
        
        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(self.max_parallel)
        
        async def run_with_semaphore(job, device_id):
            async with semaphore:
                return await self.run_job(job, device_id)
        
        # Assign device IDs cyclically
        tasks = [
            run_with_semaphore(job, i % self.max_parallel)
            for i, job in enumerate(filtered_jobs)
        ]
        
        # Run all tasks
        start_time = datetime.now()
        self.results = await asyncio.gather(*tasks)
        end_time = datetime.now()
        
        # Prepare run entry with single-pass aggregation
        status_file = self.root / "data_out/parallel_training/status.json"
        status_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Single pass aggregation for all statistics
        agg_train = 0
        agg_test = 0
        succeeded = 0
        skipped = 0
        failed = 0
        
        for r in self.results:
            # Aggregate sample counts
            if r.get('dataset_train_samples') is not None:
                agg_train += r['dataset_train_samples']
            if r.get('dataset_test_samples') is not None:
                agg_test += r['dataset_test_samples']
            
            # Count status types
            status = r.get('status')
            if status == 'succeeded':
                succeeded += 1
            elif status == 'skipped':
                skipped += 1
            else:
                failed += 1

        run_entry = {
            'run_id': end_time.strftime('%Y%m%dT%H%M%S'),
            'total_jobs': len(filtered_jobs),
            'max_parallel': self.max_parallel,
            'total_duration_seconds': (end_time - start_time).total_seconds(),
            'timestamp': end_time.isoformat(),
            'aggregate_train_samples': agg_train if agg_train else None,
            'aggregate_test_samples': agg_test if agg_test else None,
            'jobs': self.results,
        }

        # Ranking computation
        ranking = self._compute_ranking(self.results)
        if ranking:
            run_entry['job_ranking'] = ranking
        # Append mode historical persistence (correctly placed inside run_all_parallel)
        if status_file.exists():
            try:
                with status_file.open('r', encoding='utf-8') as f:
                    existing = json.load(f)
            except Exception:
                existing = {}
        else:
            existing = {}

        # Normalize legacy format
        runs = []
        if 'runs' in existing and isinstance(existing['runs'], list):
            runs = existing['runs']
        elif 'jobs' in existing:
            legacy = dict(existing)
            runs = [legacy]
        runs.append(run_entry)
        new_status = {
            'runs': runs,
            'total_runs': len(runs),
            'last_updated': end_time.isoformat()
        }
        try:
            new_status['cumulative_train_samples'] = sum((r.get('aggregate_train_samples') or 0) for r in runs) or None
            new_status['cumulative_test_samples'] = sum((r.get('aggregate_test_samples') or 0) for r in runs) or None
        except Exception:
            pass
        with status_file.open('w', encoding='utf-8') as f:
            json.dump(new_status, f, indent=2)
        
        # Print summary using pre-computed counts
        print("\n" + "="*70)
        print("Parallel Training Summary")
        print("="*70)

        print(f"\nTotal Jobs: {len(self.results)}")
        print(f"Succeeded: {succeeded}")
        print(f"Skipped: {skipped}")
        print(f"Failed: {failed}")
        print(f"Total Time: {(end_time - start_time).total_seconds():.1f}s")
        print(f"\nStatus file: {status_file}")
        
        # Show failed jobs if any
        if failed > 0:
            print("\nFailed Jobs:")
            for r in self.results:
                if r.get('status') not in ('succeeded', 'skipped'):
                    print(f"  - {r['name']}: {r.get('error', 'return code ' + str(r.get('return_code')))}")
        if skipped > 0:
            print("\nSkipped Jobs:")
            for r in self.results:
                if r.get('status') == 'skipped':
                    print(f"  - {r['name']}: {r.get('reason', 'min_train_samples threshold')} train_samples={r.get('dataset_train_samples')}")

def main():
    parser = argparse.ArgumentParser(description="Parallel training launcher with historical status & evaluation")
    parser.add_argument("--config", default="autotrain_fast.yaml", help="Training config YAML (default: autotrain_fast.yaml)")
    parser.add_argument("--max-parallel", type=int, default=3, help="Max concurrent jobs (default: 3)")
    parser.add_argument("--filter", default="*", help="Job name filter pattern (e.g., 'phi35*' or 'quick*')")
    parser.add_argument("--list", action="store_true", help="List jobs without running")
    parser.add_argument("--min-train-samples", type=int, default=None, help="Skip jobs whose counted train samples are below this threshold")
    parser.add_argument("--generate-samples", type=int, default=3, help="Number of sample generations to produce after successful training")
    parser.add_argument("--no-eval", action="store_true", help="Disable post-training evaluation and sample generation entirely")
    parser.add_argument("--cleanup", action="store_true", help="Remove intermediate checkpoint artifacts after successful training")
    parser.add_argument("--ranking-metric", choices=["perplexity_improvement", "post_perplexity", "diversity_avg", "combined_improvement", "distinct_diversity"], default="perplexity_improvement", help="Metric used to rank jobs in status history (distinct_diversity alias of diversity_avg)")

    args = parser.parse_args()

    trainer = ParallelTrainer(
        args.config,
        max_parallel=args.max_parallel,
        min_train_samples=args.min_train_samples,
        generate_samples=args.generate_samples,
        perform_evaluation=not args.no_eval,
        cleanup=args.cleanup,
        ranking_metric=args.ranking_metric,
    )

    if args.list:
        print(f"Jobs in {args.config}:")
        for i, job in enumerate(trainer.jobs, 1):
            print(f"{i}. {job['name']}")
            print(f"   Dataset: {job['dataset']}")
            print(f"   Samples: {job.get('max_train_samples', 'all')}")
            print(f"   Model: {job['hf_model_id']}")
        return

    # Run parallel training
    asyncio.run(trainer.run_all_parallel(args.filter))

    # Determine exit status (skipped jobs are not failures)
    failures = [r for r in trainer.results if r.get('status') not in ('succeeded', 'skipped')]
    if failures:
        print("\n[parallel_train] One or more jobs failed. Exiting with code 1.")
        sys.exit(1)
    else:
        print("\n[parallel_train] All jobs completed (including skips). Exiting with code 0.")
        sys.exit(0)

if __name__ == "__main__":
    main()
