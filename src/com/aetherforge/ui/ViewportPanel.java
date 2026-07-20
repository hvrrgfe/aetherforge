package com.aetherforge.ui;

import com.aetherforge.model.Entity;
import com.aetherforge.util.Colors;
import javax.swing.*;
import javax.swing.UIManager;
import java.awt.*;
import java.awt.event.*;
import java.util.List;
import java.util.Map;
import java.util.WeakHashMap;

/**
 * 2D viewport with entity entrance/exit animation (scale+fade).
 */
public class ViewportPanel extends JPanel {

    private final MainWindow window;
    private Point dragStart;
    private boolean isDragging;
    private int dragOffsetX, dragOffsetY;
    private Entity dragEntity;

    // animation state
    private final Map<Entity, Long> appearTimes = new WeakHashMap<>();
    private Entity fadingOut;
    private long fadeStartTime;
    private static final long APPEAR_MS = 200;
    private static final long FADE_MS   = 150;
    private Timer animTimer;

    public ViewportPanel(MainWindow window) {
        this.window = window;
        setBackground(Colors.BACKGROUND_DEEPEST);
        setFocusable(true);
        setCursor(Cursor.getPredefinedCursor(Cursor.CROSSHAIR_CURSOR));

        ViewportMouseHandler mouseHandler = new ViewportMouseHandler();
        addMouseListener(mouseHandler);
        addMouseMotionListener(mouseHandler);
        addMouseWheelListener(mouseHandler);

        addKeyListener(new KeyAdapter() {
            @Override
            public void keyPressed(KeyEvent e) {
                if (e.getKeyCode() == KeyEvent.VK_DELETE && window.getSelectedEntity() != null) {
                    window.deleteSelectedEntity();
                }
            }
        });
    }

    /** Called when a new entity is added to the scene. Starts entrance animation. */
    public void animateEntityIn(Entity entity) {
        appearTimes.put(entity, System.currentTimeMillis());
        startAnimTimer();
    }

    /** Called to start fade-out before actual removal. Returns true if animating. */
    public boolean animateEntityOut(Entity entity) {
        fadingOut = entity;
        fadeStartTime = System.currentTimeMillis();
        startAnimTimer();
        return true;
    }

    private void startAnimTimer() {
        if (animTimer != null && animTimer.isRunning()) return;
        animTimer = new Timer(16, e -> {
            long now = System.currentTimeMillis();
            boolean keepGoing = false;

            // check appear animations
            for (Map.Entry<Entity, Long> entry : appearTimes.entrySet()) {
                if (now - entry.getValue() < APPEAR_MS) keepGoing = true;
            }
            // cleanup finished appears
            appearTimes.entrySet().removeIf(e2 -> now - e2.getValue() >= APPEAR_MS);

            // check fade-out
            if (fadingOut != null) {
                if (now - fadeStartTime < FADE_MS) {
                    keepGoing = true;
                } else {
                    fadingOut = null;
                }
            }

            repaint();
            if (!keepGoing) {
                ((Timer)e.getSource()).stop();
            }
        });
        animTimer.start();
    }

    @Override
    protected void paintComponent(Graphics g) {
        super.paintComponent(g);
        Graphics2D g2 = (Graphics2D) g.create();
        g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
        g2.setRenderingHint(RenderingHints.KEY_TEXT_ANTIALIASING, RenderingHints.VALUE_TEXT_ANTIALIAS_LCD_HRGB);
        g2.setRenderingHint(RenderingHints.KEY_RENDERING, RenderingHints.VALUE_RENDER_QUALITY);

        int w = getWidth(), h = getHeight();
        double zoom = window.getCameraZoom();
        double camX = window.getCameraX();
        double camY = window.getCameraY();
        long now = System.currentTimeMillis();

        drawGrid(g2, w, h, zoom, camX, camY);
        drawOrigin(g2, w, h, zoom, camX, camY);

        List<Entity> entities = window.getEntities();
        for (Entity entity : entities) {
            float alpha = 1f;
            float scale = 1f;

            // entrance animation
            Long appeared = appearTimes.get(entity);
            if (appeared != null) {
                float t = Math.min(1f, (float)(now - appeared) / APPEAR_MS);
                // ease-out quad: t = t * (2 - t)
                float eased = t * (2f - t);
                alpha = eased;
                scale = 0.8f + 0.2f * eased;
            }

            paintEntity(g2, entity, zoom, camX, camY, w, h, alpha, scale);
        }

        // draw fading-out entity (still in viewport but removed from list)
        if (fadingOut != null) {
            float t = Math.min(1f, (float)(now - fadeStartTime) / FADE_MS);
            float alpha = 1f - t;
            float scale = 1f - 0.2f * t;
            paintEntity(g2, fadingOut, zoom, camX, camY, w, h, alpha, scale);
        }

        Entity selected = window.getSelectedEntity();
        if (selected != null) {
            drawSelectionHighlight(g2, selected, zoom, camX, camY, w, h);
        }

        drawViewportHUD(g2, w, h, zoom, camX, camY);
        g2.dispose();
    }

