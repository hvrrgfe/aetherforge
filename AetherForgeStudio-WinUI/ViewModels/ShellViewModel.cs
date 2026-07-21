using System;
using System.Collections.ObjectModel;
using System.ComponentModel;
using System.Runtime.CompilerServices;

namespace AetherForgeStudio.ViewModels;

public class ShellViewModel : INotifyPropertyChanged
{
    private string _selectedPage = "Dashboard";
    private string _worldRevision = "Rev 0";
    private string _activeTask = "None";
    private string _tokenUsage = "0";
    private string _pendingChanges = "0";
    private string _statusMessage = "Ready";

    public string SelectedPage
    {
        get => _selectedPage;
        set { _selectedPage = value; OnPropertyChanged(); }
    }

    public string WorldRevision
    {
        get => _worldRevision;
        set { _worldRevision = value; OnPropertyChanged(); }
    }

    public string ActiveTask
    {
        get => _activeTask;
        set { _activeTask = value; OnPropertyChanged(); }
    }

    public string TokenUsage
    {
        get => _tokenUsage;
        set { _tokenUsage = value; OnPropertyChanged(); }
    }

    public string PendingChanges
    {
        get => _pendingChanges;
        set { _pendingChanges = value; OnPropertyChanged(); }
    }

    public string StatusMessage
    {
        get => _statusMessage;
        set { _statusMessage = value; OnPropertyChanged(); }
    }

    public event PropertyChangedEventHandler? PropertyChanged;
    protected void OnPropertyChanged([CallerMemberName] string? name = null)
        => PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(name));
}