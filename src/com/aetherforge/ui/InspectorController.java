package com.aetherforge.ui;

import com.aetherforge.model.Entity;
import com.aetherforge.model.Scene;
import com.aetherforge.util.Colors;
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
        panel.setBackground(Colors.bgDeepest());
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
            empty.setForeground(Colors.textMuted());
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
            // Name editing
            addStringField(I18n.get("inspector.name"), sel.getName(), s -> { sel.setName(s); scene.fireChange(); });

            addEditField("X", sel.getX(), v -> { sel.setX(v); scene.fireChange(); });
            addEditField("Y", sel.getY(), v -> { sel.setY(v); scene.fireChange(); });
            addEditField(I18n.get("inspector.width"), sel.getWidth(), v -> { sel.setWidth(v); scene.fireChange(); });
            addEditField(I18n.get("inspector.height"), sel.getHeight(), v -> { sel.setHeight(v); scene.fireChange(); });

            // Color swatch
            addColorField(sel);
        }

        panel.revalidate();
        panel.repaint();
    }

    private void addTitle(String text) {
        JLabel l = new JLabel("  " + text);
        l.setFont(UIManager.getFont("defaultFont").deriveFont(Font.BOLD, 12f));
        l.setForeground(Colors.textPrimary());
        l.setBorder(new EmptyBorder(DP8, DP8, DP4, DP8));
        panel.add(l);
        JSeparator sep = new JSeparator();
        sep.setForeground(Colors.borderLine());
        sep.setBackground(Colors.borderLine());
        panel.add(sep);
    }

    private void addRow(String label, String value) {
        JPanel row = new JPanel(new BorderLayout());
        row.setBackground(Colors.bgDeepest());
        row.setBorder(new EmptyBorder(DP4, DP12, DP4, DP12));
        row.setMaximumSize(new Dimension(9999, 24));
        JLabel l = new JLabel(label);
        l.setFont(UIManager.getFont("defaultFont").deriveFont(Font.PLAIN, 11f));
        l.setForeground(Colors.textMuted());
        l.setPreferredSize(new Dimension(60, 16));
        JLabel v = new JLabel(value);
        v.setFont(UIManager.getFont("defaultFont").deriveFont(Font.PLAIN, 11f));
        v.setForeground(Colors.textPrimary());
        row.add(l, BorderLayout.WEST);
        row.add(v, BorderLayout.CENTER);
        panel.add(row);
    }

    private void addSection(String text) {
        JLabel l = new JLabel("  " + text);
        l.setFont(UIManager.getFont("defaultFont").deriveFont(Font.BOLD, 10f));
        l.setForeground(Colors.textMuted());
        panel.add(l);
    }

    @FunctionalInterface
    private interface ValueSetter { void set(double v); }

    private void addEditField(String label, double value, ValueSetter setter) {
        JPanel row = new JPanel(new BorderLayout());
        row.setBackground(Colors.bgDeepest());
        row.setBorder(new EmptyBorder(1, DP10, 1, DP10));
        row.setMaximumSize(new Dimension(9999, 24));
        JLabel l = new JLabel(label);
        l.setFont(UIManager.getFont("defaultFont").deriveFont(Font.PLAIN, 11f));
        l.setForeground(Colors.textMuted());
        l.setPreferredSize(new Dimension(60, 18));
        JTextField field = new JTextField(String.valueOf((int) value));
        field.setFont(UIManager.getFont("defaultFont").deriveFont(Font.PLAIN, 11f));
        field.setForeground(Colors.textPrimary());
        field.setBackground(Colors.bgDark());
        field.setCaretColor(Colors.BLUE);
        field.setBorder(BorderFactory.createCompoundBorder(
            BorderFactory.createLineBorder(Colors.borderLine(), 1), new EmptyBorder(1, DP4, 1, DP4)));
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
                    field.setForeground(Colors.textPrimary());
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
            field.setForeground(Colors.textPrimary());
            field.setText(String.valueOf((int) v));
        } catch (NumberFormatException e) {
            field.setForeground(Colors.RED);
        }
    }

    @FunctionalInterface
    private interface StringSetter { void set(String s); }

    private void addStringField(String label, String value, StringSetter setter) {
        JPanel row = new JPanel(new BorderLayout());
        row.setBackground(Colors.bgDeepest());
        row.setBorder(new EmptyBorder(1, DP10, 1, DP10));
        row.setMaximumSize(new Dimension(9999, 24));
        JLabel l = new JLabel(label);
        l.setFont(UIManager.getFont("defaultFont").deriveFont(Font.PLAIN, 11f));
        l.setForeground(Colors.textMuted());
        l.setPreferredSize(new Dimension(60, 18));
        JTextField field = new JTextField(value);
        field.setFont(UIManager.getFont("defaultFont").deriveFont(Font.PLAIN, 11f));
        field.setForeground(Colors.textPrimary());
        field.setBackground(Colors.bgDark());
        field.setCaretColor(Colors.BLUE);
        field.setBorder(BorderFactory.createCompoundBorder(
            BorderFactory.createLineBorder(Colors.borderLine(), 1), new EmptyBorder(1, DP4, 1, DP4)));
        field.addActionListener(e -> { setter.set(field.getText()); scene.fireChange(); });
        field.addFocusListener(new java.awt.event.FocusAdapter() {
            @Override public void focusLost(java.awt.event.FocusEvent e) { setter.set(field.getText()); scene.fireChange(); }
        });
        row.add(l, BorderLayout.WEST);
        row.add(field, BorderLayout.CENTER);
        panel.add(row);
    }

    private void addColorField(com.aetherforge.model.Entity entity) {
        java.awt.Color[] palette = com.aetherforge.util.Colors.ENTITY_PALETTE;

        JPanel row = new JPanel(new FlowLayout(FlowLayout.LEFT, 4, 2));
        row.setBackground(Colors.bgDeepest());
        row.setBorder(new EmptyBorder(4, DP10, 4, DP10));
        row.setMaximumSize(new Dimension(9999, 32));

        JLabel label = new JLabel(I18n.get("inspector.type") + " color");
        label.setFont(UIManager.getFont("defaultFont").deriveFont(Font.PLAIN, 11f));
        label.setForeground(Colors.textMuted());
        label.setPreferredSize(new Dimension(60, 20));
        row.add(label);

        for (java.awt.Color c : palette) {
            JButton swatch = new JButton() {
                @Override
                protected void paintComponent(Graphics g) {
                    Graphics2D g2 = (Graphics2D) g.create();
                    g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
                    boolean isCurrent = entity.getColor().equals(c);
                    g2.setColor(c);
                    g2.fillOval(2, 2, getWidth() - 4, getHeight() - 4);
                    if (isCurrent) {
                        g2.setColor(java.awt.Color.WHITE);
                        g2.setStroke(new BasicStroke(2f));
                        g2.drawOval(1, 1, getWidth() - 2, getHeight() - 2);
                    }
                    g2.dispose();
                }
            };
            swatch.setPreferredSize(new Dimension(20, 20));
            swatch.setFocusPainted(false);
            swatch.setBorderPainted(false);
            swatch.setContentAreaFilled(false);
            swatch.setCursor(Cursor.getPredefinedCursor(Cursor.HAND_CURSOR));
            swatch.setToolTipText(String.format("#%06x", c.getRGB() & 0xFFFFFF));
            swatch.addActionListener(e -> { entity.setColor(c); scene.fireChange(); refresh(); });
            row.add(swatch);
        }
        panel.add(row);
    }
}
