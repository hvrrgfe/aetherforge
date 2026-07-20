package com.aetherforge.ui;

import com.aetherforge.model.*;
import com.aetherforge.util.Colors;
import com.aetherforge.util.EntityIcon;
import com.aetherforge.util.I18n;
import javax.swing.*;
import javax.swing.border.EmptyBorder;
import javax.swing.tree.*;
import java.awt.*;

/**
 * 场景控制器 — 管理场景树 + 实体 CRUD + 撤销/重做
 * 不直接操作 Viewport，通过 Scene 事件通知
 */
public class SceneController implements SceneListener {

    private final Scene scene;
    private final JTree tree;
    private final DefaultTreeModel treeModel;
    private final DefaultMutableTreeNode treeRoot;
    private final JPanel toolbar;

    public SceneController(Scene scene) {
        this.scene = scene;
        this.treeRoot = new DefaultMutableTreeNode(I18n.get("scene.root"));
        this.treeModel = new DefaultTreeModel(treeRoot);
        this.tree = new JTree(treeModel);
        this.toolbar = createToolbar();
        setupTree();
        scene.addListener(this);
    }

    public JTree getTree() { return tree; }
    public JPanel getToolbar() { return toolbar; }

    private void setupTree() {
        tree.setRootVisible(true);
        tree.setShowsRootHandles(true);
        tree.setBackground(Colors.bgPanel());
        tree.setForeground(Colors.textPrimary());
        tree.setFont(UIManager.getFont("defaultFont").deriveFont(Font.PLAIN, 13f));
        tree.setRowHeight(28);
        tree.setBorder(new EmptyBorder(4, 4, 4, 4));
        tree.setCellRenderer(new SceneTreeRenderer());
        tree.addTreeSelectionListener(e -> onTreeSelection(e));

        JPopupMenu popup = new JPopupMenu();
        popup.setBackground(Colors.bgRaised());
        popup.setBorder(BorderFactory.createLineBorder(Colors.borderLine()));
        JMenuItem addItem = new JMenuItem("+ " + I18n.get("tree.new"));
        addItem.setForeground(Colors.textPrimary());
        addItem.setBackground(Colors.bgRaised());
        addItem.addActionListener(e -> createEntity());
        popup.add(addItem);
        JMenuItem delItem = new JMenuItem(I18n.get("tree.delete"));
        delItem.setForeground(Colors.textPrimary());
        delItem.setBackground(Colors.bgRaised());
        delItem.addActionListener(e -> deleteSelected());
        popup.add(delItem);
        tree.setComponentPopupMenu(popup);
    }

    public void createEntity() {
        scene.executeCommand(new CreateEntityCommand(scene, "entity", I18n.get("entity.new")));
    }

    public void deleteSelected() {
        Entity sel = scene.getSelectedEntity();
        if (sel == null) return;
        scene.executeCommand(new DeleteEntityCommand(scene, sel));
    }

    public void undo() { scene.undo(); }
    public void redo() { scene.redo(); }

    private void onTreeSelection(javax.swing.event.TreeSelectionEvent e) {
        TreePath path = e.getNewLeadSelectionPath();
        if (path != null && path.getLastPathComponent() instanceof DefaultMutableTreeNode) {
            Object userObj = ((DefaultMutableTreeNode) path.getLastPathComponent()).getUserObject();
            if (userObj instanceof Entity) {
                scene.setSelectedEntity((Entity) userObj);
            }
        }
    }

