package com.aetherforge.model;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.JsonObject;
import java.io.IOException;
import java.io.PrintWriter;
import java.nio.file.*;

/**
 * 项目管理器 — 创建、打开、保存项目
 * 
 * 使用示例：
 *   ProjectManager pm = new ProjectManager();
 *   Project p = pm.createProject("MyGame", "D:/projects/my_game");
 *   pm.saveProject(p);
 *   Project loaded = pm.loadProject("D:/projects/my_game/project.json");
 */
public class ProjectManager {

    private static final Gson GSON = new GsonBuilder().setPrettyPrinting().create();

    /** 当前打开的项目 */
    private Project currentProject;

    public Project getCurrentProject() { return currentProject; }

    /**
     * 创建空白项目
     * @param name 项目名称
     * @param rootPath 项目根目录
     * @return 项目对象
     */
    public Project createProject(String name, String rootPath) throws IOException {
        Path root = Paths.get(rootPath);

        // 创建目录结构
        createDirectories(root);

        Project project = new Project(name, rootPath);

        // 创建默认主场景（空场景）
        String defaultScene = "{\n  \"camera\": { \"x\": 0, \"y\": 0, \"zoom\": 1.0 },\n  \"entities\": [],\n  \"entityCount\": 0\n}";
        Files.writeString(root.resolve("scenes").resolve("main.scene"), defaultScene, StandardOpenOption.CREATE, StandardOpenOption.TRUNCATE_EXISTING);
        project.getRecentScenes().add("main.scene");
        project.setSceneCount(1);

        // 保存 project.json
        saveProject(project);

        this.currentProject = project;
        return project;
    }

    /**
     * 加载项目
     * @param projectJsonPath 项目配置文件路径
     */
    public Project loadProject(String projectJsonPath) throws IOException {
        String json = Files.readString(Paths.get(projectJsonPath));
        this.currentProject = GSON.fromJson(json, Project.class);
        return currentProject;
    }

    /**
     * 保存项目元数据到 project.json
     */
    public void saveProject() throws IOException {
        if (currentProject == null) throw new IllegalStateException("No project open");
        saveProject(currentProject);
    }

    /**
     * 保存项目元数据到 project.json
     */
    public void saveProject(Project project) throws IOException {
        project.markModified();
        Path projectFile = Paths.get(project.getRootPath(), "project.json");
        Files.createDirectories(projectFile.getParent());
        Files.writeString(projectFile, GSON.toJson(project), StandardOpenOption.CREATE, StandardOpenOption.TRUNCATE_EXISTING);
    }

    /** 关闭当前项目 */
    public void closeProject() {
        this.currentProject = null;
    }

    // ─────────── 目录结构 ───────────

    public static final String[] PROJECT_DIRS = {
        "scenes", "assets", "scripts", "tests", "saves"
    };

    private void createDirectories(Path root) throws IOException {
        Files.createDirectories(root);
        for (String dir : PROJECT_DIRS) {
            Files.createDirectories(root.resolve(dir));
        }
        // 创建 .gitkeep 占位文件使空目录可追踪
        for (String dir : PROJECT_DIRS) {
            Path gitkeep = root.resolve(dir).resolve(".gitkeep");
            if (Files.notExists(gitkeep)) {
                Files.writeString(gitkeep, "");
            }
        }
    }

    /**
     * 获取场景文件的绝对路径
     */
    public Path getScenePath(String sceneName) {
        if (currentProject == null) return null;
        String fileName = sceneName.endsWith(".scene") ? sceneName : sceneName + ".scene";
        return Paths.get(currentProject.getRootPath(), "scenes", fileName);
    }

    /**
     * 获取项目有效路径
     */
    public Path resolve(String subPath) {
        if (currentProject == null) return null;
        return Paths.get(currentProject.getRootPath(), subPath);
    }
}