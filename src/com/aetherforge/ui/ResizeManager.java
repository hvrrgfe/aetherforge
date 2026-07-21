package com.aetherforge.ui;

import java.awt.*;
import java.awt.event.MouseAdapter;
import java.awt.event.MouseEvent;
import javax.swing.JFrame;

/**
 * 窗口缩放管理器 — 从 MainWindow 提取的独立组件
 * 支持 8 方向拖拽缩放，自动更新光标形状
 */
public class ResizeManager {

    private static final int RESIZE_MARGIN = 6;

    private static final int RN = 0, R_N = 1, R_S = 2, R_W = 4, R_E = 8;

    private final JFrame frame;
    private int resizeDirection = RN;
    private int startX, startY, startWidth, startHeight;

    public ResizeManager(JFrame frame) {
        this.frame = frame;
        MouseAdapter resizer = new ResizeAdapter();
        frame.addMouseListener(resizer);
        frame.addMouseMotionListener(resizer);
    }

    private int computeDirection(int mx, int my) {
        int w = frame.getWidth(), h = frame.getHeight(), d = RN;
        if (my < RESIZE_MARGIN) d |= R_N;
        if (my > h - RESIZE_MARGIN) d |= R_S;
        if (mx < RESIZE_MARGIN) d |= R_W;
        if (mx > w - RESIZE_MARGIN) d |= R_E;
        return d;
    }

    private void updateCursor(int direction) {
        int cursor = switch (direction) {
            case R_N, R_S -> Cursor.N_RESIZE_CURSOR;
            case R_W, R_E -> Cursor.E_RESIZE_CURSOR;
            case R_N | R_W, R_S | R_E -> Cursor.NW_RESIZE_CURSOR;
            case R_N | R_E, R_S | R_W -> Cursor.NE_RESIZE_CURSOR;
            default -> Cursor.DEFAULT_CURSOR;
        };
        frame.setCursor(Cursor.getPredefinedCursor(cursor));
    }

    private class ResizeAdapter extends MouseAdapter {
        @Override
        public void mouseMoved(MouseEvent e) {
            if (isMaximized()) return;
            resizeDirection = computeDirection(e.getX(), e.getY());
            updateCursor(resizeDirection);
        }

        @Override
        public void mousePressed(MouseEvent e) {
            if (isMaximized()) return;
            resizeDirection = computeDirection(e.getX(), e.getY());
            if (resizeDirection != RN) {
                startX = e.getXOnScreen();
                startY = e.getYOnScreen();
                startWidth = frame.getWidth();
                startHeight = frame.getHeight();
            }
        }

        @Override
        public void mouseDragged(MouseEvent e) {
            if (isMaximized() || resizeDirection == RN) return;
            int dx = e.getXOnScreen() - startX;
            int dy = e.getYOnScreen() - startY;
            int nx = frame.getX(), ny = frame.getY();
            int nw = startWidth, nh = startHeight;

            if ((resizeDirection & R_E) != 0) nw = startWidth + dx;
            if ((resizeDirection & R_W) != 0) { nw = startWidth - dx; nx = frame.getX() + dx; }
            if ((resizeDirection & R_S) != 0) nh = startHeight + dy;
            if ((resizeDirection & R_N) != 0) { nh = startHeight - dy; ny = frame.getY() + dy; }

            Dimension min = frame.getMinimumSize();
            if (nw < min.width) {
                if ((resizeDirection & R_W) != 0) nx = frame.getX() + startWidth - min.width;
                nw = min.width;
            }
            if (nh < min.height) {
                if ((resizeDirection & R_N) != 0) ny = frame.getY() + startHeight - min.height;
                nh = min.height;
            }
            frame.setBounds(nx, ny, nw, nh);
        }

        @Override
        public void mouseExited(MouseEvent e) {
            resizeDirection = RN;
            frame.setCursor(Cursor.getDefaultCursor());
        }
    }

    private boolean isMaximized() {
        return (frame.getExtendedState() & JFrame.MAXIMIZED_BOTH) != 0;
    }
}
