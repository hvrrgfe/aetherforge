package com.aetherforge.ui;

import com.aetherforge.model.*;
import com.aetherforge.util.*;
import javax.swing.*;
import java.awt.*;
import java.awt.event.*;
import java.awt.geom.*;
import java.awt.image.BufferedImage;
import java.io.IOException;
import java.nio.file.*;

public class GameViewer extends JFrame implements SceneListener {

    private Scene scene;
    private ProjectManager projectManager;
    private GameViewport viewport;
    private JLabel infoLabel;
    private JLabel fpsLabel;
    private Timer renderTimer;
    private int fps;
    private int frameCount;
    private long lastFpsTime;
    private boolean running = true;

    public GameViewer() {
        this.scene = new Scene();
        this.projectManager = new ProjectManager();
        initUI();
        startRenderLoop();
    }

    private void initUI() {
        setTitle("AetherForge Game Viewer");
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        setSize(1200, 800);
        setMinimumSize(new Dimension(800, 600));
        setLocationRelativeTo(null);
        setIconImage(createIcon());

        JMenuBar mb = new JMenuBar();
        mb.setBackground(new Color(0x1a, 0x1a, 0x2a));
        mb.setBorder(BorderFactory.createLineBorder(new Color(0x2a, 0x2a, 0x4a)));
        JMenu fileMenu = new JMenu("File");
        fileMenu.setForeground(Color.LIGHT_GRAY);

        JMenuItem openItem = new JMenuItem("Open Project...");
        openItem.setAccelerator(KeyStroke.getKeyStroke(KeyEvent.VK_O, InputEvent.CTRL_DOWN_MASK));
        openItem.addActionListener(e -> openProject());
        fileMenu.add(openItem);

        JMenuItem closeItem = new JMenuItem("Close Project");
        closeItem.addActionListener(e -> closeProject());
        fileMenu.add(closeItem);

        fileMenu.addSeparator();
        JMenuItem exitItem = new JMenuItem("Exit");
        exitItem.setAccelerator(KeyStroke.getKeyStroke(KeyEvent.VK_Q, InputEvent.CTRL_DOWN_MASK));
        exitItem.addActionListener(e -> System.exit(0));
        fileMenu.add(exitItem);
        mb.add(fileMenu);

        JMenu viewMenu = new JMenu("View");
        viewMenu.setForeground(Color.LIGHT_GRAY);
        JMenuItem resetCam = new JMenuItem("Reset Camera");
        resetCam.setAccelerator(KeyStroke.getKeyStroke(KeyEvent.VK_R, InputEvent.CTRL_DOWN_MASK));
        resetCam.addActionListener(e -> resetCamera());
        viewMenu.add(resetCam);
        JCheckBoxMenuItem gridItem = new JCheckBoxMenuItem("Show Grid", true);
        gridItem.addActionListener(e -> { if (viewport != null) viewport.showGrid = gridItem.isSelected(); });
        viewMenu.add(gridItem);
        mb.add(viewMenu);
        setJMenuBar(mb);

        viewport = new GameViewport(scene);
        add(viewport, BorderLayout.CENTER);

        JPanel infoBar = new JPanel(new BorderLayout());
        infoBar.setBackground(new Color(0x12, 0x12, 0x22));
        infoBar.setBorder(BorderFactory.createEmptyBorder(4, 12, 4, 12));
        infoLabel = new JLabel("No project open");
        infoLabel.setForeground(new Color(0x88, 0x88, 0x88));
        infoLabel.setFont(new Font("Consolas", Font.PLAIN, 12));
        infoBar.add(infoLabel, BorderLayout.WEST);
        fpsLabel = new JLabel("FPS: --");
        fpsLabel.setForeground(new Color(0x44, 0xff, 0x88));
        fpsLabel.setFont(new Font("Consolas", Font.PLAIN, 12));
        infoBar.add(fpsLabel, BorderLayout.EAST);
        add(infoBar, BorderLayout.SOUTH);
    }

    private Image createIcon() {
        BufferedImage img = new BufferedImage(32, 32, BufferedImage.TYPE_INT_ARGB);
        Graphics2D g = img.createGraphics();
        g.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
        g.setColor(new Color(0x44, 0x88, 0xff));
        g.fillOval(4, 4, 24, 24);
        g.setColor(new Color(0x0a, 0x0a, 0x12));
        g.fillOval(10, 10, 12, 12);
        g.dispose();
        return img;
    }

