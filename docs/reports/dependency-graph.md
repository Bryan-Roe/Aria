# Dependency Graph

## main.py

## local_dev_adapter.py
- __future__
- argparse
- azure.functions
- collections.abc
- flask
- flask_cors
- http.server
- importlib
- json
- logging
- os
- pathlib
- shared.local_settings
- sys
- types
- typing

## app.py
- __future__
- argparse
- collections.abc
- importlib
- json
- logging
- math
- openai
- os
- re
- shared.local_summary
- sys
- typing
- urllib
- urllib.parse

## run_automation.py
- argparse
- os
- pathlib
- signal
- subprocess
- sys

## token_utils.py
- __future__
- importlib.util
- pathlib
- sys

## setup_monetization.py
- importlib.util
- json
- pathlib
- subprocess
- sys

## lora_infer_bridge.py
- __future__
- importlib.util
- pathlib
- sys

## run_continuous_automation.py
- argparse
- datetime
- os
- pathlib
- signal
- subprocess
- sys
- time

## run_main_if_referenced.py
- sys

## LMSTUDIO_AGI_INTEGRATION_IMPL.py
- os
- urllib.parse
- urllib.request

## blueprint.py
- azure.functions

## autotrain.py
- __future__
- importlib
- sys
- typing
- warnings

## chat_providers.py
- __future__
- importlib.util
- pathlib
- sys

## agi_provider.py
- __future__
- importlib.util
- pathlib
- sys
- types
- typing

## .github/hooks/scripts/scope_drift_guard.py
- __future__
- collections.abc
- json
- os
- re
- sys
- typing

## .github/hooks/scripts/no_verify_bypass_guard.py
- __future__
- collections.abc
- json
- os
- re
- sys
- typing

## .github/hooks/scripts/quantum_cost_gate.py
- collections.abc
- json
- os
- re
- sys
- typing

## .github/hooks/scripts/dataset_write_guard.py
- __future__
- json
- os
- re
- sys
- typing

## .github/hooks/scripts/secrets_leak_guard.py
- __future__
- collections.abc
- json
- os
- re
- sys
- typing

## .github/hooks/scripts/lora_adapter_completeness_guard.py
- __future__
- collections.abc
- json
- os
- pathlib
- re
- sys
- typing

## .github/hooks/scripts/enforce_task_complete.py
- __future__
- json
- os
- re
- sys
- typing

## .github/hooks/scripts/git_commit_hygiene.py
- __future__
- collections.abc
- json
- os
- pathlib
- re
- subprocess
- sys
- typing

## .github/hooks/scripts/pr_checklist_guard.py
- __future__
- json
- os
- subprocess
- sys

## .github/hooks/scripts/dry_run_reminder.py
- __future__
- collections.abc
- json
- os
- re
- sys
- typing

## .github/hooks/scripts/requirements_security_gate.py
- __future__
- json
- os
- re
- shutil
- subprocess
- sys
- tempfile
- tomli
- tomllib
- typing

## .github/hooks/scripts/dependabot_alert_gate.py
- __future__
- json
- os
- pathlib
- subprocess
- sys
- time
- typing

## .github/hooks/scripts/quantum_command_gate.py
- __future__
- collections.abc
- json
- os
- re
- sys
- typing

## ai-projects/llm-maker/web_server.py
- http.server
- json
- logging
- os
- pathlib
- sys
- tool_executor
- tool_maker
- tool_registry
- tool_validator
- urllib.parse
- website_maker

## ai-projects/llm-maker/llm_maker_mcp_server.py
- asyncio
- json
- logging
- mcp.server
- mcp.server.stdio
- mcp.types
- pathlib
- src.tool_executor
- src.tool_maker
- src.tool_registry
- src.tool_validator
- sys

## ai-projects/llm-maker/examples/fibonacci.py

## ai-projects/llm-maker/examples/text_processor.py
- re

## ai-projects/llm-maker/examples/quick_start.py
- pathlib
- sys
- tool_executor
- tool_maker
- tool_registry

## ai-projects/llm-maker/tests/test_executor.py
- pathlib
- pytest
- src.tool_executor
- sys
- tool_executor

## ai-projects/llm-maker/tests/test_validator.py
- pathlib
- pytest
- sys
- tool_validator

## ai-projects/llm-maker/tests/test_registry.py
- pathlib
- pytest
- sys
- tempfile
- tool_registry

## ai-projects/llm-maker/tests/test_validate_perf.py
- pathlib
- sys
- time
- tool_validator

## ai-projects/llm-maker/src/tool_maker.py
- logging
- pathlib
- shared.chat_providers
- sys
- tool_registry
- tool_validator
- yaml

## ai-projects/llm-maker/src/website_maker.py
- argparse
- datetime
- json
- os
- re
- shared.chat_providers
- shutil
- sys

## ai-projects/llm-maker/src/tool_validator.py
- ast
- logging
- pathlib
- yaml

## ai-projects/llm-maker/src/tool_executor.py
- RestrictedPython
- RestrictedPython.Guards
- contextlib
- importlib
- logging
- signal
- threading
- traceback
- typing

## ai-projects/llm-maker/src/__init__.py
- tool_executor
- tool_maker
- tool_registry
- tool_validator
- website_maker

## ai-projects/llm-maker/src/tool_registry.py
- dataclasses
- datetime
- json
- logging
- pathlib
- typing
- uuid

## ai-projects/email-spam-workflow/main.py
- __future__
- agent_framework
- argparse
- asyncio
- azure.ai.agentserver.agentframework
- dotenv
- sys
- workflow

## ai-projects/email-spam-workflow/workflow.py
- __future__
- agent_framework
- agent_framework.azure
- azure.identity.aio
- collections.abc
- os
- typing

## ai-projects/quantum-ml/quantum_llm_quickstart.py
- __future__
- argparse
- json
- logging
- pathlib
- src.quantum_llm_datasets
- src.quantum_llm_integrated
- sys
- time
- torch
- typing

## ai-projects/quantum-ml/hyperparameter_optimization.py
- datetime
- itertools
- json
- matplotlib.pyplot
- numpy
- pathlib
- sklearn.model_selection
- src.dataset_loader
- src.hybrid_qnn
- sys
- torch
- torch.utils.data
- warnings

## ai-projects/quantum-ml/validate_quantum_llm.py
- argparse
- importlib
- json
- logging
- pathlib
- src.quantum_llm_advanced
- src.quantum_llm_datasets
- src.quantum_llm_integrated
- src.quantum_llm_monitor
- sys
- time
- torch
- typing

## ai-projects/quantum-ml/benchmark_all_datasets.py
- datetime
- json
- matplotlib.pyplot
- numpy
- pandas
- pathlib
- sklearn.decomposition
- sklearn.impute
- sklearn.model_selection
- sklearn.preprocessing
- src.hybrid_qnn
- sys
- torch
- torch.utils.data

## ai-projects/quantum-ml/train_heart_disease.py
- joblib
- matplotlib.pyplot
- numpy
- pandas
- pathlib
- sklearn.decomposition
- sklearn.impute
- sklearn.model_selection
- sklearn.preprocessing
- src.hybrid_qnn
- sys
- torch
- torch.utils.data

## ai-projects/quantum-ml/test_azure_quantum.py
- __future__
- argparse
- azure_quantum_integration
- datetime
- logging
- numpy
- pathlib
- pytest
- qiskit
- sys
- typing
- yaml

## ai-projects/quantum-ml/quantum_llm_demo.py
- ai_projects.quantum_ml.src.quantum_llm
- asyncio
- collections
- json
- numpy
- pathlib
- sys
- traceback

## ai-projects/quantum-ml/quantum_llm_integration.py
- argparse
- json
- logging
- pathlib
- sys

## ai-projects/quantum-ml/test_quantum_hardware.py
- azure.quantum
- logging
- numpy
- pathlib
- pytest
- qiskit
- sys

## ai-projects/quantum-ml/deploy_to_azure_quantum.py
- argparse
- datetime
- json
- pathlib
- qiskit
- src.azure_quantum_integration

## ai-projects/quantum-ml/deploy_quantum_models_azure.py
- pathlib
- pickle
- qiskit
- src.azure_quantum_integration
- time
- torch
- yaml

## ai-projects/quantum-ml/web_app.py
- datetime
- flask
- flask_cors
- io
- json
- logging
- numpy
- os
- pandas
- pathlib
- pennylane
- re
- sklearn.decomposition
- sklearn.impute
- sklearn.metrics
- sklearn.model_selection
- sklearn.preprocessing
- src.dataset_loader
- sys
- threading
- time

## ai-projects/quantum-ml/submit_circuit_azure.py
- azure.quantum
- qiskit
- qiskit_qir
- time
- traceback

## ai-projects/quantum-ml/train_custom_dataset.py
- argparse
- joblib
- json
- matplotlib.pyplot
- numpy
- os
- pandas
- pathlib
- sklearn.datasets
- sklearn.decomposition
- sklearn.impute
- sklearn.model_selection
- sklearn.preprocessing
- src.hybrid_qnn
- sys
- torch
- torch.utils.data
- yaml

## ai-projects/quantum-ml/submit_qsharp_circuit.py
- azure.quantum
- time
- traceback

## ai-projects/quantum-ml/dataset_architecture_analyzer.py
- datetime
- json
- numpy
- pandas
- pathlib
- sklearn.preprocessing

## ai-projects/quantum-ml/test_entanglement_patterns.py
- datetime
- hybrid_qnn
- matplotlib.pyplot
- numpy
- pandas
- pathlib
- pytest
- sklearn.decomposition
- sklearn.impute
- sklearn.model_selection
- sklearn.preprocessing
- sys
- torch
- torch.utils.data

## ai-projects/quantum-ml/hyperparameter_tuning.py
- dataset_loader
- datetime
- hybrid_qnn
- itertools
- json
- pathlib
- sklearn.model_selection
- sys
- torch
- torch.utils.data

## ai-projects/quantum-ml/demo_dashboard.py
- requests
- sys
- time

## ai-projects/quantum-ml/classical_baseline_comparison.py
- datetime
- json
- matplotlib.pyplot
- numpy
- pandas
- pathlib
- seaborn
- sklearn.decomposition
- sklearn.ensemble
- sklearn.impute
- sklearn.metrics
- sklearn.model_selection
- sklearn.neural_network
- sklearn.preprocessing
- sklearn.svm
- warnings

## ai-projects/quantum-ml/run_azure_quantum_free.py
- qiskit
- src.azure_quantum_integration

## ai-projects/quantum-ml/quantum_mcp_server.py
- asyncio
- azure_quantum_integration
- collections
- concurrent.futures
- hashlib
- logging
- mcp.server
- mcp.server.stdio
- mcp.types
- numpy
- os
- pathlib
- qiskit
- qiskit_aer
- quantum_classifier
- random
- re
- sklearn.datasets
- sklearn.model_selection
- sklearn.preprocessing
- sys
- tempfile
- time
- typing
- yaml

## ai-projects/quantum-ml/quick_test_datasets.py
- datetime
- json
- numpy
- pandas
- pathlib
- sklearn.decomposition
- sklearn.impute
- sklearn.model_selection
- sklearn.preprocessing
- src.hybrid_qnn
- sys
- time
- torch
- torch.utils.data

## ai-projects/quantum-ml/train_pennylane_simple.py
- argparse
- datetime
- json
- numpy
- pandas
- pathlib
- pennylane
- sklearn.decomposition
- sklearn.impute
- sklearn.model_selection
- sklearn.preprocessing
- time

## ai-projects/quantum-ml/deploy_banknote_to_azure.py
- azure.identity
- azure.quantum
- datetime
- json
- pathlib
- qiskit
- qiskit_qir
- sys
- time
- yaml

## ai-projects/quantum-ml/train_ionosphere.py
- joblib
- matplotlib.pyplot
- numpy
- pandas
- pathlib
- sklearn.decomposition
- sklearn.model_selection
- sklearn.preprocessing
- src.hybrid_qnn
- sys
- torch
- torch.utils.data

## ai-projects/quantum-ml/example_mcp_client.py
- asyncio
- azure.ai.inference
- azure.ai.inference.models
- azure.core.credentials
- contextlib
- mcp
- mcp.client.stdio
- os

## ai-projects/quantum-ml/production/banknote_api.py
- datetime
- flask
- flask_cors
- joblib
- json
- numpy
- os
- pathlib
- src.hybrid_qnn
- sys
- torch

## ai-projects/quantum-ml/production/test_api.py
- datetime
- json
- pytest
- requests
- time

## ai-projects/quantum-ml/examples/create_circuits.py
- numpy
- pathlib
- pennylane
- qiskit
- qiskit.circuit
- src.quantum_classifier
- sys

## ai-projects/quantum-ml/examples/azure_integration.py
- pathlib
- qiskit
- src.azure_quantum_integration
- sys
- yaml

