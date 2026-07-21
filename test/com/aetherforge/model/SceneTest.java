package com.aetherforge.model;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

/**
 * Scene 命令模式单元测试
 */
class SceneTest {
    private Scene scene;

    @BeforeEach
    void setUp() {
        scene = new Scene();
    }

    @Test
    void testAddEntity() {
        assertEquals(0, scene.getEntities().size());
        Entity e = new Entity("test", "Test");
        scene.addEntity(e);
        assertEquals(1, scene.getEntities().size());
        assertTrue(scene.getEntities().contains(e));
    }

    @Test
    void testRemoveEntity() {
        Entity e = new Entity("test", "Test");
        scene.addEntity(e);
        scene.removeEntity(e);
        assertEquals(0, scene.getEntities().size());
    }

    @Test
    void testSelection() {
        Entity e = new Entity("player", "Player");
        scene.addEntity(e);
        scene.setSelectedEntity(e);
        assertSame(e, scene.getSelectedEntity());
        scene.clearSelection();
        assertNull(scene.getSelectedEntity());
    }

    @Test
    void testUndoRedoCreate() {
        assertEquals(0, scene.getEntities().size());
        scene.executeCommand(new CreateEntityCommand(scene, "player", "Hero"));
        assertEquals(1, scene.getEntities().size());

        scene.undo();
        assertEquals(0, scene.getEntities().size());

        scene.redo();
        assertEquals(1, scene.getEntities().size());
    }

    @Test
    void testUndoRedoDelete() {
        Entity e = new Entity("test", "Test");
        scene.addEntity(e);
        assertEquals(1, scene.getEntities().size());

        scene.executeCommand(new DeleteEntityCommand(scene, e));
        assertEquals(0, scene.getEntities().size());

        scene.undo();
        assertEquals(1, scene.getEntities().size());

        scene.redo();
        assertEquals(0, scene.getEntities().size());
    }

    @Test
    void testMoveCommand() {
        Entity e = new Entity("test", "Test");
        e.setPosition(10, 20);
        scene.addEntity(e);
        scene.setSelectedEntity(e);

        scene.executeCommand(new MoveEntityCommand(scene, e, 10, 20, 100, 200));
        assertEquals(100.0, e.getX());
        assertEquals(200.0, e.getY());

        scene.undo();
        assertEquals(10.0, e.getX());
        assertEquals(20.0, e.getY());

        scene.redo();
        assertEquals(100.0, e.getX());
        assertEquals(200.0, e.getY());
    }

    @Test
    void testMaxUndoStack() {
        for (int i = 0; i < 150; i++) {
            scene.executeCommand(new CreateEntityCommand(scene, "e", "E" + i));
        }
        // 栈上限 100
        assertTrue(scene.canUndo());
        // 实际撤销次数受限于 MAX_UNDO
        int undoCount = 0;
        while (scene.canUndo()) {
            scene.undo();
            undoCount++;
        }
        assertEquals(100, undoCount);
    }

    @Test
    void testCameraOperations() {
        assertEquals(1.0, scene.getCameraZoom());
        scene.zoomCamera(2.0);
        assertEquals(2.0, scene.getCameraZoom());
        scene.moveCamera(50, 100);
        assertEquals(50.0, scene.getCameraX());
        assertEquals(100.0, scene.getCameraY());
        scene.resetCamera();
        assertEquals(0.0, scene.getCameraX());
        assertEquals(0.0, scene.getCameraY());
        assertEquals(1.0, scene.getCameraZoom());
    }

    @Test
    void testCameraClamp() {
        scene.setCameraZoom(100); // 应被 clamp 到 20
        assertEquals(20.0, scene.getCameraZoom());
        scene.setCameraZoom(-1); // 应被 clamp 到 0.05
        assertEquals(0.05, scene.getCameraZoom());
    }
}
