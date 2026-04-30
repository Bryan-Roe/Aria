## Summary

Updates the AGI prompt/docs to clarify chain-of-thought handling: keep internal reasoning hidden by default, and only expose reasoning when explicitly using the public `reason.prompt.md` workflow.

## Changes
- Refines prompt guidance around chain-of-thought vs. user-visible reasoning
- Aligns prompt documentation/examples so reviewers and contributors know which prompt to use for which behavior

## Validation
- Reviewed prompt usage locations and ensured the guidance matches existing prompt files
- No runtime code paths changed

## Checklist
- [x] No production code changes
- [x] No tests required (documentation/prompt-only change)