## ai-projects/quantum-ml/examples/run_simulations.py
- matplotlib
- matplotlib.pyplot
- numpy
- pathlib
- pennylane
- qiskit
- qiskit_aer
- qiskit_aer.noise

## ai-projects/quantum-ml/examples/train_models.py
- matplotlib
- matplotlib.pyplot
- numpy
- pathlib
- quantum_classifier
- sklearn.datasets
- sklearn.model_selection
- sklearn.preprocessing
- src.quantum_classifier
- sys

## ai-projects/quantum-ml/scripts/submit_variational_hardware.py
- __future__
- argparse
- azure_quantum_integration
- datetime
- json
- numpy
- pathlib
- qiskit
- sys
- yaml

## ai-projects/quantum-ml/scripts/test_provider_gates.py
- __future__
- argparse
- azure_quantum_integration
- datetime
- json
- numpy
- pathlib
- pytest
- qiskit
- sys
- yaml

## ai-projects/quantum-ml/scripts/upgrade_qiskit_to_1x.py
- __future__
- argparse
- datetime
- pathlib
- qiskit
- re
- shutil
- subprocess
- sys

## ai-projects/quantum-ml/scripts/train_from_dataset.py
- argparse
- json
- numpy
- pandas
- pathlib
- quantum_classifier
- sklearn.decomposition
- sklearn.model_selection
- sklearn.preprocessing
- sys
- yaml

## ai-projects/quantum-ml/scripts/run_hardware_tests.py
- __future__
- argparse
- pathlib
- sys
- test_azure_quantum

## ai-projects/quantum-ml/scripts/validate_qiskit_env.py
- __future__
- importlib
- json
- pkgutil
- sys

## ai-projects/quantum-ml/scripts/run_experiment_grid.py
- __future__
- pathlib
- subprocess
- sys

## ai-projects/quantum-ml/scripts/visualize_hardware_results.py
- __future__
- json
- matplotlib.pyplot
- pandas
- pathlib
- subprocess
- yaml

## ai-projects/quantum-ml/scripts/submit_small_stabilizer.py
- __future__
- argparse
- azure_quantum_integration
- datetime
- json
- numpy
- pathlib
- qiskit
- sys
- yaml

## ai-projects/quantum-ml/scripts/run_simulated_circuit.py
- __future__
- argparse
- datetime
- json
- numpy
- pathlib
- qiskit
- qiskit_aer
- qiskit_aer.noise
- yaml

## ai-projects/quantum-ml/src/quantum_llm_advanced.py
- collections
- dataclasses
- hybrid_qnn
- logging
- math
- torch
- torch.nn
- torch.nn.functional

## ai-projects/quantum-ml/src/quantum_llm_integrated.py
- argparse
- json
- logging
- pathlib
- quantum_circuit_optimizer
- quantum_llm_advanced
- quantum_llm_hybrid_trainer
- quantum_llm_monitor
- torch
- torch.nn
- torch.utils.data
- typing
- yaml

## ai-projects/quantum-ml/src/quantum_circuit_optimizer.py
- collections
- dataclasses
- logging
- numpy
- pennylane
- time
- torch
- torch.nn
- typing

## ai-projects/quantum-ml/src/quantum_classifier_enhanced.py
- logging
- numpy
- pathlib
- pennylane
- sklearn.datasets
- sklearn.model_selection
- sklearn.preprocessing
- torch
- torch.nn
- yaml

## ai-projects/quantum-ml/src/dataset_loader.py
- numpy
- pandas
- pathlib
- sklearn.decomposition
- sklearn.impute
- sklearn.preprocessing
- typing

## ai-projects/quantum-ml/src/azure_quantum_integration.py
- azure.identity
- azure.quantum
- azure.quantum.qiskit
- json
- logging
- pathlib
- qiskit
- typing
- yaml

## ai-projects/quantum-ml/src/azure_ml_integration.py
- azureml.core
- azureml.core.compute
- azureml.core.model
- azureml.core.runconfig
- azureml.core.webservice
- logging
- pathlib
- typing

## ai-projects/quantum-ml/src/quantum_transformer.py
- hybrid_qnn
- logging
- math
- pathlib
- sys
- torch
- torch.nn
- torch.nn.functional

## ai-projects/quantum-ml/src/quantum_llm_hybrid_trainer.py
- dataclasses
- json
- logging
- numpy
- pathlib
- time
- torch
- torch.nn
- torch.optim
- torch.utils.data
- typing

## ai-projects/quantum-ml/src/__init__.py

## ai-projects/quantum-ml/src/quantum_classifier.py
- logging
- numpy
- pathlib
- pennylane
- sklearn.datasets
- sklearn.model_selection
- torch
- torch.nn
- yaml

## ai-projects/quantum-ml/src/hybrid_qnn.py
- logging
- pennylane
- torch
- torch.nn
- yaml

## ai-projects/quantum-ml/src/api.py
- automate_quantum_job
- azure_quantum_integration
- quantum_classifier
- quantum_llm_integrated

## ai-projects/quantum-ml/src/automate_quantum_job.py
- azure.quantum
- azure.quantum.qiskit
- qiskit
- time

## ai-projects/quantum-ml/src/quantum_llm_monitor.py
- collections
- dataclasses
- json
- logging
- numpy
- pathlib
- psutil
- time
- torch
- typing

## ai-projects/quantum-ml/src/quantum_llm_datasets.py
- json
- logging
- numpy
- pathlib
- random
- torch
- torch.utils.data
- typing

## ai-projects/quantum-ml/src/quantum_code_llm.py
- __future__
- dataclasses
- pathlib
- string
- torch
- torch.nn
- torch.nn.functional
- typing

## ai-projects/quantum-ml/src/quantum_llm/pipeline.py
- __future__
- asyncio
- chat_providers
- collections.abc
- config
- json
- logging
- numpy
- pathlib
- quantum_embeddings
- quantum_router
- quantum_sampler
- sys
- time
- typing

## ai-projects/quantum-ml/src/quantum_llm/quantum_sampler.py
- __future__
- circuit_cache
- collections.abc
- logging
- numpy
- pennylane
- qiskit
- qiskit.circuit
- qiskit_aer
- warnings

## ai-projects/quantum-ml/src/quantum_llm/config.py
- __future__
- dataclasses
- math
- os
- typing

## ai-projects/quantum-ml/src/quantum_llm/quantum_embeddings.py
- __future__
- logging
- numpy
- pennylane
- qiskit
- qiskit.circuit
- qiskit_aer
- quantum_sampler

## ai-projects/quantum-ml/src/quantum_llm/__init__.py
- circuit_cache
- config
- pipeline
- quantum_embeddings
- quantum_router
- quantum_sampler

## ai-projects/quantum-ml/src/quantum_llm/circuit_cache.py
- __future__
- collections
- hashlib
- logging
- numpy
- time
- typing

## ai-projects/quantum-ml/src/quantum_llm/quantum_router.py
- __future__
- logging
- numpy
- pennylane
- quantum_sampler

## ai-projects/quantum-ml/experiments/analyze_plots.py
- pathlib

## ai-projects/quantum-ml/experiments/run_all_experiments.py
- datetime
- experiments.analyze_plots
- experiments.extended_datasets
- experiments.parameter_tuning
- pathlib
- sys
- time

## ai-projects/quantum-ml/experiments/parameter_tuning.py
- matplotlib
- matplotlib.pyplot
- numpy
- pathlib
- quantum_classifier
- sklearn.datasets
- sklearn.model_selection
- sklearn.preprocessing
- src.quantum_classifier
- sys
- yaml

## ai-projects/quantum-ml/experiments/quick_demo.py
- extended_datasets
- pathlib
- sys
- time
- traceback

## ai-projects/quantum-ml/experiments/extended_datasets.py
- matplotlib
- matplotlib.pyplot
- numpy
- pathlib
- quantum_classifier
- sklearn.datasets
- sklearn.decomposition
- sklearn.model_selection
- sklearn.preprocessing
- src.quantum_classifier
- sys

## ai-projects/quantum-ml/experiments/auto_optimize.py
- matplotlib.pyplot
- numpy
- pathlib
- sklearn.datasets
- sklearn.model_selection
- sklearn.preprocessing
- src.quantum_classifier
- sys
- torch
- torch.nn
- torch.optim
- torch.utils.data
- yaml

## ai-projects/lmstudio-mcp/lmstudio_mcp_server.py
- agi_mcp_tools
- asyncio
- httpx
- json
- logging
- mcp.server
- mcp.server.stdio
- mcp.types
- os
- sys
- typing

## ai-projects/lmstudio-mcp/agi_provider_examples.py
- asyncio
- lmstudio_agi_integration
- pathlib
- sys
- traceback

## ai-projects/lmstudio-mcp/lmstudio_agi_integration.py
- asyncio
- json
- lmstudio_agent_integration
- logging
- re
- traceback
- typing

## ai-projects/lmstudio-mcp/quickstart.py
- asyncio
- httpx
- pathlib
- subprocess
- sys
- traceback

## ai-projects/lmstudio-mcp/agi_mcp_tools.py
- __future__
- agi_provider
- pathlib
- sys
- typing

## ai-projects/lmstudio-mcp/__init__.py
- lmstudio_mcp_server

## ai-projects/lmstudio-mcp/privacy_first_ai.py
- asyncio
- dataclasses
- datetime
- enum
- hashlib
- json
- lmstudio_agent_integration
- lmstudio_agi_integration
- logging
- pathlib
- traceback
- typing

## ai-projects/lmstudio-mcp/test_lmstudio_mcp.py
- asyncio
- lmstudio_mcp_server
- os
- pathlib
- sys
- traceback

## ai-projects/lmstudio-mcp/verify_agent_integration.py
- asyncio
- lmstudio_agent_integration
- lmstudio_mcp_server
- os
- pathlib
- sys
- traceback

## ai-projects/lmstudio-mcp/privacy_deployment_config.py
- typing

## ai-projects/lmstudio-mcp/lmstudio_agent_integration.py
- __future__
- asyncio
- collections.abc
- json
- lmstudio_mcp_server
- logging
- os
- pathlib
- sys
- traceback
- typing

## ai-projects/my-agent-230a13f1/main.py
- asyncio
- azure.ai.agentserver.responses

## ai-projects/chat-cli/src/quantum_agent_selector.py
- __future__
- dataclasses
- enum
- os
- random
- time
- typing

## ai-projects/chat-cli/src/quantum_provider.py
- chat_providers
- collections.abc
- json
- logging
- pathlib
- quantum_transformer
- sys
- torch
- torch.nn.functional
- typing

## ai-projects/chat-cli/src/local_agi_provider.py
- __future__
- collections.abc
- core.llm.client
- json
- typing

## ai-projects/chat-cli/src/token_utils.py
- __future__
- collections.abc
- dataclasses
- math
- tiktoken
- transformers

## ai-projects/chat-cli/src/lora_infer_bridge.py
- __future__
- json
- pathlib
- peft
- sys
- torch
- transformers

## ai-projects/chat-cli/src/__init__.py

## ai-projects/chat-cli/src/chat_cli.py
- __future__
- argparse
- colorama
- datetime
- importlib
- json
- os
- pathlib
- sys
- time
- typing

## ai-projects/chat-cli/src/test_chat_cli.py
- __future__
- chat_cli
- contextlib
- io
- pathlib
- sys
- types
- unittest
- unittest.mock

## ai-projects/chat-cli/src/test_chat_providers.py
- __future__
- agi_provider
- chat_cli
- chat_providers
- json
- os
- pathlib
- pytest
- sys
- tempfile
- time
- typing
- unittest
- unittest.mock

## ai-projects/chat-cli/src/api.py
- agi_provider
- chat_providers
- token_utils

## ai-projects/chat-cli/src/chat_providers.py
- __future__
- agi_provider
- collections.abc
- dataclasses
- json
- local_agi_provider
- logging
- openai
- os
- pathlib
- peft
- quantum_provider
- random
- shared.azure_utils
- shared.local_calc
- shared.local_settings
- shared.local_summary
- subprocess
- sys
- threading
- time
- torch
- transformers
- typing
- urllib.error
- urllib.request

## ai-projects/chat-cli/src/agi_provider.py
- __future__
- asyncio
- chat_providers
- collections.abc
- dataclasses
- html
- logging
- math
- os
- quantum_agent_selector
- re
- shared.agi_memory_redis
- shared.agi_persistence
- shared.agi_persistence_sqlite
- time
- typing

## ai-projects/chat-cli/src/_smoke_test.py
- __future__
- importlib
- typing

## ai-projects/writer-reviewer-workflow/main.py
- agent_framework
- argparse
- asyncio
- azure.ai.agentserver.agentframework
- dotenv
- pathlib
- prototype_workflow
- sys
- workflow

## ai-projects/writer-reviewer-workflow/prototype_workflow.py
- __future__
- dataclasses
- json
- keyword
- pathlib
- re
- shutil
- subprocess
- sys
- time
- typing

