package com.aetherforge.util;

import java.awt.Color;

/**
 * 颜色常量（支持主题切换 — 调用 updateTheme() 刷新）
 */
public final class Colors {
    private Colors() {}

    // 背景色（通过 updateTheme() 修改）
    private static Color BACKGROUND_DEEPEST   = new Color(0x0a, 0x0a, 0x0a);
    private static Color BACKGROUND_DARK      = new Color(0x12, 0x12, 0x12);
    private static Color BACKGROUND_PANEL     = new Color(0x18, 0x18, 0x18);
    private static Color BACKGROUND_RAISED    = new Color(0x20, 0x20, 0x20);
    private static Color BACKGROUND_HOVER     = new Color(0x28, 0x28, 0x28);
    private static Color BACKGROUND_INPUT     = new Color(0x0c, 0x0c, 0x0c);

    // 文字色
    private static Color TEXT_PRIMARY     = new Color(0xe8, 0xe8, 0xe8);
    private static Color TEXT_SECONDARY   = new Color(0x99, 0x99, 0x99);
    private static Color TEXT_MUTED       = new Color(0x55, 0x55, 0x55);

    // 边框和网格
    private static Color BORDER_LINE = new Color(0x20, 0x20, 0x20);
    private static Color GRID_LINE   = new Color(0x14, 0x14, 0x14);
    private static Color ORIGIN_LINE = new Color(0x2a, 0x2a, 0x2a);

    // 实体颜色调色板（在 Inspector 和 Entity 之间共享）
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

    // 固定色（引用 Theme 避免重复定义）
    public static final Color BLUE   = com.aetherforge.util.Theme.BLUE;
    public static final Color GREEN  = com.aetherforge.util.Theme.GREEN;
    public static final Color RED    = com.aetherforge.util.Theme.RED;
    public static final Color ORANGE = com.aetherforge.util.Theme.ORANGE;
    public static final Color RESIZE_HANDLE  = new Color(0x33, 0x33, 0x33);
    public static final Color GLOW_OUTER     = new Color(0x40, 0x80, 0xf0, 40);
    public static final Color GLOW_INNER     = new Color(0x40, 0x80, 0xf0, 80);
    public static final Color HOVER_OVERLAY  = new Color(0x40, 0x80, 0xf0, 30);

    /** 根据 Theme 刷新所有动态颜色 */
    public static void updateTheme() {
        BACKGROUND_DEEPEST = Theme.bg0();
        BACKGROUND_DARK    = Theme.bg1();
        BACKGROUND_PANEL   = Theme.bg2();
        BACKGROUND_RAISED  = Theme.bg3();
        BACKGROUND_HOVER   = Theme.bg4();
        BACKGROUND_INPUT   = Theme.inputBg();
        TEXT_PRIMARY   = Theme.text1();
        TEXT_SECONDARY = Theme.text2();
        TEXT_MUTED     = Theme.text3();
        BORDER_LINE = Theme.border();
        GRID_LINE   = Theme.grid();
        ORIGIN_LINE = Theme.origin();
    }

    // ─── Getters（工厂方法，不对外暴露可变字段） ───
    public static Color bgDeepest()   { return BACKGROUND_DEEPEST; }
    public static Color bgDark()      { return BACKGROUND_DARK; }
    public static Color bgPanel()     { return BACKGROUND_PANEL; }
    public static Color bgRaised()    { return BACKGROUND_RAISED; }
    public static Color bgHover()     { return BACKGROUND_HOVER; }
    public static Color bgInput()     { return BACKGROUND_INPUT; }
    public static Color textPrimary()   { return TEXT_PRIMARY; }
    public static Color textSecondary() { return TEXT_SECONDARY; }
    public static Color textMuted()     { return TEXT_MUTED; }
    public static Color borderLine()    { return BORDER_LINE; }
    public static Color gridLine()      { return GRID_LINE; }
    public static Color originLine()    { return ORIGIN_LINE; }
}