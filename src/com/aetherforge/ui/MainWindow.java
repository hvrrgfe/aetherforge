package com.aetherforge.ui;

import com.aetherforge.model.Entity;
import com.aetherforge.model.Scene;
import com.aetherforge.model.SceneListener;
import com.aetherforge.util.Colors;
import com.aetherforge.util.I18n;
import com.aetherforge.util.Theme;
import javax.swing.*;
import java.awt.*;
import java.awt.event.*;
import java.awt.image.BufferedImage;
import java.time.LocalTime;
import java.time.format.DateTimeFormatter;
import java.io.*;
import javax.swing.filechooser.FileNameExtensionFilter;

/**
 * AetherForge Studio 主窗口 — 精简协调器
 * 布局委托给 LayoutBuilder，场景委托给 SceneController
 * 检查器委托给 InspectorController，视口委托给 ViewportPanel
 */
public class MainWindow extends JFrame implements SceneListener {

    private Scene scene = null;
    private ViewportPanel viewport = null;
    private SceneController sceneController = null;
    private InspectorController inspectorController = null;
    private JLabel statusLabel;
    private JTextArea consoleArea = null;
    private JButton langBtn = null, themeBtn = null;
    private boolean isMaximized;
    private int normalX, normalY, normalWidth, normalHeight;

    private static final DateTimeFormatter TIME_FMT = DateTimeFormatter.ofPattern("HH:mm:ss");

    public MainWindow() {
        try {
            this.scene = new Scene();
            loadDemoScene();

            this.viewport = new ViewportPanel(scene);
            this.sceneController = new SceneController(scene);
            this.inspectorController = new InspectorController(scene);

            scene.addListener(this);
            setupWindow();
            assembleUI();
            setupKeyboard();
            setupLanguageAndTheme();
        } catch (Exception e) {
            e.printStackTrace();
            JOptionPane.showMessageDialog(null, "Failed to initialize: " + e.getMessage(),
                "Fatal Error", JOptionPane.ERROR_MESSAGE);
            System.exit(1);
        }
    }

    private void setupWindow() {
        setTitle("AetherForge Studio");
        setUndecorated(true);
        setBackground(Colors.bgDeepest());
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        setSize(1400, 900);
        setMinimumSize(new Dimension(1000, 600));
        setLocationRelativeTo(null);
        setIconImage(createIcon());
    }

    private Image createIcon() {
        BufferedImage img = new BufferedImage(64, 64, BufferedImage.TYPE_INT_ARGB);
        Graphics2D g = img.createGraphics();
        g.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
        g.setColor(Colors.BLUE);
        g.fillPolygon(new int[]{32, 56, 32, 8}, new int[]{4, 32, 60, 32}, 4);
        g.setColor(Colors.bgDeepest());
        g.fillPolygon(new int[]{32, 48, 32, 16}, new int[]{14, 32, 50, 32}, 4);
        g.dispose();
        return img;
    }

