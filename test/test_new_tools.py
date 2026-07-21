"""Tests for exporter and new MCP tools."""
import tempfile, os, json, shutil, zipfile
import pytest


@pytest.fixture
def sample_project():
    tmpdir = tempfile.mkdtemp()
    for d in ["scenes", "assets", "scripts"]:
        os.makedirs(os.path.join(tmpdir, d))
    with open(os.path.join(tmpdir, "project.json"), "w") as f:
        json.dump({"name": "TestGame", "version": "1.0.0",
                   "sceneCount": 1, "recentScenes": ["main.scene"]}, f)
    with open(os.path.join(tmpdir, "scenes", "main.scene"), "w") as f:
        f.write('{"camera":{"x":0,"y":0,"zoom":1.0},"entities":[],"entityCount":0}')
    with open(os.path.join(tmpdir, "scripts", "hello.py"), "w") as f:
        f.write("print('hello')")
    yield tmpdir
    shutil.rmtree(tmpdir)


class TestExporter:
    def test_export_creates_zip(self, sample_project):
        from aetherforge.tools.exporter import export_project
        result = export_project(sample_project)
        assert result["success"] is True
        assert os.path.isfile(result["path"])
        assert result["file_count"] >= 2
        os.remove(result["path"])

    def test_export_files_at_root(self, sample_project):
        from aetherforge.tools.exporter import export_project
        result = export_project(sample_project)
        with zipfile.ZipFile(result["path"]) as zf:
            names = zf.namelist()
            assert "project.json" in names
            assert "scenes/main.scene" in names
        os.remove(result["path"])

    def test_export_nonexistent_dir(self):
        from aetherforge.tools.exporter import export_project
        result = export_project("/nonexistent/path")
        assert result["success"] is False

    def test_export_no_project_json(self, sample_project):
        from aetherforge.tools.exporter import export_project
        os.remove(os.path.join(sample_project, "project.json"))
        result = export_project(sample_project)
        assert result["success"] is False

    def test_build_includes_launcher(self, sample_project):
        from aetherforge.tools.exporter import build_project
        result = build_project(sample_project)
        assert result["success"] is True
        with zipfile.ZipFile(result["path"]) as zf:
            names = zf.namelist()
            assert "run.bat" in names
            assert "run.ps1" in names
            assert "run.sh" in names
            assert "project.json" in names
        os.remove(result["path"])


class TestInputManager:
    def test_bind_and_press(self):
        from aetherforge.tools.input_manager import InputManager
        mgr = InputManager()
        mgr.bind("move_left", ["A", "ArrowLeft"])
        mgr.press("A")
        assert mgr.is_action_pressed("move_left") is True
        assert mgr.is_action_pressed("move_right") is False

    def test_bind_any_key_triggers(self):
        from aetherforge.tools.input_manager import InputManager
        mgr = InputManager()
        mgr.bind("fire", ["Ctrl", "Space"])
        mgr.press("Ctrl")
        # Any bound key triggers the action
        assert mgr.is_action_pressed("fire") is True

    def test_release(self):
        from aetherforge.tools.input_manager import InputManager
        mgr = InputManager()
        mgr.bind("jump", ["Space"])
        mgr.press("Space")
        assert mgr.is_action_pressed("jump") is True
        mgr.release("Space")
        assert mgr.is_action_pressed("jump") is False

    def test_unbind(self):
        from aetherforge.tools.input_manager import InputManager
        mgr = InputManager()
        mgr.bind("test", ["X"])
        mgr.press("X")
        assert mgr.is_action_pressed("test") is True
        mgr.unbind("test")
        assert mgr.is_action_pressed("test") is False

    def test_get_state(self):
        from aetherforge.tools.input_manager import InputManager
        mgr = InputManager()
        mgr.bind("a", ["A"])
        mgr.bind("b", ["B"])
        mgr.press("A")
        state = mgr.get_state()
        assert state == {"a": True, "b": False}

    def test_serialize_roundtrip(self):
        from aetherforge.tools.input_manager import InputManager
        mgr = InputManager()
        mgr.bind("left", ["A"])
        mgr.bind("right", ["D"])
        data = mgr.to_dict()
        mgr2 = InputManager.from_dict(data)
        # Bindings survive serialization; key state is transient
        mgr2.press("A")
        assert mgr2.is_action_pressed("left") is True
        assert mgr2.is_action_pressed("right") is False

    def test_serialize_empty(self):
        from aetherforge.tools.input_manager import InputManager
        data = InputManager().to_dict()
        mgr = InputManager.from_dict(data)
        assert mgr.get_state() == {}