## ai-projects/writer-reviewer-workflow/workflow.py
- agent_framework
- agent_framework.azure
- azure.identity.aio
- os

## ai-projects/cooking-ai/tests/debug_agent_extract.py
- agents.recipe_agent
- pathlib
- providers.local
- sys

## ai-projects/cooking-ai/tests/_debug_local.py
- providers.local

## ai-projects/cooking-ai/tests/test_schemas.py
- __future__
- json
- pathlib
- pytest
- sys
- utils.json_utils

## ai-projects/cooking-ai/tests/test_agent.py
- __future__
- agents.recipe_agent
- json
- pathlib
- providers.local
- pytest
- sys
- utils.json_utils

## ai-projects/cooking-ai/tests/debug_extract_local.py
- pathlib
- providers.local
- sys

## ai-projects/cooking-ai/tests/run_tests.py
- __future__
- importlib
- pathlib
- sys

## ai-projects/cooking-ai/tests/debug_run_local.py
- pathlib
- providers.local
- sys

## ai-projects/cooking-ai/src/main.py
- __future__
- agents.recipe_agent
- argparse
- os
- providers.github_models
- providers.local

## ai-projects/cooking-ai/src/__init__.py

## ai-projects/cooking-ai/src/utils/json_utils.py
- __future__
- json
- jsonschema
- re

## ai-projects/cooking-ai/src/providers/github_models.py
- __future__
- openai
- os
- typing

## ai-projects/cooking-ai/src/providers/local.py
- __future__
- json
- re

## ai-projects/cooking-ai/src/providers/__init__.py

## ai-projects/cooking-ai/src/agents/recipe_agent.py
- __future__
- typing
- utils.json_utils

## ai-projects/lora-training/quantum-ai/src/azure_quantum_integration.py
- azure.quantum
- azure.quantum.qiskit
- logging
- os
- qiskit
- qiskit.providers
- typing

## ai-projects/lora-training/quantum-ai/src/quantum_classifier.py
- logging
- numpy
- qiskit
- qiskit.circuit
- qiskit.circuit.library
- qiskit.primitives
- qiskit_algorithms.optimizers
- qiskit_machine_learning.algorithms
- qiskit_machine_learning.neural_networks
- sklearn.datasets
- sklearn.model_selection
- sklearn.preprocessing

## ai-projects/lora-training/quantum-ai/src/hybrid_qnn.py
- logging
- numpy
- qiskit
- qiskit.circuit
- qiskit.primitives
- qiskit_machine_learning.connectors
- qiskit_machine_learning.neural_networks
- sklearn.datasets
- sklearn.model_selection
- sklearn.preprocessing
- torch
- torch.nn
- torch.optim
- torch.utils.data

## ai-projects/lora-training/microsoft_phi-silica-3.6_v1/python mcp.py
- asyncio
- azure.ai.inference
- azure.ai.inference.models
- azure.core.credentials
- contextlib
- json
- mcp
- mcp.client.sse
- mcp.client.stdio
- mcp.client.streamable_http
- os

## ai-projects/lora-training/microsoft_phi-silica-3.6_v1/azure_foundry_deploy.py
- argparse
- azure.ai.ml
- azure.ai.ml.constants
- azure.ai.ml.entities
- azure.identity
- pathlib
- time

## ai-projects/lora-training/microsoft_phi-silica-3.6_v1/azure_ml_training.py
- argparse
- azure.ai.ml
- azure.ai.ml.constants
- azure.ai.ml.entities
- azure.identity
- pathlib
- typing

## ai-projects/lora-training/microsoft_phi-silica-3.6_v1/foundry/score_foundry.py
- json
- os
- pathlib
- peft
- torch
- transformers

## ai-projects/lora-training/microsoft_phi-silica-3.6_v1/azureml/submit_sentence_transformer_azureml.py
- __future__
- argparse
- os
- pathlib
- shutil
- subprocess
- sys

## ai-projects/lora-training/microsoft_phi-silica-3.6_v1/scripts/data_augmenter.py
- argparse
- dataclasses
- json
- pathlib
- random
- typing

## ai-projects/lora-training/microsoft_phi-silica-3.6_v1/scripts/auto_eval.py
- argparse
- dataclasses
- datasets
- json
- numpy
- pathlib
- peft
- rouge_score
- sacrebleu
- time
- torch
- transformers
- typing
- yaml

## ai-projects/lora-training/microsoft_phi-silica-3.6_v1/scripts/train_lora.py
- argparse
- collections.abc
- dataclasses
- datasets
- ipaddress
- json
- math
- metrics_logger
- os
- otel_callback
- pathlib
- peft
- re
- shared.tracing
- socket
- torch
- traceback
- transformers
- typing
- urllib.parse
- urllib.request
- yaml

## ai-projects/lora-training/microsoft_phi-silica-3.6_v1/scripts/gpu_optimizer.py
- argparse
- dataclasses
- pathlib
- subprocess
- torch
- typing
- yaml

## ai-projects/lora-training/microsoft_phi-silica-3.6_v1/scripts/prepare_dataset.py
- argparse
- collections.abc
- csv
- json
- pathlib
- random
- typing

## ai-projects/lora-training/microsoft_phi-silica-3.6_v1/scripts/metrics_logger.py
- applicationinsights
- base64
- datetime
- hashlib
- hmac
- json
- opentelemetry
- opentelemetry.exporter.otlp.proto.grpc.trace_exporter
- opentelemetry.sdk.trace
- opentelemetry.sdk.trace.export
- os
- pathlib
- sys
- typing
- urllib.request

## ai-projects/lora-training/microsoft_phi-silica-3.6_v1/scripts/train_sentence_transformer.py
- __future__
- argparse
- contextlib
- datasets
- huggingface_hub
- logging
- os
- pathlib
- sentence_transformers
- sentence_transformers.base.sampler
- sentence_transformers.sentence_transformer.evaluation
- sentence_transformers.sentence_transformer.losses
- torch
- traceback

## ai-projects/lora-training/microsoft_phi-silica-3.6_v1/scripts/dataset_analyzer.py
- argparse
- collections
- dataclasses
- json
- matplotlib.pyplot
- numpy
- pathlib
- typing

## ai-projects/lora-training/microsoft_phi-silica-3.6_v1/scripts/training_monitor.py
- argparse
- dataclasses
- datetime
- json
- pathlib
- queue
- threading
- time
- typing

## ai-projects/lora-training/microsoft_phi-silica-3.6_v1/scripts/lr_finder.py
- argparse
- json
- matplotlib.pyplot
- numpy
- pathlib
- scipy.ndimage
- torch
- torch.utils.data
- transformers
- typing

## ai-projects/lora-training/microsoft_phi-silica-3.6_v1/scripts/model_exporter.py
- argparse
- huggingface_hub
- onnx
- onnxruntime.transformers
- pathlib
- time
- torch
- transformers

## ai-projects/lora-training/microsoft_phi-silica-3.6_v1/scripts/model_server.py
- argparse
- asyncio
- datetime
- fastapi
- os
- pathlib
- pydantic
- time
- torch
- transformers
- typing
- uvicorn

## ai-projects/lora-training/microsoft_phi-silica-3.6_v1/scripts/otel_callback.py
- __future__
- logging
- opentelemetry
- opentelemetry.exporter.otlp.proto.grpc.trace_exporter
- opentelemetry.sdk.trace
- opentelemetry.sdk.trace.export
- os
- sys
- transformers
- typing

## ai-projects/lora-training/microsoft_phi-silica-3.6_v1/scripts/semantic_pruning.py
- argparse
- dataclasses
- json
- numpy
- pathlib
- sentence_transformers
- typing

## ai-projects/lora-training/microsoft_phi-silica-3.6_v1/scripts/run_pipeline.py
- argparse
- json
- pathlib
- subprocess
- sys
- time
- typing

## ai-projects/lora-training/microsoft_phi-silica-3.6_v1/scripts/rag_pipeline.py
- argparse
- dataclasses
- json
- numpy
- pathlib
- sentence_transformers
- torch
- transformers
- typing

## ai-projects/lora-training/microsoft_phi-silica-3.6_v1/local_train/train_local.py
- argparse
- dataclasses
- datasets
- json
- math
- pathlib
- peft
- torch
- transformers
- yaml

## examples/ai_starters/local_model_chat.py
- transformers

## examples/ai_starters/fastapi_local_chat.py
- examples.ai_starters.local_model_chat
- fastapi
- fastapi.responses
- functools
- pydantic
- uvicorn

## examples/ai_starters/sql_to_local_ai_orchestrator.py
- __future__
- argparse
- examples.ai_starters.local_model_chat
- importlib
- json
- pathlib
- psycopg
- psycopg2
- sqlite3
- typing
- urllib.parse

## examples/ai_starters/agent_with_tools.py
- __future__
- ast
- collections.abc
- dataclasses
- pathlib
- re

## ai_projects/__init__.py

## ai_projects/quantum_ml/__init__.py
- pathlib

## apps/dashboard/app.py
- csv
- datetime
- flask
- flask_socketio
- io
- json
- os
- pathlib
- re
- scripts.autotrain
- shlex
- signal
- subprocess
- sys
- threading
- time
- traceback
- typing
- yaml

## apps/dashboard/websocket_server.py
- asyncio
- contextlib
- datetime
- importlib
- json
- os
- pathlib
- watchdog.events
- watchdog.observers

## apps/dashboard/serve.py
- collections
- datetime
- gpu_monitor
- http.server
- json
- os
- pathlib
- psutil
- random
- re
- socketserver
- subprocess
- sys
- time
- traceback
- urllib.parse
- vram_calculator
- webbrowser
- yaml

## apps/dashboard/gpu_monitor.py
- json
- psutil
- subprocess

## apps/aria/Repository analyzer.py
- __future__
- collections.abc
- dataclasses
- logging
- pathlib
- registry
- risk_manager
- typing

## apps/aria/stage_state_store.py
- __future__
- copy
- json
- os
- pathlib
- threading
- typing

## apps/aria/server.py
- agi_provider
- datetime
- http.server
- importlib.util
- json
- logging
- math
- os
- pathlib
- random
- re
- shared.chat_providers
- shared.local_settings
- socket
- sys
- time
- torch
- traceback
- transformers
- urllib.request

## apps/aria/test_auto_execute.py
- json
- pytest
- requests
- sys
- traceback

## tests/test_app_local_logic.py
- __future__
- app
- builtins
- os
- pytest
- sys

## tests/test_config_paths.py
- __future__
- pathlib
- pytest
- scripts.config_paths

## tests/test_json_utils_load_status.py
- __future__
- os
- pathlib
- shared.json_utils
- sys
- time

## tests/test_runtime_env.py
- __future__
- json
- shared.runtime_env
- subprocess

## tests/test_qai_app_startup.py
- __future__
- importlib.util
- pathlib
- pytest
- sys

## tests/test_provider_fallback.py
- __future__
- os
- pathlib
- pytest
- shared.config
- shared.import_helpers
- sys
- unittest.mock

## tests/test_stripe_webhooks.py
- __future__
- json
- pathlib
- shared.stripe_webhooks
- sys

## tests/test_request_validator.py
- __future__
- json
- pytest
- shared.request_validator
- unittest.mock

## tests/test_agi_prune.py
- json
- pathlib
- scripts.agi_persistence_prune
- shared.agi_persistence_sqlite
- sys
- time

## tests/test_setup_monetization.py
- __future__
- importlib.util
- json
- pathlib

## tests/test_quantum_llm_health_check.py
- json
- pathlib
- pytest
- subprocess
- sys

## tests/test_database_integration.py
- __future__
- math
- pathlib
- shared.chat_memory
- sys

## tests/test_multi_agent.py
- __future__
- importlib
- json
- pathlib
- pytest
- sys
- types

## tests/test_serve_api_routes.py
- http.server
- importlib.util
- json
- pathlib
- pytest
- socket
- sys
- threading
- time
- unittest.mock
- urllib.parse
- urllib.request

## tests/test_hypothesis_agent.py
- __future__
- core.agents.hypothesis_agent
- core.memory.store
- core.task
- json
- typing

## tests/test_request_validator_agi.py
- __future__
- pathlib
- shared.request_validator
- sys

## tests/test_provider_gates.py
- __future__
- importlib.util
- pathlib
- pytest

## tests/test_training_analytics_cli.py
- __future__
- pathlib
- pytest
- subprocess
- sys
- tempfile

## tests/test_notifications.py
- __future__
- core.notifications
- urllib.error

## tests/test_git_commit_hygiene_hook.py
- __future__
- importlib.util
- io
- json
- pathlib
- sys

## tests/test_status_freshness_agent.py
- __future__
- datetime
- json
- pathlib
- scripts.agents.base
- scripts.agents.status_freshness_agent
- sys

## tests/test_app_providers.py
- __future__
- app
- json
- os
- pytest
- sys
- types

