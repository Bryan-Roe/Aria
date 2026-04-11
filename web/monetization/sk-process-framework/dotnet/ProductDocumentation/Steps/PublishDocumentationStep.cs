using Microsoft.SemanticKernel;

namespace Steps;

/// <summary>
/// Metadata returned after documentation is published.
/// </summary>
public sealed class PublishResult
{
    public bool Success { get; init; }
    public string OutputPath { get; init; } = string.Empty;
    public int WordCount { get; init; }
    public DateTimeOffset PublishedAt { get; init; }
    public string Message { get; init; } = string.Empty;
}

/// <summary>
/// Publishes finalized product documentation to disk and returns publish metadata.
/// </summary>
public sealed class PublishDocumentationStep : KernelProcessStep
{
    private static readonly string OutputDirectory =
        Path.Combine(AppContext.BaseDirectory, "published");

    [KernelFunction]
    public PublishResult PublishDocumentation(string documentation, int reviewScore = 0)
    {
        try
        {
            Directory.CreateDirectory(OutputDirectory);

            string timestamp = DateTimeOffset.UtcNow.ToString("yyyyMMdd-HHmmss");
            string fileName = $"product-documentation-{timestamp}.md";
            string outputPath = Path.Combine(OutputDirectory, fileName);

            // Add a front-matter header with publish metadata
            string header =
                $"""
                ---
                published_at: {DateTimeOffset.UtcNow:O}
                review_score: {reviewScore}
                generator: Contoso SK Process Framework
                ---

                """;

            File.WriteAllText(outputPath, header + documentation);

            int wordCount = documentation.Split(
                [' ', '\t', '\n', '\r'], StringSplitOptions.RemoveEmptyEntries).Length;

            return new PublishResult
            {
                Success = true,
                OutputPath = outputPath,
                WordCount = wordCount,
                PublishedAt = DateTimeOffset.UtcNow,
                Message = $"Documentation published successfully ({wordCount} words, review score: {reviewScore}/10).",
            };
        }
        catch (Exception ex)
        {
            return new PublishResult
            {
                Success = false,
                Message = $"Failed to publish documentation: {ex.Message}",
                PublishedAt = DateTimeOffset.UtcNow,
            };
        }
    }
}
