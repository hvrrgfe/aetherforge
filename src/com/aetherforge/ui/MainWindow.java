package com.aetherforge.ui;

import com.aetherforge.model.Entity;
import com.aetherforge.model.Scene;
import com.aetherforge.model.SceneListener;
import com.aetherforge.model.Project;
import com.aetherforge.model.ProjectManager;
import com.aetherforge.util.Colors;
import com.aetherforge.util.I18n;
import com.aetherforge.util.Theme;
import javax.swing.*;
import javax.swing.filechooser.FileNameExtensionFilter;
import java.awt.*;
import java.awt.event.*;
import java.awt.image.BufferedImage;
import java.io.*;
import java.nio.file.Path;
import java.time.LocalTime;
import java.time.format.DateTimeFormatter;

/**
 * AetherForge Studio 濞戞捁宕甸悰銉╁矗?闁?缂侇喖澧介悾婵嬪础韫囨氨娈堕柛? * 閻㈩垰鍟惇顒佹叏閺冣偓婢ь厾绱?LayoutBuilder闁挎稑鑻┃鈧柡鍜佸灠椤瑩骞嶅Ο鑲╄埗 SceneController
 * 婵☆偀鍋撻柡灞诲劚濞呮帗鎱ㄩ弮鈧晶顓犵磼?InspectorController闁挎稑鐭侀～瀣矗閿濆拋娼ら柟鍨焽缁?ViewportPanel
 * 缂佹劖顨呰ぐ娑氱不閿涘嫭鍊炲┑顔芥⒐婢ь厾绱?TitleBarManager / ResizeManager
 */
public class MainWindow extends JFrame implements SceneListener {

    private Scene scene;
    private ViewportPanel viewport;
    private SceneController sceneController;
    private InspectorController inspectorController;
    private JLabel statusLabel;
    private JTextArea consoleArea;
    private JButton langButton, themeButton;
    private ProjectManager projectManager = new ProjectManager();
    private JMenuItem saveMenuItem, loadMenuItem, newMenuItem, aboutMenuItem, modelManagerMenuItem;

    private TitleBarManager titleBarManager;