    private void assembleUI() {
        // 标题栏
        WindowDragHandler drag = new WindowDragHandler();
        JPanel tb = LayoutBuilder.createTitleBar(drag,
            () -> setState(JFrame.ICONIFIED),
            () -> toggleMaximized(),
            () -> System.exit(0));

        // 汉堡菜单按钮（放在标题左侧）
        JButton menuBtn = new JButton("\u2630");
        menuBtn.setFont(UIManager.getFont("defaultFont").deriveFont(Font.PLAIN, 14f));
        menuBtn.setFocusPainted(false); menuBtn.setBorderPainted(false);
        menuBtn.setContentAreaFilled(false);
        menuBtn.setForeground(Colors.textSecondary());
        menuBtn.setPreferredSize(new Dimension(36, LayoutBuilder.DP40));
        menuBtn.setCursor(Cursor.getPredefinedCursor(Cursor.HAND_CURSOR));
        JPopupMenu fileMenu = new JPopupMenu();
        fileMenu.setBackground(Colors.bgRaised());
        fileMenu.setBorder(BorderFactory.createLineBorder(Colors.borderLine()));

        JMenuItem saveItem = new JMenuItem(I18n.get("app.title") + " - Save (Ctrl+S)");
        saveItem.setForeground(Colors.textPrimary());
        saveItem.setBackground(Colors.bgRaised());
        saveItem.addActionListener(e -> saveScene());
        fileMenu.add(saveItem);

        JMenuItem loadItem = new JMenuItem(I18n.get("app.title") + " - Open (Ctrl+O)");
        loadItem.setForeground(Colors.textPrimary());
        loadItem.setBackground(Colors.bgRaised());
        loadItem.addActionListener(e -> loadScene());
        fileMenu.add(loadItem);
        fileMenu.addSeparator();
        JMenuItem newItem = new JMenuItem(I18n.get("tree.new") + " Scene (Ctrl+Shift+N)");
        newItem.setForeground(Colors.textPrimary());
        newItem.setBackground(Colors.bgRaised());
        newItem.addActionListener(e -> newScene());
        fileMenu.add(newItem);

        menuBtn.addActionListener(e -> fileMenu.show(menuBtn, 0, menuBtn.getHeight()));
        tb.add(menuBtn, BorderLayout.LINE_START);

        // 左：场景树
        JPanel leftPanel = LayoutBuilder.createPanelWithHeader("panel.explorer",
            LayoutBuilder.styledScroll(sceneController.getTree()));

        // 中：视口 + 控制台
        JPanel centerPanel = new JPanel(new BorderLayout());
        centerPanel.setBackground(Colors.bgDeepest());
        centerPanel.add(LayoutBuilder.createViewportToolbar(
            () -> sceneController.createEntity(), () -> sceneController.deleteSelected()
        ), BorderLayout.NORTH);
        centerPanel.add(viewport, BorderLayout.CENTER);

        // 控制台
        JTextArea console = new JTextArea();
        console.setBackground(Colors.bgDeepest());
        console.setForeground(Colors.textSecondary());
        console.setFont(UIManager.getFont("defaultFont").deriveFont(Font.PLAIN, 12f));
        console.setEditable(false);
        console.setBorder(BorderFactory.createEmptyBorder(4, 8, 4, 8));
        console.setCaretColor(Colors.BLUE);
        // Keep a reference for logging
        this.consoleArea = console;
        console.putClientProperty("log", console);

        JPanel consolePanel = LayoutBuilder.createPanelWithHeader("panel.output",
            LayoutBuilder.styledScroll(console));
        // Let JSplitPane control console height (not fixed)

        JSplitPane vertSplit = LayoutBuilder.splitV(centerPanel, consolePanel);

        // 右：检查器
        JPanel rightPanel = LayoutBuilder.createPanelWithHeader("panel.properties",
            LayoutBuilder.styledScroll(inspectorController.getPanel()));

        // 组装
        JSplitPane horizSplit = LayoutBuilder.splitH(leftPanel, vertSplit);
        JSplitPane mainSplit = LayoutBuilder.splitH(horizSplit, rightPanel);
        JPanel statusBar = createStatusBar(console);

        setContentPane(LayoutBuilder.buildContent(tb, mainSplit, statusBar));

        SwingUtilities.invokeLater(() -> {
            horizSplit.setDividerLocation(224);
            mainSplit.setDividerLocation(getWidth() - 240);
            vertSplit.setDividerLocation(0.75);
        });
    }

    private JPanel createStatusBar(JTextArea console) {
        JPanel bar = LayoutBuilder.createStatusBar();
        JPanel left = new JPanel(new FlowLayout(FlowLayout.LEFT, 0, 0));
        left.setOpaque(false);
        statusLabel = new JLabel("  " + I18n.get("status.ready"));
        statusLabel.setFont(UIManager.getFont("defaultFont").deriveFont(Font.PLAIN, 11f));
        statusLabel.setForeground(Colors.textMuted());
        left.add(statusLabel);
        bar.add(left, BorderLayout.WEST);

        JPanel right = new JPanel(new FlowLayout(FlowLayout.RIGHT, 8, 0));
        right.setOpaque(false);
        langBtn = new JButton(I18n.get("lang.en"));
        langBtn.setFont(UIManager.getFont("defaultFont").deriveFont(Font.PLAIN, 11f));
        langBtn.setFocusPainted(false); langBtn.setBorderPainted(false);
        langBtn.setContentAreaFilled(false);
        langBtn.setForeground(Colors.textMuted());
        langBtn.setCursor(Cursor.getPredefinedCursor(Cursor.HAND_CURSOR));
        langBtn.addActionListener(e -> {
            I18n.toggle();
            applyThemeAndLanguage();
        });
        themeBtn = new JButton(I18n.get("theme.dark"));
        themeBtn.setFont(UIManager.getFont("defaultFont").deriveFont(Font.PLAIN, 11f));
        themeBtn.setFocusPainted(false); themeBtn.setBorderPainted(false);
        themeBtn.setContentAreaFilled(false);
        themeBtn.setForeground(Colors.textMuted());
        themeBtn.setCursor(Cursor.getPredefinedCursor(Cursor.HAND_CURSOR));
        themeBtn.addActionListener(e -> {
            Theme.toggle();
            applyThemeAndLanguage();
        });
        right.add(langBtn);
        right.add(themeBtn);
        bar.add(right, BorderLayout.EAST);
        return bar;
    }

