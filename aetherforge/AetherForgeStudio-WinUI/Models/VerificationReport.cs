using System;
using System.Collections.Generic;

namespace AetherForgeStudio.Models;

public class VerificationReport
{
    /// <summary>The task ID this report belongs to.</summary>
    public string TaskId { get; set; } = string.Empty;
    /// <summary>Overall verification status (passed/failed).</summary>
    public string Status { get; set; } = string.Empty;
    public int PassedChecks { get; set; }
    public int FailedChecks { get; set; }
    public bool CommitAllowed { get; set; }
    public List<string> BlockingReasons { get; set; } = new();
    public List<Dictionary<string, object>> Checks { get; set; } = new();
}