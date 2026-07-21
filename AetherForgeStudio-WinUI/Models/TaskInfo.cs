namespace AetherForgeStudio.Models;
public class TaskInfo
{
    /// <summary>Unique task identifier.</summary>
    public string TaskId { get; set; } = "";
    /// <summary>Task objective/goal description.</summary>
    public string Goal { get; set; } = "";
    /// <summary>Current execution phase.</summary>
    public string Phase { get; set; } = "pending";
    /// <summary>Progress percentage (0-1).</summary>
    public double Progress { get; set; }
    public int PassedChecks { get; set; }
    /// <summary>Number of failed verification checks.</summary>
    public int FailedChecks { get; set; }
    /// <summary>The world revision this task operates on.</summary>
    public int WorldRevision { get; set; }
    /// <summary>Error message if task failed.</summary>
    public string Error { get; set; } = "";
}