## tests/test_workflow_validation_workflow.py
- __future__
- json
- pathlib
- pytest
- tests.workflow_test_helpers
- yaml

## tests/test_monitor_autonomous_training.py
- importlib.util
- io
- json
- pathlib
- re
- sys

## tests/test_quantum_autorun_unit.py
- importlib
- pathlib
- sys
- unittest.mock

## tests/test_cycle_observer.py
- __future__
- core.bus
- core.cycle_observer
- core.memory.store
- core.runner
- pytest

## tests/test_agi_launcher_task.py
- __future__
- json
- pathlib
- pytest

## tests/test_autotrain_root_shim.py
- __future__
- importlib.util
- pathlib
- scripts.autotrain
- warnings

## tests/test_agi_persistence_sqlite.py
- agi_provider

## tests/test_ui_playwright.py
- json
- os
- pathlib
- playwright.sync_api
- pytest
- requests
- shutil
- socket
- subprocess
- time

## tests/test_import_helpers.py
- pathlib
- shared.import_helpers
- sys

## tests/test_system_health_check.py
- __future__
- importlib.util
- json
- pathlib
- sys
- types

## tests/test_agi_features.py
- __future__
- core.agents.critique_agent
- core.agents.debate_agent
- core.agents.goal_evolution_agent
- core.agents.human_feedback_agent
- core.agents.hypothesis_agent
- core.agents.llm_agent
- core.agents.reasoning_agent
- core.agents.reflection_agent
- core.agents.summarizer_agent
- core.agents.tool_agent
- core.agents.training_agent
- core.bus
- core.ingestion.pipeline
- core.knowledge.graph
- core.llm.client
- core.memory.store
- core.notifications
- core.registry
- core.router
- core.runner
- core.task
- datetime
- http.server
- json
- pathlib
- sys
- threading
- types
- uuid

## tests/test_validate_site_bundles.py
- __future__
- json
- scripts.validate_site_bundles

## tests/test_performance_optimizations.py
- ai_runner
- chat_memory
- collections
- generate_evaluation_set
- heapq
- json
- lora_infer_bridge
- math
- pathlib
- pytest
- re
- shared.sql_repository
- sys
- time
- token_utils
- training_analytics

## tests/test_quantum_autorun_dry_run_behavior.py
- __future__
- pathlib
- quantum_autorun
- sys

## tests/test_integration_smoke_schema.py
- __future__
- pytest
- re
- scripts.integration_smoke
- sys
- typing

## tests/test_cleanup_artifacts.py
- __future__
- importlib
- importlib.util
- os
- pathlib
- sys
- time

## tests/test_quantum_llm_local_smoke.py
- __future__
- asyncio
- pathlib
- quantum_llm
- sys

## tests/test_config_validator.py
- config_validator
- pathlib
- pytest
- sys
- tempfile

## tests/test_quantum_integration.py
- __future__
- asyncio
- json
- mount.quantum_integration
- pathlib
- pytest
- types

## tests/test_connection_pool_mock.py
- shared.chat_memory

## tests/test_run_continuous_automation.py
- __future__
- datetime
- importlib.util
- pathlib
- subprocess

## tests/test_aria_bot_root_shim.py
- __future__
- importlib.util
- pathlib
- pytest
- subprocess
- sys

## tests/test_core_agents.py
- __future__
- collections.abc
- core.agents.critique_agent
- core.agents.debate_agent
- core.agents.goal_evolution_agent
- core.agents.human_feedback_agent
- core.agents.hypothesis_agent
- core.agents.llm_agent
- core.agents.planner_agent
- core.agents.reasoning_agent
- core.agents.reflection_agent
- core.agents.summarizer_agent
- core.agents.tool_agent
- core.agents.training_agent
- core.bus
- core.memory.store
- core.task
- pytest

## tests/test_repair_data_out_status.py
- __future__
- datetime
- json
- pathlib
- scripts.repair_data_out_status
- sys

## tests/test_aria_bot_dev_entrypoints.py
- __future__
- json
- pathlib
- pytest

## tests/test_training_analytics.py
- importlib.util
- json
- pathlib
- pytest
- sys

## tests/test_merge_gate_setup_guardrails.py
- __future__
- pathlib
- pytest
- yaml

## tests/test_agi_stream_utils_js.py
- __future__
- pathlib
- pytest
- shutil
- subprocess

## tests/test_config_validation_gates.py
- os
- pathlib
- pytest
- subprocess
- sys

## tests/test_agents_base.py
- __future__
- json
- pathlib
- pytest
- scripts.agents.base
- sys

## tests/test_azure_quantum_integration.py
- enum
- importlib
- json
- pathlib
- pytest
- sys
- unittest.mock

## tests/test_autonomous_code_agent.py
- __future__
- autonomous_code_agent
- pathlib
- pytest
- subprocess
- sys
- types

## tests/test_app_main.py
- __future__
- app
- os
- pytest
- sys

## tests/test_quantum_command_gate_hook.py
- __future__
- json
- os
- pathlib
- subprocess
- sys

## tests/test_http_utils.py
- os
- pathlib
- shared.http_utils
- sys
- tempfile

## tests/test_aria_auto_execute_html.py
- pathlib

## tests/test_gradio_webhook_ui.py
- importlib.util
- os

## tests/test_agent_mode_delegation_contracts.py
- __future__
- pathlib
- pytest
- re

## tests/test_script_utils.py
- __future__
- pathlib
- shared.script_utils
- sys

## tests/test_train_vision.py
- importlib
- pathlib
- pytest

## tests/test_azure_quantum_runner.py
- importlib
- pathlib
- pytest
- sys

## tests/test_agi_persistence_endpoint.py
- function_app
- json
- pytest
- shared.agi_persistence_sqlite
- time
- unittest.mock

## tests/test_core_infra.py
- __future__
- core.agents.human_feedback_agent
- core.bus
- core.memory.store
- core.queue
- core.task
- datetime
- pytest

## tests/test_status_schema_fixtures.py
- __future__
- json
- pathlib
- pytest
- re
- scripts.ci_orchestrator
- scripts.integration_smoke

## tests/test_consensus_engine.py
- pathlib
- pytest
- shared.consensus_engine
- sys

## tests/test_gradio_demo.py
- importlib.util
- os
- sys
- types

## tests/test_azureml_validation.py
- importlib
- pathlib

## tests/test_performance_critical_fixes.py
- aria_web.server
- pathlib
- shared.chat_memory
- sys
- time
- traceback
- unittest.mock

## tests/test_training_health_report_workflow.py
- __future__
- json
- os
- pathlib
- subprocess
- sys
- textwrap
- yaml

## tests/test_writer_reviewer_prototype_workflow.py
- __future__
- importlib.util
- json
- pathlib
- pytest
- subprocess
- sys

## tests/test_dry_run_reminder_hook.py
- __future__
- json
- os
- pathlib
- subprocess
- sys

## tests/test_actionlint_shellcheck_workflows.py
- __future__
- pathlib
- pytest

## tests/test_quantum_sampler_nonfinite.py
- __future__
- pathlib
- quantum_llm
- sys

## tests/test_chat_memory.py
- __future__
- math
- os
- random
- shared.chat_memory
- unittest.mock

## tests/test_lora_adapter_completeness_guard_hook.py
- __future__
- json
- os
- pathlib
- subprocess
- sys
- tempfile

## tests/test_azure_openai_provider_resilience.py
- __future__
- importlib
- pytest
- typing
- unittest.mock

## tests/test_core_knowledge.py
- __future__
- core.knowledge.graph
- core.memory.store
- json

## tests/test_lmstudio_cache_thread_safety.py
- chat_providers
- pathlib
- sys
- threading
- time
- unittest

## tests/test_quantum_llm.py
- __future__
- asyncio
- json
- numpy
- pathlib
- pytest
- quantum_llm
- sys

## tests/test_workflow_yamllint_regressions.py
- __future__
- pathlib
- pytest
- yaml

## tests/test_ui_selenium.py
- json
- logging
- os
- pathlib
- pytest
- requests
- selenium
- selenium.webdriver.chrome.options
- selenium.webdriver.support.ui
- socket
- subprocess
- sys
- time
- urllib.parse

## tests/test_vision_inference.py
- PIL
- __future__
- base64
- binascii
- importlib.util
- io
- numpy
- pathlib
- pytest
- scripts.vision_inference
- sys
- time
- torch
- typing
- unittest.mock

## tests/test_app_validation.py
- __future__
- app
- io
- os
- pytest
- sys
- types

## tests/test_quantum_llm_quickstart.py
- __future__
- importlib.util
- pathlib
- pytest
- subprocess
- sys

## tests/test_setup_env_check.py
- __future__
- importlib.util
- json
- pathlib

## tests/test_provider_detection_cache.py
- __future__
- chat_providers
- pathlib
- sys
- time
- unittest.mock

## tests/test_actionlint_workflow.py
- __future__
- pathlib
- pytest
- yaml

## tests/test_integration_contract_gate_script.py
- __future__
- pathlib
- pytest

## tests/test_route_access_gates.py
- __future__
- function_app
- json
- pathlib
- pytest
- sys
- unittest.mock

## tests/test_devcontainer_config.py
- __future__
- json
- pathlib
- pytest

## tests/test_quantum_llm_provider_result_normalization.py
- __future__
- asyncio
- pathlib
- quantum_llm
- sys

## tests/test_web_app_security.py
- collections.abc
- flask.testing
- importlib.util
- json
- pathlib
- pytest
- sys
- time
- typing
- unittest.mock

## tests/test_summary_workflow.py
- __future__
- pathlib
- pytest
- yaml

## tests/test_best_model_selection.py

## tests/test_openai_provider_resilience.py
- __future__
- importlib
- pytest
- typing
- unittest.mock

## tests/test_auto_fix_workflow.py
- __future__
- pathlib
- pytest
- yaml

## tests/test_module_registry.py
- __future__
- pathlib
- pytest
- shared.core.module_registry
- sys
- unittest.mock

## tests/test_pages_workflow.py
- __future__
- pathlib
- pytest
- yaml

## tests/test_agents_md_audit_agent.py
- __future__
- json
- pathlib
- scripts.agents.agents_md_audit_agent
- scripts.agents.base
- sys

## tests/test_consolidated_html.py
- pathlib
- pytest
- re

## tests/test_codeql_workflow_paths_ignore.py
- __future__
- pathlib
- pytest
- subprocess
- yaml

## tests/test_master_orchestrator_schedule.py
- __future__
- datetime
- pytest
- scripts.master_orchestrator

## tests/test_agi_smoke.py
- function_app
- json
- pytest
- unittest.mock

## tests/test_email_notifications.py
- __future__
- json
- pytest
- shared.email_notifications

## tests/validate_performance_optimizations.py
- pathlib
- server
- shared.chat_memory
- sys
- time
- traceback

## tests/test_local_calc_extended.py
- __future__
- pathlib
- shared.local_calc
- sys

## tests/test_server_start_sys_executable.py
- pathlib
- pytest
- socket
- subprocess
- sys
- time

## tests/test_reflection_agent.py
- __future__
- core.agents.reflection_agent
- core.memory.store
- core.task
- json
- typing

## tests/test_aria_bot.py
- __future__
- aria_bot
- aria_bot.commit_system
- aria_bot.defaults
- aria_bot.executor
- aria_bot.planner
- aria_bot.registry
- aria_bot.validator
- json
- pathlib
- pytest
- subprocess
- sys

## tests/test_aria_server.py
- http
- importlib.util
- json
- pathlib
- re
- sys

## tests/test_local_settings.py
- __future__
- json
- os
- pathlib
- shared.local_settings
- sys

## tests/test_http_utils_extended.py
- __future__
- pathlib
- shared.http_utils
- sys

## tests/test_core_models.py
- __future__
- core
- core.agent
- core.registry
- core.task
- pathlib
- pytest
- subprocess
- sys

## tests/test_token_utils.py
- __future__
- shared.token_utils

## tests/test_local_dev_adapter.py
- __future__
- json
- local_dev_adapter
- pytest

## tests/test_orchestrator_health_in_status_endpoint.py
- importlib.util
- json
- pathlib
- sys
- tests.test_orchestrator_health_integration
- types

## tests/test_quantum_llm_circuit_cache.py
- __future__
- asyncio
- json
- numpy
- pathlib
- pytest
- quantum_llm
- sys
- time

## tests/test_aria_tests_workflow.py
- __future__
- pathlib
- pytest

## tests/test_dependabot_alert_gate_hook.py
- __future__
- importlib.util
- io
- json
- os
- pathlib
- sys
- time

## tests/test_cleanup_query_metrics.py
- cleanup_query_metrics
- pathlib
- pytest
- sys

## tests/test_dab_verify.py
- __future__
- json
- os
- pathlib
- pytest
- scripts.dab_verify

## tests/test_fast_validate.py
- __future__
- importlib
- importlib.util
- pathlib
- pytest