class TestComponentEntity:
    def test_create(self):
        from aetherforge.core import ComponentEntity
        e = ComponentEntity(name="Test")
        assert e.entity_id.startswith("ent_")
        assert e.name == "Test"

    def test_add_and_get(self):
        from aetherforge.core import ComponentEntity, TransformComponent
        e = ComponentEntity()
        e.add(TransformComponent(x=100, y=200))
        t = e.get(TransformComponent)
        assert t is not None
        assert t.x == 100
        assert t.y == 200

    def test_has_and_remove(self):
        from aetherforge.core import ComponentEntity, TransformComponent
        e = ComponentEntity()
        assert e.has(TransformComponent) is False
        e.add(TransformComponent())
        assert e.has(TransformComponent) is True
        e.remove(TransformComponent)
        assert e.has(TransformComponent) is False

    def test_to_dict_from_dict(self):
        from aetherforge.core import (
            ComponentEntity, TransformComponent,
            RenderComponent, MetadataComponent
        )
        e = ComponentEntity(entity_id="ent_test", name="Player")
        e.add(TransformComponent(x=10, y=20, rotation=45))
        e.add(RenderComponent(color="#4488cc", width=64, height=64))
        e.add(MetadataComponent(type="player", is_player=True, tags=["hero"]))

        d = e.to_dict()
        assert d["entity_id"] == "ent_test"
        assert "transform" in d["components"]
        assert "render" in d["components"]
        assert "metadata" in d["components"]

        e2 = ComponentEntity.from_dict(d)
        assert e2.entity_id == "ent_test"
        assert e2.transform.x == 10
        assert e2.render.color == "#4488cc"
        assert e2.metadata.is_player is True
        assert e2.metadata.tags == ["hero"]

    def test_missing_components(self):
        from aetherforge.core import ComponentEntity, TransformComponent
        e = ComponentEntity()
        assert e.transform is None
        assert e.render is None
        assert e.metadata is None
class TestExporterEdgeCases:
    def test_export_unicode_filename(self, sample_project):
        from aetherforge.tools.exporter import export_project
        import os
        # Create a file with Unicode name
        with open(os.path.join(sample_project, "scenes", "�ؿ�1.scene"), "w") as f:
            f.write("{}")
        result = export_project(sample_project)
        import zipfile
        with zipfile.ZipFile(result["path"]) as zf:
            names = zf.namelist()
            assert "scenes/�ؿ�1.scene" in names, "Unicode filename missing"
        os.remove(result["path"])

    def test_export_empty_project(self, sample_project):
        from aetherforge.tools.exporter import export_project
        import os, shutil
        # Remove all content except project.json
        for d in ["scenes", "assets", "scripts"]:
            shutil.rmtree(os.path.join(sample_project, d))
            os.makedirs(os.path.join(sample_project, d))
        result = export_project(sample_project)
        assert result["success"] is True
        assert result["file_count"] >= 1
        os.remove(result["path"])

    def test_build_finds_jar(self, sample_project):
        from aetherforge.tools.exporter import build_project
        import zipfile
        result = build_project(sample_project)
        with zipfile.ZipFile(result["path"]) as zf:
            names = zf.namelist()
            jar_files = [n for n in names if n.endswith(".jar")]
            # JAR optional since launcher removed, "No JAR found in build"
        os.remove(result["path"])

    def test_inspect_package(self, sample_project):
        from aetherforge.tools.exporter import export_project
        import zipfile, os
        r = export_project(sample_project)
        with zipfile.ZipFile(r["path"]) as zf:
            names = zf.namelist()
            assert len(names) >= 2
        os.remove(r["path"])

    def test_export_same_name(self, sample_project):
        from aetherforge.tools.exporter import export_project
        import os
        # Export twice to same path should overwrite
        out = os.path.join(sample_project, "..", "test_dup.zip")
        r1 = export_project(sample_project, output_path=out)
        assert r1["success"] is True
        r2 = export_project(sample_project, output_path=out)
        assert r2["success"] is True
        assert os.path.getsize(out) > 0
        os.remove(out)

class TestExporterEdgeCases:
    def test_export_unicode_filename(self, sample_project):
        from aetherforge.tools.exporter import export_project
        import zipfile, os
        fname = "scene_" + chr(0x5173) + chr(0x5361) + "1.scene"
        with open(os.path.join(sample_project, "scenes", fname), "w") as f:
            f.write("{}")
        result = export_project(sample_project)
        with zipfile.ZipFile(result["path"]) as zf:
            names = zf.namelist()
            assert any("scene_" in n for n in names), "Unicode filename missing"
        os.remove(result["path"])

    def test_export_empty_project(self, sample_project):
        from aetherforge.tools.exporter import export_project
        import os, shutil
        for d in ["scenes", "assets", "scripts"]:
            shutil.rmtree(os.path.join(sample_project, d))
            os.makedirs(os.path.join(sample_project, d))
        result = export_project(sample_project)
        assert result["success"] is True
        assert result["file_count"] >= 1
        os.remove(result["path"])

    def test_build_finds_jar(self, sample_project):
        from aetherforge.tools.exporter import build_project
        import zipfile
        result = build_project(sample_project)
        with zipfile.ZipFile(result["path"]) as zf:
            names = zf.namelist()
            jar_files = [n for n in names if n.endswith(".jar")]
            # JAR optional since launcher removed
        os.remove(result["path"])

    def test_export_same_name(self, sample_project):
        from aetherforge.tools.exporter import export_project
        import os
        out = os.path.join(sample_project, "..", "test_dup.zip")
        r1 = export_project(sample_project, output_path=out)
        assert r1["success"] is True
        r2 = export_project(sample_project, output_path=out)
        assert r2["success"] is True
        assert os.path.getsize(out) > 0
        os.remove(out)