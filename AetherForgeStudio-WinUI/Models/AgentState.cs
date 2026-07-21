namespace AetherForgeStudio.Models;
public class AgentState
{
    /// <summary>Agent display name.</summary>
    public string Name { get; set; } = "";
    /// <summary>Current status (idle/working/error).</summary>
    public string Status { get; set; } = "idle";
    /// <summary>Agent role (Explorer/Planner/Builder/Verifier/Critic).</summary>
    public string Role { get; set; } = "";
    /// <summary>Number of facts discovered.</summary>
    public int Facts { get; set; }
    /// <summary>Number of issues found.</summary>
    public int Issues { get; set; }
}