    private JPanel createToolbar() {
        JPanel tb = new JPanel(new FlowLayout(FlowLayout.LEFT, 2, 2));
        tb.setBackground(Colors.bgRaised());
        tb.setPreferredSize(new Dimension(0, 24));

        JButton undoBtn = new JButton("\u2190");
        undoBtn.setFont(UIManager.getFont("defaultFont").deriveFont(Font.PLAIN, 12f));
        undoBtn.setFocusPainted(false); undoBtn.setBorderPainted(false);
        undoBtn.setContentAreaFilled(false);
        undoBtn.setForeground(Colors.textSecondary());
        undoBtn.setCursor(Cursor.getPredefinedCursor(Cursor.HAND_CURSOR));
        undoBtn.addActionListener(e -> undo());
        undoBtn.setToolTipText(I18n.get("log.undo"));

        JButton redoBtn = new JButton("\u2192");
        redoBtn.setFont(UIManager.getFont("defaultFont").deriveFont(Font.PLAIN, 12f));
        redoBtn.setFocusPainted(false); redoBtn.setBorderPainted(false);
        redoBtn.setContentAreaFilled(false);
        redoBtn.setForeground(Colors.textSecondary());
        redoBtn.setCursor(Cursor.getPredefinedCursor(Cursor.HAND_CURSOR));
        redoBtn.addActionListener(e -> redo());
        redoBtn.setToolTipText(I18n.get("log.redo"));

        tb.add(undoBtn);
        tb.add(redoBtn);
        return tb;
    }

    // ─── SceneListener ───

    @Override
    public void sceneChanged() {
        refreshTree();
    }

    @Override
    public void selectionChanged(Entity selected) {
        tree.repaint();
    }

    private void refreshTree() {
        treeRoot.removeAllChildren();
        for (Entity entity : scene.getEntities()) {
            DefaultMutableTreeNode node = new DefaultMutableTreeNode(entity);
            treeRoot.add(node);
        }
        treeModel.reload();
    }

    // ─── 树节点渲染器 ───

    // ─── 语言切换时刷新文本 ───

    public void refreshLanguage() {
        // Update tree root name
        treeRoot.setUserObject(I18n.get("scene.root"));
        treeModel.nodeChanged(treeRoot);
        // Rebuild popup
        JPopupMenu popup = new JPopupMenu();
        popup.setBackground(Colors.bgRaised());
        popup.setBorder(BorderFactory.createLineBorder(Colors.borderLine()));
        JMenuItem addItem = new JMenuItem("+ " + I18n.get("tree.new"));
        addItem.setForeground(Colors.textPrimary());
        addItem.setBackground(Colors.bgRaised());
        addItem.addActionListener(e -> createEntity());
        popup.add(addItem);
        JMenuItem delItem = new JMenuItem(I18n.get("tree.delete"));
        delItem.setForeground(Colors.textPrimary());
        delItem.setBackground(Colors.bgRaised());
        delItem.addActionListener(e -> deleteSelected());
        popup.add(delItem);
        tree.setComponentPopupMenu(popup);
        tree.repaint();
    }

    private class SceneTreeRenderer extends DefaultTreeCellRenderer {
        @Override
        public Component getTreeCellRendererComponent(JTree tree, Object value,
                boolean selected, boolean expanded, boolean leaf, int row, boolean hasFocus) {
            JLabel label = (JLabel) super.getTreeCellRendererComponent(
                tree, value, selected, expanded, leaf, row, false);
            label.setOpaque(true);
            boolean isSel = value instanceof DefaultMutableTreeNode
                && ((DefaultMutableTreeNode) value).getUserObject() instanceof Entity e
                && scene.isSelected(e);
            label.setBackground(isSel ? Colors.bgHover() : Colors.bgPanel());
            label.setForeground(isSel ? Colors.BLUE : Colors.textPrimary());
            label.setBorder(new EmptyBorder(2, 4, 2, 4));
            if (value instanceof DefaultMutableTreeNode) {
                Object userObj = ((DefaultMutableTreeNode) value).getUserObject();
                if (userObj instanceof Entity en) {
                    label.setIcon(new EntityIcon(en.getColor(), 8));
                } else {
                    label.setIcon(new EntityIcon(Colors.ORANGE, 8));
                }
            }
            if (hasFocus && isSel) {
                label.setBorder(BorderFactory.createCompoundBorder(
                    BorderFactory.createLineBorder(Colors.BLUE, 1), new EmptyBorder(1, 3, 1, 3)));
            }
            return label;
        }
    }
}
