using System;
using System.Collections.ObjectModel;
using System.ComponentModel;
using System.Runtime.CompilerServices;

namespace AetherForgeStudio.ViewModels;

public class CheckResultInfo
{
    public string Name { get; set; } = string.Empty;
    public bool Passed { get; set; }
    public string Message { get; set; } = string.Empty;
    public string Icon => Passed ? "\u2713" : "\u2717";
}

public class VerificationViewModel : INotifyPropertyChanged
{
    public ObservableCollection<CheckResultInfo> Checks { get; set; } = new();

    private string _status = "Waiting";
    private bool _commitAllowed = false;
    private string _blockingReason = "";
    private int _passedCount = 0;
    private int _failedCount = 0;

    public string Status { get => _status; set { _status = value; OnPropertyChanged(); } }
    public bool CommitAllowed { get => _commitAllowed; set { _commitAllowed = value; OnPropertyChanged(); } }
    public string BlockingReason { get => _blockingReason; set { _blockingReason = value; OnPropertyChanged(); } }
    public int PassedCount { get => _passedCount; set { _passedCount = value; OnPropertyChanged(); } }
    public int FailedCount { get => _failedCount; set { _failedCount = value; OnPropertyChanged(); } }

    public void UpdateChecks(System.Collections.Generic.List<System.Collections.Generic.Dictionary<string, object>> checks)
    {
        Checks.Clear();
        if (checks == null) return;
        foreach (var c in checks)
        {
            var name = c.ContainsKey("name") ? c["name"]?.ToString() ?? "check" : "check";
            var severity = c.ContainsKey("severity") ? c["severity"]?.ToString() ?? "pass" : "pass";
            var msg = c.ContainsKey("message") ? c["message"]?.ToString() ?? "" : "";
            Checks.Add(new CheckResultInfo { Name = name, Passed = severity == "pass", Message = msg });
        }
        OnPropertyChanged(nameof(Checks));
    }

    public event PropertyChangedEventHandler? PropertyChanged;
    protected void OnPropertyChanged([CallerMemberName] string? name = null)
        => PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(name));
}