using Microsoft.Web.WebView2.Core;
using Microsoft.Web.WebView2.WinForms;
using System.Diagnostics;

namespace AetherForgeStudio_WebView2;

public class MainForm : Form
{
    private WebView2? _webView;
    private Panel? _loadingPanel;
    private Label? _statusLabel;
    private System.Windows.Forms.Timer? _serverCheckTimer;
    private bool _serverReady = false;
    private const string ServerUrl = "http://127.0.0.1:7890";
    private const int DefaultWidth = 1400;
    private const int DefaultHeight = 900;

    public MainForm()
    {
        InitializeForm();
        SetupLoadingUI();
        CheckServerAndStart();
    }

    private void InitializeForm()
    {
        Text = "AetherForge Studio - 游戏开发工作台";
        ClientSize = new Size(DefaultWidth, DefaultHeight);
        StartPosition = FormStartPosition.CenterScreen;
        Icon = SystemIcons.Application;
        BackColor = Color.FromArgb(10, 10, 18);
        ForeColor = Color.FromArgb(224, 224, 224);
        MinimumSize = new Size(800, 600);

        var titleBar = new Panel
        {
            Height = 32,
            Dock = DockStyle.Top,
            BackColor = Color.FromArgb(13, 13, 24),
        };

        var titleLabel = new Label
        {
            Text = "  AETHERFORGE STUDIO",
            ForeColor = Color.FromArgb(68, 136, 255),
            Font = new Font("Segoe UI", 11, FontStyle.Bold),
            Height = 32,
            Left = 12,
            AutoSize = true,
            TextAlign = ContentAlignment.MiddleLeft,
        };
        titleBar.Controls.Add(titleLabel);

        var closeBtn = new Button
        {
            Text = "?",
            FlatStyle = FlatStyle.Flat,
            BackColor = Color.Transparent,
            ForeColor = Color.FromArgb(120, 120, 140),
            Size = new Size(46, 32),
            Location = new Point(ClientSize.Width - 46, 0),
            Anchor = AnchorStyles.Top | AnchorStyles.Right,
            FlatAppearance = { BorderSize = 0, MouseOverBackColor = Color.FromArgb(232, 17, 35) },
            Cursor = Cursors.Hand,
        };
        closeBtn.Click += (_, _) => Close();
        titleBar.Controls.Add(closeBtn);

        Controls.Add(titleBar);
    }

    private void SetupLoadingUI()
    {
        _loadingPanel = new Panel
        {
            Dock = DockStyle.Fill,
            BackColor = Color.FromArgb(10, 10, 18),
        };

        _statusLabel = new Label
        {
            Text = "正在连接 AetherForge 引擎...",
            ForeColor = Color.FromArgb(68, 136, 255),
            Font = new Font("Segoe UI", 14, FontStyle.Regular),
            AutoSize = true,
            TextAlign = ContentAlignment.MiddleCenter,
        };

        var spinner = new Label
        {
            Text = "?",
            ForeColor = Color.FromArgb(68, 136, 255),
            Font = new Font("Segoe UI", 32, FontStyle.Regular),
            AutoSize = true,
            TextAlign = ContentAlignment.MiddleCenter,
        };

        _loadingPanel.Resize += (_, _) =>
        {
            _statusLabel!.Location = new Point(
                (_loadingPanel.Width - _statusLabel.Width) / 2,
                _loadingPanel.Height / 2 - 20);
            spinner.Location = new Point(
                (_loadingPanel.Width - spinner.Width) / 2,
                _loadingPanel.Height / 2 - 70);
        };

        _loadingPanel.Controls.Add(spinner);
        _loadingPanel.Controls.Add(_statusLabel);
        Controls.Add(_loadingPanel);

        var spinTimer = new System.Windows.Forms.Timer { Interval = 500 };
        int spinState = 0;
        spinTimer.Tick += (_, _) =>
        {
            spinState = (spinState + 1) % 4;
            spinner.Text = spinState switch
            {
                0 => "?", 1 => "?", 2 => "?", _ => "?"
            };
        };
        spinTimer.Start();
    }

    private async void CheckServerAndStart()
    {
        _serverCheckTimer = new System.Windows.Forms.Timer { Interval = 2000 };
        _serverCheckTimer.Tick += async (_, _) =>
        {
            if (await CheckServerHealth())
            {
                _serverCheckTimer.Stop();
                _serverReady = true;
                BeginInvoke(() => InitializeWebView());
            }
        };
        _serverCheckTimer.Start();

        if (await CheckServerHealth())
        {
            _serverCheckTimer.Stop();
            _serverReady = true;
            BeginInvoke(() => InitializeWebView());
        }
    }

    private async Task<bool> CheckServerHealth()
    {
        try
        {
            using var client = new HttpClient { Timeout = TimeSpan.FromSeconds(2) };
            var response = await client.GetAsync($"{ServerUrl}/api/summary");
            return response.IsSuccessStatusCode;
        }
        catch
        {
            UpdateStatus("等待服务器启动... (python run_web.py)");
            return false;
        }
    }

    private void UpdateStatus(string text)
    {
        if (_statusLabel != null)
        {
            BeginInvoke(() => _statusLabel.Text = text);
        }
    }

    private async void InitializeWebView()
    {
        if (_loadingPanel != null)
        {
            Controls.Remove(_loadingPanel);
            _loadingPanel.Dispose();
            _loadingPanel = null;
        }

        _webView = new WebView2
        {
            Dock = DockStyle.Fill,
        };

        _webView.CoreWebView2InitializationCompleted += (_, args) =>
        {
            if (args.IsSuccess && _webView?.CoreWebView2 != null)
            {
                _webView.CoreWebView2.Settings.AreDevToolsEnabled = true;
                _webView.CoreWebView2.Settings.IsStatusBarEnabled = false;
                _webView.CoreWebView2.Navigate(ServerUrl);
            }
        };

        Controls.Add(_webView);

        try
        {
            var env = await CoreWebView2Environment.CreateAsync();
            await _webView.EnsureCoreWebView2Async(env);
        }
        catch (Exception ex)
        {
            UpdateStatus("WebView2 初始化失败: " + ex.Message);
        }
    }
}
