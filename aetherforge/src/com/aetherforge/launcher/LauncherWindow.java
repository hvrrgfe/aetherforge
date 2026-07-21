package com.aetherforge.launcher;

import com.aetherforge.util.Colors;
import com.aetherforge.util.DarkScrollBarUI;
import javax.swing.*;
import javax.swing.border.EmptyBorder;
import java.awt.*;
import java.awt.event.WindowAdapter;
import java.awt.event.WindowEvent;
import java.awt.image.BufferedImage;

/**
 * AetherForge 启动器 — 主窗口
 * 三栏布局：组件启动 / 模型管理 / 设置
 */
public class LauncherWindow extends JFrame {

    private final ComponentPanel componentPanel;
    private final ModelPanel modelPanel;
    private final SettingsPanel settingsPanel;

    public LauncherWindow() {
        super("AetherForge 启动器");
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        setSize(960, 680);
        setMinimumSize(new Dimension(800, 560));
        setLocationRelativeTo(null);
        setIconImage(createIcon());

        componentPanel = new ComponentPanel();
        modelPanel = new ModelPanel();
        settingsPanel = new SettingsPanel(componentPanel, modelPanel);

        buildUI();

        addWindowListener(new WindowAdapter() {
            @Override
            public void windowClosing(WindowEvent e) {
                componentPanel.shutdownAll();
            }
        });
    }

    private void buildUI() {
        JPanel root = new JPanel(new BorderLayout());
        root.setBackground(Colors.bgDeepest());

        // 标题栏
        JPanel header = buildHeader();
        root.add(header, BorderLayout.NORTH);

        // 标签页
        JTabbedPane tabs = new JTabbedPane();
        tabs.setFont(UIManager.getFont("defaultFont").deriveFont(Font.PLAIN, 13f));
        tabs.setBackground(Colors.bgPanel());
        tabs.setForeground(Colors.textPrimary());
        tabs.setBorder(BorderFactory.createEmptyBorder(4, 4, 0, 4));

        tabs.addTab("\u25B6 启动", buildScrolledPanel(componentPanel));
        tabs.addTab("\u2699 模型管理", buildScrolledPanel(modelPanel));
        tabs.addTab("\u2630 设置", settingsPanel);

        root.add(tabs, BorderLayout.CENTER);

        // 状态栏
        JPanel statusBar = new JPanel(new BorderLayout());
        statusBar.setBackground(Colors.bgRaised());
        statusBar.setPreferredSize(new Dimension(0, 28));
        statusBar.setBorder(new EmptyBorder(0, 10, 0, 10));

        JLabel versionLabel = new JLabel("AetherForge v1.2.1");
        versionLabel.setFont(UIManager.getFont("defaultFont").deriveFont(11f));
        versionLabel.setForeground(Colors.textMuted());
        statusBar.add(versionLabel, BorderLayout.WEST);

        JLabel statusLabel = new JLabel("就绪");
        statusLabel.setFont(UIManager.getFont("defaultFont").deriveFont(11f));
        statusLabel.setForeground(Colors.textMuted());
        componentPanel.setGlobalStatusLabel(statusLabel);
        statusBar.add(statusLabel, BorderLayout.EAST);

        root.add(statusBar, BorderLayout.SOUTH);

        setContentPane(root);
    }

    private JPanel buildHeader() {
        JPanel header = new JPanel(new BorderLayout());
        header.setBackground(Colors.bgDark());
        header.setPreferredSize(new Dimension(0, 56));
        header.setBorder(BorderFactory.createEmptyBorder(8, 16, 8, 16));

        JLabel icon = new JLabel("\u25B2");
        icon.setFont(UIManager.getFont("defaultFont").deriveFont(Font.BOLD, 24f));
        icon.setForeground(Colors.BLUE);
        icon.setBorder(BorderFactory.createEmptyBorder(0, 0, 0, 8));

        JLabel title = new JLabel("AetherForge");
        title.setFont(UIManager.getFont("defaultFont").deriveFont(Font.BOLD, 18f));
        title.setForeground(Colors.textPrimary());

        JLabel subtitle = new JLabel(" AI-Native 游戏引擎 — 启动器");
        subtitle.setFont(UIManager.getFont("defaultFont").deriveFont(Font.PLAIN, 12f));
        subtitle.setForeground(Colors.textMuted());
        subtitle.setBorder(BorderFactory.createEmptyBorder(4, 0, 0, 0));

        JPanel left = new JPanel(new BorderLayout());
        left.setOpaque(false);
        JPanel titleRow = new JPanel(new FlowLayout(FlowLayout.LEFT, 0, 0));
        titleRow.setOpaque(false);
        titleRow.add(icon);
        titleRow.add(title);
        left.add(titleRow, BorderLayout.NORTH);
        left.add(subtitle, BorderLayout.SOUTH);
        header.add(left, BorderLayout.WEST);

        return header;
    }

    private JScrollPane buildScrolledPanel(JComponent panel) {
        JScrollPane sp = new JScrollPane(panel);
        sp.setBorder(BorderFactory.createEmptyBorder());
        sp.getVerticalScrollBar().setUI(new DarkScrollBarUI());
        sp.getHorizontalScrollBar().setUI(new DarkScrollBarUI());
        sp.setBackground(Colors.bgDeepest());
        return sp;
    }

    private Image createIcon() {
        BufferedImage img = new BufferedImage(64, 64, BufferedImage.TYPE_INT_ARGB);
        Graphics2D g = img.createGraphics();
        g.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
        g.setColor(Colors.BLUE);
        g.fillPolygon(new int[]{32, 56, 32, 8}, new int[]{4, 32, 60, 32}, 4);
        g.setColor(Colors.bgDeepest());
        g.fillPolygon(new int[]{32, 48, 32, 16}, new int[]{14, 32, 50, 32}, 4);
        g.dispose();
        return img;
    }
}