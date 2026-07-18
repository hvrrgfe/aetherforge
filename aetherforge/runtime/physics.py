"""Physics Engine - 2D physics using pymunk (Chipmunk2D wrapper).

Supports: rigid bodies, collisions, gravity, forces, joints.
All physics objects are linked to world entities by entity_id.
"""
import math, sys
sys.path.insert(0, ".")
from aetherforge.config import get_config

class PhysicsEngine:
    """Manages physics simulation for the game world."""

    def __init__(self, world=None):
        self.world = world
        self._bodies = {}  # entity_id -> pymunk.Body
        self._shapes = {}  # entity_id -> pymunk.Shape
        self._constraints = []  # list of pymunk.Constraint
        self._space = None
        self._initialized = False
        self._disabled = False

    def init(self):
        cfg = get_config().physics
        if not cfg.enabled:
            self._disabled = True
            return
        try:
            import pymunk
            self._space = pymunk.Space()
            self._space.gravity = (cfg.gravity_x, cfg.gravity_y)
            self._space.collision_bias = 0.1
            self._initialized = True
        except ImportError:
            print("  [physics] pymunk not installed, physics disabled")
            self._disabled = True

    def tick(self, dt):
        if self._disabled or not self._initialized:
            return {}
        dt = min(dt, 0.033)  # cap to ~30fps min
        self._space.step(dt)
        # Sync pymunk body positions back to world entities
        updates = {}
        for eid, body in self._bodies.items():
            if body.body_type == 0:  # dynamic only
                ent = self.world.get_entity(eid) if self.world else None
                if ent:
                    ent.position["x"] = body.position.x
                    ent.position["y"] = body.position.y
                    updates[eid] = {"x": body.position.x, "y": body.position.y}
        return updates

    def add_body(self, entity_id, shape="box", width=32, height=32,
                 mass=1.0, dynamic=True, friction=0.5, elasticity=0.2,
                 position=None):
        if self._disabled or not self._initialized:
            return {"entity_id": entity_id, "success": False, "error": "Physics disabled"}

        import pymunk
        pos = position or {"x": 0, "y": 0}
        body_type = pymunk.Body.DYNAMIC if dynamic else pymunk.Body.STATIC

        body = pymunk.Body(mass, pymunk.moment_for_box(mass, (width, height)), body_type)
        body.position = (pos["x"], pos["y"])
        body.entity_id = entity_id  # tag for identification

        if shape == "circle":
            s = pymunk.Circle(body, max(width, height) / 2)
        else:
            s = pymunk.Poly.create_box(body, (width, height))

        s.friction = friction
        s.elasticity = elasticity
        s.collision_type = 1
        s.entity_id = entity_id

        self._space.add(body, s)
        self._bodies[entity_id] = body
        self._shapes[entity_id] = s
        return {"entity_id": entity_id, "success": True}

    def remove_body(self, entity_id):
        if entity_id in self._bodies:
            body = self._bodies.pop(entity_id)
            shape = self._shapes.pop(entity_id, None)
            if shape:
                self._space.remove(shape)
            self._space.remove(body)
            return True
        return False

    def apply_force(self, entity_id, fx, fy):
        body = self._bodies.get(entity_id)
        if body and body.body_type == 0:  # dynamic
            body.apply_impulse_at_local_point((fx, fy), (0, 0))
            return True
        return False

    def apply_force_at_world(self, entity_id, fx, fy, wx=0, wy=0):
        body = self._bodies.get(entity_id)
        if body and body.body_type == 0:
            body.apply_impulse_at_world_point((fx, fy), (wx, wy))
            return True
        return False

    def set_velocity(self, entity_id, vx, vy):
        body = self._bodies.get(entity_id)
        if body:
            body.velocity = (vx, vy)
            return True
        return False

    def set_gravity(self, gx, gy):
        if self._space:
            self._space.gravity = (gx, gy)
            return True
        return False

    def get_body_info(self, entity_id):
        body = self._bodies.get(entity_id)
        if not body:
            return None
        shape = self._shapes.get(entity_id)
        return {
            "entity_id": entity_id,
            "position": {"x": body.position.x, "y": body.position.y},
            "velocity": {"x": body.velocity.x, "y": body.velocity.y},
            "angle": body.angle,
            "angular_velocity": body.angular_velocity,
            "mass": body.mass,
            "is_dynamic": body.body_type == 0,
            "shape_type": type(shape).__name__ if shape else "unknown",
        }

    def ray_cast(self, start_x, start_y, end_x, end_y):
        """Cast a ray and return the first hit entity_id."""
        if self._disabled or not self._initialized:
            return None
        import pymunk
        info = self._space.segment_query_first((start_x, start_y), (end_x, end_y), 1, pymunk.ShapeFilter())
        if info and hasattr(info.shape, "entity_id"):
            return info.shape.entity_id
        return None

    def get_bodies_in_radius(self, cx, cy, radius):
        """Find all physics bodies within radius of a point."""
        results = []
        for eid, body in self._bodies.items():
            dx = body.position.x - cx
            dy = body.position.y - cy
            if math.sqrt(dx*dx + dy*dy) <= radius:
                results.append(eid)
        return results

    def cleanup(self):
        self._bodies.clear()
        self._shapes.clear()
        self._constraints.clear()
        self._space = None
        self._initialized = False