## tests/test_subscription_manager.py
- __future__
- datetime
- json
- pytest
- shared.subscription_manager

## tests/test_object_api_integration.py
- __future__
- http.server
- json
- pathlib
- pytest
- server
- socket
- sys
- threading
- time
- urllib.error
- urllib.request

## tests/test_aria_accessibility_html.py
- pathlib
- re

## tests/test_autotrain.py
- datetime
- importlib.util
- pathlib
- pytest
- sys

## tests/test_telemetry.py
- __future__
- os
- shared.telemetry
- sys
- unittest.mock

## tests/test_chat_web_embedded_script.py
- __future__
- pathlib

## tests/test_train_quantum_llm_chat.py
- __future__
- importlib.util
- pathlib
- types

## tests/test_evaluate_vision.py
- importlib
- pathlib
- pytest

## tests/test_ai_runner.py
- __future__
- os
- pathlib
- pytest
- shared.ai_runner
- shared.ai_safety_middleware
- subprocess
- unittest.mock

## tests/test_scorecard_workflow.py
- __future__
- pathlib
- pytest
- yaml

## tests/test_gradio_webhook.py
- os
- scripts

## tests/test_root_shims.py
- __future__
- importlib.util
- pathlib

## tests/test_gradio_hello.py
- importlib.util
- os
- pytest

## tests/test_quantum_provider_selection.py
- __future__
- importlib
- pytest
- sys
- types
- typing

## tests/test_marker_audit_agent.py
- __future__
- json
- pathlib
- scripts.agents.base
- scripts.agents.marker_audit_agent
- sys

## tests/test_lmstudio_agi_integration.py
- agi_provider
- chat_providers
- os
- pathlib
- sys
- unittest.mock

## tests/test_gradio_autoimprove.py
- importlib.util
- os

## tests/test_app_cli.py
- __future__
- app
- os
- pytest
- sys

## tests/test_db_logging.py
- __future__
- json
- os
- pathlib
- pytest
- shared.db_logging
- unittest.mock

## tests/test_docstring_audit_agent.py
- __future__
- json
- pathlib
- scripts.agents.base
- scripts.agents.docstring_audit_agent
- sys

## tests/test_run_main_if_referenced.py
- __future__
- importlib.util
- pathlib
- pytest

## tests/test_scope_drift_guard_hook.py
- __future__
- json
- os
- pathlib
- subprocess
- sys

## tests/test_quantum_llm_status_check.py
- __future__
- json
- pathlib
- pytest
- subprocess
- sys

## tests/test_orchestrator_health_integration.py
- datetime
- importlib.util
- json
- pathlib
- pytest
- sys
- types

## tests/test_cosmos_client.py
- __future__
- os
- shared.cosmos_client
- unittest.mock

## tests/test_enforce_task_complete_hook.py
- __future__
- json
- os
- pathlib
- pytest
- subprocess
- sys

## tests/test_gradio_utils.py
- scripts

## tests/test_status_dashboard.py
- __future__
- datetime
- importlib.util
- json
- pathlib

## tests/test_ai_safety_middleware.py
- __future__
- shared.ai_safety_middleware

## tests/test_ci_orchestrator_integration_baseline.py
- __future__
- pytest
- scripts.ci_orchestrator

## tests/test_local_dev_adapter_http.py
- __future__
- json
- local_dev_adapter
- pytest

## tests/test_local_summary_extended.py
- __future__
- pathlib
- pytest
- shared.local_summary
- sys

## tests/test_run_automation.py
- __future__
- importlib.util
- pathlib
- subprocess
- sys

## tests/test_mount_app_health.py
- __future__
- datetime
- fastapi.testclient
- importlib

## tests/test_no_verify_bypass_guard_hook.py
- __future__
- importlib.util
- io
- json
- pathlib
- sys

## tests/test_lora_cleanup.py
- json
- pathlib
- pytest

## tests/test_agi_persistence_auth.py
- function_app
- json
- pathlib
- pytest
- sys
- time
- unittest.mock

## tests/test_aria_tags_extended.py
- __future__
- pathlib
- server
- sys

## tests/test_stage_state_store.py
- __future__
- importlib.util
- json
- pathlib
- sys

## tests/test_sql_integration.py
- logging
- os
- pytest
- shared.sql_engine
- shared.sql_repository
- sqlalchemy
- typing

## tests/test_setup_verify_workflow_wiring.py
- __future__
- pathlib
- pytest
- tests.workflow_test_helpers
- yaml

## tests/test_job_yaml_schema.py
- pathlib
- pytest
- yaml

## tests/test_performance_keyword_sets.py
- pyodbc
- pytest
- server
- shared.chat_memory
- time

## tests/test_secrets_leak_guard_hook.py
- __future__
- json
- os
- pathlib
- subprocess
- sys

## tests/test_quantum_autorun_integration.py
- json
- pathlib
- pytest
- subprocess
- sys

## tests/test_provider_response_handling.py
- chat_providers
- pathlib
- sys
- unittest.mock

## tests/test_chat_memory_unit.py
- pytest
- shared
- threading
- unittest.mock

## tests/test_quantum_mcp_server_qiskit_compat.py
- __future__
- asyncio
- pathlib
- pytest
- qiskit
- quantum_mcp_server
- sys
- types

## tests/test_quantum_provider.py
- __future__
- importlib.util
- json
- pathlib
- pytest
- sys
- torch

## tests/test_lmstudio_agi_integration_impl.py
- __future__
- importlib.util
- pathlib
- urllib.request

## tests/test_quantum_llm_metrics_analyzer.py
- __future__
- importlib
- importlib.util
- pathlib
- pytest
- sys

## tests/test_function_app_endpoints.py
- azure.functions
- function_app
- inspect
- json
- pathlib
- pytest
- requests
- shared.request_validator
- sys
- torch
- types
- unittest.mock

## tests/test_training_integration.py
- asyncio
- mount.training_integration
- pathlib
- subprocess
- sys
- types
- unittest.mock

## tests/test_sql_local_tools.py
- __future__
- json
- os
- pathlib
- pytest
- scripts.sql_local_tools
- shared.sql_engine
- sys
- typing

## tests/test_run_repo_agents.py
- __future__
- json
- pathlib
- scripts
- scripts.agents.base
- sys

## tests/test_markdown_links_no_root_relative.py
- __future__
- pathlib
- pytest
- re

## tests/test_ignore_verify.py
- __future__
- pathlib
- pytest
- scripts.ignore_verify
- sys
- typing

## tests/test_ui_pyppeteer.py
- __future__
- asyncio
- contextlib
- json
- logging
- os
- pathlib
- pyppeteer
- pytest
- requests
- socket
- subprocess
- sys
- time

## tests/test_core_cli.py
- __future__
- core.__main__
- json
- pytest

## tests/test_watch_continuous_automation.py
- __future__
- datetime
- importlib
- os
- pathlib
- sys

## tests/test_validate_qiskit_env.py
- importlib.util
- pathlib

## tests/test_quantum_mcp_server_security.py
- __future__
- asyncio
- os
- pathlib
- pytest
- qiskit
- quantum_mcp_server
- sys
- tempfile
- time
- unittest.mock

## tests/test_orchestrator_backoff.py
- __future__
- json
- pathlib
- pytest
- scripts.autonomous_training_orchestrator
- shared.config
- sys
- tenacity

## tests/test_auto_merge_workflow.py
- __future__
- pathlib
- pytest
- yaml

## tests/test_quantum_web_ui.py
- __future__
- importlib.util
- pathlib
- pytest
- sys

## tests/test_generate_ai_tokens.py
- __future__
- json
- pathlib
- pytest
- scripts.generate_ai_tokens
- subprocess
- sys
- unittest.mock

## tests/test_validate_mcp_setup.py
- pathlib
- scripts.validate_mcp_setup

## tests/test_quantum_llm_trainer.py
- json
- pathlib
- pytest
- quantum_llm_trainer
- sys
- tempfile

## tests/test_avatar_integration.py
- importlib
- pathlib
- pytest

## tests/test_auto_assign_reviewers_workflow.py
- __future__
- pathlib
- pytest
- yaml

## tests/test_agi_memory_redis.py
- agi_provider
- shared.agi_memory_redis

## tests/test_local_agi_sse_integration.py
- importlib.util
- json
- pathlib
- sys
- unittest.mock

## tests/test_agent_with_tools_example.py
- __future__
- importlib.util
- pathlib
- pytest
- sys

## tests/test_aria_auto_execute.py
- pytest
- requests

## tests/test_sql_engine_extended.py
- __future__
- os
- pytest
- shared.sql_engine
- time
- unittest.mock

## tests/test_quantum_llm_stream_errors.py
- __future__
- asyncio
- pathlib
- quantum_llm
- sys

## tests/test_parallel_status.py
- json
- pathlib
- pytest

## tests/test_workflow_lint_blockers.py
- __future__
- pathlib
- pytest
- yaml

## tests/test_quantum_web_app.py
- importlib.util
- logging
- numpy
- pathlib
- pytest
- sys
- types

## tests/test_core_router.py
- __future__
- core.agent
- core.agents.llm_agent
- core.agents.planner_agent
- core.memory.store
- core.registry
- core.router
- core.runner
- core.task

## tests/test_sql_repository_extended.py
- __future__
- os
- pytest
- shared.sql_engine
- shared.sql_repository
- unittest.mock

## tests/test_dashboard_utils.py
- importlib.util
- json
- pathlib
- sys

## tests/test_regex_optimizations.py
- email_notifications
- final_validation
- function_app
- local
- pathlib
- pytest
- re
- sys
- time
- validate_dashboard

## tests/test_aria_index_provider_wiring.py
- pathlib

## tests/test_site_bundle_validation_workflow.py
- __future__
- pathlib
- pytest
- tests.workflow_test_helpers
- yaml

## tests/test_agi_provider.py
- agi_provider
- asyncio
- chat_providers
- collections.abc
- pathlib
- pytest
- sys

## tests/test_resource_monitor.py
- __future__
- importlib.util
- json
- pathlib

## tests/test_status_schema.py
- __future__
- json
- pathlib
- pytest
- scripts.ci_orchestrator
- scripts.master_orchestrator
- scripts.repo_automation

## tests/test_shared_config.py
- __future__
- shared.config

## tests/test_referral_system.py
- __future__
- json
- pytest
- shared.referral_system
- unittest.mock

## tests/test_notification_system.py
- importlib.util
- pathlib
- scripts.notification_system
- subprocess
- sys
- unittest.mock

## tests/test_auto_create_pr_workflow.py
- __future__
- pathlib
- pytest

## tests/test_keep_working_config.py
- __future__
- importlib.util
- json
- pathlib
- pytest

## tests/test_quantum_provider_checkpoint_loading.py
- __future__
- json
- pathlib
- pytest
- quantum_provider
- sys
- typing

## tests/test_training_integration_validation.py
- asyncio
- mount.training_integration
- pathlib
- sys
- types
- unittest.mock

## tests/test_core_runtime.py
- __future__
- core.agents.tool_agent
- core.runner
- core.task

## tests/test_lmstudio_http_fallback.py
- __future__
- chat_providers
- json
- pathlib
- sys
- unittest.mock

## tests/test_quantum_provider_checkpoint_metadata.py
- json
- pathlib
- pytest
- sys

## tests/test_app_local_fallback.py
- app
- os
- sys

## tests/test_dataset_write_guard_hook.py
- __future__
- json
- os
- pathlib
- subprocess
- sys

## tests/test_local_calc.py
- shared.local_calc
- unittest

## tests/test_phase_optimizations.py
- aria_web.server
- batch_evaluator
- pathlib
- pytest
- shared.chat_memory
- sys
- time
- unittest.mock

## tests/test_agi_persistence.py
- agi_provider
- json

## tests/test_evaluation_framework.py
- json
- pathlib
- subprocess
- sys

## tests/test_ollama_provider.py
- __future__
- chat_providers
- pathlib
- pytest
- sys
- unittest.mock
- urllib.error

## tests/test_markdown_quality_workflow.py
- __future__
- pathlib
- pytest
- yaml

## tests/test_performance_utils.py
- __future__
- json
- pathlib
- shared.performance_utils
- sys
- time
- types

## tests/test_local_dev_adapter-v2.py
- __future__
- json
- local_dev_adapter
- os
- pathlib
- pytest

## tests/test_json_utils.py
- __future__
- json
- pathlib
- pytest
- shared.json_utils
- sys

## tests/test_train_lora_model_resolution.py
- __future__
- importlib.util
- pathlib

## tests/test_quantum_code_llm.py
- __future__
- pathlib
- pytest
- quantum_code_llm
- sys
- torch

## tests/test_azureml_submission_gating.py
- importlib
- pathlib

## tests/test_data_struct_utils.py
- __future__
- generated_tools.data_struct_utils
- pathlib
- sys

## tests/conftest.py
- json
- pathlib
- pytest
- sys
- unittest.mock
- websockets
- websockets.client

