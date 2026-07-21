using System;
using System.Net.WebSockets;
using System.Text;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using System.Collections.Generic;

namespace AetherForgeStudio.Services;

public class WebSocketService
{
    private ClientWebSocket _ws = null!;
    private CancellationTokenSource _cts = null!;
    private readonly string _url;
    public event Action<string, string> OnAgentStatusChanged = null!;
    public event Action<int, List<Dictionary<string, object>>> OnWorldChanged = null!;
    public event Action<string, int, int, int> OnVerificationUpdated = null!;
    public event Action<string> OnConnected = null!;
    public event Action<string> OnDisconnected = null!;

    public WebSocketService(string url = "ws://127.0.0.1:7890/ws")
    {
        _url = url;
    }

    public async Task ConnectAsync()
    {
        _ws = new ClientWebSocket();
        _cts = new CancellationTokenSource();
        try
        {
            await _ws.ConnectAsync(new Uri(_url), _cts.Token);
            OnConnected?.Invoke("Connected");
            _ = Task.Run(() => ReceiveLoop(_cts.Token));
        }
        catch (Exception ex)
        {
            OnDisconnected?.Invoke($"Connection failed: {ex.Message}");
        }
    }

    private async Task ReceiveLoop(CancellationToken ct)
    {
        var buffer = new byte[8192];
        while (!ct.IsCancellationRequested && _ws.State == WebSocketState.Open)
        {
            try
            {
                var result = await _ws.ReceiveAsync(new ArraySegment<byte>(buffer), ct);
                if (result.MessageType == WebSocketMessageType.Close) break;
                var json = Encoding.UTF8.GetString(buffer, 0, result.Count);
                ProcessEvent(json);
            }
            catch (Exception ex) { System.Diagnostics.Debug.WriteLine($"WS recv error: {ex.Message}"); break; }
        }
        OnDisconnected?.Invoke("Disconnected");
    }

    private void ProcessEvent(string json)
    {
        try
        {
            using var doc = JsonDocument.Parse(json);
            var root = doc.RootElement;
            var type = root.GetProperty("type").GetString();

            switch (type)
            {
                case "agent_status_changed":
                    var role = root.GetProperty("agent_role").GetString()!;
                    var status = root.GetProperty("data").GetProperty("status").GetString()!;
                    OnAgentStatusChanged?.Invoke(role, status);
                    break;

                case "world_changed":
                    var rev = root.GetProperty("data").GetProperty("world_revision").GetInt32();
                    var changes = new List<Dictionary<string, object>>();
                    if (root.GetProperty("data").TryGetProperty("changes", out var ch))
                    {
                        foreach (var c in ch.EnumerateArray())
                        {
                            var d = new Dictionary<string, object>();
                            foreach (var p in c.EnumerateObject())
                                d[p.Name] = p.Value.ToString();
                            changes.Add(d);
                        }
                    }
                    OnWorldChanged?.Invoke(rev, changes);
                    break;

                case "verification_updated":
                    var taskId = root.GetProperty("task_id").GetString()!;
                    var data = root.GetProperty("data");
                    var passed = data.GetProperty("passed_checks").GetInt32();
                    var failed = data.GetProperty("failed_checks").GetInt32();
                    var blocking = data.GetProperty("blocking_findings").GetInt32();
                    OnVerificationUpdated?.Invoke(taskId, passed, failed, blocking);
                    break;
            }
        }
        catch (Exception ex)
        {
            System.Diagnostics.Debug.WriteLine($"WebSocket process error: {ex.Message}");
        }
    }

    public async Task DisconnectAsync()
    {
        _cts?.Cancel();
        if (_ws?.State == WebSocketState.Open)
            await _ws.CloseAsync(WebSocketCloseStatus.NormalClosure, "", CancellationToken.None);
        _ws?.Dispose();
    }
}