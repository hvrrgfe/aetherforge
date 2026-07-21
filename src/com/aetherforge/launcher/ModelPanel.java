package com.aetherforge.launcher;

import com.aetherforge.util.Colors;
import com.aetherforge.util.DarkScrollBarUI;
import com.aetherforge.tools.ModelDownloadClient;
import com.aetherforge.model.dto.ModelInfo;
import com.aetherforge.model.dto.DownloadProgress;
import javax.swing.*;
import javax.swing.border.EmptyBorder;
import javax.swing.table.DefaultTableModel;
import java.awt.*;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

/**
 * 模型管理面板 — AI 模型下载器（图像生成 + 音乐音效）
 * 连接 Python 引擎查询真实模型状态，支持下载/删除/刷新
 */
public class ModelPanel extends JPanel {

    private final JTabbedPane modelTabs;
    private final JTable imageTable, musicTable;
    private final DefaultTableModel imageModel, musicModel;
    private final Map<String, ModelInfo> imageModelCache = new ConcurrentHashMap<>();
    private final Map<String, ModelInfo> musicModelCache = new ConcurrentHashMap<>();
    private final JProgressBar downloadProgress;
    private final JLabel statusLabel, progressLabel, connLabel;
    private final JButton downloadBtn, deleteBtn, refreshBtn;
    private final Timer progressTimer;
    private final ModelDownloadClient client;
    private volatile boolean serverOnline = false;

    private static final String[] COLUMNS = {"名称", "模型 ID", "参数", "大小", "状态"};
    private static final int COL_NAME = 0, COL_ID = 1, COL_PARAMS = 2, COL_SIZE = 3, COL_STATUS = 4;

    // 图像生成模型（离线/服务端不可用时作为后备显示）
    private static final String[][] IMAGE_MODELS = {
        {"Anything V5", "stablediffusionapi/anything-v5", "1.4B", "~2.5GB", "未下载"},
        {"Stable Diffusion 1.5", "runwayml/stable-diffusion-v1-5", "1.4B", "~2.5GB", "未下载"},
        {"Stable Diffusion 2.1", "stabilityai/stable-diffusion-2-1", "1.4B", "~2.5GB", "未下载"},
        {"SDXL", "stabilityai/stable-diffusion-xl-base-1.0", "2.6B", "~7GB", "未下载"},
        {"SD3 Medium", "stabilityai/stable-diffusion-3-medium", "2.0B", "~5GB", "未下载"},
        {"FLUX.1 Schnell", "black-forest-labs/FLUX.1-schnell", "3.5B", "~8GB", "未下载"},
        {"FLUX.1 Dev", "black-forest-labs/FLUX.1-dev", "12B", "~24GB", "未下载"},
    };

    // 音乐/音效生成模型
    private static final String[][] MUSIC_MODELS = {
        {"MusicGen Small", "facebook/musicgen-small", "300M", "~1.2GB", "未下载"},
        {"MusicGen Medium", "facebook/musicgen-medium", "1.5B", "~4GB", "未下载"},
        {"MusicGen Large", "facebook/musicgen-large", "3.3B", "~8GB", "未下载"},
        {"MusicGen Melody", "facebook/musicgen-melody", "1.5B", "~4GB", "未下载"},
        {"AudioGen", "facebook/audiogen-medium", "1.5B", "~4GB", "未下载"},
    };

