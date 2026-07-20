package com.aetherforge.ui;

import com.aetherforge.model.Entity;
import com.aetherforge.util.Colors;
import com.aetherforge.util.DarkScrollBarUI;
import com.aetherforge.util.EntityIcon;
import com.aetherforge.util.I18n;
import com.aetherforge.util.Theme;
import javax.swing.*;
import javax.swing.UIManager;
import javax.swing.border.EmptyBorder;
import javax.swing.tree.*;
import java.awt.*;
import java.awt.event.*;
import java.awt.image.BufferedImage;
import java.time.LocalTime;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.List;

/**
 * AetherForge Studio 主窗口
 * Codex 风格无边框暗色主题游戏引擎编辑器
 * 布局：场景树 | 视口+控制台 | 检查器
 */
public class MainWindow extends JFrame {

    // ─── 数据模型 ───
    private final List<Entity> entities = new ArrayList<>();
    private Entity selectedEntity;
    private double cameraX, cameraY, cameraZoom = 1.0;

    // ─── UI 组件 ───
    private final JTree sceneTree;
    private final DefaultTreeModel treeModel;
    private final DefaultMutableTreeNode treeRoot;
    private final JPanel inspectorPanel;
    private final JTextArea consoleArea;
    private final ViewportPanel viewportPanel;
    private JLabel statusLabel;

    // ─── 窗口状态 ───
    private boolean isMaximized;
    private int normalX, normalY, normalWidth, normalHeight;
    private static final DateTimeFormatter TIME_FMT = DateTimeFormatter.ofPattern("HH:mm:ss");

    // ═══════════════════════════════════════════════════════════
    //  构造
    // ═══════════════════════════════════════════════════════════

    public MainWindow() {
        sceneTree = new JTree(new DefaultMutableTreeNode(I18n.get("scene.root")));
        treeModel = (DefaultTreeModel) sceneTree.getModel();
        treeRoot = (DefaultMutableTreeNode) treeModel.getRoot();
        inspectorPanel = new JPanel();
        consoleArea = new JTextArea();
        viewportPanel = new ViewportPanel(this);

        setupWindowProperties();
        installWindowResizer();
        setupInspectorPanel();
        setupConsoleArea();
        setupSceneTree();
        assembleMainLayout();

        loadDemoEntities();
        setupLanguageAndTheme();
        logMessage(I18n.get("app.title") + " " + I18n.get("statusbar.ready"));
    }

    // ═══════════════════════════════════════════════════════════
    //  窗口基础配置
    // ═══════════════════════════════════════════════════════════

    private void setupWindowProperties() {
        setTitle("AetherForge Studio");
        setUndecorated(true);
        setBackground(Colors.BACKGROUND_DEEPEST);
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        setSize(1400, 900);
        setMinimumSize(new Dimension(1000, 600));
        setLocationRelativeTo(null);
        setIconImage(createWindowIcon());
    }

    private Image createWindowIcon() {
        BufferedImage image = new BufferedImage(64, 64, BufferedImage.TYPE_INT_ARGB);
        Graphics2D g = image.createGraphics();
        g.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
        g.setColor(Colors.BLUE);
        g.fillPolygon(new int[]{32, 56, 32, 8}, new int[]{4, 32, 60, 32}, 4);
        g.setColor(Colors.BACKGROUND_DEEPEST);
        g.fillPolygon(new int[]{32, 48, 32, 16}, new int[]{14, 32, 50, 32}, 4);
        g.dispose();
        return image;
    }

    // ═══════════════════════════════════════════════════════════
    //  标题栏
    // ═══════════════════════════════════════════════════════════

    private JPanel createTitleBar() {
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
        titleBar.setPreferredSize(new Dimension(0, 38));

        // Logo
        JLabel logoLabel = new JLabel() {
            @Override
            protected void paintComponent(Graphics g) {
                Graphics2D g2 = (Graphics2D) g.create();
                g2.setRenderingHint(RenderingHints.KEY_TEXT_ANTIALIASING, RenderingHints.VALUE_TEXT_ANTIALIAS_LCD_HRGB);
                g2.setColor(Colors.BLUE);
                int cy = getHeight() / 2;
                g2.fillPolygon(new int[]{10, 17, 10, 3}, new int[]{cy-7, cy, cy+7, cy}, 4);
                g2.setFont(UIManager.getFont("defaultFont").deriveFont(Font.BOLD, 12f));
                g2.setColor(Colors.TEXT_PRIMARY);
                g2.drawString("AetherForge Studio", 26, cy + 4);
                g2.dispose();
            }
        };
        logoLabel.setPreferredSize(new Dimension(200, 38));
        logoLabel.setBorder(new EmptyBorder(0, 12, 0, 0));

        // 窗口控制按钮
        JPanel buttonPanel = new JPanel(new FlowLayout(FlowLayout.RIGHT, 0, 0));
        buttonPanel.setOpaque(false);
        buttonPanel.add(createWindowButton(WindowButton.MINIMIZE));
        buttonPanel.add(createWindowButton(WindowButton.MAXIMIZE));
        buttonPanel.add(createWindowButton(WindowButton.CLOSE));

        titleBar.add(logoLabel, BorderLayout.WEST);
        titleBar.add(buttonPanel, BorderLayout.EAST);

        // 窗口拖拽
        WindowDragHandler dragHandler = new WindowDragHandler();
        titleBar.addMouseListener(dragHandler);
        titleBar.addMouseMotionListener(dragHandler);
        logoLabel.addMouseListener(dragHandler);
        logoLabel.addMouseMotionListener(dragHandler);

        return titleBar;
    }

