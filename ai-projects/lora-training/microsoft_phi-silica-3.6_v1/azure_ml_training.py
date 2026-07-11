"""
Azure Machine Learning Training for Phi-3.6 LoRA Fine-tuning
Enables cloud-based GPU training with automatic scaling and monitoring
"""

import argparse
from pathlib import Path
from typing import Any

try:
    from azure.ai.ml import Input, MLClient, Output, command
    from azure.ai.ml.constants import AssetTypes
    from azure.ai.ml.entities import (
        AmlCompute,
        CodeConfiguration,
        Data,
        Environment,
        ManagedOnlineDeployment,
        ManagedOnlineEndpoint,
        Model,
    )
    from azure.identity import AzureCliCredential, DefaultAzureCredential

    AZURE_ML_AVAILABLE = True
except ImportError:
    AZURE_ML_AVAILABLE = False
    print("Azure ML SDK not installed. Run: pip install azure-ai-ml azure-identity")


class AzureMLLoRATrainer:
    """Manages Azure ML training jobs for Phi-3.6 LoRA fine-tuning"""

    def __init__(self, subscription_id: str, resource_group: str, workspace_name: str):
        """
        Initialize Azure ML client.

        Args:
            subscription_id: Azure subscription ID
            resource_group: Resource group name
            workspace_name: ML workspace name
        """
        if not AZURE_ML_AVAILABLE:
            raise ImportError("Azure ML SDK required. Install: pip install azure-ai-ml azure-identity")

        # Try CLI credential first, then default
        try:
            credential = AzureCliCredential()
            credential.get_token("https://management.azure.com/.default")
        except Exception:
            credential = DefaultAzureCredential()

        self.ml_client = MLClient(
            credential=credential,
            subscription_id=subscription_id,
            resource_group_name=resource_group,
            workspace_name=workspace_name,
        )

        self.workspace_name = workspace_name
        print(f"✓ Connected to Azure ML workspace: {workspace_name}")

    def create_or_get_compute(
        self,
        compute_name: str = "phi36-gpu-cluster",
        vm_size: str = "Standard_NC6s_v3",  # Tesla V100 GPU
        min_instances: int = 0,
        max_instances: int = 4,
        idle_time_before_scale_down: int = 300,
    ) -> AmlCompute:
        """
        Create or retrieve GPU compute cluster for training.

        Args:
            compute_name: Cluster name
            vm_size: VM size (Standard_NC6s_v3 = 1x V100, Standard_NC12s_v3 = 2x V100)
            min_instances: Min nodes (0 for auto-scale)
            max_instances: Max nodes
            idle_time_before_scale_down: Scale-down delay in seconds

        Returns:
            Compute cluster configuration
        """
        try:
            compute = self.ml_client.compute.get(compute_name)
            print(f"✓ Using existing compute: {compute_name}")
        except Exception:
            print(f"Creating compute cluster: {compute_name}...")
            compute = AmlCompute(
                name=compute_name,
                type="amlcompute",
                size=vm_size,
                min_instances=min_instances,
                max_instances=max_instances,
                idle_time_before_scale_down=idle_time_before_scale_down,
                tier="dedicated",  # or "low_priority" for cost savings
            )
            compute = self.ml_client.compute.begin_create_or_update(compute).result()
            print(f"✓ Compute cluster created: {compute_name}")

        return compute

    def create_environment(self, env_name: str = "phi36-lora-env", python_version: str = "3.10") -> Environment:
        """
        Create Azure ML environment with all dependencies.

        Args:
            env_name: Environment name
            python_version: Python version

        Returns:
            Environment configuration
        """
        # Use curated PyTorch environment as base

        # Create custom environment with additional dependencies
        env = Environment(
            name=env_name,
            description="Phi-3.6 LoRA fine-tuning environment",
            image="mcr.microsoft.com/azureml/curated/acft-hf-nlp-gpu:63",
            conda_file={
                "name": env_name,
                "channels": ["conda-forge", "pytorch"],
                "dependencies": [
                    f"python={python_version}",
                    "pip",
                    {
                        "pip": [
                            "transformers>=4.40.0",
                            "datasets>=2.18.0",
                            "peft>=0.10.0",
                            "accelerate>=0.27.0",
                            "torch>=2.2.0",
                            "bitsandbytes>=0.42.0",
                            "scikit-learn>=1.4.0",
                            "pyyaml>=6.0",
                            "azure-ai-ml>=1.15.0",
                            "mlflow>=2.11.0",
                        ]
                    },
                ],
            },
        )

        try:
            env = self.ml_client.environments.create_or_update(env)
            print(f"✓ Environment registered: {env_name}")
        except Exception as e:
            print(f"Note: {e}")
            env = self.ml_client.environments.get(env_name, label="latest")
            print(f"✓ Using existing environment: {env_name}")

        return env

    def upload_dataset(
        self,
        dataset_path: str,
        dataset_name: str = "dolly-chat-dataset",
        description: str = "Dolly 15k chat dataset for Phi-3.6 fine-tuning",
    ) -> Data:
        """
        Upload dataset to Azure ML.

        Args:
            dataset_path: Local path to dataset directory
            dataset_name: Name for registered dataset
            description: Dataset description

        Returns:
            Registered dataset
        """
        dataset = Data(
            path=dataset_path,
            type=AssetTypes.URI_FOLDER,
            description=description,
            name=dataset_name,
        )

        dataset = self.ml_client.data.create_or_update(dataset)
        print(f"✓ Dataset uploaded: {dataset_name} (v{dataset.version})")
        return dataset

    def submit_training_job(
        self,
        experiment_name: str = "phi36-lora-training",
        compute_name: str = "phi36-gpu-cluster",
        dataset_name: str = "dolly-chat-dataset",
        config_path: str = "./lora/lora.yaml",
        max_train_samples: int | None = None,
        display_name: str | None = None,
    ) -> Any:
        """
        Submit LoRA training job to Azure ML.

        Args:
            experiment_name: Name of experiment
            compute_name: Compute cluster name
            dataset_name: Registered dataset name
            config_path: Path to lora.yaml config
            max_train_samples: Optional limit for quick tests
            display_name: Optional custom display name

        Returns:
            Submitted job
        """
        # Get dataset
        self.ml_client.data.get(dataset_name, label="latest")

        # Prepare training script directory
        script_dir = Path(__file__).parent / "scripts"

        # Build command arguments
        args = [
            "--config",
            config_path,
            "--dataset",
            Input(type=AssetTypes.URI_FOLDER, path=f"azureml:{dataset_name}@latest"),
            "--hf-model-id",
            "microsoft/Phi-3.5-mini-instruct",
        ]

        if max_train_samples:
            args.extend(["--max-train-samples", max_train_samples])

        # Create job
        job = command(
            code=str(script_dir.parent),  # Upload entire directory
            command="python scripts/train_lora.py " + " ".join(str(a) for a in args),
            environment=f"{self.workspace_name}/phi36-lora-env@latest",
            compute=compute_name,
            experiment_name=experiment_name,
            display_name=display_name or f"phi36-lora-{Path(config_path).stem}",
            outputs={"model_output": Output(type=AssetTypes.URI_FOLDER, mode="rw_mount")},
            # Enable MLflow tracking
            environment_variables={
                "MLFLOW_TRACKING_URI": "azureml://tracking",
                "HF_HUB_DISABLE_SYMLINKS_WARNING": "1",
                "PYTHONUTF8": "1",
            },
        )

        # Submit
        submitted_job = self.ml_client.jobs.create_or_update(job)
        print(f"✓ Training job submitted: {submitted_job.name}")
        print(f"  Monitor at: {submitted_job.studio_url}")

        return submitted_job

    def register_model(
        self,
        job_name: str,
        model_name: str = "phi36-lora-adapter",
        model_path: str = "lora_adapter",
    ) -> Model:
        """
        Register trained LoRA adapter as Azure ML model.

        Args:
            job_name: Training job name
            model_name: Name for registered model
            model_path: Path within job outputs

        Returns:
            Registered model
        """
        model = Model(
            path=f"azureml://jobs/{job_name}/outputs/model_output/{model_path}",
            name=model_name,
            description="Phi-3.6 LoRA fine-tuned adapter",
            type=AssetTypes.CUSTOM_MODEL,
            tags={
                "model": "Phi-3.5-mini-instruct",
                "method": "LoRA",
                "framework": "transformers",
            },
        )

        model = self.ml_client.models.create_or_update(model)
        print(f"✓ Model registered: {model_name} (v{model.version})")
        return model