    public ModelPanel() {
        setLayout(new BorderLayout());
        setBackground(Colors.bgDeepest());
        setBorder(new EmptyBorder(12, 12, 12, 12));

        this.client = new ModelDownloadClient();

        // 顶部说明
        JPanel header = new JPanel(new BorderLayout());
        header.setOpaque(false);
        header.setBorder(new EmptyBorder(0, 4, 4, 4));

        JLabel title = new JLabel("AI 模型管理器");
        title.setFont(UIManager.getFont("defaultFont").deriveFont(Font.BOLD, 16f));
        title.setForeground(Colors.textPrimary());

        // 连接状态指示
        JPanel titleRow = new JPanel(new FlowLayout(FlowLayout.LEFT, 8, 0));
        titleRow.setOpaque(false);

        connLabel = new JLabel("🔴 未连接");
        connLabel.setFont(UIManager.getFont("defaultFont").deriveFont(11f));
        connLabel.setForeground(new Color(220, 80, 80));

        JLabel desc = new JLabel("连接 Python 引擎后自动获取模型列表，支持下载和删除");
        desc.setFont(UIManager.getFont("defaultFont").deriveFont(11f));
        desc.setForeground(Colors.textMuted());

        titleRow.add(title);
        titleRow.add(Box.createHorizontalStrut(12));
        titleRow.add(connLabel);

        header.add(titleRow, BorderLayout.NORTH);
        header.add(desc, BorderLayout.SOUTH);
        add(header, BorderLayout.NORTH);

        // 模型表格
        imageModel = new DefaultTableModel(COLUMNS, 0) {
            public boolean isCellEditable(int r, int c) { return false; }
        };
        musicModel = new DefaultTableModel(COLUMNS, 0) {
            public boolean isCellEditable(int r, int c) { return false; }
        };

        imageTable = createTable(imageModel);
        musicTable = createTable(musicModel);

        modelTabs = new JTabbedPane();
        modelTabs.setFont(UIManager.getFont("defaultFont").deriveFont(Font.PLAIN, 12f));
        modelTabs.setBackground(Colors.bgPanel());
        modelTabs.setForeground(Colors.textPrimary());
        modelTabs.addTab("\uD83D\uDDBC 图像生成模型", wrapTable(imageTable));
        modelTabs.addTab("\uD83C\uDFB5 音乐/音效生成模型", wrapTable(musicTable));

        // 默认加载离线数据（服务端连接后会被替换）
        loadModelData(imageModel, IMAGE_MODELS);
        loadModelData(musicModel, MUSIC_MODELS);

        add(modelTabs, BorderLayout.CENTER);

        // 底部：进度条 + 操作按钮
        JPanel bottom = new JPanel(new BorderLayout(8, 4));
        bottom.setOpaque(false);
        bottom.setBorder(new EmptyBorder(8, 4, 0, 4));

        // 进度区域
        JPanel progressPanel = new JPanel(new BorderLayout(8, 2));
        progressPanel.setOpaque(false);

        progressLabel = new JLabel("等待下载...");
        progressLabel.setFont(progressLabel.getFont().deriveFont(11f));
        progressLabel.setForeground(Colors.textSecondary());

        downloadProgress = new JProgressBar(0, 100);
        downloadProgress.setStringPainted(true);
        downloadProgress.setVisible(false);
        downloadProgress.setPreferredSize(new Dimension(downloadProgress.getPreferredSize().width, 18));

        progressPanel.add(progressLabel, BorderLayout.WEST);
        progressPanel.add(downloadProgress, BorderLayout.CENTER);
        bottom.add(progressPanel, BorderLayout.NORTH);

        // 状态栏
        statusLabel = new JLabel("就绪 - 点击「刷新列表」连接引擎");
        statusLabel.setFont(statusLabel.getFont().deriveFont(11f));
        statusLabel.setForeground(Colors.textMuted());
        statusLabel.setBorder(new EmptyBorder(2, 2, 0, 2));
        bottom.add(statusLabel, BorderLayout.CENTER);

        // 按钮
        JPanel btnPanel = new JPanel(new FlowLayout(FlowLayout.RIGHT, 6, 0));
        btnPanel.setOpaque(false);

        downloadBtn = createButton("⬇ 下载选中", new Color(70, 160, 220), e -> downloadSelected());
        refreshBtn = createButton("🔄 刷新列表", Colors.BLUE, e -> refreshModels());
        deleteBtn = createButton("🗑 删除选中", new Color(220, 80, 80), e -> deleteSelected());

        btnPanel.add(downloadBtn);
        btnPanel.add(refreshBtn);
        btnPanel.add(deleteBtn);
        bottom.add(btnPanel, BorderLayout.SOUTH);

        add(bottom, BorderLayout.SOUTH);

        // 定时轮询下载进度
        progressTimer = new Timer(2000, e -> pollProgress());
        progressTimer.start();

        // 启动后异步连接服务端
        SwingUtilities.invokeLater(() -> {
            statusLabel.setText("正在连接引擎...");
            checkServerAndRefresh();
        });
    }

    // ==================== 表格与 UI 辅助 ====================

    private JTable createTable(DefaultTableModel model) {
        JTable table = new JTable(model);
        table.setBackground(Colors.bgPanel());
        table.setForeground(Colors.textPrimary());
        table.setFont(UIManager.getFont("defaultFont").deriveFont(12f));
        table.setRowHeight(28);
        table.setSelectionMode(ListSelectionModel.SINGLE_SELECTION);
        table.setGridColor(Colors.borderLine());
        table.setSelectionBackground(new Color(60, 105, 160));
        table.setSelectionForeground(Color.WHITE);
        table.getTableHeader().setBackground(Colors.bgDeepest());
        table.getTableHeader().setForeground(Colors.textSecondary());
        table.getTableHeader().setFont(UIManager.getFont("defaultFont").deriveFont(Font.BOLD, 11f));
        return table;
    }