    private static final DateTimeFormatter TIME_FORMAT = DateTimeFormatter.ofPattern("HH:mm:ss");
    private static final int MAX_LOG_LINES = 500;

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
            JOptionPane.showMessageDialog(null,
                "Failed to initialize: " + e.getMessage(),
                "Fatal Error", JOptionPane.ERROR_MESSAGE);
            System.exit(1);
        }
    }

    private void setupWindow() {
        setTitle("AetherForge Studio - No Project");
        setUndecorated(true);
        setBackground(Colors.bgDeepest());
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        setSize(1400, 900);
        setMinimumSize(new Dimension(1000, 600));
        setLocationRelativeTo(null);
        setIconImage(createAppIcon());
    }

    private Image createAppIcon() {
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
        JButton menuButton = createMenuButton();
        this.titleBarManager = new TitleBarManager(this, menuButton);

        JPanel scenePanel = buildScenePanel();
        JSplitPane mainSplit = new JSplitPane(
            JSplitPane.HORIZONTAL_SPLIT,
            scenePanel, buildViewportPanel());
        mainSplit.setBorder(BorderFactory.createEmptyBorder());
        mainSplit.setBackground(Colors.bgDeepest());
        mainSplit.setDividerSize(2);
        mainSplit.setResizeWeight(0);
        mainSplit.setContinuousLayout(true);
        mainSplit.setDividerLocation(240);

        JPanel statusBar = buildStatusBar();
        JPanel content = new JPanel(new BorderLayout());
        content.setBackground(Colors.bgDeepest());
        content.add(titleBarManager.getTitleBar(), BorderLayout.NORTH);
        content.add(mainSplit, BorderLayout.CENTER);
        content.add(statusBar, BorderLayout.SOUTH);
        setContentPane(content);

        new ResizeManager(this);
    }

    private JButton createMenuButton() {
        JButton menuBtn = new JButton("\u2630");
        menuBtn.setFont(UIManager.getFont("defaultFont").deriveFont(Font.PLAIN, 14f));
        menuBtn.setFocusPainted(false);
        menuBtn.setBorderPainted(false);
        menuBtn.setContentAreaFilled(false);
        menuBtn.setForeground(Colors.textSecondary());
        menuBtn.setPreferredSize(new Dimension(36, 40));
        menuBtn.setCursor(Cursor.getPredefinedCursor(Cursor.HAND_CURSOR));
        menuBtn.addActionListener(e -> showFileMenu(menuBtn));
        return menuBtn;
    }

    private void showFileMenu(JButton anchor) {
        JPopupMenu fileMenu = new JPopupMenu();
        fileMenu.setBackground(Colors.bgRaised());
        fileMenu.setBorder(BorderFactory.createLineBorder(Colors.borderLine()));

        saveMenuItem = createMenuItem(I18n.get("log.saved"),
            e -> saveScene());
        fileMenu.add(saveMenuItem);

        loadMenuItem = createMenuItem("Load Scene",
            e -> loadScene());
        fileMenu.add(loadMenuItem);

        JMenuItem openProjectItem = createMenuItem("Open Project (Ctrl+Shift+O)",
            e -> openProject());
        fileMenu.add(openProjectItem);
        fileMenu.addSeparator();

        JMenuItem closeProjectItem = createMenuItem("Close Project",
            e -> closeProject());
        fileMenu.add(closeProjectItem);
        fileMenu.addSeparator();

        newMenuItem = createMenuItem("New Scene",
            e -> newScene());
        fileMenu.add(newMenuItem);

        modelManagerMenuItem = createMenuItem("Model Manager",
            e -> openModelManager());
        fileMenu.add(modelManagerMenuItem);
        fileMenu.addSeparator();

        aboutMenuItem = createMenuItem("About",
            e -> showAbout());
        fileMenu.add(aboutMenuItem);

        fileMenu.show(anchor, 0, anchor.getHeight());
    }

    private JMenuItem createMenuItem(String text, ActionListener action) {
        JMenuItem item = new JMenuItem(text);
        item.setForeground(Colors.textPrimary());
        item.setBackground(Colors.bgRaised());
        item.addActionListener(action);
        return item;
    }

    private JPanel buildScenePanel() {
        JPanel panel = new JPanel(new BorderLayout());
        panel.setBackground(Colors.bgPanel());
        JPanel header = new JPanel(new BorderLayout());
        header.setBackground(Colors.bgRaised());
        header.setPreferredSize(new Dimension(0, 28));
        header.setBorder(BorderFactory.createEmptyBorder(0, 10, 0, 10));
        JLabel headerLabel = new JLabel(I18n.get("panel.explorer"));
        headerLabel.setFont(UIManager.getFont("defaultFont").deriveFont(Font.BOLD, 10f));
        headerLabel.setForeground(Colors.textMuted());
        header.add(headerLabel, BorderLayout.WEST);
        panel.add(header, BorderLayout.NORTH);
        JSplitPane split = new JSplitPane(
            JSplitPane.VERTICAL_SPLIT,
            buildSceneTreePanel(),
            buildConsolePanel());
        split.setBorder(BorderFactory.createEmptyBorder());
        split.setBackground(Colors.bgDeepest());
        split.setDividerSize(2);
        split.setResizeWeight(1.0);
        split.setContinuousLayout(true);
        panel.add(split, BorderLayout.CENTER);
        return panel;
    }

    private JPanel buildSceneTreePanel() {
        JPanel panel = new JPanel(new BorderLayout());
        panel.setBackground(Colors.bgPanel());
        panel.add(sceneController.getToolbar(), BorderLayout.NORTH);
        JScrollPane scrollPane = new JScrollPane(sceneController.getTree());
        scrollPane.setBorder(BorderFactory.createEmptyBorder());
        scrollPane.getVerticalScrollBar().setUI(new com.aetherforge.util.DarkScrollBarUI());
        scrollPane.setBackground(Colors.bgPanel());
        panel.add(scrollPane, BorderLayout.CENTER);
        return panel;
    }

    private JPanel buildConsolePanel() {
        JPanel panel = new JPanel(new BorderLayout());
        panel.setBackground(Colors.bgPanel());
        JPanel header = new JPanel(new BorderLayout());
        header.setBackground(Colors.bgRaised());
        header.setPreferredSize(new Dimension(0, 24));
        header.setBorder(BorderFactory.createEmptyBorder(0, 8, 0, 8));
        JLabel headerLabel = new JLabel(I18n.get("panel.output"));
        headerLabel.setFont(UIManager.getFont("defaultFont").deriveFont(Font.BOLD, 9f));
        headerLabel.setForeground(Colors.textMuted());
        header.add(headerLabel, BorderLayout.WEST);
        panel.add(header, BorderLayout.NORTH);
        consoleArea = new JTextArea(6, 30);
        consoleArea.setBackground(Colors.bgDark());
        consoleArea.setForeground(Colors.textPrimary());
        consoleArea.setFont(new Font("Consolas", Font.PLAIN, 11));
        consoleArea.setEditable(false);
        consoleArea.setCaretColor(Colors.BLUE);
        consoleArea.setBorder(BorderFactory.createEmptyBorder(4, 8, 4, 8));
        JScrollPane consoleScroll = new JScrollPane(consoleArea);
        consoleScroll.setBorder(BorderFactory.createEmptyBorder());
        consoleScroll.getVerticalScrollBar().setUI(new com.aetherforge.util.DarkScrollBarUI());
        consoleScroll.setBackground(Colors.bgPanel());
        panel.add(consoleScroll, BorderLayout.CENTER);
        return panel;
    }

    private JPanel buildViewportPanel() {
        JPanel panel = new JPanel(new BorderLayout());
        panel.setBackground(Colors.bgDeepest());
        JToolBar toolbar = new JToolBar();
        toolbar.setBackground(Colors.bgRaised());
        toolbar.setFloatable(false);
        toolbar.setBorder(BorderFactory.createEmptyBorder(2, 4, 2, 4));

        ButtonGroup toolGroup = new ButtonGroup();
        String[] toolNames = {
            I18n.get("viewport.tool.select"),
            I18n.get("viewport.tool.move"),
            I18n.get("viewport.tool.scale")
        };
        for (int i = 0; i < toolNames.length; i++) {
            int index = i;
            JToggleButton tb = new JToggleButton(toolNames[i]);
            tb.setFont(UIManager.getFont("defaultFont").deriveFont(Font.PLAIN, 11f));
            tb.setFocusPainted(false);
            tb.setBackground(Colors.bgRaised());
            tb.setForeground(Colors.textSecondary());
            tb.setPreferredSize(new Dimension(52, 24));
            tb.setCursor(Cursor.getPredefinedCursor(Cursor.HAND_CURSOR));
            if (i == 0) tb.setSelected(true);
            tb.addItemListener(ev -> {
                tb.setBackground(tb.isSelected() ? Colors.bgHover() : Colors.bgRaised());
                tb.setForeground(tb.isSelected() ? Colors.BLUE : Colors.textSecondary());
                if (tb.isSelected()) {
                    viewport.setToolMode(ViewportPanel.ToolMode.values()[index]);
                }
            });
            toolGroup.add(tb);
            toolbar.add(tb);
        }

        toolbar.add(Box.createHorizontalStrut(8));
        JButton addBtn = createSmallToolbarButton("+");
        addBtn.addActionListener(e -> sceneController.createEntity());
        toolbar.add(addBtn);
        JButton delBtn = createSmallToolbarButton("-");
        delBtn.addActionListener(e -> sceneController.deleteSelected());
        toolbar.add(delBtn);

        panel.add(toolbar, BorderLayout.NORTH);
        panel.add(viewport, BorderLayout.CENTER);

        // 右侧检查器面板
        JScrollPane inspectorScroll = new JScrollPane(inspectorController.getPanel());
        inspectorScroll.setBorder(BorderFactory.createEmptyBorder());
        inspectorScroll.getVerticalScrollBar().setUI(new com.aetherforge.util.DarkScrollBarUI());
        inspectorScroll.setBackground(Colors.bgDeepest());
        inspectorScroll.setPreferredSize(new Dimension(220, 0));
        panel.add(inspectorScroll, BorderLayout.EAST);

        return panel;
    }

    private JButton createSmallToolbarButton(String text) {
        JButton btn = new JButton(text);
        btn.setFont(UIManager.getFont("defaultFont").deriveFont(Font.BOLD, 13f));
        btn.setFocusPainted(false);
        btn.setBorderPainted(false);
        btn.setBackground(Colors.bgRaised());
        btn.setForeground(Colors.textSecondary());
        btn.setPreferredSize(new Dimension(24, 24));
        btn.setCursor(Cursor.getPredefinedCursor(Cursor.HAND_CURSOR));
        return btn;
    }

    private JPanel buildStatusBar() {
        JPanel bar = new JPanel(new BorderLayout());
        bar.setBackground(Colors.bgRaised());
        bar.setPreferredSize(new Dimension(0, 24));
        statusLabel = new JLabel(I18n.get("statusbar.ready"));
        statusLabel.setFont(UIManager.getFont("defaultFont").deriveFont(Font.PLAIN, 11f));
        statusLabel.setForeground(Colors.textMuted());
        statusLabel.setBorder(BorderFactory.createEmptyBorder(0, 10, 0, 10));
        bar.add(statusLabel, BorderLayout.WEST);
        return bar;
    }

    private void setupKeyboard() {
        InputMap inputMap = getRootPane().getInputMap(JComponent.WHEN_IN_FOCUSED_WINDOW);
        ActionMap actionMap = getRootPane().getActionMap();

        inputMap.put(KeyStroke.getKeyStroke(KeyEvent.VK_Z, Toolkit.getDefaultToolkit().getMenuShortcutKeyMaskEx()), "undo");
        actionMap.put("undo", new AbstractAction() {
            public void actionPerformed(ActionEvent e) { sceneController.undo(); }
        });

        inputMap.put(KeyStroke.getKeyStroke(KeyEvent.VK_Y, Toolkit.getDefaultToolkit().getMenuShortcutKeyMaskEx()), "redo");
        actionMap.put("redo", new AbstractAction() {
            public void actionPerformed(ActionEvent e) { sceneController.redo(); }
        });

        inputMap.put(KeyStroke.getKeyStroke(KeyEvent.VK_N, Toolkit.getDefaultToolkit().getMenuShortcutKeyMaskEx()), "newEntity");
        actionMap.put("newEntity", new AbstractAction() {
            public void actionPerformed(ActionEvent e) { sceneController.createEntity(); }
        });

        inputMap.put(KeyStroke.getKeyStroke(KeyEvent.VK_DELETE, 0), "delete");
        actionMap.put("delete", new AbstractAction() {
            public void actionPerformed(ActionEvent e) { sceneController.deleteSelected(); }
        });
    }

    private void setupLanguageAndTheme() {
        I18n.addChangeListener(lang -> {
            sceneController.refreshLanguage();
            refreshMenuTexts();
            repaint();
        });
        Theme.addChangeListener(profile -> {
            Colors.updateTheme();
            SwingUtilities.updateComponentTreeUI(this);
            repaint();
        });
    }

    private void refreshMenuTexts() {
        // Refresh title bar
        setTitle("AetherForge Studio - " +
            (projectManager.getCurrentProject() != null
                ? projectManager.getCurrentProject().getName()
                : I18n.get("statusbar.ready")));
    }

    private void loadDemoScene() {
        scene.addEntity(new Entity("player", I18n.get("entity.player")));
        scene.addEntity(new Entity("goblin", I18n.get("entity.goblin")));
        scene.addEntity(new Entity("merchant", I18n.get("entity.merchant")));
        scene.addEntity(new Entity("chest", I18n.get("entity.chest")));
        scene.addEntity(new Entity("oak", I18n.get("entity.oak")));
        scene.fireLog(I18n.get("log.loaded") + " 5 " + I18n.get("log.entities"));
    }

    // 闁崇儤鍔忛弲鏌ュ煛閹般劍娅滈柍鐑樺姀閺呮煡鍩￠幇銊︽珳闁崇儤鍔忛弲鏌ュ煛閹般劍娅滈柍鐑樺姀閺呮煡鍩￠幇銊︽珳闁崇儤鍔忛弲鏌ュ煛閹般劍娅滈柍鐑樺姀閺呮煡鍩￠幇銊︽珳闁崇儤鍔忛弲鏌ュ煛閹般劍娅滈柍鐑樺姀閺呮煡鍩￠幇銊︽珳闁崇儤鍔忛弲鏌ュ煛閹般劍娅滈柍鐑樺姀閺呮煡鍩￠幇銊︽珳
    //  闁哄倸娲ｅ▎銏ゅ箼瀹ュ嫮绋?    // 闁崇儤鍔忛弲鏌ュ煛閹般劍娅滈柍鐑樺姀閺呮煡鍩￠幇銊︽珳闁崇儤鍔忛弲鏌ュ煛閹般劍娅滈柍鐑樺姀閺呮煡鍩￠幇銊︽珳闁崇儤鍔忛弲鏌ュ煛閹般劍娅滈柍鐑樺姀閺呮煡鍩￠幇銊︽珳闁崇儤鍔忛弲鏌ュ煛閹般劍娅滈柍鐑樺姀閺呮煡鍩￠幇銊︽珳闁崇儤鍔忛弲鏌ュ煛閹般劍娅滈柍鐑樺姀閺呮煡鍩￠幇銊︽珳

    private void saveScene() {
        if (projectManager.getCurrentProject() != null) {
            try {
                Project p = projectManager.getCurrentProject();
                Path scenesDir = Path.of(p.getRootPath(), "scenes");
                java.nio.file.Files.createDirectories(scenesDir);
                String json = scene.toJson();
                java.nio.file.Files.writeString(scenesDir.resolve("scene.scene"), json);
                updateStatus("Scene saved to project");
                scene.fireLog(I18n.get("log.saved"));
            } catch (IOException ex) {
                scene.fireLog("Save failed: " + ex.getMessage());
            }
        } else {
            JFileChooser fc = new JFileChooser();
            fc.setDialogTitle("Save Scene...");
            fc.setFileFilter(new FileNameExtensionFilter("AetherForge Scene (*.json)", "json"));
            if (fc.showSaveDialog(this) == JFileChooser.APPROVE_OPTION) {
                try {
                    java.nio.file.Files.writeString(fc.getSelectedFile().toPath(), scene.toJson());
                    scene.fireLog(I18n.get("log.saved"));
                } catch (IOException ex) {
                    JOptionPane.showMessageDialog(this,
                        "Save failed: " + ex.getMessage(), "Error", JOptionPane.ERROR_MESSAGE);
                }
            }
        }
    }

    private void loadScene() {
        if (projectManager.getCurrentProject() != null) {
            try {
                JFileChooser fc = new JFileChooser(
                    projectManager.getCurrentProject().getRootPath() + "/scenes");
                fc.setFileFilter(new FileNameExtensionFilter("AetherForge Scene (*.scene)", "scene"));
                if (fc.showOpenDialog(this) == JFileChooser.APPROVE_OPTION) {
                    String json = java.nio.file.Files.readString(fc.getSelectedFile().toPath());
                    Scene loaded = Scene.fromJson(json);
                    scene.getEntities().clear();
                    for (Entity e : loaded.getEntities()) scene.addEntity(e);
                    scene.fireChange();
                    scene.fireLog("Scene loaded from project");
                }
            } catch (IOException ex) {
                scene.fireLog("Load failed: " + ex.getMessage());
            }
        } else {
            JFileChooser fc = new JFileChooser();
            fc.setDialogTitle("Open Scene...");
            fc.setFileFilter(new FileNameExtensionFilter("AetherForge Scene (*.json)", "json"));
            if (fc.showOpenDialog(this) == JFileChooser.APPROVE_OPTION) {
                try {
                    String json = java.nio.file.Files.readString(fc.getSelectedFile().toPath());
                    Scene loaded = Scene.fromJson(json);
                    scene.getEntities().clear();
                    for (Entity e : loaded.getEntities()) scene.addEntity(e);
                    scene.fireChange();
                    scene.fireLog("Scene loaded");
                } catch (IOException ex) {
                    JOptionPane.showMessageDialog(this,
                        "Load failed: " + ex.getMessage(), "Error", JOptionPane.ERROR_MESSAGE);
                }
            }
        }
    }

    private void openProject() {
        JFileChooser fc = new JFileChooser();
        fc.setDialogTitle("Open AetherForge Project...");
        fc.setFileSelectionMode(JFileChooser.DIRECTORIES_ONLY);
        if (fc.showOpenDialog(this) == JFileChooser.APPROVE_OPTION) {
            Path path = fc.getSelectedFile().toPath();
            Project p;
            try { p = projectManager.loadProject(path.toString()); } catch (java.io.IOException ex) { p = null; }
            if (p != null) {
                setTitle("AetherForge Studio - " + p.getName());
                updateStatus("Project loaded: " + p.getName());
                loadProjectEntities(p);
            } else {
                JOptionPane.showMessageDialog(this,
                    "Invalid project: " + path, "Error", JOptionPane.ERROR_MESSAGE);
            }
        }
    }

    private void loadProjectEntities(Project p) {
        scene.getEntities().clear();
        Path scenesDir = Path.of(p.getRootPath(), "scenes");
        if (java.nio.file.Files.exists(scenesDir)) {
            try (var stream = java.nio.file.Files.list(scenesDir)) {
                stream.filter(f -> f.toString().endsWith(".scene")).findFirst().ifPresent(f -> {
                    try {
                        String json = java.nio.file.Files.readString(f);
                        Scene loaded = Scene.fromJson(json);
                        for (Entity e : loaded.getEntities()) scene.addEntity(e);
                    } catch (IOException ex) {
                        scene.fireLog("Load failed: " + ex.getMessage());
                    }
                });
            } catch (IOException ex) {
                scene.fireLog("List scenes failed: " + ex.getMessage());
            }
        }
        scene.fireChange();
    }

    private void closeProject() {
        projectManager.closeProject();
        setTitle("AetherForge Studio - No Project");
        updateStatus("Project closed");
        scene.getEntities().clear();
        loadDemoScene();
        scene.fireChange();
    }

    private void newScene() {
        scene.getEntities().clear();
        scene.resetCamera();
        scene.fireChange();
        scene.fireLog("New scene created");
    }

    private void openModelManager() {
        ModelManagerDialog dialog = new ModelManagerDialog(this);
        dialog.setVisible(true);
    }

    private void showAbout() {
        ImageIcon icon = new ImageIcon(createAppIcon());
        JOptionPane.showMessageDialog(this,
            "AetherForge Studio v1.2.0\n" +
            "2D Game Engine Editor\n\n" +
            "Built with Java + FlatLaf\n" +
            "github.com/hvrrgfe/aetherforge",
            I18n.get("app.title"),
            JOptionPane.INFORMATION_MESSAGE,
            icon);
    }

    // 闁崇儤鍔忛弲鏌ュ煛閹般劍娅滈柍鐑樺姀閺呮煡鍩￠幇銊︽珳闁崇儤鍔忛弲鏌ュ煛閹般劍娅滈柍鐑樺姀閺呮煡鍩￠幇銊︽珳闁崇儤鍔忛弲鏌ュ煛閹般劍娅滈柍鐑樺姀閺呮煡鍩￠幇銊︽珳闁崇儤鍔忛弲鏌ュ煛閹般劍娅滈柍鐑樺姀閺呮煡鍩￠幇銊︽珳闁崇儤鍔忛弲鏌ュ煛閹般劍娅滈柍鐑樺姀閺呮煡鍩￠幇銊︽珳
    //  SceneListener
    // 闁崇儤鍔忛弲鏌ュ煛閹般劍娅滈柍鐑樺姀閺呮煡鍩￠幇銊︽珳闁崇儤鍔忛弲鏌ュ煛閹般劍娅滈柍鐑樺姀閺呮煡鍩￠幇銊︽珳闁崇儤鍔忛弲鏌ュ煛閹般劍娅滈柍鐑樺姀閺呮煡鍩￠幇銊︽珳闁崇儤鍔忛弲鏌ュ煛閹般劍娅滈柍鐑樺姀閺呮煡鍩￠幇銊︽珳闁崇儤鍔忛弲鏌ュ煛閹般劍娅滈柍鐑樺姀閺呮煡鍩￠幇銊︽珳

    @Override
    public void sceneChanged() {
        int count = scene.getEntities().size();
        updateStatus(count + " " + I18n.get("status.entities"));
    }

    @Override
    public void selectionChanged(Entity selected) { /* handled by controllers */ }

    @Override
    public void logMessage(String message) {
        if (consoleArea != null) {
            String timestamp = LocalTime.now().format(TIME_FORMAT);
            consoleArea.append("[" + timestamp + "] " + message + "\n");
            int lines = consoleArea.getLineCount();
            if (lines > MAX_LOG_LINES) {
                try {
                    int end = consoleArea.getLineEndOffset(lines - MAX_LOG_LINES - 1);
                    consoleArea.replaceRange("", 0, end);
                } catch (Exception ignored) {}
            }
            consoleArea.setCaretPosition(consoleArea.getDocument().getLength());
        }
    }

    private void updateStatus(String text) {
        if (statusLabel != null) {
            statusLabel.setText("  " + text);
        }
    }
}
