r"""
Azure AI Foundry (Managed Online Endpoint) deployment for Phi-3.x + LoRA adapter.
- Registers LoRA adapter as a model asset (if given a local path)
- Creates a managed online endpoint and GPU deployment
- Uses foundry/score_foundry.py scoring script to load base model + adapter

Usage (PowerShell):
  python azure_foundry_deploy.py `
    --subscription-id <SUB> `
    --resource-group rg-phi36-ml `
    --workspace-name phi36-ml-workspace `
    --adapter-path .\data_out\lora_training\lora_adapter `
    --endpoint-name phi36-lora-ep `
    --base-model-id microsoft/Phi-3.5-mini-instruct
"""
from pathlib import Path
import argparse
import time

try:
    from azure.identity import AzureCliCredential, DefaultAzureCredential
    from azure.ai.ml import MLClient
    from azure.ai.ml.entities import (
        ManagedOnlineEndpoint,
        ManagedOnlineDeployment,
        Model,
        Environment,
        CodeConfiguration,
    )
    from azure.ai.ml.constants import AssetTypes
except Exception:
    raise SystemExit("Install Azure ML SDK: pip install azure-ai-ml azure-identity")


def get_credential():
    try:
        cred = AzureCliCredential()
        cred.get_token("https://management.azure.com/.default")
        return cred
    except Exception:
        return DefaultAzureCredential()


def ensure_model(ml: MLClient, adapter_path: str | None, model_name: str) -> Model:
    if adapter_path:
        p = Path(adapter_path)
        if not p.exists():
            raise FileNotFoundError(f"Adapter path not found: {p}")
        m = Model(
            name=model_name,
            path=str(p),
            type=AssetTypes.CUSTOM_MODEL,
            description="LoRA adapter for Phi-3.x",
            tags={"method": "LoRA"},
        )
        return ml.models.create_or_update(m)
    # Fallback: fetch existing by name
    return ml.models.get(name=model_name, label="latest")


def create_environment(ml: MLClient, env_name: str) -> Environment:
    env = Environment(
        name=env_name,
        description="Environment for Phi-3 + LoRA serving",
        image="mcr.microsoft.com/azureml/curated/acft-hf-nlp-gpu:63",
        conda_file={
            "name": env_name,
            "channels": ["conda-forge", "pytorch"],
            "dependencies": [
                "python=3.10",
                "pip",
                {"pip": [
                    "transformers>=4.40.0",
                    "peft>=0.10.0",
                    "accelerate>=0.27.0",
                    "torch>=2.2.0",
                ]}
            ]
        },
    )
    try:
        return ml.environments.create_or_update(env)
    except Exception:
        return ml.environments.get(env_name, label="latest")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--subscription-id", required=True)
    ap.add_argument("--resource-group", required=True)
    ap.add_argument("--workspace-name", required=True)
    ap.add_argument("--adapter-path", default=None, help="Local path to lora_adapter (registers as model)")
    ap.add_argument("--model-name", default="phi36-lora-adapter")
    ap.add_argument("--endpoint-name", default=None)
    ap.add_argument("--deployment-name", default="blue")
    ap.add_argument("--base-model-id", default="microsoft/Phi-3.5-mini-instruct")
    ap.add_argument("--instance-type", default="Standard_NC6s_v3")
    ap.add_argument("--instance-count", type=int, default=1)
    args = ap.parse_args()

    cred = get_credential()
    ml = MLClient(cred, args.subscription_id, args.resource_group, args.workspace_name)

    # Register model (adapter)
    model = ensure_model(ml, args.adapter_path, args.model_name)
    print(f"✓ Model ready: {model.name} v{model.version}")

    # Create environment
    env_name = "phi36-lora-serving"
    env = create_environment(ml, env_name)
    print(f"✓ Environment ready: {env.name}:{env.version}")

    # Endpoint
    endpoint_name = args.endpoint_name or f"phi36-lora-ep-{int(time.time())}"
    ep = ManagedOnlineEndpoint(name=endpoint_name, auth_mode="key")
    ml.begin_create_or_update(ep).result()
    print(f"✓ Endpoint created: {endpoint_name}")

    # Deployment: code is the foundry folder (includes score_foundry.py). Model mounts at working dir.
    code_dir = Path(__file__).resolve().parent / "foundry"
    dep = ManagedOnlineDeployment(
        name=args.deployment_name,
        endpoint_name=endpoint_name,
        model=f"azureml:{model.name}:{model.version}",
        code_configuration=CodeConfiguration(code=str(code_dir), scoring_script="score_foundry.py"),
        environment=f"{env.name}:{env.version}",
        instance_type=args.instance_type,
        instance_count=args.instance_count,
        environment_variables={
            "BASE_MODEL_ID": args.base_model_id,
            "ADAPTER_SUBPATH": "lora_adapter",
            "USE_BF16": "1",
            "MAX_NEW_TOKENS": "128",
        },
    )
    ml.begin_create_or_update(dep).result()

    # Route traffic
    ep.traffic = {args.deployment_name: 100}
    ml.begin_create_or_update(ep).result()

    # Get keys + invoke URL
    keys = ml.online_endpoints.get_keys(endpoint_name)
    details = ml.online_endpoints.get(endpoint_name)
    print("\n=== Deployment ready ===")
    print(f"Endpoint: {endpoint_name}")
    print(f"Scoring URL: {details.scoring_uri}")
    print(f"Primary key: {keys.primary_key}")


if __name__ == "__main__":
    main()
