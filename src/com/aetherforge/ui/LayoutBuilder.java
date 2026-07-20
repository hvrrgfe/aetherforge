package com.aetherforge.ui;

import com.aetherforge.util.Colors;
import com.aetherforge.util.DarkScrollBarUI;
import com.aetherforge.util.I18n;
import javax.swing.*;
import javax.swing.border.EmptyBorder;
import java.awt.*;
import java.awt.event.MouseAdapter;

public final class LayoutBuilder {

    private LayoutBuilder() {}

    public static final int DP4 = 4, DP8 = 8, DP10 = 10, DP12 = 12;
    public static final int DP16 = 16, DP24 = 24, DP28 = 28, DP40 = 40;
    public static final int DP240 = 240;

    public static JPanel buildContent(JPanel titleBar, JSplitPane mainSplit, JPanel statusBar) {
        JPanel content = new JPanel(new BorderLayout());
        content.setBackground(Colors.BACKGROUND_DEEPEST);
        content.add(titleBar, BorderLayout.NORTH);
        content.add(mainSplit, BorderLayout.CENTER);
        content.add(statusBar, BorderLayout.SOUTH);
        return content;
    }

    public static JPanel createTitleBar(MouseAdapter dragHandler) {
        JPanel titleBar = new JPanel(new BorderLayout()) {
            @Override
            protected void paintComponent(Graphics g) {
                Graphics2D g2 = (Graphics2D) g.create();
                g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
                g2.setColor(Colors.BACKGROUND_DARK);
                g2.fillRect(0, 0, getWidth(), getHeight());
                g2.setColor(Colors.BORDER_LINE);
                g2.fillRect(0, getHeight() - 1, getWidth(), 1);
                g2.dispose();
            }
        };
        titleBar.setPreferredSize(new Dimension(0, DP40));
        JPanel left = new JPanel(new FlowLayout(FlowLayout.LEFT, DP8, 0));
        left.setOpaque(false);
        JLabel icon = new JLabel(new com.aetherforge.util.EntityIcon(Colors.BLUE, DP16));
        icon.setBorder(new EmptyBorder(0, DP12, 0, DP4));
        JLabel tl = new JLabel("AetherForge Studio");
        tl.setFont(UIManager.getFont("defaultFont").deriveFont(Font.PLAIN, 12f));
        tl.setForeground(Colors.TEXT_SECONDARY);
        left.add(icon); left.add(tl);
        titleBar.add(left, BorderLayout.WEST);
        JPanel right = new JPanel(new FlowLayout(FlowLayout.RIGHT, 0, 0));
        right.setOpaque(false);
        right.add(createTitleButton(TitleBtn.MINIMIZE));
        right.add(createTitleButton(TitleBtn.MAXIMIZE));
        right.add(createTitleButton(TitleBtn.CLOSE));
        titleBar.add(right, BorderLayout.EAST);
        titleBar.addMouseListener(dragHandler);
        titleBar.addMouseMotionListener(dragHandler);
        return titleBar;
    }

    public enum TitleBtn { MINIMIZE, MAXIMIZE, CLOSE }

    public static JButton createTitleButton(TitleBtn type) {
        JButton btn = new JButton() {
            @Override
            protected void paintComponent(Graphics g) {
                Graphics2D g2 = (Graphics2D) g.create();
                g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
                if (getModel().isRollover()) {
                    g2.setColor(type == TitleBtn.CLOSE ? new Color(0xe8,0x11,0x23) : Colors.BACKGROUND_HOVER);
                    g2.fillRect(0, 0, getWidth(), getHeight());
                }
                if (getModel().isPressed()) {
                    g2.setColor(type == TitleBtn.CLOSE ? new Color(0xc0,0x0e,0x1a) : Colors.BACKGROUND_RAISED);
                    g2.fillRect(0, 0, getWidth(), getHeight());
                }
                g2.setColor(type == TitleBtn.CLOSE && getModel().isRollover() ? Color.WHITE : Colors.TEXT_SECONDARY);
                int cx = getWidth() / 2, cy = getHeight() / 2, sv = 10;
                g2.setStroke(new BasicStroke(1.2f));
                switch (type) {
                    case MINIMIZE -> g2.drawLine(cx - sv/2, cy, cx + sv/2, cy);
                    case MAXIMIZE -> g2.drawRect(cx - sv/2, cy - sv/2 + 1, sv, sv - 1);
                    case CLOSE -> { g2.drawLine(cx - sv/2, cy - sv/2, cx + sv/2, cy + sv/2);
                                    g2.drawLine(cx + sv/2, cy - sv/2, cx - sv/2, cy + sv/2); }
                }
                g2.dispose();
            }
        };
        btn.setPreferredSize(new Dimension(48, DP40));
        btn.setFocusPainted(false); btn.setBorderPainted(false);
        btn.setContentAreaFilled(false);
        btn.setCursor(Cursor.getPredefinedCursor(Cursor.HAND_CURSOR));
        return btn;
    }

