using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using AetherForgeStudio.Services;
namespace AetherForgeStudio.Pages;
public sealed partial class AgentWorkspacePage : Page
{
    private readonly AgentStateService _agentSvc = new(new AetherForgeApiService());
    private string _currentTaskId = "";
    public AgentWorkspacePage() { this.InitializeComponent(); }
    private async void StartTaskBtn_Click(object sender, RoutedEventArgs e)
    {
        var goal = GoalInput.Text;
        if (string.IsNullOrEmpty(goal)) return;
        var result = await _agentSvc.StartTaskAsync(goal);
        StatusText.Text = "任务已启动";
    }
    private async void RefreshStatusBtn_Click(object sender, RoutedEventArgs e)
    {
        if (string.IsNullOrEmpty(_currentTaskId)) return;
        var info = await _agentSvc.GetTaskInfoAsync(_currentTaskId);
        TaskProgress.Value = info.Progress;
        PhaseText.Text = "阶段: " + info.Phase;
    }
}
