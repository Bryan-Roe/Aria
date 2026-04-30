<!-- ⚠️  REQUIRED: Replace ALL placeholder text below before submitting.
     PRs that still contain the placeholder text will fail the CI description-check.

     Example of a well-filled description:
     ───────────────────────────────────────────────────────────────────────────
     ## Summary
     Rewrote `agi.prompt.md` to shift the AGI agent from a brainstorming/reasoning
     role to an execution-first autonomous coding agent. The previous prompt asked
     the model to "show its reasoning chain," which conflicted with the repo
     convention of hiding chain-of-thought from users. The new prompt enforces
     momentum-driven execution: plan → implement → verify, without exposing
     internal reasoning steps.

     ## Changes
     - Changed `agent: agent` → `agent: ai` with a descriptive `description` field
     - Replaced open-ended reasoning template with concrete execution workflow
     - Added Output Contract section enforcing concise, verifiable responses
     - Removed the instruction to expose the reasoning chain; added explicit constraint
       "Do not expose hidden chain-of-thought"

     ## Testing
     - Manually triggered the prompt in Copilot Chat with a sample coding task;
       confirmed the model produced a plan → implementation → summary without
       exposing internal chain-of-thought steps.
     - All unit tests passed: `python scripts/test_runner.py --unit`
     ───────────────────────────────────────────────────────────────────────────
-->

## Summary

<!-- 1-3 sentences: WHAT changed and WHY it is needed. Do not leave this as the default text. -->

## Changes

<!-- Bullet list of user-visible or behaviorally significant changes. At minimum one bullet. -->
-

## Testing

<!-- Describe how you validated the change. Include commands run and their outcomes. -->
-

## Checklist

- [ ] I added or updated tests for new behavior
- [ ] I updated relevant documentation (README, `.github/copilot-instructions.md`, instruction files)
- [ ] All unit tests pass locally (`python scripts/test_runner.py --unit`)
- [ ] No hardcoded secrets or API keys introduced
- [ ] PR title clearly describes the change (not a generic codespace/branch name)
