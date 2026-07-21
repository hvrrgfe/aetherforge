package com.aetherforge.ui;

import com.aetherforge.model.dto.DownloadProgress;
import com.aetherforge.model.dto.ModelInfo;
import com.aetherforge.tools.ModelDownloadClient;
import com.aetherforge.util.Colors;
import com.aetherforge.util.DarkScrollBarUI;
import javax.swing.*;
import javax.swing.border.EmptyBorder;
import javax.swing.table.DefaultTableCellRenderer;
import javax.swing.table.DefaultTableModel;
import javax.swing.table.TableRowSorter;
import java.awt.*;
import java.awt.event.WindowAdapter;
import java.awt.event.WindowEvent;
import java.util.ArrayList;
import java.util.List;

public class ModelManagerDialog extends JDialog {
    private final ModelDownloadClient client;
    private final JTabbedPane tabbedPane;
    private final JTable imageTable, musicTable;
    private final DefaultTableModel imageModel, musicModel;
    private final JLabel statusLabel;
    private JButton refreshBtn, downloadBtn, deleteBtn, selectBtn;
    private final JProgressBar globalProgress;
    private final JLabel connectionLabel;
    private Timer pollTimer;
    private final java.util.concurrent.atomic.AtomicBoolean running = new java.util.concurrent.atomic.AtomicBoolean(true);
    private boolean serverOnline = false;
    private boolean isDownloading = false;
    private static final String[] COLS = {"Name", "Model ID", "Type", "Params", "Size", "Source", "Status"};
    private static final int C_NAME=0, C_ID=1, C_TYPE=2, C_PARAMS=3, C_SIZE=4, C_SOURCE=5, C_STATUS=6;

    public ModelManagerDialog(JFrame parent) {
        super(parent, "AI Model Manager", false);
        this.client = new ModelDownloadClient();
        setSize(900, 600);
        setMinimumSize(new Dimension(700, 400));
        setLocationRelativeTo(parent);
        setBackground(Colors.bgDeepest());
        imageModel = new DefaultTableModel(COLS, 0) { public boolean isCellEditable(int r, int c) { return false; } };
        musicModel = new DefaultTableModel(COLS, 0) { public boolean isCellEditable(int r, int c) { return false; } };
        imageTable = createTable(imageModel);
        musicTable = createTable(musicModel);
        tabbedPane = new JTabbedPane();
        tabbedPane.setFont(UIManager.getFont("defaultFont").deriveFont(Font.PLAIN, 12f));
        tabbedPane.setBackground(Colors.bgPanel());
        tabbedPane.setForeground(Colors.textPrimary());
        tabbedPane.addTab("Image Models", wrapTable(imageTable));
        tabbedPane.addTab("Music/SFX Models", wrapTable(musicTable));
        JPanel bottom = new JPanel(new BorderLayout());
        bottom.setBackground(Colors.bgRaised());
        bottom.setPreferredSize(new Dimension(0, 32));
        bottom.setBorder(new EmptyBorder(2, 8, 2, 8));
        connectionLabel = new JLabel("checking...");
        connectionLabel.setFont(UIManager.getFont("defaultFont").deriveFont(Font.PLAIN, 11f));
        connectionLabel.setForeground(Colors.textMuted());
        globalProgress = new JProgressBar(0, 100);
        globalProgress.setPreferredSize(new Dimension(120, 16));
        globalProgress.setStringPainted(true);
        globalProgress.setVisible(false);
        statusLabel = new JLabel("ready");
        statusLabel.setFont(UIManager.getFont("defaultFont").deriveFont(Font.PLAIN, 11f));
        statusLabel.setForeground(Colors.textMuted());
        bottom.add(connectionLabel, BorderLayout.WEST);
        bottom.add(globalProgress, BorderLayout.CENTER);
        bottom.add(statusLabel, BorderLayout.EAST);
        JPanel content = new JPanel(new BorderLayout());
        content.setBackground(Colors.bgDeepest());
        content.add(createToolbar(), BorderLayout.NORTH);
        content.add(tabbedPane, BorderLayout.CENTER);
        content.add(bottom, BorderLayout.SOUTH);
        setContentPane(content);
        addWindowListener(new WindowAdapter() {
            public void windowClosed(WindowEvent e) {
                running.set(false);
                stopPolling();
            }
        });
        checkConnection();
    }
    private JToolBar createToolbar() {
        JToolBar tb = new JToolBar();
        tb.setFloatable(false);
        tb.setBackground(Colors.bgRaised());
        tb.setBorder(new EmptyBorder(2, 6, 2, 6));
        refreshBtn = createTBtn("Refresh", "Reload model list from server");
        refreshBtn.addActionListener(e -> refreshAll());
        downloadBtn = createTBtn("Download", "Download selected model");
        downloadBtn.addActionListener(e -> downloadSelected());
        deleteBtn = createTBtn("Delete", "Delete local model");
        deleteBtn.addActionListener(e -> deleteSelected());
        selectBtn = createTBtn("Activate", "Use selected model for generation");
        selectBtn.addActionListener(e -> selectAsActive());
        tb.add(refreshBtn); tb.add(downloadBtn); tb.add(deleteBtn); tb.add(selectBtn);
        tb.add(Box.createHorizontalGlue());
        JButton closeBtn = createTBtn("Close", "Close dialog");
        closeBtn.addActionListener(e -> setVisible(false));
        tb.add(closeBtn);
        return tb;
    }

