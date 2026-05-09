using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Steps;

/// <summary>
/// State for the documentation review step, tracking review history.
/// </summary>
public class ReviewDocumentationState
{
    public ChatHistory? ChatHistory { get; set; }
    public int ReviewCount { get; set; } = 0;
}

/// <summary>
/// Result produced by the documentation review step.
/// </summary>
public sealed class ReviewResult
{
    /// <summary>Quality score from 1–10.</summary>
    public int Score { get; init; }

    /// <summary>Whether the documentation meets the quality bar (score >= 7).</summary>
    public bool Approved => Score >= 7;

    /// <summary>Detailed feedback for the documentation author.</summary>
    public string Feedback { get; init; } = string.Empty;

    /// <summary>The original documentation text that was reviewed.</summary>
    public string Documentation { get; init; } = string.Empty;
}

/// <summary>
/// A process step that uses an LLM to critically review generated product documentation
/// and return a quality score plus actionable feedback.
/// </summary>
public sealed class ReviewDocumentationStep : KernelProcessStep<ReviewDocumentationState>
{
    private ReviewDocumentationState _state = new();

    private const string SystemPrompt =
        """
        You are a senior technical writer and product marketing expert reviewing customer-facing product documentation.
        Your job is to evaluate documentation for clarity, completeness, accuracy, tone, and marketability.

        When given documentation to review, respond ONLY with a JSON object in this exact format:
        {
          "score": <integer 1-10>,
          "approved": <true if score >= 7, otherwise false>,
          "strengths": ["<strength 1>", "<strength 2>"],
          "issues": ["<issue 1>", "<issue 2>"],
          "suggestions": ["<suggestion 1>", "<suggestion 2>"],
          "summary": "<one-sentence overall verdict>"
        }

        Scoring guide:
        - 9–10: Exceptional — publish immediately
        - 7–8: Good — minor polish needed but approvable
        - 5–6: Average — significant improvements required before publishing
        - 1–4: Poor — major rewrite needed

        Be honest and specific. Vague feedback is useless.
        """;

    public override ValueTask ActivateAsync(KernelProcessStepState<ReviewDocumentationState> state)
    {
        this._state = state.State!;
        this._state.ChatHistory ??= new ChatHistory(SystemPrompt);
        return base.ActivateAsync(state);
    }

    [KernelFunction]
    public async Task<ReviewResult> ReviewDocumentationAsync(Kernel kernel, string documentation)
    {
        this._state.ReviewCount++;
        this._state.ChatHistory!.AddUserMessage(
            $"Please review the following product documentation:\n\n{documentation}");

        IChatCompletionService chatService = kernel.GetRequiredService<IChatCompletionService>();
        ChatMessageContent response = await chatService.GetChatMessageContentAsync(this._state.ChatHistory);

        string rawJson = response.Content?.Trim() ?? "{}";

        // Strip markdown code fences if the model wrapped the JSON
        if (rawJson.StartsWith("```"))
        {
            rawJson = rawJson
                .Split('\n')
                .Where(line => !line.TrimStart().StartsWith("```"))
                .Aggregate((a, b) => $"{a}\n{b}")
                .Trim();
        }

        int score = 5;
        string feedback = rawJson;

        try
        {
            using System.Text.Json.JsonDocument doc = System.Text.Json.JsonDocument.Parse(rawJson);
            System.Text.Json.JsonElement root = doc.RootElement;

            if (root.TryGetProperty("score", out System.Text.Json.JsonElement scoreEl))
                score = scoreEl.GetInt32();

            var parts = new List<string>();
            if (root.TryGetProperty("summary", out System.Text.Json.JsonElement summaryEl))
                parts.Add($"Summary: {summaryEl.GetString()}");

            if (root.TryGetProperty("strengths", out System.Text.Json.JsonElement strengthsEl))
            {
                var items = strengthsEl.EnumerateArray().Select(e => e.GetString()).Where(s => s != null);
                parts.Add($"Strengths: {string.Join("; ", items)}");
            }

            if (root.TryGetProperty("issues", out System.Text.Json.JsonElement issuesEl))
            {
                var items = issuesEl.EnumerateArray().Select(e => e.GetString()).Where(s => s != null);
                if (items.Any())
                    parts.Add($"Issues: {string.Join("; ", items)}");
            }

            if (root.TryGetProperty("suggestions", out System.Text.Json.JsonElement suggestionsEl))
            {
                var items = suggestionsEl.EnumerateArray().Select(e => e.GetString()).Where(s => s != null);
                if (items.Any())
                    parts.Add($"Suggestions: {string.Join("; ", items)}");
            }

            feedback = string.Join("\n", parts);
        }
        catch
        {
            // If parsing fails keep the raw JSON as feedback and use default score
        }

        // Add assistant response to history so follow-up reviews have context
        this._state.ChatHistory.AddAssistantMessage(rawJson);

        return new ReviewResult
        {
            Score = Math.Clamp(score, 1, 10),
            Feedback = feedback,
            Documentation = documentation,
        };
    }
}
