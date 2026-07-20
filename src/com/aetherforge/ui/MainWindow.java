package com.aetherforge.ui;

import com.aetherforge.model.Entity;
import com.aetherforge.util.Colors;
import com.aetherforge.util.DarkScrollBarUI;
import com.aetherforge.util.EntityIcon;
import com.aetherforge.util.I18n;
import com.aetherforge.util.Theme;
import javax.swing.*;
import javax.swing.border.EmptyBorder;
import javax.swing.tree.*;
import java.awt.*;
import java.awt.event.*;
import java.awt.image.BufferedImage;
import java.time.LocalTime;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.List;

public class MainWindow extends JFrame {

    private final List<Entity> entities = new ArrayList<>();
    private Entity selectedEntity;
    private double cameraX, cameraY, cameraZoom = 1.0;

    private final JTree sceneTree;
    private final DefaultTreeModel treeModel;
    private final DefaultMutableTreeNode treeRoot;
    private final JPanel inspectorPanel;
    private final JTextArea consoleArea;
    private final ViewportPanel viewportPanel;
    private JLabel statusLabel;
    private JLabel fpsLabel;
    private JLabel entityCountLabel;
    private JButton langBtn;
    private JButton themeBtn;

    private boolean isMaximized;
    private int normalX, normalY, normalWidth, normalHeight;
    private static final DateTimeFormatter TIME_FMT = DateTimeFormatter.ofPattern("HH:mm:ss");