def main():
    """CLI for Azure ML training"""
    parser = argparse.ArgumentParser(description="Azure ML training for Phi-3.6 LoRA")

    # Azure settings
    parser.add_argument("--subscription-id", required=True, help="Azure subscription ID")
    parser.add_argument("--resource-group", required=True, help="Resource group name")
    parser.add_argument("--workspace-name", required=True, help="ML workspace name")

    # Actions
    parser.add_argument(
        "--action",
        choices=["setup", "upload", "train", "register"],
        default="train",
        help="Action to perform",
    )

    # Training settings
    parser.add_argument("--experiment-name", default="phi36-lora-training", help="Experiment name")
    parser.add_argument("--compute-name", default="phi36-gpu-cluster", help="Compute cluster name")
    parser.add_argument(
        "--vm-size",
        default="Standard_NC6s_v3",
        help="VM size for compute (Standard_NC6s_v3 = 1x V100)",
    )
    parser.add_argument("--dataset-path", default="../../datasets/chat/dolly", help="Local dataset path")
    parser.add_argument("--dataset-name", default="dolly-chat-dataset", help="Dataset name in Azure ML")
    parser.add_argument("--config", default="./lora/lora.yaml", help="Path to lora.yaml config")
    parser.add_argument(
        "--max-train-samples",
        type=int,
        default=None,
        help="Limit training samples (for testing)",
    )

    # Model registration
    parser.add_argument("--job-name", help="Job name for model registration")
    parser.add_argument("--model-name", default="phi36-lora-adapter", help="Registered model name")

    args = parser.parse_args()

    # Initialize trainer
    trainer = AzureMLLoRATrainer(
        subscription_id=args.subscription_id,
        resource_group=args.resource_group,
        workspace_name=args.workspace_name,
    )

    if args.action == "setup":
        print("\n=== Setting up Azure ML infrastructure ===")
        trainer.create_or_get_compute(compute_name=args.compute_name, vm_size=args.vm_size)
        trainer.create_environment()
        print("\n✓ Setup complete!")

    elif args.action == "upload":
        print("\n=== Uploading dataset ===")
        trainer.upload_dataset(dataset_path=args.dataset_path, dataset_name=args.dataset_name)
        print("\n✓ Upload complete!")

    elif args.action == "train":
        print("\n=== Submitting training job ===")
        job = trainer.submit_training_job(
            experiment_name=args.experiment_name,
            compute_name=args.compute_name,
            dataset_name=args.dataset_name,
            config_path=args.config,
            max_train_samples=args.max_train_samples,
        )
        print("\n✓ Job submitted!")
        print(f"\nTo monitor: {job.studio_url}")

    elif args.action == "register":
        if not args.job_name:
            print("Error: --job-name required for model registration")
            return
        print("\n=== Registering model ===")
        trainer.register_model(job_name=args.job_name, model_name=args.model_name)
        print("\n✓ Model registered!")


if __name__ == "__main__":
    if not AZURE_ML_AVAILABLE:
        print("\n" + "=" * 70)
        print("  Azure ML SDK Required")
        print("=" * 70)
        print("\nInstall dependencies:")
        print("  pip install azure-ai-ml azure-identity")
        print("\nAuthenticate:")
        print("  az login")
        print("=" * 70)
    else:
        main()
