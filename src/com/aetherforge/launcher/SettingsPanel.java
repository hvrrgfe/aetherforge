package com.aetherforge.launcher;

import com.aetherforge.util.Colors;
import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.reflect.TypeToken;
import javax.swing.*;
import javax.swing.border.EmptyBorder;
import java.awt.*;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.LinkedHashMap;
import java.util.Map;

/**
 * 设置面板 — 配置路径和环境，持久化到 ~/.aetherforge/launcher-config.json
 */
public class SettingsPanel extends JPanel {

    private final JTextField pythonPathField;
    private final JTextField modelPathField;
    private final JTextField serverPortField;
    private final JLabel statusLabel;

    private static final Path CONFIG_DIR = Path.of(System.getProperty("user.home"), ".aetherforge");
    private static final Path CONFIG_FILE = CONFIG_DIR.resolve("launcher-config.json");
    private static final Gson GSON = new GsonBuilder().setPrettyPrinting().create();

    public SettingsPanel(ComponentPanel componentPanel, ModelPanel modelPanel) {
        setLayout(new BoxLayout(this, BoxLayout.Y_AXIS));
        setBackground(Colors.bgDeepest());
        setBorder(new EmptyBorder(16, 16, 16, 16));

        // Python 环境
        addSection("Python 环境", "配置 Python 解释器路径");
        pythonPathField = addPathField("Python 路径:", "python", "选择 Python 可执行文件");
        add(Box.createVerticalStrut(16));

        // 模型路径
        addSection("模型存储", "AI 模型下载目录");
        String defaultModelPath = Path.of(System.getProperty("user.home"), "models").toString();
        modelPathField = addPathField("模型目录:", defaultModelPath, "选择模型存储目录");
        add(Box.createVerticalStrut(16));

        // 服务器端口
        addSection("服务器", "AetherForge 引擎服务器配置");
        JPanel portRow = new JPanel(new FlowLayout(FlowLayout.LEFT, 8, 4));
        portRow.setOpaque(false);
        portRow.setMaximumSize(new Dimension(9999, 32));

        JLabel portLabel = new JLabel("端口:");
        portLabel.setFont(UIManager.getFont("defaultFont").deriveFont(12f));
        portLabel.setForeground(Colors.textPrimary());
        portLabel.setPreferredSize(new Dimension(100, 24));

        serverPortField = new JTextField("7890");
        serverPortField.setFont(UIManager.getFont("defaultFont").deriveFont(12f));
        serverPortField.setForeground(Colors.textPrimary());
        serverPortField.setBackground(Colors.bgInput());
        serverPortField.setCaretColor(Colors.BLUE);
        serverPortField.setBorder(BorderFactory.createCompoundBorder(
            BorderFactory.createLineBorder(Colors.borderLine()),
            new EmptyBorder(4, 8, 4, 8)
        ));
        serverPortField.setPreferredSize(new Dimension(100, 28));

        portRow.add(portLabel);
        portRow.add(serverPortField);
        add(portRow);

        add(Box.createVerticalStrut(24));

        // 状态提示
        statusLabel = new JLabel(" ");
        statusLabel.setFont(UIManager.getFont("defaultFont").deriveFont(11f));
        statusLabel.setForeground(Colors.GREEN);
        add(statusLabel);

        // 应用按钮
        JPanel btnRow = new JPanel(new FlowLayout(FlowLayout.RIGHT));
        btnRow.setOpaque(false);

        JButton saveBtn = new JButton("保存设置");
        saveBtn.setFont(UIManager.getFont("defaultFont").deriveFont(Font.BOLD, 13f));
        saveBtn.setFocusPainted(false);
        saveBtn.setBackground(Colors.BLUE);
        saveBtn.setForeground(Color.WHITE);
        saveBtn.setBorder(BorderFactory.createEmptyBorder(8, 24, 8, 24));
        saveBtn.setCursor(Cursor.getPredefinedCursor(Cursor.HAND_CURSOR));
        saveBtn.addActionListener(e -> saveSettings());

        JButton resetBtn = new JButton("恢复默认");
        resetBtn.setFont(UIManager.getFont("defaultFont").deriveFont(Font.BOLD, 13f));
        resetBtn.setFocusPainted(false);
        resetBtn.setBackground(Colors.bgRaised());
        resetBtn.setForeground(Colors.textSecondary());
        resetBtn.setBorder(BorderFactory.createEmptyBorder(8, 24, 8, 24));
        resetBtn.setCursor(Cursor.getPredefinedCursor(Cursor.HAND_CURSOR));
        resetBtn.addActionListener(e -> resetSettings());

        btnRow.add(resetBtn);
        btnRow.add(Box.createHorizontalStrut(8));
        btnRow.add(saveBtn);
        add(btnRow);

        // 底部填充
        add(Box.createVerticalGlue());

        // 关于
        add(Box.createVerticalStrut(16));
        JPanel aboutPanel = new JPanel(new BorderLayout());
        aboutPanel.setOpaque(false);
        aboutPanel.setBorder(new EmptyBorder(8, 4, 8, 4));

        JLabel aboutLabel = new JLabel("<html>AetherForge v1.2.1 &mdash; AI-Native 游戏创作与运行时系统<br>" +
            "GitHub: <font color='#4080f0'>github.com/hvrrgfe/aetherforge</font></html>");
        aboutLabel.setFont(UIManager.getFont("defaultFont").deriveFont(10f));
        aboutLabel.setForeground(Colors.textMuted());

        aboutPanel.add(aboutLabel, BorderLayout.WEST);
        add(aboutPanel);

        // 初始化时加载已保存的设置
        loadSettings();
    }

