using System;
using System.ComponentModel;
using System.Runtime.CompilerServices;

namespace AetherForgeStudio.ViewModels;

public class TokenUsageViewModel : INotifyPropertyChanged
{
    private int _usedTokens = 0;
    private int _maxTokens = 30000;
    private int _agentCalls = 0;
    private int _maxCalls = 30;
    private double _cacheHitRate = 0;
    private string _contextMode = "Incremental";

    public int UsedTokens { get => _usedTokens; set { _usedTokens = value; OnPropertyChanged(); OnPropertyChanged(nameof(TokenPercent)); } }
    public int MaxTokens { get => _maxTokens; set { _maxTokens = value; OnPropertyChanged(); OnPropertyChanged(nameof(TokenPercent)); } }
    public int AgentCalls { get => _agentCalls; set { _agentCalls = value; OnPropertyChanged(); } }
    public int MaxCalls { get => _maxCalls; set { _maxCalls = value; OnPropertyChanged(); } }
    public double CacheHitRate { get => _cacheHitRate; set { _cacheHitRate = value; OnPropertyChanged(); } }
    public string ContextMode { get => _contextMode; set { _contextMode = value; OnPropertyChanged(); } }

    public double TokenPercent => MaxTokens > 0 ? (double)UsedTokens / MaxTokens * 100 : 0;

    public event PropertyChangedEventHandler? PropertyChanged;
    protected void OnPropertyChanged([CallerMemberName] string? name = null)
        => PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(name));
}