    private enum WindowButton { MINIMIZE, MAXIMIZE, CLOSE }

    private JButton createWindowButton(WindowButton type) {
        JButton button = new JButton() {
            @Override
            protected void paintComponent(Graphics g) {
                Graphics2D g2 = (Graphics2D) g.create();
                g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
                g2.setRenderingHint(RenderingHints.KEY_STROKE_CONTROL, RenderingHints.VALUE_STROKE_PURE);

                int w = getWidth(), h = getHeight();
                boolean hover = getModel().isRollover();
                boolean pressed = getModel().isArmed();

                // 背景
                if (type == WindowButton.CLOSE) {
                    g2.setColor(hover ? (pressed ? new Color(0xd0,0x30,0x60) : new Color(0xf0,0x40,0x70))
                                      : Colors.BACKGROUND_DARK);
                } else {
                    g2.setColor(hover ? (pressed ? Colors.BACKGROUND_HOVER : Colors.BACKGROUND_RAISED)
                                      : Colors.BACKGROUND_DARK);
                }
                g2.fillRect(0, 0, w, h);

                // 图标
                g2.setColor(hover && type == WindowButton.CLOSE ? Color.WHITE : Colors.TEXT_SECONDARY);
                g2.setStroke(new BasicStroke(1.5f));
                int cx = w/2, cy = h/2, s = 10;

                switch (type) {
                    case MINIMIZE -> g2.drawLine(cx-s/2, cy, cx+s/2, cy);
                    case MAXIMIZE -> g2.drawRect(cx-s/2, cy-s/2+1, s, s-1);
                    case CLOSE -> {
                        g2.drawLine(cx-s/2, cy-s/2, cx+s/2, cy+s/2);
                        g2.drawLine(cx+s/2, cy-s/2, cx-s/2, cy+s/2);
                    }
                }
                g2.dispose();
            }
        };

        button.setPreferredSize(new Dimension(46, 38));
        button.setFocusPainted(false);
        button.setBorderPainted(false);
        button.setContentAreaFilled(false);
        button.setCursor(Cursor.getPredefinedCursor(Cursor.HAND_CURSOR));

        button.addActionListener(e -> {
            switch (type) {
                case MINIMIZE -> setState(JFrame.ICONIFIED);
                case MAXIMIZE -> toggleMaximized();
                case CLOSE    -> System.exit(0);
            }
        });
        return button;
    }

    /** 窗口拖拽 */
    private class WindowDragHandler extends MouseAdapter {
        private int startScreenX, startScreenY, frameX, frameY;

        @Override
        public void mousePressed(MouseEvent e) {
            startScreenX = e.getXOnScreen();
            startScreenY = e.getYOnScreen();
            frameX = getX();
            frameY = getY();
        }

        @Override
        public void mouseDragged(MouseEvent e) {
            if (isMaximized) return;
            setLocation(frameX + e.getXOnScreen() - startScreenX,
                       frameY + e.getYOnScreen() - startScreenY);
        }

        @Override
        public void mouseClicked(MouseEvent e) {
            if (e.getClickCount() == 2) toggleMaximized();
        }
    }

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
    //  场景树
    // ═══════════════════════════════════════════════════════════

    private void setupSceneTree() {
        sceneTree.setRootVisible(true);
        sceneTree.setShowsRootHandles(true);
        sceneTree.setBackground(Colors.BACKGROUND_PANEL);
        sceneTree.setForeground(Colors.TEXT_PRIMARY);
        sceneTree.setFont(UIManager.getFont("defaultFont").deriveFont(Font.PLAIN, 13f));
        sceneTree.setRowHeight(26);
        sceneTree.setBorder(new EmptyBorder(4, 4, 4, 4));
        sceneTree.setCellRenderer(new SceneTreeRenderer());
        sceneTree.addTreeSelectionListener(e -> onTreeSelection(e));

        // 右键菜单
        JPopupMenu popup = new JPopupMenu();
        popup.setBackground(Colors.BACKGROUND_RAISED);

        JMenuItem addItem = new JMenuItem("+ " + I18n.get("tree.new"));
        addItem.setForeground(Colors.TEXT_PRIMARY);
        addItem.setBackground(Colors.BACKGROUND_RAISED);
        addItem.addActionListener(e -> createNewEntity());
        popup.add(addItem);

        JMenuItem delItem = new JMenuItem(I18n.get("tree.delete"));
        delItem.setForeground(Colors.TEXT_PRIMARY);
        delItem.setBackground(Colors.BACKGROUND_RAISED);
        delItem.addActionListener(e -> deleteSelectedEntity());
        popup.add(delItem);

        sceneTree.setComponentPopupMenu(popup);
    }

