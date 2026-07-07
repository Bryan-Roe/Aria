# Copyright (c) Microsoft. All rights reserved.
# cspell:ignore dotenv

"""Provision the Azure AI Foundry Memory Store used by this sample.

Creates the memory store named by ``MEMORY_STORE_NAME`` if it does not
already exist. The store is configured with the user-profile
capability so the agent can remember stable facts about a user across
sessions; chat-summary is disabled to keep the demo focused on durable
preferences. Safe to re-run: if a store with the same name already
exists, the script leaves it alone.

Usage (from this directory, with the venv activated and ``az login`` done):

    python provision_memory_store.py

Required env vars (also read from a local ``.env`` file if present):

    FOUNDRY_PROJECT_ENDPOINT                      e.g.
        https://<account>.services.ai.azure.com/
        api/projects/<project>
    AZURE_AI_MODEL_DEPLOYMENT_NAME                Chat model deployment
                                                  used by the memory store
    AZURE_AI_EMBEDDING_MODEL_DEPLOYMENT_NAME      Embedding model
                                                  deployment used by
                                                  the memory store
    MEMORY_STORE_NAME                             Name of the memory store to
                                                  create

Your identity needs ``Azure AI User`` on the Foundry project scope.
"""

import os
from importlib import import_module
from typing import Any, Protocol, cast

from azure.core.exceptions import ResourceNotFoundError
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv

load_dotenv()


class _NamedResource(Protocol):  # pylint: disable=too-few-public-methods
    name: str
    id: str


class _MemoryStores(Protocol):
    def get(self, *, name: str) -> _NamedResource:
        """Return a memory store by name."""
        ...

    def create(
        self,
        *,
        name: str,
        description: str,
        definition: object,
    ) -> _NamedResource:
        """Create and return a memory store."""
        ...


class _ProjectBeta(Protocol):  # pylint: disable=too-few-public-methods
    memory_stores: _MemoryStores


class _ProjectClient(Protocol):  # pylint: disable=too-few-public-methods
    beta: _ProjectBeta


def _load_projects_symbols() -> tuple[Any, Any, Any]:
    """Load Azure AI Projects types only when the script runs."""
    try:
        projects_module = import_module("azure.ai.projects")
    except ModuleNotFoundError as exc:
        raise RuntimeError("Missing dependency 'azure-ai-projects'. Install it before running this script.") from exc

    return (
        projects_module.AIProjectClient,
        projects_module.MemoryStoreDefaultDefinition,
        projects_module.MemoryStoreDefaultOptions,
    )


def main() -> None:
    """Create the configured memory store if it does not already exist."""
    (
        ai_project_client_cls,
        memory_store_definition_cls,
        memory_store_options_cls,
    ) = _load_projects_symbols()

    endpoint = os.environ["FOUNDRY_PROJECT_ENDPOINT"]
    memory_store_name = os.environ["MEMORY_STORE_NAME"]
    chat_model = os.environ["AZURE_AI_MODEL_DEPLOYMENT_NAME"]
    embedding_model = os.environ["AZURE_AI_EMBEDDING_MODEL_DEPLOYMENT_NAME"]

    with (
        DefaultAzureCredential() as credential,
        ai_project_client_cls(
            endpoint=endpoint,
            credential=credential,
            allow_preview=True,
        ) as project,
    ):
        memory_stores: _MemoryStores = cast(_ProjectClient, project).beta.memory_stores

        try:
            existing: _NamedResource = memory_stores.get(name=memory_store_name)
            print(f"Memory store '{existing.name}' already exists (id={existing.id}); leaving as-is.")
            return
        except ResourceNotFoundError:
            print(f"Memory store '{memory_store_name}' not found; creating it.")

        print(f"Creating memory store '{memory_store_name}'...")
        definition: object = memory_store_definition_cls(
            chat_model=chat_model,
            embedding_model=embedding_model,
            options=memory_store_options_cls(
                chat_summary_enabled=False,
                user_profile_enabled=True,
                user_profile_details=(
                    "Avoid irrelevant or sensitive data, such as age, finances, precise location, and credentials."
                ),
            ),
        )
        created: _NamedResource = memory_stores.create(
            name=memory_store_name,
            description=("Memory store for the Agent Framework foundry-hosted memory sample"),
            definition=definition,
        )
        print(f"Created memory store '{created.name}' (id={created.id}).")

        # Verify the store actually exists on the service by reading it back.
        # ``create`` returns the requested definition, but a follow-up
        # ``get`` confirms the store is persisted and reachable at runtime.
        try:
            verified: _NamedResource = memory_stores.get(name=memory_store_name)
        except ResourceNotFoundError as exc:
            raise RuntimeError(
                "Memory store "
                f"'{memory_store_name}' was not found "
                "after creation; the service may not have "
                "persisted it."
            ) from exc
        print(f"Verified memory store '{verified.name}' is available on the service (id={verified.id}).")


if __name__ == "__main__":
    main()
