package com.aetherforge.util;

import java.util.HashMap;
import java.util.Map;
import java.util.List;
import java.util.ArrayList;
import java.util.function.Consumer;

/**
 * 国际化支持 — 中/英双语实时切换
 */
public final class I18n {
    private I18n() {}

    public enum Lang { CHINESE, ENGLISH }
    private static Lang currentLang = Lang.CHINESE;
    private static final List<Consumer<Lang>> listeners = new ArrayList<>();

    private static final Map<String, String> ZH = new HashMap<>();
    private static final Map<String, String> EN = new HashMap<>();

    static {
        // ─── 界面元素 ───
        put("app.title",         "AetherForge Studio",            "AetherForge Studio");
        put("panel.explorer",    "资源管理器",                     "Explorer");
        put("panel.output",      "输出",                          "Output");
        put("panel.properties",  "属性",                          "Properties");
        put("scene.root",        "场景",                          "Scene");
        put("statusbar.ready",   "就绪",                          "Ready");
        put("viewport.tool.select", "选择",                      "Select");
        put("viewport.tool.move",   "移动",                      "Move");
        put("viewport.tool.scale",  "缩放",                      "Scale");

        // ─── 检查器 ───
        put("inspector.empty",   "未选中实体",                    "No selection");
        put("inspector.id",      "ID",                            "ID");
        put("inspector.type",    "类型",                          "Type");
        put("inspector.name",    "名称",                          "Name");
        put("inspector.position","位置",                          "Position");
        put("inspector.size",    "尺寸",                          "Size");
        put("inspector.transform","变换",                         "Transform");

        // ─── 场景树右键菜单 ───
        put("tree.new",          "新建实体",                      "New Entity");
        put("tree.delete",       "删除",                          "Delete");

        // ─── 控制台日志 ───
        put("log.ready",         "AetherForge Studio 已就绪",     "AetherForge Studio ready");
        put("log.created",       "创建实体",                      "Created entity");
        put("log.deleted",       "已删除实体",                    "Entity deleted");
        put("log.loaded",        "加载示例场景，共",              "Demo loaded,");
        put("log.entities",      "个实体",                        "entities");

        // ─── 状态栏 ───
        put("status.entities",   "实体",                          "entities");
        put("status.camera",     "相机",                          "Camera");
        put("status.zoom",       "缩放",                          "Zoom");

        // ─── 语言/主题 ───
        put("lang.zh",           "中文",                          "Chinese");
        put("lang.en",           "English",                       "English");
        put("theme.dark",        "暗色",                          "Dark");
        put("theme.light",       "亮色",                          "Light");
        put("inspector.width",    "宽",                          "Width");
        put("inspector.height",   "高",                          "Height");
        put("entity.player",      "玩家",                    "Player");
        put("entity.goblin",      "哥布林",             "Goblin");
        put("entity.merchant",    "商人",                    "Merchant");
        put("entity.chest",       "宝箱",                    "Chest");
        put("entity.oak",         "橡树",                    "Oak Tree");
        put("entity.new",         "新实体",             "New Entity");
        put("status.ready",       "  就绪",                  "Ready");
        put("theme.dracula",     "紫黑",                          "Dracula");
        put("log.undo",          "撤销",                          "Undo");
        put("log.redo",          "重做",                          "Redo");
        put("log.saved",         "已保存",                          "Scene saved");
        put("log.loaded2",       "已加载",                          "Scene loaded");
    }

    private static void put(String key, String zh, String en) {
        ZH.put(key, zh);
        EN.put(key, en);
    }

    public static String get(String key) {
        Map<String, String> map = (currentLang == Lang.CHINESE) ? ZH : EN;
        return map.getOrDefault(key, key);
    }

    public static Lang getCurrentLang() { return currentLang; }

    public static void setLang(Lang lang) {
        currentLang = lang;
        for (Consumer<Lang> l : listeners) l.accept(lang);
    }

    public static void toggle() {
        setLang(currentLang == Lang.CHINESE ? Lang.ENGLISH : Lang.CHINESE);
    }

    /** 注册语言变更回调（用于刷新 UI） */
    public static void addChangeListener(Consumer<Lang> l) { listeners.add(l); }
}