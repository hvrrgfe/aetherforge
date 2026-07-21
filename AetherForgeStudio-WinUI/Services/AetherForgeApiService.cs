using System;
using System.Net.Http;
using System.Text;
using System.Threading.Tasks;
using System.Text.Json;
namespace AetherForgeStudio.Services;
public class AetherForgeApiService
{
    private readonly HttpClient _http;
    public AetherForgeApiService(string baseUrl = "http://127.0.0.1:7890")
    {
        _http = new HttpClient { BaseAddress = new Uri(baseUrl) };
    }
    public async Task<string> CallToolAsync(string tool, string argsJson = "{}")
    {
        var payload = JsonSerializer.Serialize(new { tool, arguments = JsonSerializer.Deserialize<System.Text.Json.JsonElement>(argsJson) });
        var response = await _http.PostAsync("/api/tool", new StringContent(payload, Encoding.UTF8, "application/json"));
        return await response.Content.ReadAsStringAsync();
    }
    public async Task<string> GetWorldStateAsync()
    {
        var response = await _http.GetAsync("/api/world");
        return await response.Content.ReadAsStringAsync();
    }
    public async Task<string> GetTaskStatusAsync(string taskId)
    {
        var response = await _http.GetAsync($"/api/task/{taskId}");
        return await response.Content.ReadAsStringAsync();
    }
}