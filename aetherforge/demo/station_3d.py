"""AetherForge 3D Demo - Rainy Station in 3D with physics and audio.

AI-native: all setup done via tools, no file editing.
"""
import sys, os
from aetherforge.api.engine_v2 import EngineToolsV2


def demo_3d_setup(tools):
    """Set up a 3D rainy station demo with physics and audio."""
    assert isinstance(tools, EngineToolsV2), "Need EngineToolsV2 for 3D demo"

    w = tools.world
    w._history.clear()

    # Init subsystems
    tools.init_physics()
    tools.init_audio()
    tools.init_image_gen()
    tools.init_music_gen()

    # Weather
    tools.set_weather("rainy")

    # === 3D Scene Setup ===
    tools.set_3d_camera(px=8, py=6, pz=12, tx=0, ty=0, tz=0, fov=60)

    tools.add_3d_light(light_type="directional", color="#ffffff",
                       intensity=1.2, px=10, py=20, pz=10, shadow=True)
    tools.add_3d_light(light_type="ambient", color="#222244",
                       intensity=0.4, px=0, py=0, pz=0)

    # === Entities ===
    # 1. Station building (3D)
    r = tools.create_entity(semantic_type="building", name="Waiting Room",
        description="Abandoned train station waiting room",
        position={"x": 0, "y": 2}, size={"width": 8, "height": 6},
        visual={"color": "#5a4a3a", "shape": "box"},
        capabilities=["enter", "inspect"])
    wr_id = r.data["entity_id"]
    tools.set_3d_mesh(wr_id, geometry="box", color="#5a4a3a",
                      roughness=0.9, metalness=0.0)
    tools.set_3d_transform(wr_id, x=0, y=0, z=0, sx=8, sy=4, sz=6)

    # 2. Roof / eaves
    r = tools.create_entity(semantic_type="roof", name="Station Eaves",
        description="Eaves providing shelter",
        position={"x": 0, "y": 5}, size={"width": 12, "height": 1},
        visual={"color": "#6a5a4a", "shape": "box"})
    roof_id = r.data["entity_id"]
    tools.set_3d_mesh(roof_id, geometry="box", color="#6a5a4a",
                      roughness=0.8, metalness=0.1)
    tools.set_3d_transform(roof_id, x=0, y=4.5, z=0, sx=12, sy=0.5, sz=7)

    # 3. Iron Door
    r = tools.create_entity(semantic_type="locked_door", name="Iron Door",
        description="Rusted iron door blocking entrance",
        capabilities=["open", "lock", "unlock", "inspect", "interact"],
        requires={"item": "station_key"},
        state={"locked": True, "open": False},
        position={"x": 4, "y": 0}, size={"width": 2, "height": 3},
        visual={"color": "#8a7a6a", "shape": "box"},
        editable_properties=["position", "state", "requires"])
    door_id = r.data["entity_id"]
    tools.set_3d_mesh(door_id, geometry="box", color="#8a7a6a",
                      roughness=0.7, metalness=0.3)
    tools.set_3d_transform(door_id, x=4.01, y=0.5, z=0, sx=0.3, sy=3, sz=2)

    # 4. Player
    r = tools.create_entity(semantic_type="player", name="Traveler",
        description="A traveler arriving at the station",
        capabilities=["move", "interact", "use", "inspect", "pick_up"],
        state={"inventory": [], "health": 100},
        position={"x": -5, "y": 0}, size={"width": 1, "height": 2},
        visual={"color": "#4488cc", "shape": "box"})
    pid = r.data["entity_id"]
    tools.set_player(pid)
    tools.set_3d_mesh(pid, geometry="capsule", color="#4488cc", roughness=0.5)
    tools.set_3d_transform(pid, x=-5, y=1, z=0, sx=0.8, sy=1.8, sz=0.8)
    tools.add_physics_body(pid, shape="circle", width=1, height=1,
                           mass=1.0, dynamic=True)

    # 5. Station Key
    r = tools.create_entity(semantic_type="key_item", name="Station Key",
        description="Rusted key that unlocks the iron door",
        capabilities=["pick_up", "use"],
        state={"picked_up": False},
        position={"x": -4, "y": 0}, size={"width": 0.5, "height": 0.5},
        visual={"color": "#ccaa44", "shape": "circle"},
        tags=["key", "important"])
    key_id = r.data["entity_id"]
    tools.set_3d_mesh(key_id, geometry="torus", color="#ccaa44",
                      metalness=0.8, roughness=0.2)
    tools.set_3d_transform(key_id, x=-4, y=0.3, z=0, sx=0.4, sy=0.4, sz=0.1)

    # 6. NPC
    r = tools.create_entity(semantic_type="npc", name="Vagrant",
        description="A homeless person sheltering at the station",
        capabilities=["talk", "inspect"],
        state={"mood": "anxious", "has_info": True},
        position={"x": 2, "y": 0}, size={"width": 1, "height": 2},
        visual={"color": "#cc8844", "shape": "box"})
    npc_id = r.data["entity_id"]
    tools.set_3d_mesh(npc_id, geometry="capsule", color="#cc8844", roughness=0.6)
    tools.set_3d_transform(npc_id, x=2, y=1, z=0, sx=0.8, sy=1.8, sz=0.8)

    # NPC Behavior
    from aetherforge.core import NPCBehavior, BehaviorType
    b = NPCBehavior(entity_id=npc_id, behavior_type=BehaviorType.GOAL_ORIENTED,
        goals=[{"condition": "weather.rain == true", "priority": 10,
                "action": "seek_shelter", "desc": "Find shelter when raining"},
               {"condition": "always", "priority": 1, "action": "wander",
                "desc": "Wander around when not raining"}],
        fallback_action="wander_near_station", speed=50.0)
    w.set_behavior(b)
    tools.add_physics_body(npc_id, shape="circle", width=1, height=1,
                           mass=1.0, dynamic=True)

    # === Rules ===
    tools.create_rule(when=["player.interacts_with(Station Key)"],
        then=["key.pick_up()", "player.inventory.add(Station Key)"])

    tools.create_rule(
        when=["player.interacts_with(Iron Door)",
              "player.inventory.contains(station_key)"],
        then=["door.unlock()", "door.open()"])

    # === Quest ===
    from aetherforge.core import Quest, QuestStep
    q = Quest(name="Enter the Waiting Room",
        description="Find the station key and open the iron door",
        steps=[QuestStep(step_id="find_key", description="Find the station key"),
               QuestStep(step_id="open_door", description="Open the iron door")],
        rewards=["access_to_waiting_room"])
    w.create_quest(q)

    # === Audio ===
    w.set_audio_config({
        "intent": "Atmospheric rainy station music",
        "mood": ["lonely", "suspenseful"],
        "layers": [{"name": "rain", "volume": 0.6}, {"name": "drone", "volume": 0.4}],
    })

    tools.commit_change()
    print(f"  3D Demo: Player={pid} Door={door_id} NPC={npc_id}")
    print("  3D Rainy Station ready. Open http://localhost:7890/viewer-3d")


def run_3d_demo():
    """Run the 3D demo standalone."""
    from aetherforge.core.world_model import WorldModel
    world = WorldModel()
    tools = EngineToolsV2(world)
    demo_3d_setup(tools)

    # Start runtime
    from aetherforge.runtime.game_loop import GameRuntime
    rt = GameRuntime(world)
    rt.start()
    return world, tools, rt


if __name__ == "__main__":
    run_3d_demo()
    print("3D demo ready. Run 'python -m aetherforge.main --demo-3d' for full server")
