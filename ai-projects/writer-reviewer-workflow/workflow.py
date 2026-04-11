"""
Writer-Reviewer multi-agent workflow definition.

Two agents collaborate:
  - Writer  : receives the user request and produces initial content.
  - Reviewer: refines the Writer's content into a polished, final version.

Both agents are output executors — they each yield an AgentResponseUpdate so
the caller can observe the full collaborative exchange and surface the Reviewer's
refined text as the final result.
"""

import os

from agent_framework import WorkflowBuilder
from agent_framework.azure import AzureAIClient
from azure.identity.aio import DefaultAzureCredential

# ---------------------------------------------------------------------------
# Agent instructions
# ---------------------------------------------------------------------------

WRITER_INSTRUCTIONS = """\
You are a skilled creative content writer.
When given a topic or request, craft compelling, well-structured content.
Keep your response focused and concise — 2-4 short paragraphs.
Output only the content itself, with no preamble like "Here is the content:".
"""

REVIEWER_INSTRUCTIONS = """\
You are an expert content reviewer and editor.
You receive content produced by the Writer and deliver a refined, polished version.

Rules:
- Improve clarity, flow, tone, and impact.
- Fix any grammatical or structural issues.
- Output ONLY the final refined text — no critique headers, no meta-commentary,
  no "Here is the revised version:" preamble. Just the improved content.
"""


# ---------------------------------------------------------------------------
# Workflow factory
# ---------------------------------------------------------------------------


def build_workflow():
    """
    Build the Writer-Reviewer workflow.

    Reads configuration from the environment:
      FOUNDRY_PROJECT_ENDPOINT        – Azure AI Foundry project endpoint URL
      FOUNDRY_MODEL_DEPLOYMENT_NAME   – Name of the deployed chat model

    Returns:
        An agent_framework Workflow (writer -> reviewer, both yield output).
    """
    endpoint = os.environ.get("AZURE_AI_PROJECT_ENDPOINT", "").strip()
    model = os.environ.get("FOUNDRY_MODEL_DEPLOYMENT_NAME", "").strip()

    if not endpoint:
        raise ValueError(
            "AZURE_AI_PROJECT_ENDPOINT is not set. "
            "Add it to your .env file or environment variables."
        )
    if not model:
        raise ValueError(
            "FOUNDRY_MODEL_DEPLOYMENT_NAME is not set. "
            "Deploy a model in your Foundry project and add its name to .env."
        )

    credential = DefaultAzureCredential()

    # IMPORTANT: use separate AzureAIClient instances – the agent name is
    # registered at the client level, so sharing a single client would
    # overwrite the previous agent's name.
    writer = AzureAIClient(
        project_endpoint=endpoint,
        credential=credential,
    ).as_agent(
        name="Writer",
        model=model,
        instructions=WRITER_INSTRUCTIONS,
    )

    reviewer = AzureAIClient(
        project_endpoint=endpoint,
        credential=credential,
    ).as_agent(
        name="Reviewer",
        model=model,
        instructions=REVIEWER_INSTRUCTIONS,
    )

    # Wire the workflow: user request -> Writer -> Reviewer
    # Both agents yield AgentResponseUpdate (they are output executors).
    workflow = WorkflowBuilder(start_executor=writer).add_edge(writer, reviewer).build()
    return workflow
