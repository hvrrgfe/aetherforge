package com.aetherforge.util;

import java.awt.Color;
import java.util.function.Consumer;
import com.formdev.flatlaf.FlatDarkLaf;
import com.formdev.flatlaf.FlatLightLaf;

/**
 * 主题系统 — 支持暗色/亮色/紫黑三种主题实时切换
 */
public final class Theme {
    private Theme() {}

    public enum Profile { DARK, LIGHT, DRACULA }
    private static Profile current = Profile.DARK;
    private static Consumer<Profile> listener;

    // ─── 暗色主题（Codex 风格，默认） ───
    public static final class Dark {
        static final Color BG0 = new Color(0x0a, 0x0a, 0x0a);
        static final Color BG1 = new Color(0x12, 0x12, 0x12);
        static final Color BG2 = new Color(0x18, 0x18, 0x18);
        static final Color BG3 = new Color(0x20, 0x20, 0x20);
        static final Color BG4 = new Color(0x28, 0x28, 0x28);
        static final Color T1  = new Color(0xe8, 0xe8, 0xe8);
        static final Color T2  = new Color(0x99, 0x99, 0x99);
        static final Color T3  = new Color(0x55, 0x55, 0x55);
        static final Color BORDER = new Color(0x20, 0x20, 0x20);
        static final Color GRID   = new Color(0x14, 0x14, 0x14);
        static final Color ORIGIN = new Color(0x2a, 0x2a, 0x2a);
        static final Color INPUT  = new Color(0x0c, 0x0c, 0x0c);
    }

    // ─── 亮色主题 ───
    public static final class Light {
        static final Color BG0 = new Color(0xf5, 0xf5, 0xf5);
        static final Color BG1 = new Color(0xea, 0xea, 0xea);
        static final Color BG2 = new Color(0xde, 0xde, 0xde);
        static final Color BG3 = new Color(0xd0, 0xd0, 0xd0);
        static final Color BG4 = new Color(0xc0, 0xc0, 0xc0);
        static final Color T1  = new Color(0x1a, 0x1a, 0x1a);
        static final Color T2  = new Color(0x55, 0x55, 0x55);
        static final Color T3  = new Color(0x88, 0x88, 0x88);
        static final Color BORDER = new Color(0xc0, 0xc0, 0xc0);
        static final Color GRID   = new Color(0xe0, 0xe0, 0xe0);
        static final Color ORIGIN = new Color(0xaa, 0xaa, 0xaa);
        static final Color INPUT  = new Color(0xff, 0xff, 0xff);
    }

    // ─── 紫黑主题（Dracula 风格） ───
    public static final class Dracula {
        static final Color BG0 = new Color(0x0d, 0x0c, 0x12);
        static final Color BG1 = new Color(0x16, 0x14, 0x1e);
        static final Color BG2 = new Color(0x1e, 0x1b, 0x2a);
        static final Color BG3 = new Color(0x28, 0x24, 0x36);
        static final Color BG4 = new Color(0x32, 0x2e, 0x42);
        static final Color T1  = new Color(0xf0, 0xea, 0xff);
        static final Color T2  = new Color(0xa8, 0x9b, 0xd8);
        static final Color T3  = new Color(0x6c, 0x5c, 0x8a);
        static final Color BORDER = new Color(0x28, 0x24, 0x36);
        static final Color GRID   = new Color(0x1a, 0x17, 0x24);
        static final Color ORIGIN = new Color(0x3a, 0x34, 0x50);
        static final Color INPUT  = new Color(0x0d, 0x0c, 0x12);
    }

    // ─── 当前主题颜色（通过静态方法访问） ───
    public static Color bg0()     { return pick(Dark.BG0, Light.BG0, Dracula.BG0); }
    public static Color bg1()     { return pick(Dark.BG1, Light.BG1, Dracula.BG1); }
    public static Color bg2()     { return pick(Dark.BG2, Light.BG2, Dracula.BG2); }
    public static Color bg3()     { return pick(Dark.BG3, Light.BG3, Dracula.BG3); }
    public static Color bg4()     { return pick(Dark.BG4, Light.BG4, Dracula.BG4); }
    public static Color text1()   { return pick(Dark.T1,  Light.T1,  Dracula.T1); }
    public static Color text2()   { return pick(Dark.T2,  Light.T2,  Dracula.T2); }
    public static Color text3()   { return pick(Dark.T3,  Light.T3,  Dracula.T3); }
    public static Color border()  { return pick(Dark.BORDER, Light.BORDER, Dracula.BORDER); }
    public static Color grid()    { return pick(Dark.GRID,   Light.GRID,   Dracula.GRID); }
    public static Color origin()  { return pick(Dark.ORIGIN, Light.ORIGIN, Dracula.ORIGIN); }
    public static Color inputBg() { return pick(Dark.INPUT,  Light.INPUT,  Dracula.INPUT); }

    // ─── 固定色（不随主题变化） ───
    public static final Color BLUE   = new Color(0x40, 0x80, 0xf0);
    public static final Color GREEN  = new Color(0x40, 0xd0, 0x80);
    public static final Color RED    = new Color(0xf0, 0x40, 0x70);
    public static final Color ORANGE = new Color(0xf0, 0xa0, 0x40);

    // 兼容旧 Colors 引用
    @Deprecated
    public static final Color BACKGROUND_DEEPEST  = new Color(0x0a, 0x0a, 0x0a);
    @Deprecated
    public static final Color BACKGROUND_DARK     = new Color(0x12, 0x12, 0x12);
    @Deprecated
    public static final Color BACKGROUND_PANEL    = new Color(0x18, 0x18, 0x18);

    private static Color pick(Color dark, Color light, Color dracula) {
        return switch (current) {
            case LIGHT   -> light;
            case DRACULA -> dracula;
            default      -> dark;
        };
    }

    public static Profile getCurrent() { return current; }

    public static void setTheme(Profile p) {
        current = p;
        try {
            switch (p) {
                case DARK    -> FlatDarkLaf.setup();
                case LIGHT   -> FlatLightLaf.setup();
                case DRACULA -> FlatDarkLaf.setup(); // Dracula via custom colors below
            }
        } catch (Exception ignored) {}
        if (listener != null) listener.accept(p);
    }

    public static void toggle() {
        Profile[] values = Profile.values();
        setTheme(values[(current.ordinal() + 1) % values.length]);
    }

    public static void setChangeListener(Consumer<Profile> l) { listener = l; }
}