    /** 自定义树节点渲染器 */
    private class SceneTreeRenderer extends DefaultTreeCellRenderer {
        @Override
        public Component getTreeCellRendererComponent(JTree tree, Object value,
                boolean selected, boolean expanded, boolean leaf, int row, boolean hasFocus) {
            JLabel label = (JLabel) super.getTreeCellRendererComponent(
                tree, value, selected, expanded, leaf, row, false);
            label.setOpaque(true);
            label.setBackground(selected ? Colors.BACKGROUND_HOVER : Colors.BACKGROUND_PANEL);
            label.setForeground(selected ? Colors.BLUE : Colors.TEXT_PRIMARY);
            label.setBorder(new EmptyBorder(2, 4, 2, 4));

            if (value instanceof DefaultMutableTreeNode) {
                Object userObj = ((DefaultMutableTreeNode) value).getUserObject();
                if (userObj instanceof Entity) {
                    label.setIcon(new EntityIcon(((Entity) userObj).getColor(), 8));
                } else {
                    label.setIcon(new EntityIcon(Colors.ORANGE, 8));
                }
            }
            return label;
        }
    }

    private void onTreeSelection(javax.swing.event.TreeSelectionEvent e) {
        TreePath path = e.getNewLeadSelectionPath();
        if (path != null && path.getLastPathComponent() instanceof DefaultMutableTreeNode) {
            Object userObj = ((DefaultMutableTreeNode) path.getLastPathComponent()).getUserObject();
            if (userObj instanceof Entity) {
                selectedEntity = (Entity) userObj;
                refreshInspector();
                viewportPanel.repaint();
            }
        }
    }

    // ═══════════════════════════════════════════════════════════
    //  控制台
    // ═══════════════════════════════════════════════════════════

    private void setupConsoleArea() {
        consoleArea.setBackground(Colors.BACKGROUND_DEEPEST);
        consoleArea.setForeground(Colors.TEXT_SECONDARY);
        consoleArea.setFont(UIManager.getFont("defaultFont").deriveFont(Font.PLAIN, 12f));
        consoleArea.setEditable(false);
        consoleArea.setBorder(new EmptyBorder(4, 8, 4, 8));
        consoleArea.setCaretColor(Colors.BLUE);
    }

    // ═══════════════════════════════════════════════════════════
    //  检查器
    // ═══════════════════════════════════════════════════════════

    private void setupInspectorPanel() {
        inspectorPanel.setLayout(new BoxLayout(inspectorPanel, BoxLayout.Y_AXIS));
        inspectorPanel.setBackground(Colors.BACKGROUND_DEEPEST);
    }

    // ═══════════════════════════════════════════════════════════
    //  状态栏
    // ═══════════════════════════════════════════════════════════

    private JPanel createStatusBar() {
        JPanel statusBar = new JPanel(new BorderLayout());
        statusBar.setBackground(Colors.BACKGROUND_RAISED);
        statusBar.setPreferredSize(new Dimension(0, 22));

        JPanel leftPanel = new JPanel(new FlowLayout(FlowLayout.LEFT, 0, 0));
        leftPanel.setOpaque(false);
        statusLabel = new JLabel("  " + I18n.get("status.ready"));
        statusLabel.setFont(UIManager.getFont("defaultFont").deriveFont(Font.PLAIN, 11f));
        statusLabel.setForeground(Colors.TEXT_MUTED);
        leftPanel.add(statusLabel);
        statusBar.add(leftPanel, BorderLayout.WEST);

        JPanel rightPanel = new JPanel(new FlowLayout(FlowLayout.RIGHT, 10, 0));
        rightPanel.setOpaque(false);

        JLabel fpsLabel = new JLabel("60 FPS");
        fpsLabel.setFont(UIManager.getFont("defaultFont").deriveFont(Font.PLAIN, 11f));
        fpsLabel.setForeground(Colors.TEXT_MUTED);

        JLabel entityCount = new JLabel("0 " + I18n.get("status.entities"));
        entityCount.setFont(UIManager.getFont("defaultFont").deriveFont(Font.PLAIN, 11f));
        entityCount.setForeground(Colors.TEXT_MUTED);

        rightPanel.add(fpsLabel);
        rightPanel.add(entityCount);

        // 语言切换按钮
        JButton langBtn = new JButton(I18n.get("lang.zh"));
        langBtn.setFont(UIManager.getFont("defaultFont").deriveFont(Font.PLAIN, 10f));
        langBtn.setFocusPainted(false);
        langBtn.setBorderPainted(false);
        langBtn.setContentAreaFilled(false);
        langBtn.setForeground(Colors.TEXT_MUTED);
        langBtn.setCursor(Cursor.getPredefinedCursor(Cursor.HAND_CURSOR));
        langBtn.addActionListener(e -> {
            I18n.toggle();
            langBtn.setText(I18n.get("lang." + (I18n.getCurrentLang() == I18n.Lang.CHINESE ? "zh" : "en")));
            applyThemeAndLanguage();
        });
        langBtn.addMouseListener(new MouseAdapter() {
            public void mouseEntered(MouseEvent e) { langBtn.setForeground(Colors.BLUE); }
            public void mouseExited(MouseEvent e)  { langBtn.setForeground(Colors.TEXT_MUTED); }
        });
        rightPanel.add(langBtn);

        // 分隔符
        JLabel sep = new JLabel("|");
        sep.setFont(UIManager.getFont("defaultFont").deriveFont(Font.PLAIN, 10f));
        sep.setForeground(Colors.TEXT_MUTED);
        rightPanel.add(sep);

        // 主题切换按钮
        JButton themeBtn = new JButton(I18n.get("theme.dark"));
        themeBtn.setFont(UIManager.getFont("defaultFont").deriveFont(Font.PLAIN, 10f));
        themeBtn.setFocusPainted(false);
        themeBtn.setBorderPainted(false);
        themeBtn.setContentAreaFilled(false);
        themeBtn.setForeground(Colors.TEXT_MUTED);
        themeBtn.setCursor(Cursor.getPredefinedCursor(Cursor.HAND_CURSOR));
        themeBtn.addActionListener(e -> {
            Theme.toggle();
            String key = switch (Theme.getCurrent()) {
                case DARK -> "theme.dark";
                case LIGHT -> "theme.light";
                case DRACULA -> "theme.dracula";
            };
            themeBtn.setText(I18n.get(key));
            applyThemeAndLanguage();
        });
        themeBtn.addMouseListener(new MouseAdapter() {
            public void mouseEntered(MouseEvent e) { themeBtn.setForeground(Colors.BLUE); }
            public void mouseExited(MouseEvent e)  { themeBtn.setForeground(Colors.TEXT_MUTED); }
        });
        rightPanel.add(themeBtn);
        statusBar.add(rightPanel, BorderLayout.EAST);

        // 顶部分隔线
        JPanel separator = new JPanel();
        separator.setBackground(Colors.BORDER_LINE);
        separator.setPreferredSize(new Dimension(0, 1));
        statusBar.add(separator, BorderLayout.NORTH);

        return statusBar;
    }