    private void setupKeyboard() {
        InputMap im = getRootPane().getInputMap(JComponent.WHEN_IN_FOCUSED_WINDOW);
        ActionMap am = getRootPane().getActionMap();
        im.put(KeyStroke.getKeyStroke(KeyEvent.VK_S, InputEvent.CTRL_DOWN_MASK), "save");
        am.put("save", new AbstractAction() { public void actionPerformed(ActionEvent e) { saveScene(); } });
        im.put(KeyStroke.getKeyStroke(KeyEvent.VK_O, InputEvent.CTRL_DOWN_MASK), "open");
        am.put("open", new AbstractAction() { public void actionPerformed(ActionEvent e) { loadScene(); } });
        im.put(KeyStroke.getKeyStroke(KeyEvent.VK_N, InputEvent.CTRL_DOWN_MASK | InputEvent.SHIFT_DOWN_MASK), "newScene");
        am.put("newScene", new AbstractAction() { public void actionPerformed(ActionEvent e) { newScene(); } });
        im.put(KeyStroke.getKeyStroke(KeyEvent.VK_N, InputEvent.CTRL_DOWN_MASK), "newE");
        am.put("newE", new AbstractAction() { public void actionPerformed(ActionEvent e) { sceneController.createEntity(); } });
        im.put(KeyStroke.getKeyStroke(KeyEvent.VK_Z, InputEvent.CTRL_DOWN_MASK), "undo");
        am.put("undo", new AbstractAction() { public void actionPerformed(ActionEvent e) { sceneController.undo(); } });
        im.put(KeyStroke.getKeyStroke(KeyEvent.VK_Y, InputEvent.CTRL_DOWN_MASK), "redo");
        am.put("redo", new AbstractAction() { public void actionPerformed(ActionEvent e) { sceneController.redo(); } });
        im.put(KeyStroke.getKeyStroke(KeyEvent.VK_L, InputEvent.CTRL_DOWN_MASK), "toggleLang");
        am.put("toggleLang", new AbstractAction() { public void actionPerformed(ActionEvent e) { I18n.toggle(); applyThemeAndLanguage(); } });
        im.put(KeyStroke.getKeyStroke(KeyEvent.VK_T, InputEvent.CTRL_DOWN_MASK), "toggleTheme");
        am.put("toggleTheme", new AbstractAction() { public void actionPerformed(ActionEvent e) { Theme.toggle(); applyThemeAndLanguage(); } });
        im.put(KeyStroke.getKeyStroke(KeyEvent.VK_F5, 0), "resetCam");
        am.put("resetCam", new AbstractAction() { public void actionPerformed(ActionEvent e) { scene.resetCamera(); } });
    }

    // ═══════════════════════════════════════════════════════════
    //  主题 & 语言
    // ═══════════════════════════════════════════════════════════

    private void setupLanguageAndTheme() {
        I18n.addChangeListener(lang -> SwingUtilities.invokeLater(this::applyThemeAndLanguage));
        Theme.addChangeListener(p -> SwingUtilities.invokeLater(this::applyThemeAndLanguage));
        Colors.updateTheme();
    }

    private void applyThemeAndLanguage() {
        Colors.updateTheme();
        getContentPane().setBackground(Colors.bgDeepest());
        SwingUtilities.updateComponentTreeUI(this);
        sceneController.refreshLanguage();
        langBtn.setText(I18n.getCurrentLang() == I18n.Lang.CHINESE ? I18n.get("lang.en") : I18n.get("lang.zh"));
        themeBtn.setText(switch (Theme.getCurrent()) {
            case DARK -> I18n.get("theme.dracula");
            case LIGHT -> I18n.get("theme.dark");
            case DRACULA -> I18n.get("theme.light");
        });
        updateStatus();
    }