    private JScrollPane wrapTable(JTable table) {
        JScrollPane sp = new JScrollPane(table);
        sp.getViewport().setBackground(Colors.bgPanel());
        sp.getVerticalScrollBar().setUI(new DarkScrollBarUI());
        sp.setBorder(BorderFactory.createLineBorder(Colors.borderLine()));
        return sp;
    }

    private JButton createButton(String text, Color bg, java.awt.event.ActionListener action) {
        JButton btn = new JButton(text);
        btn.setFont(UIManager.getFont("defaultFont").deriveFont(Font.PLAIN, 12f));
        btn.setBackground(bg);
        btn.setForeground(Color.WHITE);
        btn.setFocusPainted(false);
        btn.setBorder(BorderFactory.createCompoundBorder(
            BorderFactory.createLineBorder(bg.darker(), 1),
            new EmptyBorder(6, 14, 6, 14)));
        btn.setCursor(Cursor.getPredefinedCursor(Cursor.HAND_CURSOR));
        btn.addActionListener(action);
        return btn;
    }

    private JTable currentTable() {
        return (JTable) ((JScrollPane) modelTabs.getSelectedComponent()).getViewport().getView();
    }

    private DefaultTableModel currentModel() {
        return (DefaultTableModel) currentTable().getModel();
    }

    private void loadModelData(DefaultTableModel model, String[][] data) {
        model.setRowCount(0);
        for (String[] row : data) model.addRow(row);
    }

    // ==================== 核心操作 ====================

    /**
     * 检查服务端连接并获取模型列表
     */
    private void checkServerAndRefresh() {
        new Thread(() -> {
            boolean online = client.isServerOnline();
            serverOnline = online;
            SwingUtilities.invokeLater(() -> {
                if (online) {
                    connLabel.setText("🟢 引擎已连接");
                    connLabel.setForeground(new Color(80, 200, 120));
                    statusLabel.setText("已连接引擎，获取模型列表...");
                } else {
                    connLabel.setText("🔴 引擎未连接（离线模式）");
                    connLabel.setForeground(new Color(220, 80, 80));
                    statusLabel.setText("引擎未启动，显示离线数据");
                }
            });
            if (online) {
                fetchModelsFromServer();
            }
        }).start();
    }

    /**
     * 从 Python 引擎获取真实模型列表并更新表格
     */
    private void fetchModelsFromServer() {
        try {
            List<ModelInfo> allModels = client.listModels("");
            if (allModels.isEmpty()) {
                SwingUtilities.invokeLater(() -> statusLabel.setText("服务端返回空模型列表"));
                return;
            }

            // 按类型分类
            List<ModelInfo> imageModels = new ArrayList<>();
            List<ModelInfo> musicModels = new ArrayList<>();
            for (ModelInfo m : allModels) {
                String type = m.getType() != null ? m.getType() : "";
                if ("image".equals(type)) {
                    imageModels.add(m);
                } else if ("music".equals(type) || "audio".equals(type)) {
                    musicModels.add(m);
                }
            }

            // 如果服务端没有按 type 分类，按 model_id 关键词分类
            if (imageModels.isEmpty() && musicModels.isEmpty()) {
                for (ModelInfo m : allModels) {
                    String id = m.getModelId().toLowerCase();
                    if (id.contains("stable-diffusion") || id.contains("sdxl")
                        || id.contains("flux") || id.contains("anything-v5")
                        || id.contains("sd3") || id.contains("image")) {
                        imageModels.add(m);
                    } else {
                        musicModels.add(m);
                    }
                }
            }

            // 更新缓存
            imageModelCache.clear();
            musicModelCache.clear();
            for (ModelInfo m : imageModels) imageModelCache.put(m.getModelId(), m);
            for (ModelInfo m : musicModels) musicModelCache.put(m.getModelId(), m);

            SwingUtilities.invokeLater(() -> {
                // 更新图像模型表格
                imageModel.setRowCount(0);
                for (ModelInfo m : imageModels) {
                    imageModel.addRow(new Object[]{
                        m.getName() != null ? m.getName() : m.getModelId(),
                        m.getModelId(),
                        m.getParams() != null ? m.getParams() : "",
                        m.getFormattedSize() != null ? m.getFormattedSize() : formatSizeFallback(m),
                        formatStatus(m.getStatus())
                    });
                }

                // 更新音乐模型表格
                musicModel.setRowCount(0);
                for (ModelInfo m : musicModels) {
                    musicModel.addRow(new Object[]{
                        m.getName() != null ? m.getName() : m.getModelId(),
                        m.getModelId(),
                        m.getParams() != null ? m.getParams() : "",
                        m.getFormattedSize() != null ? m.getFormattedSize() : formatSizeFallback(m),
                        formatStatus(m.getStatus())
                    });
                }

                statusLabel.setText(String.format("已加载 %d 个模型 (%d 图像, %d 音乐)",
                    allModels.size(), imageModels.size(), musicModels.size()));
            });
        } catch (Exception e) {
            SwingUtilities.invokeLater(() -> {
                statusLabel.setText("获取模型列表失败: " + e.getMessage());
            });
        }
    }