    // ═══════════════════════════════════════════════════════════
    //  布局组装
    // ═══════════════════════════════════════════════════════════

    private void assembleMainLayout() {
        // 左侧：场景树
        JPanel leftPanel = new JPanel(new BorderLayout());
        leftPanel.setBackground(Colors.BACKGROUND_PANEL);
        leftPanel.setPreferredSize(new Dimension(220, 0));

        JPanel leftHeader = new JPanel(new BorderLayout());
        leftHeader.setBackground(Colors.BACKGROUND_RAISED);
        leftHeader.setPreferredSize(new Dimension(0, 26));
        leftHeader.setBorder(new EmptyBorder(0, 10, 0, 4));
        JLabel leftTitle = new JLabel(I18n.get("panel.explorer"));
        leftTitle.setFont(UIManager.getFont("defaultFont").deriveFont(Font.BOLD, 10f));
        leftTitle.setForeground(Colors.TEXT_MUTED);
        leftHeader.add(leftTitle, BorderLayout.WEST);

        JScrollPane treeScroll = new JScrollPane(sceneTree);
        treeScroll.setBorder(BorderFactory.createEmptyBorder());
        treeScroll.getVerticalScrollBar().setUI(new DarkScrollBarUI());
        treeScroll.getHorizontalScrollBar().setUI(new DarkScrollBarUI());
        treeScroll.setBackground(Colors.BACKGROUND_PANEL);

        leftPanel.add(leftHeader, BorderLayout.NORTH);
        leftPanel.add(treeScroll, BorderLayout.CENTER);

        // 中间：视口 + 控制台
        JPanel centerPanel = new JPanel(new BorderLayout());
        centerPanel.setBackground(Colors.BACKGROUND_DEEPEST);

        // 视口工具栏
        JPanel viewportToolbar = createViewportToolbar();
        JPanel viewportContainer = new JPanel(new BorderLayout());
        viewportContainer.setBackground(Colors.BACKGROUND_DEEPEST);
        viewportContainer.add(viewportToolbar, BorderLayout.NORTH);
        viewportContainer.add(viewportPanel, BorderLayout.CENTER);

        // 底部控制台
        JPanel consolePanel = new JPanel(new BorderLayout());
        consolePanel.setBackground(Colors.BACKGROUND_PANEL);

        JPanel consoleHeader = new JPanel(new BorderLayout());
        consoleHeader.setBackground(Colors.BACKGROUND_RAISED);
        consoleHeader.setPreferredSize(new Dimension(0, 22));
        consoleHeader.setBorder(new EmptyBorder(0, 8, 0, 8));
        JLabel consoleTitle = new JLabel(I18n.get("panel.output"));
        consoleTitle.setFont(UIManager.getFont("defaultFont").deriveFont(Font.BOLD, 10f));
        consoleTitle.setForeground(Colors.TEXT_MUTED);
        consoleHeader.add(consoleTitle, BorderLayout.WEST);

        JScrollPane consoleScroll = new JScrollPane(consoleArea);
        consoleScroll.setBorder(BorderFactory.createEmptyBorder());
        consoleScroll.getVerticalScrollBar().setUI(new DarkScrollBarUI());
        consoleScroll.getHorizontalScrollBar().setUI(new DarkScrollBarUI());
        consoleScroll.setBackground(Colors.BACKGROUND_PANEL);

        consolePanel.add(consoleHeader, BorderLayout.NORTH);
        consolePanel.add(consoleScroll, BorderLayout.CENTER);
        consolePanel.setPreferredSize(new Dimension(0, 120));

        centerPanel.add(viewportContainer, BorderLayout.CENTER);
        centerPanel.add(consolePanel, BorderLayout.SOUTH);

        // 右侧：检查器
        JPanel rightPanel = new JPanel(new BorderLayout());
        rightPanel.setBackground(Colors.BACKGROUND_PANEL);
        rightPanel.setPreferredSize(new Dimension(230, 0));

        JPanel rightHeader = new JPanel(new BorderLayout());
        rightHeader.setBackground(Colors.BACKGROUND_RAISED);
        rightHeader.setPreferredSize(new Dimension(0, 26));
        rightHeader.setBorder(new EmptyBorder(0, 10, 0, 10));
        JLabel rightTitle = new JLabel(I18n.get("panel.properties"));
        rightTitle.setFont(UIManager.getFont("defaultFont").deriveFont(Font.BOLD, 10f));
        rightTitle.setForeground(Colors.TEXT_MUTED);
        rightHeader.add(rightTitle, BorderLayout.WEST);

        JScrollPane inspectorScroll = new JScrollPane(inspectorPanel);
        inspectorScroll.setBorder(BorderFactory.createEmptyBorder());
        inspectorScroll.getVerticalScrollBar().setUI(new DarkScrollBarUI());
        inspectorScroll.setBackground(Colors.BACKGROUND_PANEL);

        rightPanel.add(rightHeader, BorderLayout.NORTH);
        rightPanel.add(inspectorScroll, BorderLayout.CENTER);

        // 分割面板
        JSplitPane horizontalSplit = new JSplitPane(
            JSplitPane.HORIZONTAL_SPLIT, leftPanel, centerPanel);
        horizontalSplit.setBorder(BorderFactory.createEmptyBorder());
        horizontalSplit.setBackground(Colors.BACKGROUND_DEEPEST);
        horizontalSplit.setDividerSize(2);
        horizontalSplit.setResizeWeight(0);

        JSplitPane mainSplit = new JSplitPane(
            JSplitPane.HORIZONTAL_SPLIT, horizontalSplit, rightPanel);
        mainSplit.setBorder(BorderFactory.createEmptyBorder());
        mainSplit.setBackground(Colors.BACKGROUND_DEEPEST);
        mainSplit.setDividerSize(2);

        // 整体容器
        JPanel contentPanel = new JPanel(new BorderLayout());
        contentPanel.setBackground(Colors.BACKGROUND_DEEPEST);
        contentPanel.add(createTitleBar(), BorderLayout.NORTH);
        contentPanel.add(mainSplit, BorderLayout.CENTER);
        contentPanel.add(createStatusBar(), BorderLayout.SOUTH);

        setContentPane(contentPanel);

        // 初始分割位置
        SwingUtilities.invokeLater(() -> {
            horizontalSplit.setDividerLocation(220);
            mainSplit.setDividerLocation(getWidth() - 240);
        });
    }