## tests/test_code_coverage_workflow.py
- __future__
- pathlib
- pytest
- re

## tests/test_local_summary.py
- shared.local_summary
- unittest

## tests/test_job_queue.py
- __future__
- importlib.util
- pathlib
- pytest
- sys
- time

## tests/test_agi_panel_integration.py
- pathlib

## tests/test_evaluation_utils.py
- evaluation_utils
- json
- pathlib
- sys
- tempfile

## tests/test_autonomous_training_orchestrator.py
- __future__
- datetime
- importlib.util
- json
- os
- pathlib
- pytest
- signal

## tests/test_requirements_security_gate_hook.py
- __future__
- importlib.util
- io
- json
- pathlib
- sys

## tests/test_backup_manager.py
- json
- os
- pathlib
- scripts.backup_manager

## tests/test_parallel_train.py
- __future__
- asyncio
- importlib.util
- json
- pathlib
- pytest
- sys

## tests/test_qai_path_resolver.py
- __future__
- mount.path_resolver
- pathlib
- pytest

## tests/test_shared_logging.py
- __future__
- io
- json
- logging
- pathlib
- shared.logging
- sys

## tests/test_no_orphaned_gitlinks.py
- __future__
- pathlib
- subprocess

## tests/test_aria_command_presets.py
- json
- pathlib

## tests/test_test_runner.py
- __future__
- datetime
- json
- pathlib
- pytest
- scripts.test_runner
- subprocess
- sys

## tests/test_vram_calculator.py
- __future__
- pathlib
- pytest
- sys
- vram_calculator

## tests/test_runtime_env_extended.py
- __future__
- json
- pathlib
- shared.runtime_env
- subprocess
- sys

## tests/test_config.py
- __future__
- os
- pathlib
- pytest
- shared.config
- sys
- unittest.mock

## tests/test_agi_health_agent.py
- __future__
- json
- pathlib
- scripts.agents.agi_health_agent
- sys

## tests/test_gradio_maintenance.py
- os
- scripts
- time

## tests/test_groq_provider.py
- __future__
- chat_providers
- pathlib
- pytest
- sys
- unittest.mock
- urllib.error
- urllib.parse

## tests/test_dependabot_automerge_workflow.py
- __future__
- pathlib
- pytest
- yaml

## tests/test_http_ai_status_function.py
- __future__
- importlib.util
- json
- pathlib
- pytest
- time
- types

## tests/test_quantum_cost_gate_hook.py
- __future__
- json
- os
- pathlib
- subprocess
- sys

## tests/test_pr_checklist_guard_hook.py
- __future__
- importlib.util
- io
- json
- pathlib
- sys

## tests/test_lmstudio_mcp_agi_tools.py
- __future__
- agi_mcp_tools
- importlib.util
- pathlib
- pytest
- sys
- types

## tests/test_task_complete_stub.py
- __future__
- os
- pathlib
- subprocess

## tests/test_copilot_setup_workflow.py
- __future__
- pathlib
- pytest
- yaml

## tests/test_agi_backend_status.py
- shared.agi_backend_status

## tests/test_gradio_focused_workflow.py
- __future__
- pathlib
- pytest
- tests.workflow_test_helpers
- yaml

## tests/workflow_test_helpers.py
- __future__

## tests/test_file_cache.py
- __future__
- json
- pathlib
- pytest
- shared.file_cache
- sys
- threading
- time

## tests/test_github_actions_dataset.py
- json
- pathlib
- pytest
- subprocess
- sys

## tests/keep_working/test_keep_working.py
- json
- notebooks.keep_working_launcher
- pathlib
- sys

## tests/integration/test_quantum_llm_pipeline.py
- ai_projects.quantum_ml.src.quantum_llm.config
- ai_projects.quantum_ml.src.quantum_llm.pipeline
- pytest

## tests/unit/test_circuit_cache.py
- ai_projects.quantum_ml.src.quantum_llm.circuit_cache
- numpy
- pytest
- time

## tests/unit/test_quantum_llm_config.py
- ai_projects.quantum_ml.src.quantum_llm.config
- json
- pytest

## tests/unit/test_chat_cli_no_stream.py
- __future__
- argparse
- importlib.util
- pathlib
- types

## tests/unit/test_hello_world.py

## tests/unit/test_fallback_gesture_parser.py
- __future__
- pathlib
- server
- sys

## tests/unit/__init__.py

## tests/unit/test_quantum_llm_components.py
- ai_projects.quantum_ml.src.quantum_llm.quantum_embeddings
- ai_projects.quantum_ml.src.quantum_llm.quantum_router
- ai_projects.quantum_ml.src.quantum_llm.quantum_sampler
- numpy
- pytest

## tests/unit/test_local_settings.py
- __future__
- json
- os
- pathlib
- pytest
- shared.local_settings

## tests/unit/test_aria_schema_in_sync.py
- __future__
- json
- pathlib
- server
- sys

## tests/unit/test_devcontainer_json.py
- __future__
- json
- pathlib

## tests/unit/test_tags_to_actions.py
- pathlib
- server
- sys

## tests/unit/test_lm_studio_analyzer.py
- __future__
- importlib.util
- json
- pathlib
- pytest
- subprocess

## tests/unit/test_aria_schema_endpoint.py
- __future__
- http.server
- importlib.util
- json
- pathlib
- pytest
- sys
- threading
- urllib.request

## aria-bot/aria_bot/extract_helpers.py
- __future__
- collections.abc
- typing

## aria-bot/aria_bot/executor.py
- __future__
- collections.abc
- dataclasses
- logging
- planner
- registry
- risk_manager

## aria-bot/aria_bot/from collections.py
- collections.abc
- typing

## aria-bot/aria_bot/analyzer.py
- __future__
- collections.abc
- dataclasses
- logging
- pathlib
- registry
- risk_manager

## aria-bot/aria_bot/__init__.py
- __future__
- analyzer
- commit_system
- defaults
- executor
- orchestrator
- planner
- registry
- risk_manager
- validator

## aria-bot/aria_bot/registry.py
- __future__

## aria-bot/aria_bot/planner.py
- __future__
- analyzer
- collections.abc
- dataclasses
- defaults
- logging
- pathlib
- risk_manager

## aria-bot/aria_bot/validator.py
- __future__
- collections.abc
- dataclasses
- logging
- pathlib
- shutil
- subprocess

## aria-bot/aria_bot/cli.py
- __future__
- argparse
- collections.abc
- defaults
- json
- logging
- orchestrator
- pathlib
- sys
- typing

## aria-bot/aria_bot/defaults.py
- __future__

## aria-bot/aria_bot/__main__.py
- __future__
- cli

## aria-bot/aria_bot/risk_manager.py
- __future__
- collections.abc
- dataclasses
- os
- pathlib

## aria-bot/aria_bot/commit_system.py
- __future__
- collections.abc
- dataclasses
- logging
- pathlib
- shutil
- subprocess

## aria-bot/aria_bot/orchestrator.py
- __future__
- analyzer
- collections.abc
- commit_system
- dataclasses
- datetime
- defaults
- executor
- json
- logging
- os
- pathlib
- planner
- risk_manager
- time
- typing
- validator

## aria_web/server.py
- __future__
- importlib.util
- pathlib
- sys

## aria_web/__init__.py

## mount/chat_integration.py
- datetime
- json
- os
- pathlib
- subprocess
- sys
- typing

## mount/app.py
- asyncio
- chat_integration
- contextlib
- datetime
- fastapi
- fastapi.exception_handlers
- fastapi.middleware.cors
- fastapi.responses
- fastapi.staticfiles
- logging
- path_resolver
- pathlib
- pydantic
- quantum_integration
- time
- training_integration
- uuid
- uvicorn

## mount/train_max_performance.py
- argparse
- os
- pathlib
- psutil
- subprocess
- sys
- time
- torch
- typing

## mount/__init__.py

## mount/training_integration.py
- asyncio
- json
- logging
- os
- pathlib
- re
- subprocess
- sys
- typing

## mount/path_resolver.py
- __future__
- copy
- pathlib
- typing
- yaml

## mount/quantum_integration.py
- json
- pathlib
- re
- subprocess
- sys
- typing
- yaml

## function_app_domains/subscriptions.py
- __future__
- function_app_domains.access
- shared.email_notifications
- shared.stripe_webhooks
- shared.subscription_manager

## function_app_domains/aria_proxy.py
- __future__
- function_app_domains.access

## function_app_domains/agi.py
- __future__
- agi_provider
- function_app_domains.access
- shared.agi_persistence_sqlite

## function_app_domains/chat.py
- __future__
- function_app_domains.access
- tiktoken

## function_app_domains/__init__.py

## function_app_domains/access.py
- __future__

## function_app_domains/referrals.py
- __future__
- function_app_domains.access
- shared.referral_system

## function_app_domains/quantum.py
- __future__
- function_app_domains.access
- numpy
- pennylane
- quantum_classifier
- quantum_llm_trainer
- torch

## AI/test_agent.py
- dotenv
- evaluators
- os
- pytest_agent_evals

## AI/evaluators.py
- typing

## AI/microsoft_phi-silica-3.6_v1/scripts/otel_callback.py
- __future__
- importlib.util
- pathlib
- sys

## shared/http_utils.py
- logging
- pathlib
- typing

## shared/sql_repository.py
- __future__
- datetime
- logging
- os
- sql_engine
- sqlalchemy
- sqlite3

## shared/consensus_engine.py
- __future__
- collections.abc
- dataclasses

## shared/cosmos_client.py
- __future__
- azure.cosmos
- logging
- os
- time
- typing
- uuid

## shared/email_notifications.py
- datetime
- enum
- json
- logging
- pathlib
- re
- typing

## shared/telemetry.py
- __future__
- azure.monitor.opentelemetry
- logging
- os

## shared/local_calc.py
- __future__
- ast
- math
- operator
- re

## shared/json_utils.py
- __future__
- json
- pathlib
- time
- typing

## shared/token_utils.py
- __future__
- importlib.util
- pathlib
- sys

## shared/db_logging.py
- __future__
- json
- os
- pathlib
- pyodbc
- typing
- yaml

## shared/performance_utils.py
- collections
- collections.abc
- functools
- hashlib
- json
- pathlib
- tempfile
- time
- typing

## shared/agi_persistence.py
- __future__
- json
- os
- threading
- time
- typing
- uuid

## shared/config_validator.py
- __future__
- argparse
- dataclasses
- pathlib
- re
- sys
- typing
- yaml

## shared/agi_persistence_sqlite.py
- __future__
- json
- os
- sqlite3
- threading
- time
- typing
- uuid

## shared/local_summary.py
- __future__
- collections
- re

## shared/config.py
- __future__
- azure.identity
- azure.keyvault.secrets
- functools
- logging
- os
- pydantic
- pydantic_settings
- shared.local_settings
- typing

## shared/logging.py
- __future__
- json
- logging
- os
- sys
- time
- typing

## shared/script_utils.py
- __future__
- pathlib
- sys

## shared/__init__.py
- shared.file_cache
- shared.http_utils
- shared.import_helpers
- shared.json_utils
- shared.performance_utils
- shared.script_utils

## shared/import_helpers.py
- collections.abc
- logging
- typing

## shared/subscription_manager.py
- datetime
- enum
- json
- logging
- pathlib
- typing

## shared/agi_backend_status.py
- __future__
- os
- typing

## shared/runtime_env.py
- __future__
- collections.abc
- functools
- json
- pathlib
- subprocess
- sys
- textwrap

## shared/local_settings.py
- __future__
- collections.abc
- json
- os
- pathlib

## shared/early_stopping.py
- dataclasses
- json
- logging
- pathlib

## shared/stripe_webhooks.py
- datetime
- json
- logging
- pathlib
- shared.email_notifications
- shared.subscription_manager
- typing

## shared/chat_memory.py
- __future__
- collections.abc
- hashlib
- logging
- math
- openai
- os
- pyodbc
- struct
- threading
- time
- types
- typing

## shared/referral_system.py
- datetime
- json
- logging
- pathlib
- secrets
- shared.email_notifications
- typing

## shared/ai_runner.py
- __future__
- datetime
- logging
- os
- pathlib
- re
- shared.ai_safety_middleware
- shared.local_settings
- subprocess
- sys

## shared/chat_providers.py
- __future__
- importlib.util
- pathlib
- shared.local_settings
- sys

## shared/file_cache.py
- __future__
- json
- pathlib
- threading
- time
- typing

## shared/sql_engine.py
- __future__
- collections
- hashlib
- logging
- os
- sqlalchemy
- sqlite3
- time
- typing
- urllib.parse

## shared/request_validator.py
- __future__
- json
- logging

## shared/agi_memory_redis.py
- __future__
- collections.abc
- json
- logging
- os
- redis
- threading
- typing

## shared/evaluation_utils.py
- __future__
- json
- pathlib
- typing

