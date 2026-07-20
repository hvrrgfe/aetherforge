package com.aetherforge.ui;

import com.aetherforge.model.Entity;
import com.aetherforge.model.Scene;
import com.aetherforge.model.SceneListener;
import com.aetherforge.util.Colors;
import javax.swing.*;
import java.awt.*;
import java.awt.event.*;
import java.util.HashMap;
import java.util.Map;

/**
 * 2D viewport 依赖 Scene 而非 MainWindow
 * 通过 SceneListener 监听变更，不直接持有窗口引用
 */
public class ViewportPanel extends JPanel implements SceneListener {

    private final Scene scene;
    private Point dragStart;
    private boolean isDragging;
    private int dragOffsetX, dragOffsetY;
    private Entity dragEntity;
    private Entity hoveredEntity;

    private final Map<Entity, Long> appearTimes = new HashMap<>();
    private Entity fadingOut;
    private long fadeStartTime;
    private static final long APPEAR_MS = 280;
    private static final long FADE_MS = 200;
    public enum ToolMode { SELECT, MOVE, SCALE }
    private ToolMode toolMode = ToolMode.SELECT;
    public void setToolMode(ToolMode mode) { this.toolMode = mode; }
    public ToolMode getToolMode() { return toolMode; }
    private boolean snapEnabled = true;
    private Timer animTimer;

    public ViewportPanel(Scene scene) {
        this.scene = scene;
        setBackground(Colors.bgDeepest());
        setFocusable(true);
        setCursor(Cursor.getPredefinedCursor(Cursor.CROSSHAIR_CURSOR));

        ViewportMouseHandler mouseHandler = new ViewportMouseHandler();
        addMouseListener(mouseHandler);
        addMouseMotionListener(mouseHandler);
        addMouseWheelListener(mouseHandler);

        addKeyListener(new KeyAdapter() {
            @Override
            public void keyPressed(KeyEvent e) {
                if (e.getKeyCode() == KeyEvent.VK_S && (e.getModifiersEx() & InputEvent.SHIFT_DOWN_MASK) != 0) {
                    snapEnabled = !snapEnabled;
                }
                if (e.getKeyCode() == KeyEvent.VK_DELETE && scene.getSelectedEntity() != null) {
                    scene.executeCommand(new com.aetherforge.model.DeleteEntityCommand(scene, scene.getSelectedEntity()));
                }
            }
        });

        scene.addListener(this);

        JPopupMenu vpPopup = new JPopupMenu();
        vpPopup.setBackground(Colors.bgRaised());
        vpPopup.setBorder(BorderFactory.createLineBorder(Colors.borderLine()));
        JMenuItem createItem = new JMenuItem();
        createItem.setForeground(Colors.textPrimary());
        createItem.setBackground(Colors.bgRaised());
        createItem.addActionListener(e -> {
            scene.executeCommand(new com.aetherforge.model.CreateEntityCommand(scene, "entity", com.aetherforge.util.I18n.get("entity.new")));
        });
        vpPopup.add(createItem);
        JMenuItem delItem = new JMenuItem();
        delItem.setForeground(Colors.textPrimary());
        delItem.setBackground(Colors.bgRaised());
        delItem.addActionListener(e -> {
            if (scene.getSelectedEntity() != null)
                scene.executeCommand(new com.aetherforge.model.DeleteEntityCommand(scene, scene.getSelectedEntity()));
        });
        vpPopup.add(delItem);
        vpPopup.addSeparator();
        JMenuItem snapItem = new JMenuItem();
        snapItem.setForeground(Colors.textPrimary());
        snapItem.setBackground(Colors.bgRaised());
        snapItem.addActionListener(e -> { snapEnabled = !snapEnabled; repaint(); });
        vpPopup.add(snapItem);

        MouseAdapter popupAdapter = new MouseAdapter() {
            public void mousePressed(MouseEvent e) {
                if (e.isPopupTrigger()) showPopup(e);
            }
            public void mouseReleased(MouseEvent e) {
                if (e.isPopupTrigger()) showPopup(e);
            }
            private void showPopup(MouseEvent e) {
                createItem.setText("+ " + com.aetherforge.util.I18n.get("tree.new"));
                delItem.setText(com.aetherforge.util.I18n.get("tree.delete"));
                snapItem.setText((snapEnabled ? "Disable " : "Enable ") + "Snap");
                vpPopup.show(e.getComponent(), e.getX(), e.getY());
            }
        };
        addMouseListener(popupAdapter);
    }