    private void addSection(String title, String description) {
        JPanel section = new JPanel(new BorderLayout());
        section.setOpaque(false);
        section.setBorder(BorderFactory.createCompoundBorder(
            BorderFactory.createMatteBorder(0, 0, 1, 0, Colors.borderLine()),
            new EmptyBorder(0, 0, 8, 0)
        ));

        JLabel titleLabel = new JLabel(title);
        titleLabel.setFont(UIManager.getFont("defaultFont").deriveFont(Font.BOLD, 14f));
        titleLabel.setForeground(Colors.textPrimary());

        JLabel descLabel = new JLabel(description);
        descLabel.setFont(UIManager.getFont("defaultFont").deriveFont(11f));
        descLabel.setForeground(Colors.textMuted());

        section.add(titleLabel, BorderLayout.NORTH);
        section.add(descLabel, BorderLayout.SOUTH);
        section.setMaximumSize(new Dimension(9999, 48));
        add(section);
        add(Box.createVerticalStrut(8));
    }

    private JTextField addPathField(String label, String defaultValue, String dialogTitle) {
        JPanel row = new JPanel(new FlowLayout(FlowLayout.LEFT, 8, 4));
        row.setOpaque(false);
        row.setMaximumSize(new Dimension(9999, 32));

        JLabel lbl = new JLabel(label);
        lbl.setFont(UIManager.getFont("defaultFont").deriveFont(12f));
        lbl.setForeground(Colors.textPrimary());
        lbl.setPreferredSize(new Dimension(100, 24));

        JTextField field = new JTextField(defaultValue);
        field.setFont(UIManager.getFont("defaultFont").deriveFont(12f));
        field.setForeground(Colors.textPrimary());
        field.setBackground(Colors.bgInput());
        field.setCaretColor(Colors.BLUE);
        field.setBorder(BorderFactory.createCompoundBorder(
            BorderFactory.createLineBorder(Colors.borderLine()),
            new EmptyBorder(4, 8, 4, 8)
        ));
        field.setPreferredSize(new Dimension(400, 28));

        JButton browseBtn = new JButton("浏览...");
        browseBtn.setFont(UIManager.getFont("defaultFont").deriveFont(11f));
        browseBtn.setFocusPainted(false);
        browseBtn.setBackground(Colors.bgRaised());
        browseBtn.setForeground(Colors.textSecondary());
        browseBtn.setBorder(BorderFactory.createLineBorder(Colors.borderLine()));
        browseBtn.setCursor(Cursor.getPredefinedCursor(Cursor.HAND_CURSOR));
        browseBtn.addActionListener(e -> {
            JFileChooser fc = new JFileChooser();
            fc.setDialogTitle(dialogTitle);
            fc.setFileSelectionMode(JFileChooser.FILES_AND_DIRECTORIES);
            if (fc.showOpenDialog(this) == JFileChooser.APPROVE_OPTION) {
                field.setText(fc.getSelectedFile().getAbsolutePath());
            }
        });

        row.add(lbl);
        row.add(field);
        row.add(browseBtn);
        add(row);
        return field;
    }

    private String detectPython() {
        String[] candidates = {"python", "python3", "python310", "python311"};
        for (String cmd : candidates) {
            try {
                Process p = Runtime.getRuntime().exec(new String[]{cmd, "--version"});
                int code = p.waitFor();
                if (code == 0) return cmd;
            } catch (Exception ignored) {}
        }
        return "python";
    }

    /**
     * 从配置文件加载设置
     */
    private void loadSettings() {
        try {
            if (Files.exists(CONFIG_FILE)) {
                String content = Files.readString(CONFIG_FILE, StandardCharsets.UTF_8);
                Map<String, String> config = GSON.fromJson(content, new TypeToken<Map<String, String>>(){}.getType());
                if (config != null) {
                    if (config.containsKey("python")) pythonPathField.setText(config.get("python"));
                    if (config.containsKey("models")) modelPathField.setText(config.get("models"));
                    if (config.containsKey("port")) serverPortField.setText(config.get("port"));
                    statusLabel.setText("已加载已保存的设置");
                    statusLabel.setForeground(Colors.textMuted());
                }
            }
        } catch (Exception e) {
            // 文件不存在或格式错误，使用默认值
        }
    }

    /**
     * 保存设置到配置文件
     */
    private void saveSettings() {
        try {
            // 创建目录
            Files.createDirectories(CONFIG_DIR);

            // 构建配置 Map
            Map<String, String> config = new LinkedHashMap<>();
            config.put("python", pythonPathField.getText().trim());
            config.put("models", modelPathField.getText().trim());
            config.put("port", serverPortField.getText().trim());

            // 写 JSON 文件
            String json = GSON.toJson(config);
            Files.writeString(CONFIG_FILE, json, StandardCharsets.UTF_8);

            // 同步到系统属性（供其他组件运行时读取）
            System.setProperty("aetherforge.python", config.get("python"));
            System.setProperty("aetherforge.models", config.get("models"));
            System.setProperty("aetherforge.port", config.get("port"));

            statusLabel.setText("设置已保存到 " + CONFIG_FILE);
            statusLabel.setForeground(Colors.GREEN);
        } catch (Exception ex) {
            statusLabel.setText("保存失败: " + ex.getMessage());
            statusLabel.setForeground(Colors.RED);
            JOptionPane.showMessageDialog(this,
                "设置保存失败: " + ex.getMessage(), "错误", JOptionPane.ERROR_MESSAGE);
        }
    }

    private void resetSettings() {
        pythonPathField.setText(detectPython());
        modelPathField.setText(Path.of(System.getProperty("user.home"), "models").toString());
        serverPortField.setText("7890");
        statusLabel.setText("已恢复默认值 (尚未保存)");
        statusLabel.setForeground(Colors.textMuted());
    }
}