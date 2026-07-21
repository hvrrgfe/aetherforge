using System;

namespace AetherForgeStudio.Models;

public class TokenUsage
{
    public int UsedTokens { get; set; }
    public int MaxTokens { get; set; }
    public int AgentCalls { get; set; }
    public int MaxCalls { get; set; }
    public double CacheHitRate { get; set; }
    public string ContextMode { get; set; } = "Incremental";
    public double PercentUsed => MaxTokens > 0 ? (double)UsedTokens / MaxTokens * 100 : 0;
}