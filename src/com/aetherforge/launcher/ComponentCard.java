package com.aetherforge.launcher;

import com.aetherforge.util.Colors;
import javax.swing.*;
import javax.swing.border.EmptyBorder;
import java.awt.*;

/**
 * 组件卡片 — 每个组件的启动/停止 UI
 */
class ComponentCard extends JPanel {

    private final String title;
    private final String subtitle;
    private final String description;
    private final String command;
    private final Color accentColor;
    private final ComponentPanel parent;
    private final boolean isServer;

    private final JButton actionButton;
    private final JLabel statusLabel;
    private final JLabel indicator;
    private ComponentPanel.ManagedProcess managedProcess;
    private boolean running;

    private final Timer statusCheckTimer;

    ComponentCard(String title, String subtitle, String description,
                  String command, Color accentColor,
                  ComponentPanel parent, boolean isServer) {
        this.title = title;
        this.subtitle = subtitle;
        this.description = description;
        this.command = command;
        this.accentColor = accentColor;
        this.parent = parent;
        this.isServer = isServer;

        setLayout(new BorderLayout());
        setBackground(Colors.bgRaised());
        setBorder(BorderFactory.createCompoundBorder(
            BorderFactory.createLineBorder(Colors.borderLine(), 1),
            new EmptyBorder(12, 14, 12, 14)
        ));

        // 左侧内容
        JPanel contentPanel = new JPanel(new BorderLayout(8, 4));
        contentPanel.setOpaque(false);

        JPanel titleRow = new JPanel(new FlowLayout(FlowLayout.LEFT, 6, 0));
        titleRow.setOpaque(false);

        indicator = new JLabel("\u25CF");
        indicator.setFont(UIManager.getFont("defaultFont").deriveFont(Font.PLAIN, 10f));
        indicator.setForeground(Colors.textMuted());

        JLabel titleLabel = new JLabel(title);
        titleLabel.setFont(UIManager.getFont("defaultFont").deriveFont(Font.BOLD, 13f));
        titleLabel.setForeground(Colors.textPrimary());

        titleRow.add(indicator);
        titleRow.add(titleLabel);
        contentPanel.add(titleRow, BorderLayout.NORTH);

        JLabel subLabel = new JLabel(subtitle);
        subLabel.setFont(UIManager.getFont("defaultFont").deriveFont(11f));
        subLabel.setForeground(Colors.textSecondary());
        contentPanel.add(subLabel, BorderLayout.CENTER);

        JLabel descLabel = new JLabel(description);
        descLabel.setFont(UIManager.getFont("defaultFont").deriveFont(10f));
        descLabel.setForeground(Colors.textMuted());
        contentPanel.add(descLabel, BorderLayout.SOUTH);

        add(contentPanel, BorderLayout.CENTER);

        // 右侧操作区
        JPanel actionPanel = new JPanel(new BorderLayout(4, 4));
        actionPanel.setOpaque(false);
        actionPanel.setBorder(new EmptyBorder(0, 12, 0, 0));

        statusLabel = new JLabel("就绪");
        statusLabel.setFont(UIManager.getFont("defaultFont").deriveFont(10f));
        statusLabel.setForeground(Colors.textMuted());
        statusLabel.setHorizontalAlignment(SwingConstants.CENTER);

        actionButton = new JButton("启动");
        actionButton.setFont(UIManager.getFont("defaultFont").deriveFont(Font.BOLD, 12f));
        actionButton.setFocusPainted(false);
        actionButton.setBackground(accentColor);
        actionButton.setForeground(Color.WHITE);
        actionButton.setPreferredSize(new Dimension(80, 28));
        actionButton.setBorder(BorderFactory.createEmptyBorder(2, 12, 2, 12));
        actionButton.setCursor(Cursor.getPredefinedCursor(Cursor.HAND_CURSOR));
        actionButton.addActionListener(e -> toggleProcess());

        actionPanel.add(statusLabel, BorderLayout.NORTH);
        actionPanel.add(actionButton, BorderLayout.SOUTH);
        add(actionPanel, BorderLayout.EAST);

        // 服务器状态轮询
        if (isServer) {
            statusCheckTimer = new Timer(5000, e -> checkStatus());
            statusCheckTimer.start();
        } else {
            statusCheckTimer = null;
        }
    }

    private void toggleProcess() {
        if (running) {
            stopProcess();
        } else {
            startProcess();
        }
    }

    private void startProcess() {
        managedProcess = parent.startProcess(title, command, isServer);
        running = true;
        updateUIState();
        parent.setGlobalStatus(title + " 已启动");
    }

    private void stopProcess() {
        if (managedProcess != null) {
            managedProcess.stop();
            managedProcess = null;
        }
        running = false;
        updateUIState();
        parent.setGlobalStatus(title + " 已停止");
    }

    private void updateUIState() {
        SwingUtilities.invokeLater(() -> {
            if (running) {
                actionButton.setText("停止");
                actionButton.setBackground(Colors.RED);
                statusLabel.setText("运行中");
                statusLabel.setForeground(Colors.GREEN);
                indicator.setForeground(Colors.GREEN);
            } else {
                actionButton.setText("启动");
                actionButton.setBackground(accentColor);
                statusLabel.setText("就绪");
                statusLabel.setForeground(Colors.textMuted());
                indicator.setForeground(Colors.textMuted());
            }
        });
    }

    private void checkStatus() {
        if (!isServer || managedProcess == null) return;
        boolean alive = managedProcess.isAlive();
        if (alive != this.running) {
            this.running = alive;
            updateUIState();
        }
    }
}