    private void openProject() {
        JFileChooser fc = new JFileChooser();
        fc.setFileSelectionMode(JFileChooser.FILES_ONLY);
        fc.setFileFilter(new javax.swing.filechooser.FileNameExtensionFilter(
            "AetherForge Project (project.json)", "json"));
        fc.setDialogTitle("Select project.json");
        if (fc.showOpenDialog(this) != JFileChooser.APPROVE_OPTION) return;
        loadProject(fc.getSelectedFile().getAbsolutePath());
    }

    private void loadProject(String projectFilePath) {
        try {
            Project project = projectManager.loadProject(projectFilePath);
            String sceneName = project.getRecentScenes().isEmpty()
                ? "main.scene" : project.getRecentScenes().get(0);
            Path scenePath = projectManager.getScenePath(sceneName);
            if (scenePath != null && Files.exists(scenePath)) {
                String json = Files.readString(scenePath);
                Scene loaded = Scene.fromJson(json);
                scene.getEntities().clear();
                for (Entity e : loaded.getEntities()) scene.addEntity(e);
                scene.resetCamera();
            }
            scene.addListener(this);
            setTitle("AetherForge Game Viewer - " + project.getName());
            updateInfo();
        } catch (IOException ex) {
            JOptionPane.showMessageDialog(this, "Failed to load: " + ex.getMessage(),
                "Error", JOptionPane.ERROR_MESSAGE);
        }
    }

    private void closeProject() {
        projectManager.closeProject();
        scene.getEntities().clear();
        scene.resetCamera();
        setTitle("AetherForge Game Viewer");
        infoLabel.setText("No project open");
    }

    private void resetCamera() { scene.resetCamera(); viewport.repaint(); }

    private void updateInfo() {
        Project p = projectManager.getCurrentProject();
        if (p != null) {
            infoLabel.setText(String.format("  %s  |  %d entities  |  Camera: %.0f, %.0f @ %.0f%%",
                p.getName(), scene.getEntities().size(),
                scene.getCameraX(), scene.getCameraY(), scene.getCameraZoom() * 100));
        }
    }

    private void startRenderLoop() {
        renderTimer = new Timer(16, e -> {
            if (!running) return;
            viewport.repaint();
            frameCount++;
            long now = System.currentTimeMillis();
            if (now - lastFpsTime >= 1000) {
                fps = frameCount;
                frameCount = 0;
                lastFpsTime = now;
                fpsLabel.setText(String.format("FPS: %d", fps));
                updateInfo();
            }
        });
        renderTimer.start();
    }

    @Override public void sceneChanged() { updateInfo(); viewport.repaint(); }
    @Override public void selectionChanged(Entity entity) {}
    @Override public void logMessage(String msg) {}

    public static void main(String[] args) {
        try { UIManager.setLookAndFeel(UIManager.getCrossPlatformLookAndFeelClassName()); }
        catch (Exception ignored) {}
        SwingUtilities.invokeLater(() -> {
            GameViewer viewer = new GameViewer();
            viewer.setVisible(true);
            if (args.length > 0 && args[0] != null && !args[0].isEmpty()) {
                String path = args[0];
                java.io.File f = new java.io.File(path);
                if (f.isDirectory()) path = path + "/project.json";
                viewer.loadProject(path);
            }
        });
    }
}


class GameViewport extends JPanel {
    final Scene scene;
    boolean showGrid = true;
    private Point lastMousePos;

    GameViewport(Scene scene) {
        this.scene = scene;
        setBackground(new Color(0x0a, 0x0a, 0x12));
        setFocusable(true);
        addMouseWheelListener(e -> {
            double factor = e.getPreciseWheelRotation() < 0 ? 1.1 : 0.9;
            scene.zoomCamera(factor);
            repaint();
        });
        MouseAdapter panHandler = new MouseAdapter() {
            @Override public void mousePressed(MouseEvent e) {
                lastMousePos = e.getPoint();
                setCursor(Cursor.getPredefinedCursor(Cursor.MOVE_CURSOR));
            }
            @Override public void mouseDragged(MouseEvent e) {
                if (lastMousePos != null) {
                    double dx = (e.getX() - lastMousePos.x) / scene.getCameraZoom();
                    double dy = (e.getY() - lastMousePos.y) / scene.getCameraZoom();
                    scene.moveCamera(-dx, -dy);
                    lastMousePos = e.getPoint();
                    repaint();
                }
            }
            @Override public void mouseReleased(MouseEvent e) {
                lastMousePos = null;
                setCursor(Cursor.getDefaultCursor());
            }
        };
        addMouseListener(panHandler);
        addMouseMotionListener(panHandler);
    }