    // ═══════════════════════════════════════════════════════════
    //  场景
    // ═══════════════════════════════════════════════════════════

    private void loadDemoScene() {
        java.util.List<com.aetherforge.model.Entity> demos = java.util.Arrays.asList(
            createDemo("p1", I18n.get("entity.player"), "player", Colors.BLUE, true, true, 0, 0, 32, 32),
            createDemo("g1", I18n.get("entity.goblin"), "enemy", Colors.RED, false, false, 150, 80, 32, 32),
            createDemo("m1", I18n.get("entity.merchant"), "npc", Colors.GREEN, false, false, -120, -70, 28, 36),
            createDemo("c1", I18n.get("entity.chest"), "object", Colors.ORANGE, false, false, -60, 130, 24, 20),
            createDemo("t1", I18n.get("entity.oak"), "env", new Color(0x30, 0xc0, 0x50), false, false, 200, -120, 40, 50)
        );
        for (com.aetherforge.model.Entity e : demos) scene.addEntity(e);
    }

    private com.aetherforge.model.Entity createDemo(String id, String name, String type,
            Color color, boolean circle, boolean player, double x, double y, double w, double h) {
        com.aetherforge.model.Entity e = new com.aetherforge.model.Entity(type, name);
        e.setX(x); e.setY(y); e.setWidth(w); e.setHeight(h);
        e.setColor(color); e.setCircle(circle); e.setPlayer(player);
        return e;
    }

    // ═══════════════════════════════════════════════════════════
    //  SceneListener
    // ═══════════════════════════════════════════════════════════

    @Override
    public void sceneChanged() { updateStatus(); }

    @Override
    public void selectionChanged(com.aetherforge.model.Entity selected) {}

    @Override
    public void logMessage(String msg) {
        String ts = LocalTime.now().format(TIME_FMT);
        String line = "[" + ts + "] " + msg + "\n";
        if (consoleArea != null) {
            consoleArea.append(line);
            consoleArea.setCaretPosition(consoleArea.getDocument().getLength());
        } else {
            System.out.print(line);
        }
    }

    private void updateStatus() {
        if (statusLabel != null) {
            statusLabel.setText(String.format("  %d %s | %s: %d, %d | %s: %.0f%%",
                scene.getEntities().size(), I18n.get("status.entities"),
                I18n.get("status.camera"), (int) scene.getCameraX(), (int) scene.getCameraY(),
                I18n.get("status.zoom"), scene.getCameraZoom() * 100));
        }
    }

    // ═══════════════════════════════════════════════════════════
    //  窗口控制
    // ═══════════════════════════════════════════════════════════

    private void toggleMaximized() {
        Rectangle bounds = GraphicsEnvironment.getLocalGraphicsEnvironment().getMaximumWindowBounds();
        if (isMaximized) {
            setBounds(normalX, normalY, normalWidth, normalHeight);
            isMaximized = false;
        } else {
            normalX = getX(); normalY = getY();
            normalWidth = getWidth(); normalHeight = getHeight();
            setBounds(bounds);
            isMaximized = true;
        }
    }

    // ═══════════════════════════════════════════════════════════
    //  文件操作
    // ═══════════════════════════════════════════════════════════

    private void newScene() {
        int r = JOptionPane.showConfirmDialog(this, "Clear scene? Unsaved changes lost.",
            "New Scene", JOptionPane.OK_CANCEL_OPTION, JOptionPane.WARNING_MESSAGE);
        if (r != JOptionPane.OK_OPTION) return;
        scene.getEntities().clear();
        scene.resetCamera();
        scene.fireChange();
        scene.fireLog("New scene");
    }

    private void saveScene() {
        JFileChooser fc = new JFileChooser();
        fc.setDialogTitle(I18n.get("scene.root") + " - " + I18n.get("panel.properties"));
        fc.setFileFilter(new FileNameExtensionFilter("AetherForge Scene (*.json)", "json"));
        fc.setSelectedFile(new java.io.File("scene.json"));
        if (fc.showSaveDialog(this) == JFileChooser.APPROVE_OPTION) {
            try (PrintWriter pw = new PrintWriter(fc.getSelectedFile(), "UTF-8")) {
                pw.write(scene.toJson());
                scene.fireLog("Scene saved");
            } catch (IOException ex) {
                JOptionPane.showMessageDialog(this, "Save failed: " + ex.getMessage(),
                    "Error", JOptionPane.ERROR_MESSAGE);
            }
        }
    }