    private JPanel createViewportToolbar() {
        JPanel toolbar = new JPanel(new FlowLayout(FlowLayout.LEFT, 2, 3));
        toolbar.setBackground(Colors.BACKGROUND_RAISED);
        toolbar.setPreferredSize(new Dimension(0, 26));
        toolbar.setBorder(new EmptyBorder(0, 4, 0, 4));

        String[] toolNames = {I18n.get("viewport.tool.select"), I18n.get("viewport.tool.move"), I18n.get("viewport.tool.scale")};
        ButtonGroup toolGroup = new ButtonGroup();

        for (String name : toolNames) {
            JToggleButton toolButton = new JToggleButton(name);
            toolButton.setFont(UIManager.getFont("defaultFont").deriveFont(Font.PLAIN, 11f));
            toolButton.setFocusPainted(false);
            toolButton.setBorderPainted(false);
            toolButton.setBackground(Colors.BACKGROUND_RAISED);
            toolButton.setForeground(Colors.TEXT_SECONDARY);
            toolButton.setPreferredSize(new Dimension(50, 20));
            toolButton.setCursor(Cursor.getPredefinedCursor(Cursor.HAND_CURSOR));
            toolButton.addItemListener(e -> {
                toolButton.setBackground(toolButton.isSelected()
                    ? Colors.BACKGROUND_HOVER : Colors.BACKGROUND_RAISED);
                toolButton.setForeground(toolButton.isSelected()
                    ? Colors.BLUE : Colors.TEXT_SECONDARY);
            });
            toolGroup.add(toolButton);
            toolbar.add(toolButton);
        }
        return toolbar;
    }

    // ═══════════════════════════════════════════════════════════
    //  检查器内容
    // ═══════════════════════════════════════════════════════════