## shared/ai_safety_middleware.py
- __future__
- collections.abc
- dataclasses
- datetime
- re
- typing

## shared/domain/__init__.py

## shared/utilities/__init__.py

## shared/infrastructure/__init__.py

## shared/premium/__init__.py

## shared/core/entrypoints_registry.py
- logging
- pathlib
- typing
- yaml

## shared/core/__init__.py
- module_registry

## shared/core/module_registry.py
- importlib
- importlib.util
- logging
- pathlib
- sys
- typing

## notebooks/test_agent.py
- dotenv
- evaluators
- os
- pytest_agent_evals

## notebooks/keep_working_launcher.py
- argparse
- dataclasses
- datetime
- getpass
- importlib
- json
- pathlib
- platform
- shlex
- shutil
- sqlite3
- subprocess
- sys
- textwrap
- time

## notebooks/evaluators.py
- typing

## notebooks/notebook_utils/utils.py
- json
- numpy
- pathlib
- random
- typing

## quantum-ai/web_app.py
- __future__
- collections.abc
- importlib.util
- logging
- numpy
- pathlib
- sys
- typing

## quantum-ai/examples/quantum_code_chat.py
- __future__
- argparse
- os
- quantum_code_llm
- sys

## quantum-ai/examples/quantum_code_llm_demo.py
- __future__
- os
- quantum_code_llm
- sys

## quantum-ai/scripts/validate_qiskit_env.py
- __future__
- importlib.util
- pathlib

## quantum-ai/scripts/smoke_quantum_code_llm.py
- __future__
- api
- argparse
- pathlib
- sys

## quantum-ai/src/__init__.py
- api

## quantum-ai/src/api.py
- quantum_code_llm
- typing

## quantum-ai/src/quantum_code_llm.py
- __future__
- dataclasses
- importlib.util
- math
- numpy
- pathlib
- pennylane
- random
- time
- torch
- torch.nn
- torch.utils.data
- typing

## aria_bot/__init__.py
- __future__
- importlib.util
- pathlib
- sys

## aria_bot/__main__.py
- __future__
- importlib

## scripts/aria_automation.py
- argparse
- dataclasses
- datetime
- json
- pathlib
- psutil
- signal
- socket
- subprocess
- sys
- threading
- time
- typing

## scripts/repo_health_automation.py
- __future__
- argparse
- collections.abc
- dataclasses
- datetime
- json
- pathlib
- subprocess
- sys
- time

## scripts/integration_smoke.py
- __future__
- argparse
- config_paths
- dataclasses
- json
- pathlib
- subprocess
- sys
- time
- typing
- urllib.error
- urllib.parse
- urllib.request

## scripts/final_validation.py
- functools
- pathlib
- re

## scripts/test_autonomous_agent.py
- pathlib
- pytest
- subprocess
- sys

## scripts/train_quantum_llm_chat.py
- argparse
- datetime
- inspect
- json
- logging
- pathlib
- quantum_transformer
- sys
- torch
- torch.nn
- torch.utils.data

## scripts/ignore_verify.py
- __future__
- pathlib
- subprocess

## scripts/setup_env_check.py
- json
- os
- pathlib
- subprocess
- sys
- urllib.request

## scripts/multi_agent.py
- __future__
- argparse
- concurrent.futures
- dataclasses
- datetime
- importlib
- json
- logging
- pathlib
- sys
- time
- typing

## scripts/autonomous_training_demo.py
- argparse
- datetime
- json
- logging
- math
- os
- pathlib
- random
- sys
- time

## scripts/validate_dashboard.py
- pathlib
- re

## scripts/evaluate_model.py
- argparse
- collections
- datetime
- evaluate_lora_model
- json
- pathlib
- sys

## scripts/evaluate_quantum_model.py
- __future__
- argparse
- json
- pathlib
- shared.evaluation_utils
- sys
- typing

## scripts/validate_foundry_config.py
- __future__
- json
- pathlib
- re

## scripts/validate_composite_actions.py
- __future__
- pathlib
- yaml

## scripts/generate_synthetic_autonomous_datasets.py
- __future__
- argparse
- json
- pathlib

## scripts/autonomous_code_agent.py
- __future__
- argparse
- dataclasses
- datetime
- glob
- importlib
- json
- logging
- os
- pathlib
- re
- subprocess
- sys
- time
- traceback
- typing
- urllib.error
- urllib.request

## scripts/test_runner.py
- argparse
- datetime
- importlib.util
- json
- pathlib
- re
- subprocess
- sys
- time

## scripts/dab_verify.py
- __future__
- argparse
- json
- os
- pathlib
- typing

## scripts/test_ai_improvements.py
- hybrid_qnn
- pathlib
- pytest
- sys
- torch
- traceback
- train_lora

## scripts/generate_ai_tokens.py
- __future__
- argparse
- dataclasses
- json
- logging
- os
- pathlib
- re
- secrets
- subprocess
- sys
- time
- typing
- urllib.error
- urllib.parse
- urllib.request

## scripts/autonomous_training_orchestrator.py
- __future__
- argparse
- atexit
- config_validator
- datetime
- json
- logging
- math
- os
- pathlib
- quantum_llm_trainer
- random
- shared.config_validator
- signal
- sys
- tenacity
- time
- typing
- yaml

## scripts/gradio_demo.py
- collections
- contextlib
- datetime
- gradio
- gradio_webhook
- gtts
- html
- importlib
- importlib.util
- json
- os
- pathlib
- pyttsx3
- re
- shared.chat_providers
- subprocess
- sys
- threading
- time
- typing
- uuid
- wave

## scripts/quantum_llm_metrics_analyzer.py
- __future__
- argparse
- json
- pathlib
- statistics
- typing

## scripts/generate_site_bundle.py
- __future__
- argparse
- datetime
- json
- pathlib

## scripts/repo_automation.py
- argparse
- config_paths
- config_validator
- dataclasses
- datetime
- importlib
- io
- json
- pathlib
- psutil
- shared.config_validator
- shlex
- signal
- subprocess
- sys
- threading
- time
- typing

## scripts/test_aria_automation.py
- os
- pathlib
- pytest
- subprocess
- sys

## scripts/quantum_llm_health_check.py
- __future__
- argparse
- json
- pathlib
- sys
- typing

## scripts/ci_orchestrator.py
- __future__
- argparse
- concurrent.futures
- config_paths
- dataclasses
- datetime
- json
- pathlib
- subprocess
- sys
- time
- typing

## scripts/sql_demo_simple.py
- pathlib
- sqlite3

## scripts/master_orchestrator.py
- __future__
- argparse
- config_paths
- config_validator
- dataclasses
- datetime
- json
- pathlib
- psutil
- shared.config_validator
- signal
- subprocess
- sys
- time
- typing
- yaml

## scripts/vram_calculator.py
- __future__
- argparse
- json
- subprocess
- torch

## scripts/quantum_llm_status_check.py
- __future__
- argparse
- json
- pathlib
- sys
- time
- typing

## scripts/repair_data_out_status.py
- __future__
- argparse
- datetime
- json
- pathlib
- re

## scripts/generate_github_actions_dataset.py
- __future__
- argparse
- dataclasses
- datetime
- hashlib
- json
- pathlib
- random
- typing
- yaml

## scripts/quantum_llm_trainer.py
- argparse
- datetime
- hybrid_qnn
- json
- logging
- numpy
- pathlib
- quantum_transformer
- random
- signal
- sys
- time
- torch
- torch.nn
- torch.utils.data
- typing
- yaml

## scripts/evaluate_azure_model.py
- __future__
- argparse
- json
- openai
- os
- pathlib
- shared.evaluation_utils
- sys
- time
- typing

## scripts/config_paths.py
- __future__
- pathlib

## scripts/aria_test.py
- pathlib
- peft
- sys
- torch
- transformers
- typing

## scripts/model_deployer.py
- __future__
- argparse
- datetime
- json
- pathlib
- shutil
- sys
- typing

## scripts/resource_monitor.py
- __future__
- argparse
- datetime
- json
- os
- pathlib
- psutil
- subprocess
- time
- typing

## scripts/run_repo_agents.py
- __future__
- argparse
- collections.abc
- dataclasses
- importlib
- json
- pathlib
- scripts.agents.base
- sys

## scripts/extract_chat_logs_dataset.py
- __future__
- argparse
- hashlib
- json
- pathlib
- random

## scripts/gradio_utils.py
- datetime

## scripts/__init__.py

## scripts/gradio_webhook.py
- json
- os
- time

## scripts/aria_test_final.py
- pathlib
- peft
- re
- sys
- torch
- transformers

## scripts/status_dashboard.py
- argparse
- datetime
- json
- os
- pathlib
- shared.json_utils
- socket
- sys
- time
- typing

## scripts/provider_smoke.py
- __future__
- json
- pathlib
- shared.core.module_registry
- shared.local_settings
- sys

## scripts/generate_aria_schema.py
- __future__
- json
- pathlib
- server
- sys

## scripts/quantum_autorun.py
- __future__
- argparse
- config_paths
- dataclasses
- datetime
- json
- logging
- pathlib
- sys
- tempfile
- typing
- yaml

## scripts/job_queue.py
- dataclasses
- datetime
- enum
- heapq
- json
- pathlib
- uuid

## scripts/check_docs_for_cli_note.py
- pathlib
- re
- sys

## scripts/validate_site_bundles.py
- __future__
- json
- pathlib
- sys

## scripts/azureml_ci_validate.py
- __future__
- os
- pathlib
- shutil
- subprocess

## scripts/generate_evaluation_set.py
- __future__
- hashlib
- json
- pathlib
- typing

## scripts/run_pytest_parallel.py
- __future__
- argparse
- collections.abc
- math
- os
- pathlib
- subprocess
- sys
- typing

## scripts/lm_studio_analyzer.py
- argparse
- json
- os
- pathlib
- subprocess

## scripts/batch_evaluator.py
- __future__
- argparse
- concurrent.futures
- dataclasses
- datetime
- json
- pathlib
- performance_utils
- shutil
- subprocess
- sys
- time
- typing
- yaml

## scripts/sql_local_tools.py
- __future__
- argparse
- collections.abc
- json
- os
- pathlib
- shared.sql_engine
- sqlalchemy
- sys
- typing

## scripts/pid_auto_edit_agent.py
- __future__
- argparse
- dataclasses
- datetime
- json
- os
- pathlib
- signal
- subprocess
- sys
- time
- typing

## scripts/dashboard.py
- datetime
- os
- pathlib
- shared.json_utils
- sys
- time
- typing

## scripts/local_llm_server.py
- datetime
- http.server
- json
- sys
- threading
- time

## scripts/cleanup_artifacts.py
- argparse
- datetime
- json
- pathlib
- time

## scripts/pre_commit_check.py
- argparse
- os
- pathlib
- re
- subprocess
- sys

## scripts/check_cli_scripts_sys_path.py
- pathlib
- re
- sys

## scripts/parallel_train.py
- argparse
- asyncio
- datetime
- fnmatch
- json
- math
- os
- pathlib
- peft
- re
- shutil
- sys
- torch
- transformers
- typing
- yaml

## scripts/train_with_early_stopping.py
- asyncio
- datasets
- json
- logging
- pathlib
- shared.early_stopping
- transformers
- typing

## scripts/training_analytics.py
- argparse
- datetime
- os
- pathlib
- shared.json_utils
- statistics
- sys

## scripts/gradio_hello.py
- __future__
- datetime
- gradio
- gtts
- hashlib
- importlib
- json
- os
- pathlib
- pyttsx3
- sys
- time
- typing

## scripts/lmstudio_chat_fix.py
- __future__
- argparse
- datetime
- json
- os
- pathlib
- sys
- typing
- urllib.error
- urllib.parse
- urllib.request

## scripts/backup_manager.py
- argparse
- datetime
- hashlib
- json
- os
- pathlib
- shutil
- sys
- tarfile
- torch
- typing

## scripts/monitor_autonomous_training.py
- argparse
- csv
- datetime
- json
- os
- pathlib
- subprocess
- time

## scripts/watch_continuous_automation.py
- __future__
- argparse
- collections.abc
- dataclasses
- datetime
- os
- pathlib
- re
- time

## scripts/agi_persistence_prune.py
- __future__
- argparse
- json
- os
- sqlite3
- sys
- time
- typing

## scripts/setup_local_llm.py
- __future__
- argparse
- importlib.util
- io
- json
- pathlib
- shared.chat_providers
- shared.local_settings
- shutil
- subprocess
- sys
- time
- urllib.error
- urllib.request

## scripts/auto_bootstrap.py
- __future__
- argparse
- datetime
- json
- pathlib
- subprocess
- sys
- time

## scripts/autotrain.py
- __future__
- argparse
- config_paths
- dataclasses
- datetime
- json
- os
- pathlib
- shlex
- subprocess
- sys
- typing
- yaml

## scripts/gradio_maintenance.py
- os
- time

