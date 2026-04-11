using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Steps;

public sealed class GenerateDocumentationStep : KernelProcessStep<GeneratedDocumentationState>
{
    private GeneratedDocumentationState _state = new();

    private const string SystemPrompt =
        """
        You are an expert technical writer for Contoso. Your job is to write high-quality, engaging,
        customer-facing product documentation using ONLY the product information provided to you.

        Always structure your documentation with these sections:
        ## Overview
        A compelling two-to-three sentence summary that excites the customer.

        ## Key Features
        A bulleted list of standout features with brief, benefit-focused descriptions.

        ## Getting Started
        Step-by-step instructions to set up and first use the product.

        ## Troubleshooting
        Common issues customers might encounter and clear solutions.

        ## FAQ
        Three to five frequently asked questions with concise answers.

        Writing guidelines:
        - Use an enthusiastic but professional tone.
        - Lead with customer benefits, not technical specifications.
        - Keep sentences short and scannable.
        - Avoid jargon unless it is explained inline.
        - Make the product sound amazing — customers should feel excited to use it.

        If reviewer feedback is provided, incorporate every suggestion and rewrite the full document.
        """;

    public override ValueTask ActivateAsync(KernelProcessStepState<GeneratedDocumentationState> state)
    {
        this._state = state.State!;
        this._state.ChatHistory ??= new ChatHistory(SystemPrompt);
        return base.ActivateAsync(state);
    }

    /// <summary>Generate documentation from product info (initial generation).</summary>
    [KernelFunction]
    public async Task<string> GenerateDocumentationAsync(Kernel kernel, string productInfo)
    {
        this._state.ChatHistory!.AddUserMessage(
            $"Please generate customer-facing documentation for the following product:\n\n{productInfo}");

        IChatCompletionService chatService = kernel.GetRequiredService<IChatCompletionService>();
        ChatMessageContent response = await chatService.GetChatMessageContentAsync(this._state.ChatHistory);

        string documentation = response.Content ?? string.Empty;
        this._state.ChatHistory.AddAssistantMessage(documentation);
        this._state.GenerationCount++;
        return documentation;
    }

    /// <summary>Regenerate documentation incorporating reviewer feedback.</summary>
    [KernelFunction]
    public async Task<string> RegenerateWithFeedbackAsync(Kernel kernel, string reviewFeedback, string originalDocumentation)
    {
        // Inject the original doc as assistant context if history is empty (e.g. after a cold restart)
        if (!this._state.ChatHistory!.Any(m => m.Role == AuthorRole.Assistant))
            this._state.ChatHistory.AddAssistantMessage(originalDocumentation);

        this._state.ChatHistory.AddUserMessage(
            $"""
            A reviewer scored this documentation and provided the following feedback. Please rewrite the full documentation incorporating every suggestion:

            Reviewer feedback:
            {reviewFeedback}

            Produce the complete revised document using the same structured format as before.
            """);

        IChatCompletionService chatService = kernel.GetRequiredService<IChatCompletionService>();
        ChatMessageContent response = await chatService.GetChatMessageContentAsync(this._state.ChatHistory);

        string revised = response.Content ?? string.Empty;
        this._state.ChatHistory.AddAssistantMessage(revised);
        this._state.GenerationCount++;
        return revised;
    }
}

public class GeneratedDocumentationState
{
    public ChatHistory? ChatHistory { get; set; }

    /// <summary>How many times documentation has been generated or regenerated.</summary>
    public int GenerationCount { get; set; } = 0;
}