    public void refreshInspector() {
        inspectorPanel.removeAll();

        if (selectedEntity == null) {
            JLabel emptyHint = new JLabel("  " + I18n.get("inspector.empty"));
            emptyHint.setFont(UIManager.getFont("defaultFont").deriveFont(Font.PLAIN, 12f));
            emptyHint.setForeground(Colors.TEXT_MUTED);
            emptyHint.setBorder(new EmptyBorder(10, 10, 10, 10));
            inspectorPanel.add(emptyHint);
        } else {
            // 标题
            JLabel titleLabel = new JLabel("  " + selectedEntity.getName());
            titleLabel.setFont(UIManager.getFont("defaultFont").deriveFont(Font.BOLD, 12f));
            titleLabel.setForeground(Colors.TEXT_PRIMARY);
            titleLabel.setBorder(new EmptyBorder(8, 8, 4, 8));
            inspectorPanel.add(titleLabel);

            inspectorPanel.add(new JSeparator());
            ((JSeparator) inspectorPanel.getComponent(1)).setForeground(Colors.BORDER_LINE);
            ((JSeparator) inspectorPanel.getComponent(1)).setBackground(Colors.BORDER_LINE);

            // 基本信息
            addInspectorRow(I18n.get("inspector.id"), selectedEntity.getId());
            addInspectorRow(I18n.get("inspector.type"), selectedEntity.getType());
            addInspectorRow(I18n.get("inspector.name"), selectedEntity.getName());
            addInspectorRow(I18n.get("inspector.position"),
                String.format("%.1f, %.1f", selectedEntity.getX(), selectedEntity.getY()));
            addInspectorRow(I18n.get("inspector.size"),
                String.format("%.0f \u00D7 %.0f", selectedEntity.getWidth(), selectedEntity.getHeight()));

            // 属性编辑区
            inspectorPanel.add(Box.createVerticalStrut(8));
            JLabel propTitle = new JLabel("  " + I18n.get("inspector.transform"));
            propTitle.setFont(UIManager.getFont("defaultFont").deriveFont(Font.BOLD, 10f));
            propTitle.setForeground(Colors.TEXT_MUTED);
            inspectorPanel.add(propTitle);

            addEditableRow("X", String.valueOf((int) selectedEntity.getX()));
            addEditableRow("Y", String.valueOf((int) selectedEntity.getY()));
            addEditableRow(I18n.get("inspector.width"), String.valueOf((int) selectedEntity.getWidth()));
            addEditableRow(I18n.get("inspector.height"), String.valueOf((int) selectedEntity.getHeight()));
        }

        inspectorPanel.revalidate();
        inspectorPanel.repaint();
    }

    private void addInspectorRow(String label, String value) {
        JPanel row = new JPanel(new BorderLayout());
        row.setBackground(Colors.BACKGROUND_DEEPEST);
        row.setBorder(new EmptyBorder(2, 10, 2, 10));
        row.setMaximumSize(new Dimension(9999, 20));

        JLabel labelComponent = new JLabel(label);
        labelComponent.setFont(UIManager.getFont("defaultFont").deriveFont(Font.PLAIN, 11f));
        labelComponent.setForeground(Colors.TEXT_MUTED);
        labelComponent.setPreferredSize(new Dimension(60, 16));

        JLabel valueComponent = new JLabel(value);
        valueComponent.setFont(UIManager.getFont("defaultFont").deriveFont(Font.PLAIN, 11f));
        valueComponent.setForeground(Colors.TEXT_PRIMARY);

        row.add(labelComponent, BorderLayout.WEST);
        row.add(valueComponent, BorderLayout.CENTER);
        inspectorPanel.add(row);
    }

    private void addEditableRow(String label, String value) {
        JPanel row = new JPanel(new BorderLayout());
        row.setBackground(Colors.BACKGROUND_DEEPEST);
        row.setBorder(new EmptyBorder(1, 10, 1, 10));
        row.setMaximumSize(new Dimension(9999, 24));

        JLabel labelComp = new JLabel(label);
        labelComp.setFont(UIManager.getFont("defaultFont").deriveFont(Font.PLAIN, 11f));
        labelComp.setForeground(Colors.TEXT_MUTED);
        labelComp.setPreferredSize(new Dimension(60, 18));

        JTextField field = new JTextField(value);
        field.setFont(UIManager.getFont("defaultFont").deriveFont(Font.PLAIN, 11f));
        field.setForeground(Colors.TEXT_PRIMARY);
        field.setBackground(Colors.BACKGROUND_DARK);
        field.setCaretColor(Colors.BLUE);
        field.setBorder(BorderFactory.createCompoundBorder(
            BorderFactory.createLineBorder(Colors.BORDER_LINE, 1),
            new EmptyBorder(1, 4, 1, 4)));
        field.setCursor(Cursor.getPredefinedCursor(Cursor.TEXT_CURSOR));

        // real-time entity property editing
        String propKey = label;
        // use fixed key to survive language switch
        final String fixedKey;
        if (propKey.equals("X") || propKey.equals("Y") || 
            propKey.equals(I18n.get("inspector.width")) || propKey.equals(I18n.get("inspector.height"))) {
            if (propKey.equals(I18n.get("inspector.width"))) fixedKey = "W";
            else if (propKey.equals(I18n.get("inspector.height"))) fixedKey = "H";
            else fixedKey = propKey;
        } else {
            fixedKey = propKey;
        }

        javax.swing.event.DocumentListener dl = new javax.swing.event.DocumentListener() {
            public void insertUpdate(javax.swing.event.DocumentEvent e)  { apply(); }
            public void removeUpdate(javax.swing.event.DocumentEvent e)  { apply(); }
            public void changedUpdate(javax.swing.event.DocumentEvent e) { apply(); }
            private void apply() {
                if (selectedEntity == null) return;
                try {
                    double v = Double.parseDouble(field.getText());
                    boolean changed = false;
                    switch (fixedKey) {
                        case "X" -> { selectedEntity.setX(v); changed=true; }
                        case "Y" -> { selectedEntity.setY(v); changed=true; }
                        case "W" -> { selectedEntity.setWidth(v); changed=true; }
                        case "H" -> { selectedEntity.setHeight(v); changed=true; }
                    }
                    if (changed) { viewportPanel.repaint(); updateStatusBar(); }
                } catch (NumberFormatException ignored) {}
            }
        };
        field.getDocument().addDocumentListener(dl);

        row.add(labelComp, BorderLayout.WEST);
        row.add(field, BorderLayout.CENTER);
        inspectorPanel.add(row);
    }