    private JButton createTBtn(String text, String tip) {
        JButton b = new JButton(text);
        b.setFont(UIManager.getFont("defaultFont").deriveFont(Font.PLAIN, 11f));
        b.setFocusPainted(false); b.setBorderPainted(false);
        b.setContentAreaFilled(false);
        b.setForeground(Colors.textPrimary());
        b.setCursor(Cursor.getPredefinedCursor(Cursor.HAND_CURSOR));
        b.setToolTipText(tip);
        return b;
    }

    private JScrollPane wrapTable(JTable t) {
        JScrollPane sp = new JScrollPane(t);
        sp.setBorder(BorderFactory.createEmptyBorder());
        sp.getVerticalScrollBar().setUI(new DarkScrollBarUI());
        sp.setBackground(Colors.bgPanel());
        return sp;
    }
    private JTable createTable(DefaultTableModel model) {
        JTable t = new JTable(model);
        t.setBackground(Colors.bgPanel());
        t.setForeground(Colors.textPrimary());
        t.setFont(UIManager.getFont("defaultFont").deriveFont(Font.PLAIN, 12f));
        t.setRowHeight(28);
        t.setShowGrid(true);
        t.setGridColor(Colors.borderLine());
        t.setSelectionBackground(Colors.bgHover());
        t.setSelectionForeground(Colors.BLUE);
        t.getTableHeader().setBackground(Colors.bgRaised());
        t.getTableHeader().setForeground(Colors.textMuted());
        t.getTableHeader().setFont(UIManager.getFont("defaultFont").deriveFont(Font.BOLD, 11f));
        t.setSelectionMode(ListSelectionModel.SINGLE_SELECTION);
        t.setRowSorter(new TableRowSorter<>(model));
        t.getColumnModel().getColumn(C_STATUS).setCellRenderer(new DefaultTableCellRenderer() {
            public Component getTableCellRendererComponent(JTable t, Object v,
                    boolean sel, boolean focus, int row, int col) {
                JLabel l = (JLabel) super.getTableCellRendererComponent(t, v, sel, focus, row, col);
                String s = v != null ? v.toString() : "";
                if (s.contains("downloaded")) l.setForeground(Colors.GREEN);
                else if (s.contains("loading")) l.setForeground(Colors.BLUE);
                else l.setForeground(Colors.textMuted());
                l.setBorder(new EmptyBorder(2, 6, 2, 6));
                return l;
            }
        });
        t.getColumnModel().getColumn(C_NAME).setPreferredWidth(100);
        t.getColumnModel().getColumn(C_ID).setPreferredWidth(200);
        t.getColumnModel().getColumn(C_PARAMS).setPreferredWidth(60);
        t.getColumnModel().getColumn(C_SIZE).setPreferredWidth(60);
        t.getColumnModel().getColumn(C_SOURCE).setPreferredWidth(80);
        t.getColumnModel().getColumn(C_STATUS).setPreferredWidth(80);
        t.addMouseListener(new java.awt.event.MouseAdapter() {
            public void mouseClicked(java.awt.event.MouseEvent e) {
                if (e.getClickCount() == 2) {
                    int row = t.getSelectedRow();
                    if (row >= 0) {
                        String s = model.getValueAt(row, C_STATUS).toString();
                        if (!s.contains("downloaded")) doDownload(t, model);
                    }
                }
            }
        });
        return t;
    }
    private void checkConnection() {
        new Thread(() -> {
            boolean ok = client.isServerOnline();
            SwingUtilities.invokeLater(() -> {
                serverOnline = ok;
                if (ok) {
                    connectionLabel.setText("Connected to Python engine (127.0.0.1:7890)");
                    connectionLabel.setForeground(Colors.GREEN);
                    refreshAll();
                    startPolling();
                } else {
                    connectionLabel.setText("Python engine not running - start start_server.bat first");
                    connectionLabel.setForeground(Colors.RED);
                    statusLabel.setText("NOT CONNECTED");
                }
            });
        }).start();
    }

