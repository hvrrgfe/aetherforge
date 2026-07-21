using System.Collections.Generic;
using System.Threading.Tasks;
using AetherForgeStudio.Models;
namespace AetherForgeStudio.Services;
public class AgentStateService
{
    private readonly AetherForgeApiService _api;
    public AgentStateService(AetherForgeApiService api) { _api = api; }

    public async Task<TaskInfo> GetTaskInfoAsync(string taskId)
    {
        var json = await _api.GetTaskStatusAsync(taskId);
        return System.Text.Json.JsonSerializer.Deserialize<TaskInfo>(json) ?? new TaskInfo { TaskId = taskId };
    }

    public async Task<string> StartTaskAsync(string goal, string constraints = "")
    {
        return await _api.CallToolAsync("agent_start_task", $"{{\"goal\":\"{goal}\",\"constraints\":\"{constraints}\"}}");
    }

    public async Task<string> GetEvidenceAsync(string taskId)
    {
        return await _api.CallToolAsync("agent_get_evidence", $"{{\"task_id\":\"{taskId}\"}}");
    }
}