    // ═══════════════════════════════════════════════════════════
    //  数据操作
    // ═══════════════════════════════════════════════════════════

    private void loadDemoEntities() {
        entities.clear();
        cameraX = 0;
        cameraY = 0;
        cameraZoom = 1.0;

        addEntity(createDemoEntity("p1", I18n.get("entity.player"), "player", Colors.BLUE, true, true, 0, 0, 32, 32));
        addEntity(createDemoEntity("g1", I18n.get("entity.goblin"), "enemy", Colors.RED, false, false, 150, 80, 32, 32));
        addEntity(createDemoEntity("m1", I18n.get("entity.merchant"), "npc", Colors.GREEN, false, false, -120, -70, 28, 36));
        addEntity(createDemoEntity("c1", I18n.get("entity.chest"), "object", Colors.ORANGE, false, false, -60, 130, 24, 20));
        addEntity(createDemoEntity("t1", I18n.get("entity.oak"), "env", new Color(0x30, 0xc0, 0x50), false, false, 200, -120, 40, 50));

        updateStatusBar();
        logMessage(I18n.get("log.loaded") + " " + entities.size() + " " + I18n.get("log.entities"));
    }

    private Entity createDemoEntity(String id, String name, String type,
            Color color, boolean isCircle, boolean isPlayer,
            double x, double y, double w, double h) {
        Entity entity = new Entity(type, name);
        entity.setX(x);
        entity.setY(y);
        entity.setWidth(w);
        entity.setHeight(h);
        entity.setColor(color);
        entity.setCircle(isCircle);
        entity.setPlayer(isPlayer);
        return entity;
    }

    private void addEntity(Entity entity) {
        entities.add(entity);
        treeRoot.add(new DefaultMutableTreeNode(entity));
        treeModel.reload();
        viewportPanel.animateEntityIn(entity);
        updateStatusBar();
    }

    public void createNewEntity() {
        Entity entity = new Entity("entity", I18n.get("entity.new"));
        addEntity(entity);
        logMessage(I18n.get("log.created") + ": " + entity.getId());
    }

    public void deleteSelectedEntity() {
        if (selectedEntity == null) return;
        Entity toDelete = selectedEntity;
        // animate fade-out, then actually remove after animation
        viewportPanel.animateEntityOut(toDelete);
        javax.swing.Timer delayedRemove = new javax.swing.Timer(160, ev -> {
            entities.remove(toDelete);
            for (int i = 0; i < treeRoot.getChildCount(); i++) {
                DefaultMutableTreeNode node = (DefaultMutableTreeNode) treeRoot.getChildAt(i);
                if (node.getUserObject() == toDelete) {
                    treeRoot.remove(i);
                    break;
                }
            }
            treeModel.reload();
            selectedEntity = null;
            refreshInspector();
            viewportPanel.repaint();
            updateStatusBar();
            logMessage(I18n.get("log.deleted"));
            ((javax.swing.Timer)ev.getSource()).stop();
        });
        delayedRemove.setRepeats(false);
        delayedRemove.start();
    }

    // ═══════════════════════════════════════════════════════════
    //  状态更新
    // ═══════════════════════════════════════════════════════════

    public void updateStatusBar() {
        if (statusLabel != null) {
            statusLabel.setText(String.format(
                "  %d " + I18n.get("status.entities") + " | " + I18n.get("status.camera") + ": %d, %d | " + I18n.get("status.zoom") + ": %.0f%%",
                entities.size(), (int) cameraX, (int) cameraY, cameraZoom * 100));
        }
    }

    public void logMessage(String message) {
        String timestamp = LocalTime.now().format(TIME_FMT);
        consoleArea.append("[" + timestamp + "] " + message + "\n");
        consoleArea.setCaretPosition(consoleArea.getDocument().getLength());
    }