    private void refreshAll() {
        refreshTable(imageModel, "image");
        refreshTable(musicModel, "music");
    }

    private void refreshTable(DefaultTableModel m, String type) {
        m.setRowCount(0);
        String tn = "image".equals(type) ? "Image" : "Music";
        statusLabel.setText("Loading " + tn + " models...");
        new Thread(() -> {
            List<ModelInfo> models = client.listModels(type);
            SwingUtilities.invokeLater(() -> {
                for (ModelInfo mi : models) {
                    m.addRow(new Object[]{
                        mi.getName(), mi.getModelId(), mi.getType(),
                        mi.getParams() != null ? mi.getParams() : "-",
                        mi.getFormattedSize(), srcLabel(mi.getSource()), mi.getDisplayStatus()
                    });
                }
                statusLabel.setText(tn + " models: " + models.size());
            });
        }).start();
    }

    private String srcLabel(String s) {
        if (s == null) return "unknown";
        return switch (s) {
            case "huggingface_cache", "huggingface" -> "HF cache";
            case "local" -> "local";
            case "downloadable" -> "cloud";
            default -> s;
        };
    }
    private void downloadSelected() {
        JTable t = curTable(); DefaultTableModel m = curModel();
        if (t.getSelectedRow() < 0) { JOptionPane.showMessageDialog(this, "Select a model first"); return; }
        doDownload(t, m);
    }

    private void doDownload(JTable t, DefaultTableModel m) {
        int row = t.getSelectedRow();
        if (row < 0) return;
        if (isDownloading) { JOptionPane.showMessageDialog(this, "Already downloading another model"); return; }
        String id = m.getValueAt(row, C_ID).toString();
        String name = m.getValueAt(row, C_NAME).toString();
        String st = m.getValueAt(row, C_STATUS).toString();
        if (st.contains("downloaded")) { JOptionPane.showMessageDialog(this, name + " already downloaded"); return; }
        int r = JOptionPane.showConfirmDialog(this,
            "Download: " + name + "\nID: " + id + "\n\nThis may take a long time. Continue?",
            "Confirm Download", JOptionPane.YES_NO_OPTION);
        if (r != JOptionPane.YES_OPTION) return;
        isDownloading = true;
        downloadBtn.setEnabled(false);
        refreshBtn.setEnabled(false);
        statusLabel.setText("Starting: " + name);
        m.setValueAt("downloading...", row, C_STATUS);
        globalProgress.setVisible(true);
        globalProgress.setIndeterminate(true);
        new Thread(() -> {
            boolean ok = client.startDownload(id);
            if (ok) pollDownload(id, m, row);
            else SwingUtilities.invokeLater(() -> {
                m.setValueAt("failed", row, C_STATUS);
                statusLabel.setText("Failed: " + name);
                globalProgress.setVisible(false);
                finishDownload();
            });
        }).start();
    }