## scripts/validate_mcp_suite.py
- __future__
- argparse
- json
- pathlib
- subprocess
- sys
- typing

## scripts/aria_test_debug.py
- pathlib
- peft
- sys
- torch
- transformers

## scripts/distributed_benchmark.py
- argparse
- datetime
- functools
- json
- multiprocessing
- numpy
- pandas
- pathlib
- sklearn.decomposition
- sklearn.model_selection
- sklearn.preprocessing
- sys
- time
- torch
- torch.nn
- torch.optim
- warnings

## scripts/validate_mcp_suite_drift.py
- __future__
- argparse
- json
- pathlib
- typing

## scripts/validate_eval_artifacts.py
- __future__
- argparse
- dataclasses
- json
- pathlib
- typing

## scripts/validate_eval_workflow_setup.py
- __future__
- argparse
- dataclasses
- json
- pathlib

## scripts/automate_core_files.py
- __future__
- argparse
- datetime
- json
- pathlib
- subprocess
- sys
- typing

## scripts/sql_demo.py
- pathlib
- shared.sql_engine
- sys
- typing

## scripts/evaluation_autorun.py
- __future__
- argparse
- datetime
- json
- pathlib
- sys
- typing
- yaml

## scripts/benchmark_performance.py
- json
- pathlib
- performance_utils
- sys
- tempfile
- time

## scripts/validate_optimizations.py
- aria_web.server
- batch_evaluator
- pathlib
- shared.chat_memory
- sys
- tempfile
- time

## scripts/vision_inference.py
- PIL
- __future__
- argparse
- base64
- io
- json
- logging
- numpy
- pathlib
- torch

## scripts/notification_system.py
- argparse
- json
- pathlib
- platform
- subprocess
- time
- win10toast

## scripts/self_learning_chat.py
- scripts.training.cli.self_learning_chat

## scripts/evaluate_openai_model.py
- __future__
- argparse
- json
- openai
- os
- pathlib
- shared.evaluation_utils
- sys
- time
- typing

## scripts/aria_demo.py
- pathlib
- peft
- re
- sys
- torch
- transformers

## scripts/autonomous_agent_tasks.py
- __future__
- dataclasses
- enum
- typing

## scripts/demo_quantum_llm.py
- json
- pathlib
- sys
- traceback
- yaml

## scripts/cleanup_query_metrics.py
- __future__
- re

## scripts/fast_validate.py
- __future__
- argparse
- collections.abc
- datetime
- importlib
- importlib.util
- json
- os
- pathlib
- subprocess
- sys
- typing

## scripts/evaluate_local_model.py
- __future__
- argparse
- evaluation_utils
- json
- pathlib
- sys
- time
- typing

## scripts/task_complete_mcp_server.py
- json
- sys

## scripts/test_watcher.py
- argparse
- pathlib
- shlex
- subprocess
- time

## scripts/test_repo_automation.py
- importlib.util
- pathlib
- pytest
- repo_automation
- subprocess
- sys

## scripts/system_health_check.py
- __future__
- argparse
- dataclasses
- datetime
- importlib
- json
- pathlib
- shutil
- socket
- subprocess
- sys
- typing

## scripts/validate_mcp_setup.py
- __future__
- argparse
- asyncio
- dataclasses
- json
- mcp
- mcp.client.stdio
- os
- pathlib
- re
- typing

## scripts/sync_docs_chat.py
- __future__
- pathlib
- shutil

## scripts/demos/code_generation_quickstart.py
- pathlib
- runpy
- sys

## scripts/demos/website_generator_demo.py
- pathlib
- runpy
- sys

## scripts/demos/code_generation_demo.py
- pathlib
- runpy
- sys

## scripts/training/__init__.py

## scripts/training/train_vision.py
- PIL
- __future__
- argparse
- numpy
- pathlib
- random
- sys
- torch
- torch.nn
- torch.utils.data

## scripts/evaluation/__init__.py

## scripts/evaluation/evaluate_vision.py
- __future__
- argparse
- json
- numpy
- pathlib
- scripts.training.train_vision
- sys
- torch
- torch.utils.data

## scripts/inference/__init__.py

## scripts/inference/vision_avatar_integration.py
- __future__
- argparse
- json
- pathlib
- scripts.training.train_vision
- sys
- torch
- torch.utils.data

## scripts/agents/marker_audit_agent.py
- __future__
- argparse
- collections.abc
- json
- pathlib
- re
- scripts.agents.base
- sys

## scripts/agents/docstring_audit_agent.py
- __future__
- argparse
- ast
- collections.abc
- dataclasses
- json
- pathlib
- scripts.agents.base
- sys

## scripts/agents/agi_health_agent.py
- __future__
- agi_provider
- argparse
- collections.abc
- json
- pathlib
- scripts.agents.base
- shared.agi_backend_status
- sys
- typing

## scripts/agents/__init__.py
- __future__
- scripts.agents.base

## scripts/agents/agents_md_audit_agent.py
- __future__
- argparse
- collections.abc
- datetime
- json
- pathlib
- re
- scripts.agents.base
- sys

## scripts/agents/status_freshness_agent.py
- __future__
- argparse
- collections.abc
- datetime
- json
- pathlib
- scripts.agents.base
- sys

## scripts/agents/base.py
- __future__
- collections.abc
- dataclasses
- datetime
- json
- pathlib

## functions/http_ai_runner/__init__.py
- azure.functions
- chat_providers
- json
- logging
- os
- pathlib
- sys
- typing

## functions/http_ai_routes/__init__.py
- azure.functions
- json
- pathlib

## functions/http_chat/function_app.py
- azure.functions
- chat_providers
- json
- logging
- pathlib
- shared.http_utils
- sys

## functions/http_ai_status/__init__.py
- azure.functions
- chat_providers
- importlib.util
- json
- os
- pathlib
- runtime_env
- shared.runtime_env
- sys
- threading
- time
- yaml

## functions/timer_ai_runner/__init__.py
- azure.functions
- chat_providers
- datetime
- logging
- os
- pathlib
- sys

## functions/http_ai_provider_probe/__init__.py
- azure.functions
- chat_providers
- json
- os
- pathlib
- sys

## functions/http_chat_web/function_app.py
- azure.functions
- pathlib
- shared.http_utils
- sys

## generated_tools/data_datetime_utils.py
- __future__
- collections.abc
- datetime

## generated_tools/data_struct_utils.py
- __future__
- collections.abc
- typing

## generated_tools/data_text_utils.py
- __future__
- collections
- collections.abc
- re
- typing

## generated_tools/data_validation_utils.py
- __future__
- collections.abc
- re
- typing

## generated_tools/data_table_utils.py
- collections
- collections.abc
- typing

## generated_tools/data_record_utils.py
- __future__
- collections.abc
- typing

## generated_tools/data_stats_utils.py
- __future__
- collections.abc

## generated_tools/data_compare_utils.py
- collections.abc
- typing

## tools/codegen_from_input.py
- __future__
- argparse
- dataclasses
- datetime
- json
- pathlib
- re
- typing

## tools/repo_cleanup/detect_large_files.py
- pathlib

## tools/repo_cleanup/ai_cleanup_agent.py
- pathlib

## tools/repo_cleanup/architecture_drift.py
- pathlib

## tools/repo_cleanup/detect_duplicate_code.py
- collections
- pathlib

## tools/repo_cleanup/validate_structure.py
- pathlib

## tools/repo_cleanup/generate_repo_inventory.py
- pathlib

## tools/repo_cleanup/autofix_cleanup.py
- pathlib
- shutil

## tools/repo_cleanup/repo_scorecard.py
- pathlib

## tools/repo_cleanup/detect_dead_code.py
- pathlib

## tools/repo_cleanup/generate_dependency_graph.py
- ast
- pathlib

## tools/codegen/code_generation_quickstart.py
- collections.abc
- importlib
- pathlib
- subprocess
- sys
- traceback
- typing

## tools/codegen/website_generator_guide.py
- sys
- traceback

## tools/codegen/code_generation_templates.py
- sys

## tools/codegen/website_generator_demo.py
- sys
- traceback

## tools/codegen/code_generation_demo.py
- sys
- traceback

## tools/codegen/code_generation_examples.py
- pathlib
- sys
- tool_maker
- traceback
- website_maker

## core/agent.py
- __future__
- abc
- core.task
- typing

## core/runner.py
- __future__
- core.agents.critique_agent
- core.agents.debate_agent
- core.agents.goal_evolution_agent
- core.agents.human_feedback_agent
- core.agents.hypothesis_agent
- core.agents.llm_agent
- core.agents.planner_agent
- core.agents.reasoning_agent
- core.agents.reflection_agent
- core.agents.summarizer_agent
- core.agents.tool_agent
- core.agents.training_agent
- core.bus
- core.cycle_observer
- core.knowledge.graph
- core.memory.store
- core.registry
- core.router
- core.task
- time
- typing

## core/bus.py
- __future__
- collections
- collections.abc
- threading
- typing

## core/__init__.py
- agent
- core.agent
- core.registry
- core.task
- pathlib
- registry
- sys
- task

## core/registry.py
- __future__
- collections.abc
- core.agent

## core/queue.py
- __future__
- asyncio
- collections.abc
- contextlib
- typing

## core/task.py
- __future__
- dataclasses
- typing
- uuid

## core/cycle_observer.py
- __future__
- core.bus
- core.memory.store
- time
- typing

## core/notifications.py
- __future__
- json
- typing
- urllib.error
- urllib.parse
- urllib.request

## core/__main__.py
- __future__
- argparse
- collections.abc
- core.runner
- json
- pathlib
- sys

## core/router.py
- __future__
- core.agent
- core.registry
- core.task
- typing

## core/knowledge/__init__.py
- core.knowledge.graph

## core/knowledge/graph.py
- __future__
- collections
- core.memory.store
- json
- typing
- yaml

## core/llm/__init__.py
- core.llm.client

## core/llm/client.py
- __future__
- collections.abc
- importlib
- json
- os

## core/memory/__init__.py
- __future__
- core.memory.store
- datetime
- json
- store

## core/memory/sqlite_backend.py
- __future__
- json
- sqlite3
- typing

## core/memory/store.py
- collections
- collections.abc
- copy
- datetime
- sqlite_backend
- threading
- typing
- uuid

## core/agents/training_agent.py
- __future__
- core.agent
- core.task
- json
- pathlib
- typing

## core/agents/goal_evolution_agent.py
- __future__
- collections.abc
- core.agent
- core.llm.client
- core.memory.store
- core.task
- json
- logging
- re

## core/agents/critique_agent.py
- __future__
- core.agent
- core.llm.client
- core.memory.store
- core.task
- json
- logging
- re
- typing

## core/agents/debate_agent.py
- __future__
- core.agent
- core.llm.client
- core.memory.store
- core.task
- json
- logging
- re
- typing

## core/agents/human_feedback_agent.py
- __future__
- core.agent
- core.bus
- core.memory.store
- core.task
- typing

## core/agents/tool_agent.py
- __future__
- collections.abc
- core.agent
- core.task
- json
- typing
- urllib.parse
- urllib.request

## core/agents/planner_agent.py
- __future__
- core.agent
- core.llm.client
- core.memory.store
- core.task
- json
- typing
- uuid

## core/agents/__init__.py
- core.agents.critique_agent
- core.agents.debate_agent
- core.agents.goal_evolution_agent
- core.agents.hypothesis_agent
- core.agents.llm_agent
- core.agents.planner_agent
- core.agents.reasoning_agent
- core.agents.reflection_agent
- core.agents.summarizer_agent
- core.agents.tool_agent
- core.agents.training_agent

## core/agents/llm_agent.py
- __future__
- core.agent
- core.llm.client
- core.task
- dataclasses
- json
- typing

## core/agents/summarizer_agent.py
- __future__
- core.agent
- core.llm.client
- core.memory.store
- core.task
- json
- logging
- re
- typing

## core/agents/reflection_agent.py
- __future__
- core.agent
- core.llm.client
- core.memory.store
- core.task
- json
- logging
- re
- typing

## core/agents/hypothesis_agent.py
- __future__
- core.agent
- core.llm.client
- core.memory.store
- core.task
- json
- logging
- re
- typing

## core/agents/reasoning_agent.py
- __future__
- core.agent
- core.llm.client
- core.memory.store
- core.task
- json
- logging
- re
- typing

## core/ingestion/pipeline.py
- __future__
- abc
- core.memory.store
- csv
- json
- typing
- urllib.parse
- urllib.request

## core/ingestion/__init__.py
- core.ingestion.pipeline

## my-agent-0b2avt/main.py
- agent_framework
- agent_framework.foundry
- agent_framework_foundry_hosting
- asyncio
- azure.identity.aio
- dotenv
- logging
- os

## my-agent-0b2avt/provision_memory_store.py
- azure.core.exceptions
- azure.identity
- dotenv
- importlib
- os
- typing