    private String formatStatus(String status) {
        if (status == null) return "未知";
        return switch (status) {
            case "downloaded" -> "已下载";
            case "not_downloaded", "not downloaded" -> "未下载";
            case "downloading" -> "下载中...";
            case "error" -> "错误";
            default -> status;
        };
    }

    private String formatSizeFallback(ModelInfo m) {
        if (m.getSizeBytes() > 0) return m.getFormattedSize();
        String id = m.getModelId().toLowerCase();
        String params = m.getParams();
        if (params != null && !params.isEmpty()) return "~" + params;
        if (id.contains("flux-dev")) return "~24GB";
        if (id.contains("flux")) return "~8GB";
        if (id.contains("sdxl")) return "~7GB";
        if (id.contains("sd3")) return "~5GB";
        if (id.contains("musicgen-large")) return "~8GB";
        if (id.contains("musicgen-medium") || id.contains("musicgen-melody") || id.contains("audiogen")) return "~4GB";
        if (id.contains("musicgen-small")) return "~1.2GB";
        return "未知";
    }

    /**
     * 刷新模型列表：重新连接服务端获取最新数据
     */
    private void refreshModels() {
        statusLabel.setText("正在刷新...");
        downloadBtn.setEnabled(false);
        refreshBtn.setEnabled(false);

        new Thread(() -> {
            boolean online = client.isServerOnline();
            serverOnline = online;

            SwingUtilities.invokeLater(() -> {
                if (online) {
                    connLabel.setText("🟢 引擎已连接");
                    connLabel.setForeground(new Color(80, 200, 120));
                } else {
                    connLabel.setText("🔴 引擎未连接（离线模式）");
                    connLabel.setForeground(new Color(220, 80, 80));
                    imageModel.setRowCount(0);
                    musicModel.setRowCount(0);
                    loadModelData(imageModel, IMAGE_MODELS);
                    loadModelData(musicModel, MUSIC_MODELS);
                    statusLabel.setText("引擎离线 — 显示默认模型列表");
                    downloadBtn.setEnabled(true);
                    refreshBtn.setEnabled(true);
                }
            });

            if (online) {
                fetchModelsFromServer();
                SwingUtilities.invokeLater(() -> {
                    downloadBtn.setEnabled(true);
                    refreshBtn.setEnabled(true);
                });
            }
        }).start();
    }

    /**
     * 下载选中的模型
     */
    private void downloadSelected() {
        JTable table = currentTable();
        int row = table.getSelectedRow();
        if (row < 0) {
            JOptionPane.showMessageDialog(this, "请先选择一个模型");
            return;
        }

        String modelId = table.getValueAt(row, COL_ID).toString();
        String status = table.getValueAt(row, COL_STATUS).toString();

        if (status.contains("已下载")) {
            JOptionPane.showMessageDialog(this, "该模型已下载，无需重复下载");
            return;
        }
        if (status.contains("下载中")) {
            JOptionPane.showMessageDialog(this, "该模型正在下载中，请稍候");
            return;
        }

        int opt = JOptionPane.showConfirmDialog(this,
            "确认下载 " + modelId + " 吗？\n模型较大，请确保网络畅通",
            "确认下载", JOptionPane.YES_NO_OPTION);
        if (opt != JOptionPane.YES_OPTION) return;

        new Thread(() -> {
            try {
                if (!client.isServerOnline()) {
                    SwingUtilities.invokeLater(() -> statusLabel.setText("下载失败: 引擎未运行"));
                    return;
                }

                boolean started = client.startDownload(modelId);
                if (started) {
                    SwingUtilities.invokeLater(() -> {
                        DefaultTableModel m = currentModel();
                        downloadProgress.setVisible(true);
                        downloadProgress.setIndeterminate(true);
                        statusLabel.setText("开始下载: " + modelId);
                        for (int i = 0; i < m.getRowCount(); i++) {
                            if (m.getValueAt(i, COL_ID).toString().equals(modelId)) {
                                m.setValueAt("下载中...", i, COL_STATUS);
                                break;
                            }
                        }
                    });
                } else {
                    SwingUtilities.invokeLater(() -> statusLabel.setText("下载启动失败，请检查引擎日志"));
                }
            } catch (Exception e) {
                SwingUtilities.invokeLater(() -> {
                    downloadProgress.setVisible(false);
                    statusLabel.setText("下载失败: " + e.getMessage());
                });
            }
        }).start();
    }