    @Override
    protected void paintComponent(Graphics g) {
        super.paintComponent(g);
        Graphics2D g2 = (Graphics2D) g.create();
        g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
        int w = getWidth(), h = getHeight();
        double zoom = scene.getCameraZoom();
        double camX = scene.getCameraX();
        double camY = scene.getCameraY();

        // Grid
        if (showGrid) {
            g2.setColor(new Color(0x15, 0x15, 0x25));
            double gs = 40 * zoom;
            double ox = (w / 2.0) + camX * zoom;
            double oy = (h / 2.0) + camY * zoom;
            int startX = (int)((-ox) / gs) - 1;
            int startY = (int)((-oy) / gs) - 1;
            int endX = (int)((w - ox) / gs) + 1;
            int endY = (int)((h - oy) / gs) + 1;
            for (int i = startX; i <= endX; i++) g2.drawLine((int)(ox + i * gs), 0, (int)(ox + i * gs), h);
            for (int i = startY; i <= endY; i++) g2.drawLine(0, (int)(oy + i * gs), w, (int)(oy + i * gs));
        }

        // Draw entities
        for (Entity entity : scene.getEntities()) {
            drawEntity(g2, entity, w, h, zoom, camX, camY);
        }

        // Center crosshair
        g2.setColor(new Color(0x44, 0x88, 0xff, 60));
        g2.fillOval(w/2 - 3, h/2 - 3, 6, 6);
        g2.dispose();
    }

    private void drawEntity(Graphics2D g2, Entity entity, int w, int h,
                            double zoom, double camX, double camY) {
        double sx = w / 2.0 + (entity.getX() + camX) * zoom;
        double sy = h / 2.0 + (entity.getY() + camY) * zoom;
        double sw = entity.getWidth() * zoom;
        double sh = entity.getHeight() * zoom;

        // TEXT render type (component-based)
        com.aetherforge.model.component.RenderComponent rc =
            entity.get(com.aetherforge.model.component.RenderComponent.class);
        if (rc != null && rc.getType() == com.aetherforge.model.component.RenderComponent.RenderType.TEXT) {
            g2.setColor(rc.getTextColor());
            float fontSize = Math.max(8, (float)(rc.getFontSize() * zoom));
            g2.setFont(new Font(rc.getFontName(), Font.PLAIN, (int)fontSize));
            String text = rc.getText().isEmpty() ? entity.getName() : rc.getText();
            FontMetrics fm = g2.getFontMetrics();
            g2.drawString(text, (int)(sx - fm.stringWidth(text) / 2.0), (int)(sy + fm.getAscent() / 2.0));
            return;
        }

        // Rotation
        AffineTransform old = g2.getTransform();
        com.aetherforge.model.component.TransformComponent tc =
            entity.get(com.aetherforge.model.component.TransformComponent.class);
        if (tc != null && tc.getRotation() != 0) {
            g2.rotate(Math.toRadians(tc.getRotation()), sx, sy);
        }

        int x = (int)(sx - sw / 2);
        int y = (int)(sy - sh / 2);

        g2.setColor(entity.getColor());
        if (entity.isCircle()) {
            g2.fillOval(x, y, (int)sw, (int)sh);
        } else {
            g2.fillRect(x, y, (int)sw, (int)sh);
        }

        g2.setColor(entity.getColor().darker());
        g2.setStroke(new BasicStroke(1));
        if (entity.isCircle()) {
            g2.drawOval(x, y, (int)sw, (int)sh);
        } else {
            g2.drawRect(x, y, (int)sw, (int)sh);
        }

        if (tc != null && tc.getRotation() != 0) g2.setTransform(old);

        if (zoom > 0.3) {
            g2.setColor(Color.LIGHT_GRAY);
            g2.setFont(new Font("Microsoft YaHei UI", Font.PLAIN, Math.max(9, (int)(11 * zoom))));
            FontMetrics fm = g2.getFontMetrics();
            String label = entity.getName();
            g2.drawString(label, (int)(sx - fm.stringWidth(label) / 2), (int)(sy + sh / 2 + fm.getHeight()));
        }
    }
}