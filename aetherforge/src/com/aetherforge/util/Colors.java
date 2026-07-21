package com.aetherforge.util;

import java.awt.Color;

/**
 * 颜色常量（直接委托 Theme，消除状态重复）
 * 所有方法实时读取 Theme 当前值，支持主题热切换
 */
public final class Colors {
    private Colors() {}

    // ─── 语义化颜色（委托 Theme） ───
    public static Color bgDeepest()   { return Theme.bg0(); }
    public static Color bgDark()      { return Theme.bg1(); }
    public static Color bgPanel()     { return Theme.bg2(); }
    public static Color bgRaised()    { return Theme.bg3(); }
    public static Color bgHover()     { return Theme.bg4(); }
    public static Color bgInput()     { return Theme.inputBg(); }
    public static Color textPrimary()   { return Theme.text1(); }
    public static Color textSecondary() { return Theme.text2(); }
    public static Color textMuted()     { return Theme.text3(); }
    public static Color borderLine()    { return Theme.border(); }
    public static Color gridLine()      { return Theme.grid(); }
    public static Color originLine()    { return Theme.origin(); }

    // ─── 实体颜色调色板 ───
    public static final Color[] ENTITY_PALETTE = {
        new Color(0x40, 0x80, 0xf0),
        new Color(0xf0, 0x40, 0x70),
        new Color(0x40, 0xd0, 0x80),
        new Color(0xf0, 0xa0, 0x40),
        new Color(0x30, 0xc0, 0x50),
        new Color(0xc0, 0x50, 0xf0),
        new Color(0xf0, 0xc0, 0x40),
        new Color(0x40, 0xe0, 0xe0),
    };

    // ─── 固定色 ───
    public static final Color BLUE   = Theme.BLUE;
    public static final Color GREEN  = Theme.GREEN;
    public static final Color RED    = Theme.RED;
    public static final Color ORANGE = Theme.ORANGE;
    public static final Color RESIZE_HANDLE  = new Color(0x33, 0x33, 0x33);
    public static final Color GLOW_OUTER     = new Color(0x40, 0x80, 0xf0, 40);
    public static final Color GLOW_INNER     = new Color(0x40, 0x80, 0xf0, 80);
    public static final Color HOVER_OVERLAY  = new Color(0x40, 0x80, 0xf0, 30);

    /** 兼容旧调用——空方法，Colors 现已直接委托 Theme */
    public static void updateTheme() { /* no-op: Colors now delegates to Theme */ }
}