    /**
     * 删除选中的模型
     */
    private void deleteSelected() {
        JTable table = currentTable();
        DefaultTableModel model = currentModel();
        int row = table.getSelectedRow();
        if (row < 0) {
            JOptionPane.showMessageDialog(this, "请先选择一个模型");
            return;
        }

        String name = model.getValueAt(row, COL_NAME).toString();
        String modelId = model.getValueAt(row, COL_ID).toString();
        String status = model.getValueAt(row, COL_STATUS).toString();

        if (!status.contains("已下载")) {
            JOptionPane.showMessageDialog(this, name + " 尚未下载，无需删除");
            return;
        }

        int opt = JOptionPane.showConfirmDialog(this,
            "确定删除 " + name + " 的本地文件？\n(" + modelId + ")",
            "确认删除", JOptionPane.YES_NO_OPTION);
        if (opt != JOptionPane.YES_OPTION) return;

        new Thread(() -> {
            try {
                if (!client.isServerOnline()) {
                    SwingUtilities.invokeLater(() -> statusLabel.setText("删除失败: 引擎未运行"));
                    return;
                }

                boolean deleted = client.deleteModel(modelId);
                SwingUtilities.invokeLater(() -> {
                    if (deleted) {
                        model.setValueAt("未下载", row, COL_STATUS);
                        statusLabel.setText("已删除: " + name);
                        refreshModels();
                    } else {
                        statusLabel.setText("删除失败，请检查引擎日志");
                    }
                });
            } catch (Exception e) {
                SwingUtilities.invokeLater(() -> {
                    statusLabel.setText("删除失败: " + e.getMessage());
                });
            }
        }).start();
    }

    /**
     * 轮询下载进度
     */
    private void pollProgress() {
        if (!serverOnline) return;

        try {
            List<DownloadProgress> downloads = client.getDownloadProgress();
            if (downloads.isEmpty()) {
                downloadProgress.setVisible(false);
                return;
            }

            DownloadProgress first = downloads.get(0);
            double progress = first.getProgress();
            String modelId = first.getModelId();
            String dlStatus = first.getStatus();

            SwingUtilities.invokeLater(() -> {
                downloadProgress.setVisible(true);
                downloadProgress.setIndeterminate(false);
                downloadProgress.setValue((int) progress);
                downloadProgress.setString(String.format("%.1f%%", progress));
                progressLabel.setText("下载中: " + modelId);
                statusLabel.setText(String.format("%.1f%%", progress));

                if ("completed".equals(dlStatus) || progress >= 100) {
                    downloadProgress.setVisible(false);
                    statusLabel.setText("下载完成: " + modelId);
                    progressLabel.setText("等待下载...");
                    refreshModels();
                } else if ("error".equals(dlStatus)) {
                    downloadProgress.setVisible(false);
                    statusLabel.setText("下载失败: " + modelId);
                    progressLabel.setText("等待下载...");
                    for (int tab = 0; tab < modelTabs.getTabCount(); tab++) {
                        JTable t = (JTable) ((JScrollPane) modelTabs.getComponentAt(tab)).getViewport().getView();
                        DefaultTableModel m = (DefaultTableModel) t.getModel();
                        for (int i = 0; i < m.getRowCount(); i++) {
                            if (m.getValueAt(i, COL_ID).toString().equals(modelId)) {
                                m.setValueAt("错误", i, COL_STATUS);
                            }
                        }
                    }
                }
            });
        } catch (Exception ignored) {}
    }
    
    /**
     * 检查服务端是否在线（供外部调用）
     */
    public boolean isEngineOnline() {
        return serverOnline;
    }
}