    public void animateEntityIn(Entity entity) {
        appearTimes.put(entity, System.currentTimeMillis());
        startAnimTimer();
    }

    public boolean animateEntityOut(Entity entity) {
        fadingOut = entity;
        fadeStartTime = System.currentTimeMillis();
        startAnimTimer();
        return true;
    }

    private double getEffectiveZoom() {
        return scene.getCameraZoom();
    }

    private double getEffectiveCamX() {
        return scene.getCameraX();
    }

    private double getEffectiveCamY() {
        return scene.getCameraY();
    }

    private void updateCameraAnimation() {}

    public void smoothMoveCamera(double dx, double dy) {
        scene.moveCamera(-dx / scene.getCameraZoom(), -dy / scene.getCameraZoom());

    }

    private void startAnimTimer() {
        if (animTimer != null && animTimer.isRunning()) animTimer.stop();
        animTimer = new Timer(16, e -> {
            long now = System.currentTimeMillis();
            boolean keepGoing = false;
            var iter = appearTimes.entrySet().iterator();
            while (iter.hasNext()) {
                var entry = iter.next();
                if (now - entry.getValue() >= APPEAR_MS) iter.remove();
                else keepGoing = true;
            }
            if (fadingOut != null) {
                if (now - fadeStartTime < FADE_MS) keepGoing = true;
                else fadingOut = null;
            }
            repaint();
            if (!keepGoing) animTimer.stop();
        });
        animTimer.start();
    }

    @Override
    public void sceneChanged() { repaint(); }

    @Override
    public void selectionChanged(Entity selected) { repaint(); }

    @Override
    protected void paintComponent(Graphics g) {
        super.paintComponent(g);
        Graphics2D g2 = (Graphics2D) g.create();
        g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
        g2.setRenderingHint(RenderingHints.KEY_TEXT_ANTIALIASING, RenderingHints.VALUE_TEXT_ANTIALIAS_LCD_HRGB);
        g2.setRenderingHint(RenderingHints.KEY_RENDERING, RenderingHints.VALUE_RENDER_QUALITY);

        int w = getWidth(), h = getHeight();
        double zoom = getEffectiveZoom();
        double camX = getEffectiveCamX();
        double camY = getEffectiveCamY();
        updateCameraAnimation();
        long now = System.currentTimeMillis();

        drawGrid(g2, w, h, zoom, camX, camY);
        drawOrigin(g2, w, h, zoom, camX, camY);

        for (Entity entity : scene.getEntities()) {
            float alpha = 1f, scale = 1f;
            Long appeared = appearTimes.get(entity);
            if (appeared != null) {
                float t = Math.min(1f, (float)(now - appeared) / APPEAR_MS);
                float eased = springOut(t);
                alpha = Math.min(1f, eased * 1.1f);
                scale = 0.7f + 0.3f * eased;
            }
            paintEntity(g2, entity, zoom, camX, camY, w, h, alpha, scale,
                entity == hoveredEntity && entity != scene.getSelectedEntity());
        }

        if (fadingOut != null) {
            float t = Math.min(1f, (float)(now - fadeStartTime) / FADE_MS);
            float eased = t * t;
            paintEntity(g2, fadingOut, zoom, camX, camY, w, h, 1f - eased, 1f - 0.15f * eased, false);
        }

        Entity sel = scene.getSelectedEntity();
        if (sel != null) drawSelectionHighlight(g2, sel, zoom, camX, camY, w, h);
        drawViewportHUD(g2, w, h, zoom, camX, camY);
        g2.dispose();
    }

    private float springOut(float t) {
        float c = 4f, damp = 0.65f;
        return (float)(1.0 - Math.exp(-c * t * damp) * Math.cos(c * t * 0.8));
    }

