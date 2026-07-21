using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
namespace AetherForgeStudio;
public sealed partial class MainWindow : Window
{
    public MainWindow()
    {
        this.InitializeComponent();
        Title = "AetherForge Studio - 游戏开发工作台";
        ContentFrame.Navigate(typeof(Pages.DashboardPage));
    }
    private void NavView_ItemInvoked(NavigationView sender, NavigationViewItemInvokedEventArgs args)
    {
        var tag = args.InvokedItemContainer?.Tag?.ToString();
        ContentFrame.Navigate(tag switch
        {
            "Dashboard" => typeof(Pages.DashboardPage),
            "AgentWorkspace" => typeof(Pages.AgentWorkspacePage),
            "Verification" => typeof(Pages.VerificationPage),
            _ => typeof(Pages.DashboardPage),
        });
    }
}
