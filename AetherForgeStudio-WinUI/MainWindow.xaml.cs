using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
namespace AetherForgeStudio;
public sealed partial class MainWindow : Window
{
    public MainWindow()
    {
        this.InitializeComponent();
        Title = "AetherForge Studio";
        ContentFrame.Navigate(typeof(Pages.DashboardPage));
    }
    private void NavView_ItemInvoked(NavigationView sender, NavigationViewItemInvokedEventArgs args)
    {
        var tag = args.InvokedItemContainer?.Tag?.ToString();
                ContentFrame.Navigate(tag switch
        {
            "Dashboard" => typeof(Pages.DashboardPage),
            "AgentWorkspace" => typeof(Pages.AgentWorkspacePage),
            "WorldViewer" => typeof(Pages.WorldViewerPage),
            "Verification" => typeof(Pages.VerificationPage),
            "World" => typeof(Pages.WorldPage),
            "Entities" => typeof(Pages.EntitiesPage),
            "Quests" => typeof(Pages.QuestsPage),
            "Rules" => typeof(Pages.RulesPage),
            "Assets" => typeof(Pages.AssetsPage),
            _ => typeof(Pages.DashboardPage),
        });
    }
}