    public static JPanel createPanelWithHeader(String titleKey, JComponent body) {
        JPanel panel = new JPanel(new BorderLayout());
        panel.setBackground(Colors.BACKGROUND_PANEL);
        JPanel header = new JPanel(new BorderLayout());
        header.setBackground(Colors.BACKGROUND_RAISED);
        header.setPreferredSize(new Dimension(0, DP28));
        header.setBorder(new EmptyBorder(0, DP10, 0, DP10));
        JLabel l = new JLabel(I18n.get(titleKey));
        l.setFont(UIManager.getFont("defaultFont").deriveFont(Font.BOLD, 10f));
        l.setForeground(Colors.TEXT_MUTED);
        header.add(l, BorderLayout.WEST);
        panel.add(header, BorderLayout.NORTH);
        panel.add(body, BorderLayout.CENTER);
        return panel;
    }

    public static JScrollPane styledScroll(JComponent view) {
        JScrollPane sp = new JScrollPane(view);
        sp.setBorder(BorderFactory.createEmptyBorder());
        sp.getVerticalScrollBar().setUI(new DarkScrollBarUI());
        sp.setBackground(Colors.BACKGROUND_PANEL);
        return sp;
    }

    public static JPanel createViewportToolbar(Runnable onNew, Runnable onDelete) {
        JPanel toolbar = new JPanel(new FlowLayout(FlowLayout.LEFT, 2, 3));
        toolbar.setBackground(Colors.BACKGROUND_RAISED);
        toolbar.setPreferredSize(new Dimension(0, DP28));
        toolbar.setBorder(new EmptyBorder(0, DP4, 0, DP4));
        String[] names = {I18n.get("viewport.tool.select"), I18n.get("viewport.tool.move"), I18n.get("viewport.tool.scale")};
        ButtonGroup group = new ButtonGroup();
        for (int i = 0; i < names.length; i++) {
            JToggleButton tb = new JToggleButton(names[i]);
            tb.setFont(UIManager.getFont("defaultFont").deriveFont(Font.PLAIN, 11f));
            tb.setFocusPainted(false); tb.setBorderPainted(false);
            tb.setBackground(Colors.BACKGROUND_RAISED);
            tb.setForeground(Colors.TEXT_SECONDARY);
            tb.setPreferredSize(new Dimension(52, 24));
            tb.setCursor(Cursor.getPredefinedCursor(Cursor.HAND_CURSOR));
            tb.setRolloverEnabled(true);
            if (i == 0) tb.setSelected(true);
            tb.addItemListener(e -> {
                tb.setBackground(tb.isSelected() ? Colors.BACKGROUND_HOVER : Colors.BACKGROUND_RAISED);
                tb.setForeground(tb.isSelected() ? Colors.BLUE : Colors.TEXT_SECONDARY);
            });
            group.add(tb);
            toolbar.add(tb);
        }
        toolbar.add(Box.createHorizontalStrut(DP8));
        toolbar.add(smallBtn("+", e -> onNew.run()));
        toolbar.add(smallBtn("-", e -> onDelete.run()));
        return toolbar;
    }

    private static JButton smallBtn(String text, java.awt.event.ActionListener listener) {
        JButton btn = new JButton(text);
        btn.setFont(UIManager.getFont("defaultFont").deriveFont(Font.BOLD, 13f));
        btn.setFocusPainted(false); btn.setBorderPainted(false);
        btn.setBackground(Colors.BACKGROUND_RAISED);
        btn.setForeground(Colors.TEXT_SECONDARY);
        btn.setPreferredSize(new Dimension(24, 24));
        btn.setCursor(Cursor.getPredefinedCursor(Cursor.HAND_CURSOR));
        btn.addActionListener(listener);
        return btn;
    }

    public static JPanel createStatusBar() {
        JPanel bar = new JPanel(new BorderLayout());
        bar.setBackground(Colors.BACKGROUND_RAISED);
        bar.setPreferredSize(new Dimension(0, DP24));
        return bar;
    }

    public static JSplitPane splitH(JComponent left, JComponent right) {
        JSplitPane sp = new JSplitPane(JSplitPane.HORIZONTAL_SPLIT, left, right);
        sp.setBorder(BorderFactory.createEmptyBorder());
        sp.setBackground(Colors.BACKGROUND_DEEPEST);
        sp.setDividerSize(2);
        sp.setResizeWeight(0);
        sp.setContinuousLayout(true);
        return sp;
    }

    public static JSplitPane splitV(JComponent top, JComponent bottom) {
        JSplitPane sp = new JSplitPane(JSplitPane.VERTICAL_SPLIT, top, bottom);
        sp.setBorder(BorderFactory.createEmptyBorder());
        sp.setBackground(Colors.BACKGROUND_DEEPEST);
        sp.setDividerSize(2);
        sp.setResizeWeight(1.0);
        sp.setContinuousLayout(true);
        return sp;
    }
}