    public void repaintSceneTree() {
        sceneTree.repaint();
    }

    // ═══════════════════════════════════════════════════════════
    //  Getter / Setter（供 ViewportPanel 调用）
    // ═══════════════════════════════════════════════════════════

    
    // window edge resize support for undecorated frame
    private static final int RESIZE_MARGIN = 6;
    private int resizeDir = 0;
    private static final int R_NONE=0, R_N=1, R_S=2, R_W=4, R_E=8;

    private void installWindowResizer() {
        MouseAdapter r = new MouseAdapter() {
            int sx, sy, sw, sh;
            public void mouseMoved(MouseEvent e) {
                if (isMaximized) return;
                resizeDir = calcDir(e.getX(), e.getY());
                setResizeCursor(resizeDir);
            }
            public void mousePressed(MouseEvent e) {
                if (isMaximized) return;
                resizeDir = calcDir(e.getX(), e.getY());
                if (resizeDir != R_NONE) { sx=e.getXOnScreen(); sy=e.getYOnScreen(); sw=getWidth(); sh=getHeight(); }
            }
            public void mouseDragged(MouseEvent e) {
                if (isMaximized || resizeDir==R_NONE) return;
                int dx=e.getXOnScreen()-sx, dy=e.getYOnScreen()-sy;
                int nx=getX(), ny=getY(), nw=sw, nh=sh;
                if ((resizeDir & R_E)!=0) nw = sw + dx;
                if ((resizeDir & R_W)!=0) { nw = sw - dx; nx = getX() + dx; }
                if ((resizeDir & R_S)!=0) nh = sh + dy;
                if ((resizeDir & R_N)!=0) { nh = sh - dy; ny = getY() + dy; }
                Dimension min = getMinimumSize();
                if (nw < min.width) { if ((resizeDir & R_W)!=0) nx = getX() + sw - min.width; nw = min.width; }
                if (nh < min.height) { if ((resizeDir & R_N)!=0) ny = getY() + sh - min.height; nh = min.height; }
                setBounds(nx, ny, nw, nh);
            }
            public void mouseExited(MouseEvent e) { resizeDir=R_NONE; setCursor(Cursor.getDefaultCursor()); }
        };
        addMouseListener(r); addMouseMotionListener(r);
    }

    private int calcDir(int mx, int my) {
        int w=getWidth(), h=getHeight(), d=R_NONE;
        if (my < RESIZE_MARGIN) d|=R_N; if (my > h-RESIZE_MARGIN) d|=R_S;
        if (mx < RESIZE_MARGIN) d|=R_W; if (mx > w-RESIZE_MARGIN) d|=R_E;
        return d;
    }

    private void setResizeCursor(int d) {
        int c = Cursor.DEFAULT_CURSOR;
        if (d==R_N||d==R_S) c=Cursor.N_RESIZE_CURSOR;
        else if (d==R_W||d==R_E) c=Cursor.E_RESIZE_CURSOR;
        else if (d==(R_N|R_W)||d==(R_S|R_E)) c=Cursor.NW_RESIZE_CURSOR;
        else if (d==(R_N|R_E)||d==(R_S|R_W)) c=Cursor.NE_RESIZE_CURSOR;
        setCursor(Cursor.getPredefinedCursor(c));
    }

    

    // ═══════════════════════════════════════════════════════════
    //  语言 & 主题切换
    // ═══════════════════════════════════════════════════════════

    private void setupLanguageAndTheme() {
        I18n.setChangeListener(lang -> SwingUtilities.invokeLater(this::applyThemeAndLanguage));
        Theme.setChangeListener(p  -> SwingUtilities.invokeLater(this::applyThemeAndLanguage));
        // 确保主题颜色同步
        Colors.updateTheme();
    }

    /** 应用主题颜色到所有组件 */
    private void applyThemeAndLanguage() {
        Colors.updateTheme();
        getContentPane().setBackground(Colors.BACKGROUND_DEEPEST);
        updateComponentTree(getContentPane());
        javax.swing.SwingUtilities.updateComponentTreeUI(this);
        refreshInspector();
        updateStatusBar();
        repaintSceneTree();
        viewportPanel.repaint();
        repaint();
    }

    private void updateComponentTree(Container container) {
        for (Component comp : container.getComponents()) {
            if (comp instanceof JPanel) {
                comp.setBackground(Colors.BACKGROUND_DEEPEST);
            }
            if (comp instanceof Container) {
                updateComponentTree((Container) comp);
            }
        }
    }
public List<Entity> getEntities()          { return entities; }
    public Entity getSelectedEntity()          { return selectedEntity; }
    public void   setSelectedEntity(Entity e)  { selectedEntity = e; }
    public double getCameraX()                 { return cameraX; }
    public double getCameraY()                 { return cameraY; }
    public double getCameraZoom()              { return cameraZoom; }

    public void moveCamera(double dx, double dy) {
        cameraX += dx;
        cameraY += dy;
    }

    public void zoomCamera(double factor) {
        cameraZoom = Math.max(0.05, Math.min(20, cameraZoom * factor));
    }
}
