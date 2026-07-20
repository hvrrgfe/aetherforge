package com.aetherforge.util;

import javax.swing.*;
import java.awt.*;

public class EntityIcon implements Icon {
    private final Color color;
    private final int size;
    public EntityIcon(Color color, int size) { this.color=color; this.size=size; }
    @Override public void paintIcon(Component c, Graphics g, int x, int y) {
        Graphics2D g2 = (Graphics2D)g.create();
        g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
        g2.setColor(color);
        int cx=x+size/2, cy=y+size/2, h=(size-2)/2;
        g2.fillPolygon(new int[]{cx, cx+h, cx, cx-h}, new int[]{cy-h, cy, cy+h, cy}, 4);
        g2.dispose();
    }
    @Override public int getIconWidth() { return size; }
    @Override public int getIconHeight() { return size; }
}
