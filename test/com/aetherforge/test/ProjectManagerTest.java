package com.aetherforge.test;

import com.aetherforge.model.ProjectManager;
import com.aetherforge.model.Project;
import com.aetherforge.model.Scene;
import com.aetherforge.model.Entity;
import com.aetherforge.util.SceneSerializer;
import java.nio.file.*;

public class ProjectManagerTest {
    static int passed = 0, failed = 0;

    static void assertEq(Object expected, Object actual, String msg) {
        if (expected == null ? actual == null : expected.equals(actual)) { passed++; }
        else { failed++; System.err.println("FAIL: " + msg + " expected=" + expected + " actual=" + actual); }
    }
    static void assertTrue(boolean cond, String msg) {
        if (cond) passed++; else { failed++; System.err.println("FAIL: " + msg); }
    }

    public static void main(String[] args) throws Exception {
        testCreateProject();
        testSceneSerialization();
        testEntitySerialization();
        System.out.println("\nResults: " + passed + "/" + (passed + failed) + " passed");
        if (failed > 0) System.exit(1);
    }

    static void testCreateProject() throws Exception {
        String testRoot = Files.createTempDirectory("aftest_").toString();
        ProjectManager pm = new ProjectManager();
        Project p = pm.createProject("TestGame", testRoot);
        assertEq("TestGame", p.getName(), "name");
        assertTrue(Files.exists(Paths.get(testRoot, "project.json")), "project.json");
        assertTrue(Files.exists(Paths.get(testRoot, "scenes", "main.scene")), "main.scene");
        assertTrue(Files.exists(Paths.get(testRoot, "assets")), "assets");
        Project loaded = pm.loadProject(Paths.get(testRoot, "project.json").toString());
        assertEq("TestGame", loaded.getName(), "reload");
        Files.walk(Paths.get(testRoot)).sorted(java.util.Comparator.reverseOrder()).map(Path::toFile).forEach(java.io.File::delete);
        System.out.println("  PASS: testCreateProject");
    }

    static void testSceneSerialization() throws Exception {
        Scene scene = new Scene();
        scene.moveCamera(50, 100);
        Entity e = new Entity("player", "Hero");
        e.setPosition(100, 200); e.setColor(java.awt.Color.BLUE); e.setPlayer(true);
        scene.addEntity(e);
        String json = SceneSerializer.toJson(scene);
        Scene restored = SceneSerializer.fromJson(json);
        assertEq(1, restored.getEntities().size(), "entity count");
        assertEq("Hero", restored.getEntities().get(0).getName(), "name");
        assertEq(100.0, restored.getEntities().get(0).getX(), "x");
        assertTrue(restored.getEntities().get(0).isPlayer(), "player");
        System.out.println("  PASS: testSceneSerialization");
    }

    static void testEntitySerialization() throws Exception {
        Entity e = new Entity("npc", "Merchant");
        e.setPosition(300, 400); e.setWidth(48); e.setHeight(36);
        e.setColor(java.awt.Color.GREEN); e.setCircle(true);
        Scene scene = new Scene(); scene.addEntity(e);
        String json = SceneSerializer.toJson(scene);
        Entity r = SceneSerializer.fromJson(json).getEntities().get(0);
        assertEq("Merchant", r.getName(), "name");
        assertEq(300.0, r.getX(), "x"); assertEq(400.0, r.getY(), "y");
        assertEq(48.0, r.getWidth(), "w"); assertEq(36.0, r.getHeight(), "h");
        assertTrue(r.isCircle(), "circle"); assertEq("npc", r.getType(), "type");
        System.out.println("  PASS: testEntitySerialization");
    }
}