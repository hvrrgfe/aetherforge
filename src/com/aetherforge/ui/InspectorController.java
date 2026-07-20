package com.aetherforge.ui;

import com.aetherforge.model.Entity;
import com.aetherforge.model.Scene;
import com.aetherforge.util.Colors;
import com.aetherforge.util.I18n;
import javax.swing.*;
import javax.swing.border.EmptyBorder;
import java.awt.*;

/**
 * 检查器控制器 — 管理属性面板
 * 通过 Scene 监听器获取选中状态变化
 */
public class InspectorController implements com.aetherforge.model.SceneListener {

    private final Scene scene;
    private final JPanel panel;
    private static final int DP4 = 4, DP8 = 8, DP10 = 10, DP12 = 12;

    public InspectorController(Scene scene) {
        this.scene = scene;
        this.panel = new JPanel();
        panel.setLayout(new BoxLayout(panel, BoxLayout.Y_AXIS));
        panel.setBackground(Colors.BACKGROUND_DEEPEST);
        scene.addListener(this);
    }

    public JPanel getPanel() { return panel; }

    @Override
    public void selectionChanged(Entity selected) {
        refresh();
    }

    @Override
    public void sceneChanged() {
        refresh();
    }

    public void refresh() {
        panel.removeAll();
        Entity sel = scene.getSelectedEntity();

        if (sel == null) {
            JLabel empty = new JLabel("  " + I18n.get("inspector.empty"));
            empty.setFont(UIManager.getFont("defaultFont").deriveFont(Font.PLAIN, 12f));
            empty.setForeground(Colors.TEXT_MUTED);
            empty.setBorder(new EmptyBorder(DP10, DP10, DP10, DP10));
            panel.add(empty);
        } else {
            addTitle(sel.getName());

            addRow(I18n.get("inspector.id"), sel.getId());
            addRow(I18n.get("inspector.type"), sel.getType());
            addRow(I18n.get("inspector.name"), sel.getName());
            addRow(I18n.get("inspector.position"),
                String.format("%.1f, %.1f", sel.getX(), sel.getY()));
            addRow(I18n.get("inspector.size"),
                String.format("%.0f \u00D7 %.0f", sel.getWidth(), sel.getHeight()));

            panel.add(Box.createVerticalStrut(DP8));
            addSection(I18n.get("inspector.transform"));

            // Editable fields with FocusLost validation
            addEditField("X", sel.getX(), v -> { sel.setX(v); scene.fireChange(); });
            addEditField("Y", sel.getY(), v -> { sel.setY(v); scene.fireChange(); });
            addEditField(I18n.get("inspector.width"), sel.getWidth(), v -> { sel.setWidth(v); scene.fireChange(); });
            addEditField(I18n.get("inspector.height"), sel.getHeight(), v -> { sel.setHeight(v); scene.fireChange(); });
        }

        panel.revalidate();
        panel.repaint();
    }

    private void addTitle(String text) {
        JLabel l = new JLabel("  " + text);
        l.setFont(UIManager.getFont("defaultFont").deriveFont(Font.BOLD, 12f));
        l.setForeground(Colors.TEXT_PRIMARY);
        l.setBorder(new EmptyBorder(DP8, DP8, DP4, DP8));
        panel.add(l);
        JSeparator sep = new JSeparator();
        sep.setForeground(Colors.BORDER_LINE);
        sep.setBackground(Colors.BORDER_LINE);
        panel.add(sep);
    }

    private void addRow(String label, String value) {
        JPanel row = new JPanel(new BorderLayout());
        row.setBackground(Colors.BACKGROUND_DEEPEST);
        row.setBorder(new EmptyBorder(DP4, DP12, DP4, DP12));
        row.setMaximumSize(new Dimension(9999, 24));
        JLabel l = new JLabel(label);
        l.setFont(UIManager.getFont("defaultFont").deriveFont(Font.PLAIN, 11f));
        l.setForeground(Colors.TEXT_MUTED);
        l.setPreferredSize(new Dimension(60, 16));
        JLabel v = new JLabel(value);
        v.setFont(UIManager.getFont("defaultFont").deriveFont(Font.PLAIN, 11f));
        v.setForeground(Colors.TEXT_PRIMARY);
        row.add(l, BorderLayout.WEST);
        row.add(v, BorderLayout.CENTER);
        panel.add(row);
    }

    private void addSection(String text) {
        JLabel l = new JLabel("  " + text);
        l.setFont(UIManager.getFont("defaultFont").deriveFont(Font.BOLD, 10f));
        l.setForeground(Colors.TEXT_MUTED);
        panel.add(l);
    }

    @FunctionalInterface
    private interface ValueSetter { void set(double v); }

    private void addEditField(String label, double value, ValueSetter setter) {
        JPanel row = new JPanel(new BorderLayout());
        row.setBackground(Colors.BACKGROUND_DEEPEST);
        row.setBorder(new EmptyBorder(1, DP10, 1, DP10));
        row.setMaximumSize(new Dimension(9999, 24));
        JLabel l = new JLabel(label);
        l.setFont(UIManager.getFont("defaultFont").deriveFont(Font.PLAIN, 11f));
        l.setForeground(Colors.TEXT_MUTED);
        l.setPreferredSize(new Dimension(60, 18));
        JTextField field = new JTextField(String.valueOf((int) value));
        field.setFont(UIManager.getFont("defaultFont").deriveFont(Font.PLAIN, 11f));
        field.setForeground(Colors.TEXT_PRIMARY);
        field.setBackground(Colors.BACKGROUND_DARK);
        field.setCaretColor(Colors.BLUE);
        field.setBorder(BorderFactory.createCompoundBorder(
            BorderFactory.createLineBorder(Colors.BORDER_LINE, 1), new EmptyBorder(1, DP4, 1, DP4)));
        field.setCursor(Cursor.getPredefinedCursor(Cursor.TEXT_CURSOR));

        // FocusLost + Enter validation (not per-keystroke)
        field.addActionListener(e -> applyFieldEdit(field, setter));
        field.addFocusListener(new java.awt.event.FocusAdapter() {
            @Override
            public void focusLost(java.awt.event.FocusEvent e) { applyFieldEdit(field, setter); }
        });
        // Visual feedback on the fly
        field.addKeyListener(new java.awt.event.KeyAdapter() {
            @Override
            public void keyReleased(java.awt.event.KeyEvent e) {
                try {
                    Double.parseDouble(field.getText());
                    field.setForeground(Colors.TEXT_PRIMARY);
                } catch (NumberFormatException ex) {
                    field.setForeground(Colors.RED);
                }
            }
        });

        row.add(l, BorderLayout.WEST);
        row.add(field, BorderLayout.CENTER);
        panel.add(row);
    }

    private void applyFieldEdit(JTextField field, ValueSetter setter) {
        try {
            double v = Double.parseDouble(field.getText().trim());
            setter.set(v);
            field.setForeground(Colors.TEXT_PRIMARY);
            // Keep formatted value
            field.setText(String.valueOf((int) v));
        } catch (NumberFormatException e) {
            field.setForeground(Colors.RED);
        }
    }
}