    private static final int DP4 = 4, DP8 = 8, DP10 = 10, DP12 = 12;
    private static final int DP16 = 16, DP24 = 24, DP28 = 28, DP40 = 40;
    private static final int DP240 = 240;

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
        setupKeyboardActions();
        setupLanguageAndTheme();
        loadDemoEntities();
        logMessage(I18n.get("app.title") + " " + I18n.get("statusbar.ready"));
    }

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

    private void setupKeyboardActions() {
        InputMap im = getRootPane().getInputMap(JComponent.WHEN_IN_FOCUSED_WINDOW);
        ActionMap am = getRootPane().getActionMap();
        im.put(KeyStroke.getKeyStroke(KeyEvent.VK_N, InputEvent.CTRL_DOWN_MASK), "newEntity");
        am.put("newEntity", new AbstractAction() {
            public void actionPerformed(ActionEvent e) { createNewEntity(); }
        });
        im.put(KeyStroke.getKeyStroke(KeyEvent.VK_DELETE, 0), "delete");
        im.put(KeyStroke.getKeyStroke(KeyEvent.VK_BACK_SPACE, 0), "delete");
        am.put("delete", new AbstractAction() {
            public void actionPerformed(ActionEvent e) { deleteSelectedEntity(); }
        });
        im.put(KeyStroke.getKeyStroke(KeyEvent.VK_L, InputEvent.CTRL_DOWN_MASK), "toggleLang");
        am.put("toggleLang", new AbstractAction() {
            public void actionPerformed(ActionEvent e) { I18n.toggle(); }
        });
        im.put(KeyStroke.getKeyStroke(KeyEvent.VK_T, InputEvent.CTRL_DOWN_MASK), "toggleTheme");
        am.put("toggleTheme", new AbstractAction() {
            public void actionPerformed(ActionEvent e) { Theme.toggle(); }
        });
        im.put(KeyStroke.getKeyStroke(KeyEvent.VK_F5, 0), "resetCamera");
        am.put("resetCamera", new AbstractAction() {
            public void actionPerformed(ActionEvent e) {
                cameraX = 0; cameraY = 0; cameraZoom = 1.0;
                viewportPanel.repaint(); updateStatusBar();
            }
        });
    }

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
        titleBar.setPreferredSize(new Dimension(0, DP40));

        JPanel leftSection = new JPanel(new FlowLayout(FlowLayout.LEFT, DP8, 0));
        leftSection.setOpaque(false);
        JLabel iconLabel = new JLabel(new EntityIcon(Colors.BLUE, DP16));
        iconLabel.setBorder(new EmptyBorder(0, DP12, 0, DP4));
        JLabel titleLabel = new JLabel("AetherForge Studio");
        titleLabel.setFont(UIManager.getFont("defaultFont").deriveFont(Font.PLAIN, 12f));
        titleLabel.setForeground(Colors.TEXT_SECONDARY);
        leftSection.add(iconLabel);
        leftSection.add(titleLabel);

        JPanel rightSection = new JPanel(new FlowLayout(FlowLayout.RIGHT, 0, 0));
        rightSection.setOpaque(false);
        rightSection.add(createTitleButton(TitleButtonType.MINIMIZE));
        rightSection.add(createTitleButton(TitleButtonType.MAXIMIZE));
        rightSection.add(createTitleButton(TitleButtonType.CLOSE));

        titleBar.add(leftSection, BorderLayout.WEST);
        titleBar.add(rightSection, BorderLayout.EAST);

        WindowDragHandler dragHandler = new WindowDragHandler();
        titleBar.addMouseListener(dragHandler);
        titleBar.addMouseMotionListener(dragHandler);
        return titleBar;
    }

    private enum TitleButtonType { MINIMIZE, MAXIMIZE, CLOSE }

    private JButton createTitleButton(TitleButtonType type) {
        JButton button = new JButton() {
            @Override
            protected void paintComponent(Graphics g) {
                Graphics2D g2 = (Graphics2D) g.create();
                g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
                if (getModel().isRollover()) {
                    g2.setColor(type == TitleButtonType.CLOSE
                        ? new Color(0xe8, 0x11, 0x23) : Colors.BACKGROUND_HOVER);
                    g2.fillRect(0, 0, getWidth(), getHeight());
                }
                if (getModel().isPressed()) {
                    g2.setColor(type == TitleButtonType.CLOSE
                        ? new Color(0xc0, 0x0e, 0x1a) : Colors.BACKGROUND_RAISED);
                    g2.fillRect(0, 0, getWidth(), getHeight());
                }
                g2.setColor(type == TitleButtonType.CLOSE && getModel().isRollover()
                    ? Color.WHITE : Colors.TEXT_SECONDARY);
                int cx = getWidth() / 2, cy = getHeight() / 2, s = 10;
                g2.setStroke(new BasicStroke(1.2f));
                switch (type) {
                    case MINIMIZE -> g2.drawLine(cx - s / 2, cy, cx + s / 2, cy);
                    case MAXIMIZE -> g2.drawRect(cx - s / 2, cy - s / 2 + 1, s, s - 1);
                    case CLOSE -> {
                        g2.drawLine(cx - s / 2, cy - s / 2, cx + s / 2, cy + s / 2);
                        g2.drawLine(cx + s / 2, cy - s / 2, cx - s / 2, cy + s / 2);
                    }
                }
                g2.dispose();
            }
        };
        button.setPreferredSize(new Dimension(48, DP40));
        button.setFocusPainted(false);
        button.setBorderPainted(false);
        button.setContentAreaFilled(false);
        button.setCursor(Cursor.getPredefinedCursor(Cursor.HAND_CURSOR));
        button.addActionListener(e -> {
            switch (type) {
                case MINIMIZE -> setState(JFrame.ICONIFIED);
                case MAXIMIZE -> toggleMaximized();
                case CLOSE -> System.exit(0);
            }
        });
        return button;
    }

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

    private void setupSceneTree() {
        sceneTree.setRootVisible(true);
        sceneTree.setShowsRootHandles(true);
        sceneTree.setBackground(Colors.BACKGROUND_PANEL);
        sceneTree.setForeground(Colors.TEXT_PRIMARY);
        sceneTree.setFont(UIManager.getFont("defaultFont").deriveFont(Font.PLAIN, 13f));
        sceneTree.setRowHeight(DP28);
        sceneTree.setBorder(new EmptyBorder(DP4, DP4, DP4, DP4));
        sceneTree.setCellRenderer(new SceneTreeRenderer());
        sceneTree.addTreeSelectionListener(e -> onTreeSelection(e));

        JPopupMenu popup = new JPopupMenu();
        popup.setBackground(Colors.BACKGROUND_RAISED);
        popup.setBorder(BorderFactory.createLineBorder(Colors.BORDER_LINE));
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

    private class SceneTreeRenderer extends DefaultTreeCellRenderer {
        @Override
        public Component getTreeCellRendererComponent(JTree tree, Object value,
                boolean selected, boolean expanded, boolean leaf, int row, boolean hasFocus) {
            JLabel label = (JLabel) super.getTreeCellRendererComponent(
                tree, value, selected, expanded, leaf, row, false);
            label.setOpaque(true);
            label.setBackground(selected ? Colors.BACKGROUND_HOVER : Colors.BACKGROUND_PANEL);
            label.setForeground(selected ? Colors.BLUE : Colors.TEXT_PRIMARY);
            label.setBorder(new EmptyBorder(2, DP4, 2, DP4));
            if (value instanceof DefaultMutableTreeNode) {
                Object userObj = ((DefaultMutableTreeNode) value).getUserObject();
                if (userObj instanceof Entity) {
                    label.setIcon(new EntityIcon(((Entity) userObj).getColor(), 8));
                } else {
                    label.setIcon(new EntityIcon(Colors.ORANGE, 8));
                }
            }
            if (hasFocus && selected) {
                label.setBorder(BorderFactory.createCompoundBorder(
                    BorderFactory.createLineBorder(Colors.BLUE, 1),
                    new EmptyBorder(1, 3, 1, 3)));
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

    private void setupConsoleArea() {
        consoleArea.setBackground(Colors.BACKGROUND_DEEPEST);
        consoleArea.setForeground(Colors.TEXT_SECONDARY);
        consoleArea.setFont(UIManager.getFont("defaultFont").deriveFont(Font.PLAIN, 12f));
        consoleArea.setEditable(false);
        consoleArea.setBorder(new EmptyBorder(DP4, DP8, DP4, DP8));
        consoleArea.setCaretColor(Colors.BLUE);
        consoleArea.setSelectionColor(new Color(0x40, 0x80, 0xf0, 60));
    }

    private void setupInspectorPanel() {
        inspectorPanel.setLayout(new BoxLayout(inspectorPanel, BoxLayout.Y_AXIS));
        inspectorPanel.setBackground(Colors.BACKGROUND_DEEPEST);
    }

    private JPanel createStatusBar() {
        JPanel statusBar = new JPanel(new BorderLayout());
        statusBar.setBackground(Colors.BACKGROUND_RAISED);
        statusBar.setPreferredSize(new Dimension(0, DP24));

        JPanel leftPanel = new JPanel(new FlowLayout(FlowLayout.LEFT, 0, 0));
        leftPanel.setOpaque(false);
        statusLabel = new JLabel("  " + I18n.get("status.ready"));
        statusLabel.setFont(UIManager.getFont("defaultFont").deriveFont(Font.PLAIN, 11f));
        statusLabel.setForeground(Colors.TEXT_MUTED);
        leftPanel.add(statusLabel);
        statusBar.add(leftPanel, BorderLayout.WEST);

        JPanel rightPanel = new JPanel(new FlowLayout(FlowLayout.RIGHT, DP8, 0));
        rightPanel.setOpaque(false);
        fpsLabel = new JLabel("60 FPS");
        fpsLabel.setFont(UIManager.getFont("defaultFont").deriveFont(Font.PLAIN, 11f));
        fpsLabel.setForeground(Colors.TEXT_MUTED);
        entityCountLabel = new JLabel("0 " + I18n.get("status.entities"));
        entityCountLabel.setFont(UIManager.getFont("defaultFont").deriveFont(Font.PLAIN, 11f));
        entityCountLabel.setForeground(Colors.TEXT_MUTED);
        langBtn = new JButton(I18n.get("lang.zh"));
        langBtn.setFont(UIManager.getFont("defaultFont").deriveFont(Font.PLAIN, 11f));
        langBtn.setFocusPainted(false);
        langBtn.setBorderPainted(false);
        langBtn.setContentAreaFilled(false);
        langBtn.setForeground(Colors.TEXT_MUTED);
        langBtn.setCursor(Cursor.getPredefinedCursor(Cursor.HAND_CURSOR));
        langBtn.addActionListener(e -> I18n.toggle());
        themeBtn = new JButton(I18n.get("theme.dark"));
        themeBtn.setFont(UIManager.getFont("defaultFont").deriveFont(Font.PLAIN, 11f));
        themeBtn.setFocusPainted(false);
        themeBtn.setBorderPainted(false);
        themeBtn.setContentAreaFilled(false);
        themeBtn.setForeground(Colors.TEXT_MUTED);
        themeBtn.setCursor(Cursor.getPredefinedCursor(Cursor.HAND_CURSOR));
        themeBtn.addActionListener(e -> Theme.toggle());
        rightPanel.add(fpsLabel);
        rightPanel.add(entityCountLabel);
        rightPanel.add(langBtn);
        rightPanel.add(themeBtn);
        statusBar.add(rightPanel, BorderLayout.EAST);
        return statusBar;
    }

    private void assembleMainLayout() {
        JPanel leftPanel = new JPanel(new BorderLayout());
        leftPanel.setBackground(Colors.BACKGROUND_DEEPEST);
        JPanel leftHeader = new JPanel(new BorderLayout());
        leftHeader.setBackground(Colors.BACKGROUND_RAISED);
        leftHeader.setPreferredSize(new Dimension(0, DP28));
        leftHeader.setBorder(new EmptyBorder(0, DP10, 0, DP10));
        JLabel leftTitle = new JLabel(I18n.get("panel.explorer"));
        leftTitle.setFont(UIManager.getFont("defaultFont").deriveFont(Font.BOLD, 10f));
        leftTitle.setForeground(Colors.TEXT_MUTED);
        leftHeader.add(leftTitle, BorderLayout.WEST);
        JScrollPane treeScroll = new JScrollPane(sceneTree);
        treeScroll.setBorder(BorderFactory.createEmptyBorder());
        treeScroll.getVerticalScrollBar().setUI(new DarkScrollBarUI());
        treeScroll.setBackground(Colors.BACKGROUND_PANEL);
        leftPanel.add(leftHeader, BorderLayout.NORTH);
        leftPanel.add(treeScroll, BorderLayout.CENTER);

        JPanel centerPanel = new JPanel(new BorderLayout());
        centerPanel.setBackground(Colors.BACKGROUND_DEEPEST);
        centerPanel.add(createViewportToolbar(), BorderLayout.NORTH);
        centerPanel.add(viewportPanel, BorderLayout.CENTER);

        JPanel consolePanel = new JPanel(new BorderLayout());
        consolePanel.setBackground(Colors.BACKGROUND_PANEL);
        JPanel consoleHeader = new JPanel(new BorderLayout());
        consoleHeader.setBackground(Colors.BACKGROUND_RAISED);
        consoleHeader.setPreferredSize(new Dimension(0, DP28));
        consoleHeader.setBorder(new EmptyBorder(0, DP10, 0, DP10));
        JLabel consoleTitle = new JLabel(I18n.get("panel.output"));
        consoleTitle.setFont(UIManager.getFont("defaultFont").deriveFont(Font.BOLD, 10f));
        consoleTitle.setForeground(Colors.TEXT_MUTED);
        consoleHeader.add(consoleTitle, BorderLayout.WEST);
        JScrollPane consoleScroll = new JScrollPane(consoleArea);
        consoleScroll.setBorder(BorderFactory.createEmptyBorder());
        consoleScroll.getVerticalScrollBar().setUI(new DarkScrollBarUI());
        consoleScroll.setBackground(Colors.BACKGROUND_DEEPEST);
        consoleScroll.setPreferredSize(new Dimension(0, 160));
        consolePanel.add(consoleHeader, BorderLayout.NORTH);
        consolePanel.add(consoleScroll, BorderLayout.CENTER);

        JSplitPane verticalSplit = new JSplitPane(
            JSplitPane.VERTICAL_SPLIT, centerPanel, consolePanel);
        verticalSplit.setBorder(BorderFactory.createEmptyBorder());
        verticalSplit.setBackground(Colors.BACKGROUND_DEEPEST);
        verticalSplit.setDividerSize(2);
        verticalSplit.setResizeWeight(1.0);
        verticalSplit.setContinuousLayout(true);

        JPanel rightPanel = new JPanel(new BorderLayout());
        rightPanel.setBackground(Colors.BACKGROUND_PANEL);
        JPanel rightHeader = new JPanel(new BorderLayout());
        rightHeader.setBackground(Colors.BACKGROUND_RAISED);
        rightHeader.setPreferredSize(new Dimension(0, DP28));
        rightHeader.setBorder(new EmptyBorder(0, DP10, 0, DP10));
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

        JSplitPane horizontalSplit = new JSplitPane(
            JSplitPane.HORIZONTAL_SPLIT, leftPanel, verticalSplit);
        horizontalSplit.setBorder(BorderFactory.createEmptyBorder());
        horizontalSplit.setBackground(Colors.BACKGROUND_DEEPEST);
        horizontalSplit.setDividerSize(2);
        horizontalSplit.setResizeWeight(0);
        horizontalSplit.setContinuousLayout(true);

        JSplitPane mainSplit = new JSplitPane(
            JSplitPane.HORIZONTAL_SPLIT, horizontalSplit, rightPanel);
        mainSplit.setBorder(BorderFactory.createEmptyBorder());
        mainSplit.setBackground(Colors.BACKGROUND_DEEPEST);
        mainSplit.setDividerSize(2);
        mainSplit.setContinuousLayout(true);

        JPanel contentPanel = new JPanel(new BorderLayout());
        contentPanel.setBackground(Colors.BACKGROUND_DEEPEST);
        contentPanel.add(createTitleBar(), BorderLayout.NORTH);
        contentPanel.add(mainSplit, BorderLayout.CENTER);
        contentPanel.add(createStatusBar(), BorderLayout.SOUTH);
        setContentPane(contentPanel);

        SwingUtilities.invokeLater(() -> {
            horizontalSplit.setDividerLocation(224);
            mainSplit.setDividerLocation(getWidth() - DP240);
            verticalSplit.setDividerLocation(0.75);
        });
    }

    private JPanel createViewportToolbar() {
        JPanel toolbar = new JPanel(new FlowLayout(FlowLayout.LEFT, 2, 3));
        toolbar.setBackground(Colors.BACKGROUND_RAISED);
        toolbar.setPreferredSize(new Dimension(0, DP28));
        toolbar.setBorder(new EmptyBorder(0, DP4, 0, DP4));

        String[] toolNames = {I18n.get("viewport.tool.select"), I18n.get("viewport.tool.move"), I18n.get("viewport.tool.scale")};
        ButtonGroup toolGroup = new ButtonGroup();
        for (int i = 0; i < toolNames.length; i++) {
            JToggleButton toolButton = new JToggleButton(toolNames[i]);
            toolButton.setFont(UIManager.getFont("defaultFont").deriveFont(Font.PLAIN, 11f));
            toolButton.setFocusPainted(false);
            toolButton.setBorderPainted(false);
            toolButton.setBackground(Colors.BACKGROUND_RAISED);
            toolButton.setForeground(Colors.TEXT_SECONDARY);
            toolButton.setPreferredSize(new Dimension(52, 24));
            toolButton.setCursor(Cursor.getPredefinedCursor(Cursor.HAND_CURSOR));
            toolButton.setRolloverEnabled(true);
            if (i == 0) toolButton.setSelected(true);
            toolButton.addItemListener(e -> {
                toolButton.setBackground(toolButton.isSelected()
                    ? Colors.BACKGROUND_HOVER : Colors.BACKGROUND_RAISED);
                toolButton.setForeground(toolButton.isSelected()
                    ? Colors.BLUE : Colors.TEXT_SECONDARY);
            });
            toolGroup.add(toolButton);
            toolbar.add(toolButton);
        }
        toolbar.add(Box.createHorizontalStrut(DP8));
        JButton addBtn = new JButton("+");
        addBtn.setFont(UIManager.getFont("defaultFont").deriveFont(Font.BOLD, 13f));
        addBtn.setFocusPainted(false);
        addBtn.setBorderPainted(false);
        addBtn.setBackground(Colors.BACKGROUND_RAISED);
        addBtn.setForeground(Colors.TEXT_SECONDARY);
        addBtn.setPreferredSize(new Dimension(24, 24));
        addBtn.setCursor(Cursor.getPredefinedCursor(Cursor.HAND_CURSOR));
        addBtn.addActionListener(e -> createNewEntity());
        toolbar.add(addBtn);
        JButton delBtn = new JButton("-");
        delBtn.setFont(UIManager.getFont("defaultFont").deriveFont(Font.BOLD, 13f));
        delBtn.setFocusPainted(false);
        delBtn.setBorderPainted(false);
        delBtn.setBackground(Colors.BACKGROUND_RAISED);
        delBtn.setForeground(Colors.TEXT_SECONDARY);
        delBtn.setPreferredSize(new Dimension(24, 24));
        delBtn.setCursor(Cursor.getPredefinedCursor(Cursor.HAND_CURSOR));
        delBtn.addActionListener(e -> deleteSelectedEntity());
        toolbar.add(delBtn);
        return toolbar;
    }

    public void refreshInspector() {
        inspectorPanel.removeAll();
        if (selectedEntity == null) {
            JLabel emptyHint = new JLabel("  " + I18n.get("inspector.empty"));
            emptyHint.setFont(UIManager.getFont("defaultFont").deriveFont(Font.PLAIN, 12f));
            emptyHint.setForeground(Colors.TEXT_MUTED);
            emptyHint.setBorder(new EmptyBorder(DP10, DP10, DP10, DP10));
            inspectorPanel.add(emptyHint);
        } else {
            JLabel titleLabel = new JLabel("  " + selectedEntity.getName());
            titleLabel.setFont(UIManager.getFont("defaultFont").deriveFont(Font.BOLD, 12f));
            titleLabel.setForeground(Colors.TEXT_PRIMARY);
            titleLabel.setBorder(new EmptyBorder(DP8, DP8, DP4, DP8));
            inspectorPanel.add(titleLabel);
            JSeparator sep = new JSeparator();
            sep.setForeground(Colors.BORDER_LINE);
            sep.setBackground(Colors.BORDER_LINE);
            inspectorPanel.add(sep);
            addInspectorRow(I18n.get("inspector.id"), selectedEntity.getId());
            addInspectorRow(I18n.get("inspector.type"), selectedEntity.getType());
            addInspectorRow(I18n.get("inspector.name"), selectedEntity.getName());
            addInspectorRow(I18n.get("inspector.position"),
                String.format("%.1f, %.1f", selectedEntity.getX(), selectedEntity.getY()));
            addInspectorRow(I18n.get("inspector.size"),
                String.format("%.0f \u00D7 %.0f", selectedEntity.getWidth(), selectedEntity.getHeight()));
            inspectorPanel.add(Box.createVerticalStrut(DP8));
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
        row.setBorder(new EmptyBorder(DP4, DP12, DP4, DP12));
        row.setMaximumSize(new Dimension(9999, 24));
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
        row.setBorder(new EmptyBorder(1, DP10, 1, DP10));
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
            new EmptyBorder(1, DP4, 1, DP4)));
        field.setCursor(Cursor.getPredefinedCursor(Cursor.TEXT_CURSOR));
        String fixedKey;
        String labelText = label;
        if (labelText.equals("X") || labelText.equals("Y") ||
            labelText.equals(I18n.get("inspector.width")) || labelText.equals(I18n.get("inspector.height"))) {
            if (labelText.equals(I18n.get("inspector.width"))) fixedKey = "W";
            else if (labelText.equals(I18n.get("inspector.height"))) fixedKey = "H";
            else fixedKey = labelText;
        } else {
            fixedKey = labelText;
        }
        // FocusLost + Enter validates; won't break on partial input like "-" or "."
        field.addActionListener(e -> applyInspectorEdit(field, fixedKey));
        field.addFocusListener(new java.awt.event.FocusAdapter() {
            @Override
            public void focusLost(java.awt.event.FocusEvent e) { applyInspectorEdit(field, fixedKey); }
        });
        // Visual feedback on invalid input
        field.addKeyListener(new java.awt.event.KeyAdapter() {
            @Override
            public void keyReleased(java.awt.event.KeyEvent e) {
                try { Double.parseDouble(field.getText());
                    field.setForeground(Colors.TEXT_PRIMARY);
                    field.setBorder(BorderFactory.createCompoundBorder(
                        BorderFactory.createLineBorder(Colors.BORDER_LINE, 1),
                        new EmptyBorder(1, DP4, 1, DP4)));
                } catch (NumberFormatException ex) {
                    field.setForeground(Colors.RED);
                    field.setBorder(BorderFactory.createCompoundBorder(
                        BorderFactory.createLineBorder(Colors.RED, 1),
                        new EmptyBorder(1, DP4, 1, DP4)));
                }
            }
        });
        row.add(labelComp, BorderLayout.WEST);
        row.add(field, BorderLayout.CENTER);
        inspectorPanel.add(row);
    }

    private void loadDemoEntities() {
        entities.clear();
        cameraX = 0; cameraY = 0; cameraZoom = 1.0;
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
        entity.setX(x); entity.setY(y);
        entity.setWidth(w); entity.setHeight(h);
        entity.setColor(color); entity.setCircle(isCircle); entity.setPlayer(isPlayer);
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
        viewportPanel.animateEntityOut(toDelete);
        javax.swing.Timer delayedRemove = new javax.swing.Timer(160, ev -> {
            entities.remove(toDelete);
            for (int i = 0; i < treeRoot.getChildCount(); i++) {
                DefaultMutableTreeNode node = (DefaultMutableTreeNode) treeRoot.getChildAt(i);
                if (node.getUserObject() == toDelete) { treeRoot.remove(i); break; }
            }
            treeModel.reload();
            selectedEntity = null;
            refreshInspector();
            viewportPanel.repaint();
            updateStatusBar();
            logMessage(I18n.get("log.deleted"));
            ((javax.swing.Timer) ev.getSource()).stop();
        });
        delayedRemove.setRepeats(false);
        delayedRemove.start();
    }

    public void updateStatusBar() {
        if (statusLabel != null) {
            statusLabel.setText(String.format(
                "  %d " + I18n.get("status.entities") + " | " + I18n.get("status.camera") + ": %d, %d | " + I18n.get("status.zoom") + ": %.0f%%",
                entities.size(), (int) cameraX, (int) cameraY, cameraZoom * 100));
        }
        if (entityCountLabel != null) {
            entityCountLabel.setText(entities.size() + " " + I18n.get("status.entities"));
        }
    }

    public void logMessage(String message) {
        String timestamp = LocalTime.now().format(TIME_FMT);
        consoleArea.append("[" + timestamp + "] " + message + "\n");
        consoleArea.setCaretPosition(consoleArea.getDocument().getLength());
    }

    public void repaintSceneTree() { sceneTree.repaint(); }
    public List<Entity> getEntities() { return entities; }
    public Entity getSelectedEntity() { return selectedEntity; }
    public void setSelectedEntity(Entity e) { selectedEntity = e; }
    public double getCameraX() { return cameraX; }
    public double getCameraY() { return cameraY; }
    public double getCameraZoom() { return cameraZoom; }
    public void moveCamera(double dx, double dy) { cameraX += dx; cameraY += dy; }
    public void zoomCamera(double factor) { cameraZoom = Math.max(0.05, Math.min(20, cameraZoom * factor)); }

    private static final int RESIZE_MARGIN = 6;
    private int resizeDir = 0;
    private static final int R_NONE = 0, R_N = 1, R_S = 2, R_W = 4, R_E = 8;

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

    private void setupLanguageAndTheme() {
        I18n.setChangeListener(lang -> SwingUtilities.invokeLater(this::applyThemeAndLanguage));
        Theme.setChangeListener(p -> SwingUtilities.invokeLater(this::applyThemeAndLanguage));
        Colors.updateTheme();
    }

    private void applyThemeAndLanguage() {
        Colors.updateTheme();
        getContentPane().setBackground(Colors.BACKGROUND_DEEPEST);
        updateComponentTree(getContentPane());
        SwingUtilities.updateComponentTreeUI(this);
        langBtn.setText(getOppositeLang());
        themeBtn.setText(getOppositeTheme());
        refreshInspector();
        updateStatusBar();
        repaintSceneTree();
        viewportPanel.repaint();
        repaint();
    }

    private void updateComponentTree(Container container) {
        for (Component comp : container.getComponents()) {
            if (comp instanceof JPanel) { comp.setBackground(Colors.BACKGROUND_DEEPEST); }
            if (comp instanceof Container) { updateComponentTree((Container) comp); }
        }
    }

    private void applyInspectorEdit(JTextField field, String fixedKey) {
        if (selectedEntity == null) return;
        try {
            double v = Double.parseDouble(field.getText().trim());
            boolean changed = false;
            switch (fixedKey) {
                case "X" -> { selectedEntity.setX(v); changed = true; }
                case "Y" -> { selectedEntity.setY(v); changed = true; }
                case "W" -> { selectedEntity.setWidth(v); changed = true; }
                case "H" -> { selectedEntity.setHeight(v); changed = true; }
            }
            if (changed) { viewportPanel.repaint(); updateStatusBar(); }
            field.setForeground(Colors.TEXT_PRIMARY);
        } catch (NumberFormatException e) {
            // Keep old value, show red briefly
            field.setForeground(Colors.RED);
        }
    }

    private String getOppositeLang() {
        return I18n.getCurrentLang() == I18n.Lang.CHINESE ? I18n.get("lang.en") : I18n.get("lang.zh");
    }

    private String getOppositeTheme() {
        return switch (Theme.getCurrent()) {
            case DARK -> I18n.get("theme.dracula");
            case LIGHT -> I18n.get("theme.dark");
            case DRACULA -> I18n.get("theme.light");
        };
    }
}
