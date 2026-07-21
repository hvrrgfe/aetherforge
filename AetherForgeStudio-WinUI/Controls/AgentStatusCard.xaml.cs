using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
namespace AetherForgeStudio.Controls;
public sealed partial class AgentStatusCard : UserControl
{
    public static readonly DependencyProperty AgentNameProperty =
        DependencyProperty.Register("AgentName", typeof(string), typeof(AgentStatusCard), new PropertyMetadata("", OnNameChanged));
    public string AgentName
    {
        get => (string)GetValue(AgentNameProperty);
        set => SetValue(AgentNameProperty, value);
    }
    private static void OnNameChanged(DependencyObject d, DependencyPropertyChangedEventArgs e)
    {
        if (d is AgentStatusCard card) card.AgentNameText.Text = e.NewValue?.ToString();
    }
    public AgentStatusCard() { this.InitializeComponent(); }
}