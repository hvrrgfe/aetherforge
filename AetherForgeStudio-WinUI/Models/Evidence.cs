using System;
using System.Collections.Generic;

namespace AetherForgeStudio.Models;

public class Evidence
{
    /// <summary>Unique identifier for this evidence record.</summary>
    public string EvidenceId { get; set; } = string.Empty;
    /// <summary>Type/category of evidence (tool_call, assertion, etc.).</summary>
    public string Kind { get; set; } = string.Empty;
    /// <summary>Source tool or component that produced this evidence.</summary>
    public string Source { get; set; } = string.Empty;
    /// <summary>Current status of this evidence (pending/verified/rejected).</summary>
    public string Status { get; set; } = string.Empty;
    public Dictionary<string, object> Data { get; set; } = new();
}