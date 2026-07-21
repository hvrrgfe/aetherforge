package com.aetherforge.util;

import javax.swing.*;
import javax.swing.plaf.basic.BasicScrollBarUI;
import java.awt.*;

public class DarkScrollBarUI extends BasicScrollBarUI {
    @Override protected void configureScrollBarColors() {
        thumbColor = Colors.bgHover();
        trackColor = Colors.bgDeepest();
    }
    @Override protected JButton createDecreaseButton(int o) { return zero(); }
    @Override protected JButton createIncreaseButton(int o) { return zero(); }
    private static JButton zero() {
        JButton b = new JButton(); b.setPreferredSize(new Dimension(0,0)); return b;
    }
    @Override protected void paintThumb(Graphics g, JComponent c, Rectangle r) {
        Graphics2D g2 = (Graphics2D)g.create();
        g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
        g2.setColor(thumbColor);
        g2.fillRoundRect(r.x+2, r.y+2, r.width-4, r.height-4, 4, 4);
        g2.dispose();
    }
    @Override protected void paintTrack(Graphics g, JComponent c, Rectangle r) {}
}
