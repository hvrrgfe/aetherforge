"""AetherForge 3D Engine - Scene graph and 3D world state management.

Designed for Three.js rendering in the browser.
Python side manages scene graph and sends state to browser via REST API.
"""
import json, math, sys
sys.path.insert(0, ".")
from dataclasses import dataclass, field, asdict
from typing import Optional

@dataclass
class Vector3:
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    def to_dict(self):
        return {"x": self.x, "y": self.y, "z": self.z}

@dataclass
class Transform3D:
    position: Vector3 = field(default_factory=Vector3)
    rotation: Vector3 = field(default_factory=lambda: Vector3(0, 0, 0))  # euler angles
    scale: Vector3 = field(default_factory=lambda: Vector3(1, 1, 1))

    def to_dict(self):
        return {"position": self.position.to_dict(),
                "rotation": self.rotation.to_dict(),
                "scale": self.scale.to_dict()}

@dataclass
class MeshData:
    geometry: str = "box"  # box, sphere, plane, cylinder, torus, custom
    color: str = "#888888"
    texture: str = ""  # texture URL or generated asset name
    emissive: str = "#000000"
    metalness: float = 0.0
    roughness: float = 0.8
    transparent: bool = False
    opacity: float = 1.0
    wireframe: bool = False
    custom_geometry: dict = field(default_factory=dict)  # for GLTF/obj references

    def to_dict(self):
        return asdict(self)

@dataclass
class Light3D:
    light_type: str = "directional"  # directional, point, spot, ambient
    color: str = "#ffffff"
    intensity: float = 1.0
    position: Vector3 = field(default_factory=lambda: Vector3(0, 10, 10))
    target: str = ""  # entity_id to target
    shadow: bool = False

    def to_dict(self):
        d = asdict(self)
        d["position"] = self.position.to_dict()
        return d

@dataclass
class Camera3D:
    position: Vector3 = field(default_factory=lambda: Vector3(0, 0, 10))
    target: Vector3 = field(default_factory=Vector3)
    fov: float = 60.0
    near: float = 0.1
    far: float = 1000.0
    orthographic: bool = False
    zoom: float = 1.0

    def to_dict(self):
        return {"position": self.position.to_dict(),
                "target": self.target.to_dict(),
                "fov": self.fov, "near": self.near, "far": self.far,
                "orthographic": self.orthographic, "zoom": self.zoom}


class SceneGraph3D:
    """Manages 3D scene state - meshes, lights, camera, animations."""

    def __init__(self, world=None):
        self.world = world
        self.meshes = {}  # entity_id -> MeshData
        self.transforms = {}  # entity_id -> Transform3D
        self.lights = []  # list of Light3D
        self.camera = Camera3D()
        self.ambient_light_color = "#222233"
        self.ambient_light_intensity = 0.3
        self.fog_color = "#1a1a22"
        self.fog_density = 0.02

    def set_mesh(self, entity_id, mesh_data):
        if isinstance(mesh_data, dict):
            mesh_data = MeshData(**mesh_data)
        self.meshes[entity_id] = mesh_data
        return entity_id

    def set_transform(self, entity_id, transform):
        if isinstance(transform, dict):
            transform = Transform3D(
                position=Vector3(**transform.get("position", {})),
                rotation=Vector3(**transform.get("rotation", {})),
                scale=Vector3(**transform.get("scale", {})),
            )
        self.transforms[entity_id] = transform
        return entity_id

    def get_transform(self, entity_id):
        """Get effective transform (scene graph or entity position)."""
        if entity_id in self.transforms:
            return self.transforms[entity_id]
        # Fall back to world entity position
        if self.world:
            ent = self.world.get_entity(entity_id)
            if ent and hasattr(ent, "position"):
                return Transform3D(
                    position=Vector3(ent.position.get("x", 0),
                                     ent.position.get("y", 0), 0))
        return Transform3D()

    def add_light(self, light):
        if isinstance(light, dict):
            pos = light.pop("position", {})
            light["position"] = Vector3(**pos) if isinstance(pos, dict) else Vector3()
            light = Light3D(**light)
        self.lights.append(light)
        return len(self.lights) - 1

    def set_camera(self, camera):
        if isinstance(camera, dict):
            pos = camera.pop("position", {})
            tgt = camera.pop("target", {})
            camera["position"] = Vector3(**pos) if isinstance(pos, dict) else Vector3()
            camera["target"] = Vector3(**tgt) if isinstance(tgt, dict) else Vector3()
            camera = Camera3D(**camera)
        self.camera = camera
        return True

    def get_3d_state(self):
        """Full 3D scene state for browser rendering."""
        entities_3d = []
        for eid in (self.meshes.keys() | (self.world.entities.keys() if self.world else set())):
            mesh = self.meshes.get(eid)
            tf = self.get_transform(eid)
            ent = self.world.get_entity(eid) if self.world else None
            info = {
                "id": eid,
                "name": ent.name if ent else "",
                "type": ent.semantic_type if ent else "",
                "transform": tf.to_dict(),
            }
            if mesh:
                info["mesh"] = mesh.to_dict()
            entities_3d.append(info)

        return {
            "entities": entities_3d,
            "lights": [l.to_dict() for l in self.lights],
            "camera": self.camera.to_dict(),
            "ambient": {"color": self.ambient_light_color,
                        "intensity": self.ambient_light_intensity},
            "fog": {"color": self.fog_color, "density": self.fog_density},
        }

    def to_json(self):
        return json.dumps(self.get_3d_state(), indent=2, ensure_ascii=False)
