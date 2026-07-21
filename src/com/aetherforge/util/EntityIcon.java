package com.aetherforge.util;

import javax.swing.*;
import java.awt.*;

public class EntityIcon implements Icon {
    private final Color color;
    private final int size;
    private final String entityType;
    public EntityIcon(Color color, int size) { this(color, size, ""); }
    public EntityIcon(Color color, int size, String entityType) {
        this.color=color; this.size=size; this.entityType=entityType;
    }
    @Override public void paintIcon(Component c, Graphics g, int x, int y) {
        Graphics2D g2 = (Graphics2D)g.create();
        g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
        g2.setColor(color);
        int cx=x+size/2, cy=y+size/2, h=(size-2)/2, s2=size/2;
        switch (entityType) {
            case "player" -> {
                // 圆形
                g2.fillOval(x, y, size, size);
                g2.setColor(new java.awt.Color(0,0,0,40));
                g2.fillOval(x+s2/2, y+s2/2, s2, s2);
            }
            case "enemy" -> {
                // 菱形（默认）
                g2.fillPolygon(new int[]{cx, cx+h, cx, cx-h}, new int[]{cy-h, cy, cy+h, cy}, 4);
            }
            case "npc" -> {
                // 方形
                g2.fillRoundRect(x+1, y+1, size-2, size-2, 3, 3);
            }
            case "object" -> {
                // 六边形（简化：圆角菱形）
                g2.fillRoundRect(x+2, y+2, size-4, size-4, 4, 4);
            }
            default -> {
                g2.fillPolygon(new int[]{cx, cx+h, cx, cx-h}, new int[]{cy-h, cy, cy+h, cy}, 4);
            }
        }
        g2.dispose();
    }
    @Override public int getIconWidth() { return size; }
    @Override public int getIconHeight() { return size; }
}
