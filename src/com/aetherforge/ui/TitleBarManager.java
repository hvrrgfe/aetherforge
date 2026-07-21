package com.aetherforge.ui;

import com.aetherforge.util.Colors;
import com.aetherforge.util.I18n;
import javax.swing.*;
import java.awt.*;
import java.awt.event.MouseAdapter;
import java.awt.event.MouseEvent;
import java.awt.event.WindowEvent;

/**
 * 鏍囬鏍忕鐞嗗櫒 鈥?浠?MainWindow 鎻愬彇鐨勭嫭绔嬬粍浠? * 绠＄悊鑷粯鏍囬鏍忋€佹嫋鎷界Щ鍔ㄣ€佹渶灏忓寲/鏈€澶у寲/鍏抽棴鎸夐挳
 */
public class TitleBarManager {

    private final JFrame frame;
    private final JPanel titleBar;
    private boolean isMaximized;
    private int normalX, normalY, normalWidth, normalHeight;
    private int dragStartX, dragStartY, frameStartX, frameStartY;

    public TitleBarManager(JFrame frame, JButton menuButton) {
        this.frame = frame;
        this.titleBar = createTitleBar(menuButton);
    }

    public JPanel getTitleBar() { return titleBar; }

    public void toggleMaximized() {
        if (isMaximized) {
            frame.setBounds(normalX, normalY, normalWidth, normalHeight);
            isMaximized = false;
        } else {
            normalX = frame.getX(); normalY = frame.getY();
            normalWidth = frame.getWidth(); normalHeight = frame.getHeight();
            GraphicsEnvironment ge = GraphicsEnvironment.getLocalGraphicsEnvironment();
            Rectangle bounds = ge.getMaximumWindowBounds();
            frame.setBounds(bounds);
            isMaximized = true;
        }
    }

    public boolean isWindowMaximized() { return isMaximized; }

    private JPanel createTitleBar(JButton menuButton) {
        JPanel bar = new JPanel(new BorderLayout()) {
            @Override
            protected void paintComponent(Graphics g) {
                Graphics2D g2 = (Graphics2D) g.create();
                g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
                g2.setColor(Colors.bgDark());
                g2.fillRect(0, 0, getWidth(), getHeight());
                g2.setColor(Colors.borderLine());
                g2.fillRect(0, getHeight() - 1, getWidth(), 1);
                g2.dispose();
            }
        };
        bar.setPreferredSize(new Dimension(0, 40));

        // 宸︿晶锛氳彍鍗?+ 鍥炬爣 + 鏍囬
        JPanel left = new JPanel(new FlowLayout(FlowLayout.LEFT, 8, 0));
        left.setOpaque(false);
        if (menuButton != null) left.add(menuButton);
        JLabel icon = new JLabel(new com.aetherforge.util.EntityIcon(Colors.BLUE, 16));
        icon.setBorder(BorderFactory.createEmptyBorder(0, 12, 0, 4));
        left.add(icon);
        JLabel title = new JLabel("AetherForge Studio");
        title.setFont(UIManager.getFont("defaultFont").deriveFont(Font.PLAIN, 12f));
        title.setForeground(Colors.textSecondary());
        left.add(title);
        bar.add(left, BorderLayout.WEST);

        // 鍙充晶锛氭渶灏忓寲 / 鏈€澶у寲 / 鍏抽棴
        JPanel right = new JPanel(new FlowLayout(FlowLayout.RIGHT, 0, 0));
        right.setOpaque(false);
        right.add(createButton(TitleBtn.MINIMIZE));
        right.add(createButton(TitleBtn.MAXIMIZE));
        right.add(createButton(TitleBtn.CLOSE));
        bar.add(right, BorderLayout.EAST);

        // 鎷栨嫿
        WindowDragHandler dragHandler = new WindowDragHandler();
        bar.addMouseListener(dragHandler);
        bar.addMouseMotionListener(dragHandler);

        return bar;
    }

    private JButton createButton(TitleBtn type) {
        JButton btn = new JButton() {
            @Override
            protected void paintComponent(Graphics g) {
                Graphics2D g2 = (Graphics2D) g.create();
                g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
                if (getModel().isRollover()) {
                    g2.setColor(type == TitleBtn.CLOSE ? new Color(0xe8, 0x11, 0x23) : Colors.bgHover());
                    g2.fillRect(0, 0, getWidth(), getHeight());
                }
                if (getModel().isPressed()) {
                    g2.setColor(type == TitleBtn.CLOSE ? new Color(0xc0, 0x0e, 0x1a) : Colors.bgRaised());
                    g2.fillRect(0, 0, getWidth(), getHeight());
                }
                g2.setColor(type == TitleBtn.CLOSE && getModel().isRollover() ? Color.WHITE : Colors.textSecondary());
                int cx = getWidth() / 2, cy = getHeight() / 2, sv = 10;
                g2.setStroke(new BasicStroke(1.2f));
                switch (type) {
                    case MINIMIZE -> g2.drawLine(cx - sv / 2, cy, cx + sv / 2, cy);
                    case MAXIMIZE -> g2.drawRect(cx - sv / 2, cy - sv / 2 + 1, sv, sv - 1);
                    case CLOSE -> {
                        g2.drawLine(cx - sv / 2, cy - sv / 2, cx + sv / 2, cy + sv / 2);
                        g2.drawLine(cx + sv / 2, cy - sv / 2, cx - sv / 2, cy + sv / 2);
                    }
                }
                g2.dispose();
            }
        };
        btn.setPreferredSize(new Dimension(48, 40));
        btn.setFocusPainted(false);
        btn.setBorderPainted(false);
        btn.setContentAreaFilled(false);
        btn.setCursor(Cursor.getPredefinedCursor(Cursor.HAND_CURSOR));
        btn.addActionListener(e -> handleButton(type));
        return btn;
    }

    private void handleButton(TitleBtn type) {
        switch (type) {
            case MINIMIZE -> frame.setExtendedState(JFrame.ICONIFIED);
            case MAXIMIZE -> toggleMaximized();
            case CLOSE -> {
                WindowEvent we = new WindowEvent(frame, WindowEvent.WINDOW_CLOSING);
                Toolkit.getDefaultToolkit().getSystemEventQueue().postEvent(we);
            }
        }
    }

    private enum TitleBtn { MINIMIZE, MAXIMIZE, CLOSE }

    private class WindowDragHandler extends MouseAdapter {
        @Override
        public void mousePressed(MouseEvent e) {
            dragStartX = e.getXOnScreen();
            dragStartY = e.getYOnScreen();
            frameStartX = frame.getX();
            frameStartY = frame.getY();
        }

        @Override
        public void mouseDragged(MouseEvent e) {
            if (!isMaximized) {
                frame.setLocation(
                    frameStartX + e.getXOnScreen() - dragStartX,
                    frameStartY + e.getYOnScreen() - dragStartY
                );
            }
        }

        @Override
        public void mouseClicked(MouseEvent e) {
            if (e.getClickCount() == 2) toggleMaximized();
        }
    }
}