    private void paintEntity(Graphics2D g2, Entity entity, double zoom, double camX, double camY,
                             int pw, int ph, float alpha, float scale, boolean hovered) {
        float sx = (float)(pw / 2.0 + (entity.getX() + camX) * zoom);
        float sy = (float)(ph / 2.0 + (entity.getY() + camY) * zoom);
        float dw = (float)(entity.getWidth() * zoom * scale);
        float dh = (float)(entity.getHeight() * zoom * scale);
        g2.setComposite(AlphaComposite.getInstance(AlphaComposite.SRC_OVER, alpha));

        if (hovered) {
            g2.setColor(Colors.HOVER_OVERLAY);
            g2.fillRoundRect((int)(sx - dw/2 - 8), (int)(sy - dh/2 - 8), (int)(dw + 16), (int)(dh + 16), 6, 6);
        }

        if (entity.isCircle()) {
            g2.setColor(entity.getColor());
            g2.fillOval((int)(sx - dw/2), (int)(sy - dh/2), (int)dw, (int)dh);
            if (entity.isPlayer()) {
                g2.setColor(Colors.bgDeepest());
                g2.fillOval((int)(sx - dw/4), (int)(sy - dh/4), (int)(dw/4), (int)(dh/4));
            }
        } else {
            g2.setColor(entity.getColor());
            g2.fillRoundRect((int)(sx - dw/2), (int)(sy - dh/2), (int)dw, (int)dh, 4, 4);
        }

        if (zoom > 0.3) {
            g2.setComposite(AlphaComposite.getInstance(AlphaComposite.SRC_OVER, alpha * 0.7f));
            g2.setColor(Colors.textSecondary());
            float fs = Math.max(9, (int)(11 * Math.min(1, zoom)));
            g2.setFont(UIManager.getFont("defaultFont").deriveFont(Font.PLAIN, fs));
            FontMetrics fm = g2.getFontMetrics();
            int tw = fm.stringWidth(entity.getName());
            g2.drawString(entity.getName(), (int)(sx - tw/2.0), (int)(sy + dh/2.0 + fm.getAscent() + 3));
        }
    }

    private void drawGrid(Graphics2D g2, int w, int h, double zoom, double camX, double camY) {
        g2.setColor(Colors.gridLine());
        float gs = 32, sg = (float)(gs * zoom);
        if (sg < 4) sg = 4;
        double ox = (w / 2.0 + camX * zoom) % sg;
        double oy = (h / 2.0 + camY * zoom) % sg;
        for (double x = ox; x < w; x += sg) g2.drawLine((int)x, 0, (int)x, h);
        for (double y = oy; y < h; y += sg) g2.drawLine(0, (int)y, w, (int)y);
    }

    private void drawOrigin(Graphics2D g2, int w, int h, double zoom, double camX, double camY) {
        int ox = (int)(w/2.0 + camX * zoom);
        int oy = (int)(h/2.0 + camY * zoom);
        g2.setColor(Colors.originLine());
        g2.drawLine(ox - 20, oy, ox + 20, oy);
        g2.drawLine(ox, oy - 20, ox, oy + 20);
        g2.setColor(Colors.BLUE);
        g2.fillOval(ox - 2, oy - 2, 4, 4);
    }

    private void drawSelectionHighlight(Graphics2D g2, Entity sel, double zoom, double camX, double camY, int pw, int ph) {
        float sx = (float)(pw / 2.0 + (sel.getX() + camX) * zoom);
        float sy = (float)(ph / 2.0 + (sel.getY() + camY) * zoom);
        float dw = (float)(sel.getWidth() * zoom);
        float dh = (float)(sel.getHeight() * zoom);
        g2.setColor(Colors.GLOW_OUTER);
        g2.setStroke(new BasicStroke(2.5f));
        g2.drawRoundRect((int)(sx - dw/2 - 6), (int)(sy - dh/2 - 6), (int)(dw + 12), (int)(dh + 12), 8, 8);
        g2.setColor(Colors.GLOW_INNER);
        g2.setStroke(new BasicStroke(1.5f));
        g2.drawRoundRect((int)(sx - dw/2 - 3), (int)(sy - dh/2 - 3), (int)(dw + 6), (int)(dh + 6), 6, 6);
    }

