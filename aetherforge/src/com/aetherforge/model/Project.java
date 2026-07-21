package com.aetherforge.model;

import java.util.ArrayList;
import java.util.List;

/**
 * 项目模型 — 表示一个 AetherForge 游戏项目
 * 
 * 项目结构：
 *   my_game/
 *   ├── project.json          # 项目元数据
 *   ├── scenes/               # 场景文件
 *   │   └── main.scene
 *   ├── assets/               # 资源文件（图片、音频等）
 *   ├── scripts/              # Python 脚本
 *   ├── tests/                # 测试文件
 *   └── saves/                # 运行时存档
 */
public class Project {
    private String name;
    private String displayName;
    private String description;
    private String version = "1.0.0";
    private String author = "";
    private String rootPath;
    private int sceneCount;
    private long createdAt;
    private long modifiedAt;
    private List<String> recentScenes = new ArrayList<>();

    public Project() {}

    public Project(String name, String rootPath) {
        this.name = name;
        this.displayName = name;
        this.rootPath = rootPath;
        this.createdAt = System.currentTimeMillis();
        this.modifiedAt = this.createdAt;
    }

    // Getters & Setters
    public String getName() { return name; }
    public void setName(String name) { this.name = name; }
    public String getDisplayName() { return displayName; }
    public void setDisplayName(String displayName) { this.displayName = displayName; }
    public String getDescription() { return description; }
    public void setDescription(String description) { this.description = description; }
    public String getVersion() { return version; }
    public void setVersion(String version) { this.version = version; }
    public String getAuthor() { return author; }
    public void setAuthor(String author) { this.author = author; }
    public String getRootPath() { return rootPath; }
    public void setRootPath(String rootPath) { this.rootPath = rootPath; }
    public int getSceneCount() { return sceneCount; }
    public void setSceneCount(int sceneCount) { this.sceneCount = sceneCount; }
    public long getCreatedAt() { return createdAt; }
    public void setCreatedAt(long createdAt) { this.createdAt = createdAt; }
    public long getModifiedAt() { return modifiedAt; }
    public void setModifiedAt(long modifiedAt) { this.modifiedAt = modifiedAt; }
    public List<String> getRecentScenes() { return recentScenes; }
    public void setRecentScenes(List<String> recentScenes) { this.recentScenes = recentScenes; }

    public void markModified() { this.modifiedAt = System.currentTimeMillis(); }
}