    private void loadScene() {
        JFileChooser fc = new JFileChooser();
        fc.setDialogTitle(I18n.get("scene.root") + " - " + I18n.get("statusbar.ready"));
        fc.setFileFilter(new FileNameExtensionFilter("AetherForge Scene (*.json)", "json"));
        if (fc.showOpenDialog(this) == JFileChooser.APPROVE_OPTION) {
            try {
                String json = new String(java.nio.file.Files.readAllBytes(fc.getSelectedFile().toPath()), "UTF-8");
                Scene loaded = Scene.fromJson(json);
                // Replace scene contents
                scene.getEntities().clear();
                for (Entity e : loaded.getEntities()) scene.addEntity(e);
                scene.fireChange();
                scene.fireLog("Scene loaded");
            } catch (IOException ex) {
                JOptionPane.showMessageDialog(this, "Load failed: " + ex.getMessage(),
                    "Error", JOptionPane.ERROR_MESSAGE);
            }
        }
    }

    private class WindowDragHandler extends MouseAdapter {
        private int sx, sy, fx, fy;
        @Override
        public void mousePressed(MouseEvent e) { sx = e.getXOnScreen(); sy = e.getYOnScreen(); fx = getX(); fy = getY(); }
        @Override
        public void mouseDragged(MouseEvent e) { if (!isMaximized) setLocation(fx + e.getXOnScreen() - sx, fy + e.getYOnScreen() - sy); }
        @Override
        public void mouseClicked(MouseEvent e) { if (e.getClickCount() == 2) toggleMaximized(); }
    }

    // 窗口缩放
    private static final int RM = 6;
    private int rd = 0;
    private static final int RN=0, R_N=1, R_S=2, R_W=4, R_E=8;
    {
        MouseAdapter resizer = new MouseAdapter() {
            int sx,sy,sw,sh;
            public void mouseMoved(MouseEvent e) { if (isMaximized) return; rd=cd(e.getX(),e.getY()); setResizeCursor(rd); }
            public void mousePressed(MouseEvent e) { if (isMaximized) return; rd=cd(e.getX(),e.getY()); if(rd!=RN){sx=e.getXOnScreen();sy=e.getYOnScreen();sw=getWidth();sh=getHeight();} }
            public void mouseDragged(MouseEvent e) {
                if (isMaximized||rd==RN) return;
                int dx=e.getXOnScreen()-sx, dy=e.getYOnScreen()-sy;
                int nx=getX(), ny=getY(), nw=sw, nh=sh;
                if ((rd&R_E)!=0) nw=sw+dx; if ((rd&R_W)!=0) { nw=sw-dx; nx=getX()+dx; }
                if ((rd&R_S)!=0) nh=sh+dy; if ((rd&R_N)!=0) { nh=sh-dy; ny=getY()+dy; }
                Dimension min=getMinimumSize();
                if (nw<min.width) { if ((rd&R_W)!=0) nx=getX()+sw-min.width; nw=min.width; }
                if (nh<min.height) { if ((rd&R_N)!=0) ny=getY()+sh-min.height; nh=min.height; }
                setBounds(nx,ny,nw,nh);
            }
            public void mouseExited(MouseEvent e) { rd=RN; setCursor(Cursor.getDefaultCursor()); }
        };
        addMouseListener(resizer); addMouseMotionListener(resizer);
    }
    private int cd(int mx, int my) { int w=getWidth(), h=getHeight(), d=RN; if(my<RM)d|=R_N; if(my>h-RM)d|=R_S; if(mx<RM)d|=R_W; if(mx>w-RM)d|=R_E; return d; }
    private void setResizeCursor(int d) {
        int c = Cursor.DEFAULT_CURSOR;
        if (d==R_N||d==R_S) c=Cursor.N_RESIZE_CURSOR;
        else if (d==R_W||d==R_E) c=Cursor.E_RESIZE_CURSOR;
        else if (d==(R_N|R_W)||d==(R_S|R_E)) c=Cursor.NW_RESIZE_CURSOR;
        else if (d==(R_N|R_E)||d==(R_S|R_W)) c=Cursor.NE_RESIZE_CURSOR;
        setCursor(Cursor.getPredefinedCursor(c));
    }
}