    private void drawViewportHUD(Graphics2D g2, int w, int h, double zoom, double camX, double camY) {
        g2.setFont(UIManager.getFont("defaultFont").deriveFont(Font.PLAIN, 11f));
        g2.setColor(Colors.textMuted());
        g2.drawString(String.format("%.0f%%%s", zoom * 100, snapEnabled ? "" : " NS"), w - 75, h - 14);
        g2.setColor(Colors.borderLine());
        g2.fillRect(w - 55, h - 28, 40, 3);
        g2.setColor(Colors.BLUE);
        int fill = (int)(40 * Math.min(1, Math.max(0.05, zoom) / 20.0));
        g2.fillRect(w - 55, h - 28, fill, 3);
    }

    private class ViewportMouseHandler extends MouseAdapter {
        @Override
        public void mousePressed(MouseEvent e) {
            requestFocusInWindow();
            if (e.getClickCount() == 2 && dragEntity == null) {
                scene.resetCamera();
                return;
            }
            double wx = (e.getX() - getWidth() / 2.0) / scene.getCameraZoom() - scene.getCameraX();
            double wy = (e.getY() - getHeight() / 2.0) / scene.getCameraZoom() - scene.getCameraY();
            Entity hit = null;
            for (Entity en : scene.getEntities()) {
                if (en.containsPoint(wx, wy)) { hit = en; break; }
            }
            if (hit != null && toolMode == ToolMode.SELECT) {
                scene.setSelectedEntity(hit);
            }
            if (hit != null && (toolMode == ToolMode.MOVE || toolMode == ToolMode.SELECT)) {
                dragEntity = hit; isDragging = true;
                dragOffsetX = e.getX(); dragOffsetY = e.getY();
            } else if (hit == null) {
                if (toolMode == ToolMode.SELECT) scene.clearSelection();
                isDragging = true; dragStart = e.getPoint();
            }
            repaint();
        }
        @Override
        public void mouseDragged(MouseEvent e) {
            if (!isDragging) return;
            if (dragEntity != null) {
                double rawDx = (e.getX() - dragOffsetX) / scene.getCameraZoom();
                double rawDy = (e.getY() - dragOffsetY) / scene.getCameraZoom();
                if (snapEnabled) {
                    double newX = Math.round((dragEntity.getX() + rawDx) / 32) * 32;
                    double newY = Math.round((dragEntity.getY() + rawDy) / 32) * 32;
                    dragEntity.setPosition(newX, newY);
                } else {
                    dragEntity.setPosition(dragEntity.getX() + rawDx, dragEntity.getY() + rawDy);
                }
                dragOffsetX = e.getX(); dragOffsetY = e.getY();
            } else if (dragStart != null) {
                smoothMoveCamera(e.getX() - dragStart.x, e.getY() - dragStart.y);
                dragStart = e.getPoint();
            }
            repaint();
        }
        @Override
        public void mouseReleased(MouseEvent e) { isDragging = false; dragEntity = null; dragStart = null; }
        @Override
        public void mouseMoved(MouseEvent e) {
            double wx = (e.getX() - getWidth() / 2.0) / scene.getCameraZoom() - scene.getCameraX();
            double wy = (e.getY() - getHeight() / 2.0) / scene.getCameraZoom() - scene.getCameraY();
            Entity hit = null;
            for (Entity en : scene.getEntities()) {
                if (en.containsPoint(wx, wy)) { hit = en; break; }
            }
            if (hit != hoveredEntity) { hoveredEntity = hit; repaint(); }
            setCursor(hit != null
                ? Cursor.getPredefinedCursor(Cursor.HAND_CURSOR)
                : Cursor.getPredefinedCursor(Cursor.CROSSHAIR_CURSOR));
        }
        @Override
        public void mouseExited(MouseEvent e) { hoveredEntity = null; repaint(); }
        @Override
        public void mouseWheelMoved(MouseWheelEvent e) {
            double f = e.getWheelRotation() > 0 ? 1.0 / 1.12 : 1.12;
            scene.zoomCamera(f);
        }
    }
}
