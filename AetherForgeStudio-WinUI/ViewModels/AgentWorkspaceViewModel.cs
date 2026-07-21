using System;
using System.Collections.ObjectModel;
using System.ComponentModel;
using System.Runtime.CompilerServices;

namespace AetherForgeStudio.ViewModels;

public class AgentStatusInfo
{
    public string Role { get; set; } = string.Empty;
    public string Status { get; set; } = string.Empty;
    public string Action { get; set; } = string.Empty;
    public string Token { get; set; } = string.Empty;
    public bool IsRunning => Status == "running";
}

public class AgentWorkspaceViewModel : INotifyPropertyChanged
{
    public ObservableCollection<AgentStatusInfo> Agents { get; set; } = new();

    private string _taskId = "";
    private string _taskPhase = "";
    private double _taskProgress = 0;
    private string _goal = "";

    public string TaskId { get => _taskId; set { _taskId = value; OnPropertyChanged(); } }
    public string TaskPhase { get => _taskPhase; set { _taskPhase = value; OnPropertyChanged(); } }
    public double TaskProgress { get => _taskProgress; set { _taskProgress = value; OnPropertyChanged(); } }
    public string Goal { get => _goal; set { _goal = value; OnPropertyChanged(); } }

    public void UpdateAgentStatus(string role, string status, string action, string token = "")
    {
        foreach (var a in Agents)
        {
            if (a.Role == role)
            {
                a.Status = status;
                a.Action = action;
                if (!string.IsNullOrEmpty(token)) a.Token = token;
                OnPropertyChanged(nameof(Agents));
                return;
            }
        }
        Agents.Add(new AgentStatusInfo { Role = role, Status = status, Action = action, Token = token });
        OnPropertyChanged(nameof(Agents));
    }

    public event PropertyChangedEventHandler? PropertyChanged;
    protected void OnPropertyChanged([CallerMemberName] string? name = null)
        => PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(name));
}