    private void pollDownload(String modelId, DefaultTableModel m, int row) {
        if (!running.get()) return;
        for (int i = 0; i < 6000; i++) {
            try { Thread.sleep(100); } catch (InterruptedException e) { break; }
            if (!running.get()) return;
            List<DownloadProgress> list = client.getDownloadProgress();
            boolean found = false;
            for (DownloadProgress dp : list) {
                if (modelId.equals(dp.getModelId())) {
                    found = true;
                    double pct = dp.getProgress();
                    SwingUtilities.invokeLater(() -> {
                        globalProgress.setIndeterminate(false);
                        globalProgress.setValue((int) pct);
                        globalProgress.setString(String.format("%.1f%%", pct));
                        m.setValueAt(String.format("%.1f%%", pct), row, C_STATUS);
                        statusLabel.setText(String.format("%.1f%%", pct));
                    });
                    if (!running.get()) return;
                    if (dp.isCompleted()) {
                        SwingUtilities.invokeLater(() -> {
                            m.setValueAt("downloaded", row, C_STATUS);
                            statusLabel.setText("Done: " + modelId);
                            globalProgress.setVisible(false);
                            finishDownload();
                            refreshAll();
                        });
                        return;
                    }
                    if (dp.isError()) {
                        SwingUtilities.invokeLater(() -> {
                            m.setValueAt("error: " + dp.getStatus(), row, C_STATUS);
                            statusLabel.setText("Error: " + modelId);
                            globalProgress.setVisible(false);
                            finishDownload();
                        });
                        return;
                    }
                    break;
                }
            }
            if (!found) break;
        }
    }
    private void deleteSelected() {
        JTable t = curTable(); DefaultTableModel m = curModel();
        int row = t.getSelectedRow();
        if (row < 0) { JOptionPane.showMessageDialog(this, "Select a model first"); return; }
        String id = m.getValueAt(row, C_ID).toString();
        String name = m.getValueAt(row, C_NAME).toString();
        String st = m.getValueAt(row, C_STATUS).toString();
        if (!st.contains("downloaded")) { JOptionPane.showMessageDialog(this, name + " not downloaded"); return; }
        int r = JOptionPane.showConfirmDialog(this, "Delete " + name + "?", "Confirm", JOptionPane.YES_NO_OPTION);
        if (r != JOptionPane.YES_OPTION) return;
        new Thread(() -> {
            boolean ok = client.deleteModel(id);
            SwingUtilities.invokeLater(() -> {
                if (ok) { statusLabel.setText("Deleted " + name); refreshAll(); }
                else statusLabel.setText("Delete failed");
            });
        }).start();
    }

    private void selectAsActive() {
        JTable t = curTable(); DefaultTableModel m = curModel();
        int row = t.getSelectedRow();
        if (row < 0) { JOptionPane.showMessageDialog(this, "Select a downloaded model"); return; }
        String id = m.getValueAt(row, C_ID).toString();
        String name = m.getValueAt(row, C_NAME).toString();
        String st = m.getValueAt(row, C_STATUS).toString();
        if (!st.contains("downloaded")) { JOptionPane.showMessageDialog(this, name + " not downloaded"); return; }
        String type = tabbedPane.getSelectedIndex() == 0 ? "image" : "music";
        new Thread(() -> {
            boolean ok = client.selectModel(type, id);
            SwingUtilities.invokeLater(() -> {
                if (ok) statusLabel.setText("Activated: " + name);
                else statusLabel.setText("Select failed");
            });
        }).start();
    }

    private void finishDownload() {
        if (!isDownloading) return;
        isDownloading = false;
        downloadBtn.setEnabled(true);
        refreshBtn.setEnabled(true);
    }

    private void startPolling() {
        if (pollTimer != null && pollTimer.isRunning()) return;
        pollTimer = new Timer(5000, e -> {
            if (!serverOnline) return;
            List<DownloadProgress> list = client.getDownloadProgress();
            boolean any = false;
            for (DownloadProgress dp : list) {
                if (dp.isDownloading()) {
                    any = true;
                    globalProgress.setVisible(true);
                    globalProgress.setIndeterminate(false);
                    globalProgress.setValue((int) dp.getProgress());
                    globalProgress.setString(String.format("%.1f%%", dp.getProgress()));
                    break;
                }
            }
            if (!any) globalProgress.setVisible(false);
        });
        pollTimer.start();
    }

    private void stopPolling() {
        if (pollTimer != null) { pollTimer.stop(); pollTimer = null; }
    }

    private JTable curTable() { return tabbedPane.getSelectedIndex() == 0 ? imageTable : musicTable; }
    private DefaultTableModel curModel() { return tabbedPane.getSelectedIndex() == 0 ? imageModel : musicModel; }
}