    private void paintEntity(Graphics2D g2, Entity entity, double zoom, double camX, double camY,
            int pw, int ph, float alpha, float scale) {
        float sx = (float)(pw/2.0 + (entity.getX()+camX)*zoom);
        float sy = (float)(ph/2.0 + (entity.getY()+camY)*zoom);
        float dw = Math.max(4, (float)(entity.getWidth()*zoom*scale));
        float dh = Math.max(4, (float)(entity.getHeight()*zoom*scale));

        g2.setComposite(AlphaComposite.getInstance(AlphaComposite.SRC_OVER,
            alpha * (entity.isPlayer() ? 1f : 0.85f)));
        g2.setColor(entity.getColor());

        float ox = sx - dw/2;
        float oy = sy - dh/2;
        if (entity.isCircle()) {
            g2.fillOval((int)ox, (int)oy, (int)dw, (int)dh);
        } else {
            g2.fillRect((int)ox, (int)oy, (int)dw, (int)dh);
        }

        // label
        if (zoom > 0.3) {
            g2.setComposite(AlphaComposite.getInstance(AlphaComposite.SRC_OVER, alpha));
            g2.setColor(Colors.TEXT_SECONDARY);
            float fs = Math.max(9, (int)(11*Math.min(1,zoom)));
            g2.setFont(new Font("Segoe UI", Font.PLAIN, (int)fs));
            FontMetrics fm = g2.getFontMetrics();
            int tw = fm.stringWidth(entity.getName());
            g2.drawString(entity.getName(), (int)(sx - tw/2.0),
                (int)(sy + dh/2.0 + fm.getAscent() + 3));
        }
    }

    private void drawGrid(Graphics2D g2, int w, int h, double zoom, double camX, double camY) {
        g2.setColor(Colors.GRID_LINE);
        float gs = 32, sg = (float)(gs*zoom);
        if (sg < 4) sg = 4;
        double ox = (w/2.0 + camX*zoom) % sg;
        double oy = (h/2.0 + camY*zoom) % sg;
        for (double x = ox; x < w; x += sg) g2.drawLine((int)x,0,(int)x,h);
        for (double y = oy; y < h; y += sg) g2.drawLine(0,(int)y,w,(int)y);
    }

    private void drawOrigin(Graphics2D g2, int w, int h, double zoom, double camX, double camY) {
        int ox = (int)(w/2.0 + camX*zoom);
        int oy = (int)(h/2.0 + camY*zoom);
        g2.setColor(Colors.ORIGIN_LINE);
        g2.drawLine(ox-20, oy, ox+20, oy);
        g2.drawLine(ox, oy-20, ox, oy+20);
        g2.setColor(Colors.BLUE);
        g2.fillOval(ox-2, oy-2, 4, 4);
    }

    private void drawSelectionHighlight(Graphics2D g2, Entity sel, double zoom, double camX, double camY, int pw, int ph) {
        float sx = (float)(pw/2.0 + (sel.getX()+camX)*zoom);
        float sy = (float)(ph/2.0 + (sel.getY()+camY)*zoom);
        float dw = (float)(sel.getWidth()*zoom);
        float dh = (float)(sel.getHeight()*zoom);
        g2.setColor(new Color(0x40,0x80,0xf0,60));
        g2.setStroke(new BasicStroke(1.5f));
        g2.drawRect((int)(sx-dw/2-4),(int)(sy-dh/2-4),(int)(dw+8),(int)(dh+8));
    }

    private void drawViewportHUD(Graphics2D g2, int w, int h, double zoom, double camX, double camY) {
        g2.setFont(UIManager.getFont("defaultFont").deriveFont(java.awt.Font.PLAIN, 11f));
        g2.setColor(Colors.TEXT_MUTED);
        g2.drawString(String.format("%.0f%%", zoom*100), w-55, h-14);
        g2.setColor(Colors.BORDER_LINE);
        g2.fillRect(w-55, h-28, 40, 3);
        g2.setColor(Colors.BLUE);
        int fill = (int)(40 * Math.min(1, Math.max(0.05, zoom)/20.0));
        g2.fillRect(w-55, h-28, fill, 3);
    }

    // mouse handling
    private class ViewportMouseHandler extends MouseAdapter {
        @Override public void mousePressed(MouseEvent e) {
            requestFocusInWindow();
            double wx = (e.getX()-getWidth()/2.0)/window.getCameraZoom() - window.getCameraX();
            double wy = (e.getY()-getHeight()/2.0)/window.getCameraZoom() - window.getCameraY();
            Entity hit = null;
            for (Entity en : window.getEntities()) {
                if (en.containsPoint(wx, wy)) { hit = en; break; }
            }
            if (hit != null) {
                window.setSelectedEntity(hit);
                dragEntity = hit; isDragging = true;
                dragOffsetX = e.getX(); dragOffsetY = e.getY();
            } else {
                window.setSelectedEntity(null);
                isDragging = true; dragStart = e.getPoint();
            }
            window.refreshInspector(); window.repaintSceneTree(); repaint();
        }
        @Override public void mouseDragged(MouseEvent e) {
            if (!isDragging) return;
            if (dragEntity != null) {
                double dx = (e.getX()-dragOffsetX)/window.getCameraZoom();
                double dy = (e.getY()-dragOffsetY)/window.getCameraZoom();
                dragEntity.setPosition(dragEntity.getX()+dx, dragEntity.getY()+dy);
                dragOffsetX = e.getX(); dragOffsetY = e.getY();
                window.refreshInspector();
            } else if (dragStart != null) {
                window.moveCamera(-(e.getX()-dragStart.x)/window.getCameraZoom(),
                    -(e.getY()-dragStart.y)/window.getCameraZoom());
                dragStart = e.getPoint();
            }
            window.updateStatusBar(); repaint();
        }
        @Override public void mouseReleased(MouseEvent e) { isDragging=false; dragEntity=null; dragStart=null; }
        @Override public void mouseWheelMoved(MouseWheelEvent e) {
            double f = e.getWheelRotation()>0 ? 1.0/1.12 : 1.12;
            window.zoomCamera(f); repaint();
        }
    }

    // coordinate conversion
    public double screenToWorldX(int sx) { return (sx-getWidth()/2.0)/window.getCameraZoom() - window.getCameraX(); }
    public double screenToWorldY(int sy) { return (sy-getHeight()/2.0)/window.getCameraZoom() - window.getCameraY(); }
}