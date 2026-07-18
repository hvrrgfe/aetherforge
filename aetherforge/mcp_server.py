"""
AetherForge MCP Server - Codex natively controls all engine tools.
All 22 tools, 5 resources, intelligent workflow execution.

Run: python -m aetherforge.mcp_server
"""
import json, sys, os, asyncio, traceback
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mcp.server import Server
from mcp.types import Tool, TextContent, CallToolResult, Resource, TextResourceContents
import mcp.server.stdio
from aetherforge.core.world_model import WorldModel
from aetherforge.config import get_config
from aetherforge.api.engine_v2 import EngineToolsV2 as EngineTools
from aetherforge.demo.station import demo_setup

world = WorldModel()
engine = EngineTools(world)
server = Server('aetherforge-engine')

# Auto-generated from EngineToolsV2??????

TOOL_DEFS = [
    Tool(name='create_entity', description='Create a semantically-described entity in the world',
         inputSchema={'type': 'object', 'properties': {
             'semantic_type': {'type': 'string', 'default': 'generic'},
             'name': {'type': 'string', 'default': ''},
             'description': {'type': 'string', 'default': ''},
             'capabilities': {'type': 'array', 'items': {'type': 'string'}, 'default': []},
             'state': {'type': 'object', 'default': {}},
             'position': {'type': 'object', 'default': {'x': 0, 'y': 0}},
             'visual': {'type': 'object', 'default': {'color': '#888', 'shape': 'rectangle'}},
             'tags': {'type': 'array', 'items': {'type': 'string'}, 'default': []},
         }}),
    Tool(name='modify_entity', description='Modify entity properties (position, state, visual, etc.)',
         inputSchema={'type': 'object', 'properties': {
             'entity_id': {'type': 'string'}, 'changes': {'type': 'object'},
         }, 'required': ['entity_id', 'changes']}),
    Tool(name='remove_entity', description='Remove an entity from the world',
         inputSchema={'type': 'object', 'properties': {'entity_id': {'type': 'string'}}, 'required': ['entity_id']}),
    Tool(name='get_entity', description='Get entity details by ID',
         inputSchema={'type': 'object', 'properties': {'entity_id': {'type': 'string'}}, 'required': ['entity_id']}),
    Tool(name='find_entities', description='Query entities by type/tag/capability. Example query: "type:locked_door"',
         inputSchema={'type': 'object', 'properties': {
             'query': {'type': 'string', 'default': '', 'description': 'Search query like type:npc or tag:key'}}}),
    Tool(name='create_rule', description='Create a declarative game rule with conditions and actions',
         inputSchema={'type': 'object', 'properties': {
             'when': {'type': 'array', 'items': {'type': 'string'}, 'default': []},
             'then': {'type': 'array', 'items': {'type': 'string'}, 'default': []},
             'else_actions': {'type': 'array', 'items': {'type': 'string'}, 'default': []},
             'trigger_type': {'type': 'string', 'default': 'interaction'},
             'priority': {'type': 'integer', 'default': 0},
         }}),
    Tool(name='remove_rule', description='Remove a game rule',
         inputSchema={'type': 'object', 'properties': {'rule_id': {'type': 'string'}}, 'required': ['rule_id']}),
    Tool(name='create_quest', description='Create a quest with steps',
         inputSchema={'type': 'object', 'properties': {
             'name': {'type': 'string', 'default': ''},
             'description': {'type': 'string', 'default': ''},
             'steps': {'type': 'array', 'items': {'type': 'object'}, 'default': []},
             'rewards': {'type': 'array', 'items': {'type': 'string'}, 'default': []},
         }}),
    Tool(name='complete_quest_step', description='Mark a quest step as completed',
         inputSchema={'type': 'object', 'properties': {
             'quest_id': {'type': 'string'}, 'step_id': {'type': 'string'},
         }, 'required': ['quest_id', 'step_id']}),
    Tool(name='update_quest_state', description='Update quest state (active/completed/failed)',
         inputSchema={'type': 'object', 'properties': {
             'quest_id': {'type': 'string'}, 'state': {'type': 'string'},
         }, 'required': ['quest_id', 'state']}),
    Tool(name='set_behavior', description='Set NPC behavior pattern (wander, goal_oriented, etc.)',
         inputSchema={'type': 'object', 'properties': {
             'entity_id': {'type': 'string'},
             'behavior_type': {'type': 'string', 'default': 'goal_oriented'},
             'goals': {'type': 'array', 'items': {'type': 'object'}, 'default': []},
             'fallback': {'type': 'string', 'default': 'idle'},
             'speed': {'type': 'number', 'default': 60.0},
         }, 'required': ['entity_id']}),
    Tool(name='set_weather', description='Set world weather (rainy, clear, etc.)',
         inputSchema={'type': 'object', 'properties': {'weather': {'type': 'string'}}, 'required': ['weather']}),
    Tool(name='set_player', description='Set which entity is controlled by the player',
         inputSchema={'type': 'object', 'properties': {'entity_id': {'type': 'string'}}, 'required': ['entity_id']}),
    Tool(name='read_project', description='Get complete project summary (entity/rule/quest counts, weather)',
         inputSchema={'type': 'object', 'properties': {}}),
    Tool(name='observe', description='Get full structured world snapshot with all entities, rules, quests, events',
         inputSchema={'type': 'object', 'properties': {}}),
    Tool(name='trigger_event', description='Trigger a game event - rules with matching conditions will fire',
         inputSchema={'type': 'object', 'properties': {
             'event_type': {'type': 'string'},
             'event_data': {'type': 'object', 'default': {}},
         }, 'required': ['event_type']}),
    Tool(name='set_audio', description='Configure semantic audio for the world',
         inputSchema={'type': 'object', 'properties': {'config': {'type': 'object'}}, 'required': ['config']}),
    Tool(name='set_art_intent', description='Set art generation intent for an asset',
         inputSchema={'type': 'object', 'properties': {'intent': {'type': 'object'}}, 'required': ['intent']}),
    Tool(name='commit_change', description='Commit all changes (checkpoints cleared, irreversible)',
         inputSchema={'type': 'object', 'properties': {}}),
    Tool(name='rollback_change', description='Rollback to the last checkpoint',
         inputSchema={'type': 'object', 'properties': {}}),
    Tool(name='save_project', description='Save project to a JSON file',
         inputSchema={'type': 'object', 'properties': {'path': {'type': 'string'}}, 'required': ['path']}),
    Tool(name='load_project', description='Load project from a JSON file',
         inputSchema={'type': 'object', 'properties': {'path': {'type': 'string'}}, 'required': ['path']}),
    Tool(name='load_demo', description='Load the Rainy Station demo project (6 entities, 2 rules, 1 quest)',
         inputSchema={'type': 'object', 'properties': {}}),
    Tool(name='run_tests', description='Run 5 automated tests: world_init, entity_create, rule_create, key_door, npc_behavior',
         inputSchema={'type': 'object', 'properties': {}}),
    Tool(name='execute_workflow', description='Execute a multi-step autonomous workflow. atomic=True means all-or-nothing rollback.',
         inputSchema={'type': 'object', 'properties': {
             'steps': {'type': 'array', 'items': {'type': 'object',
                 'properties': {'tool': {'type': 'string'}, 'args': {'type': 'object'},
                                'critical': {'type': 'boolean', 'default': False}},
             }, 'default': []},
             'auto_recover': {'type': 'boolean', 'default': True},
             'atomic': {'type': 'boolean', 'default': False, 'description': 'All-or-nothing: rollback all steps on any failure'},
         }}),

    # ========== V2 Tools: Physics ==========
    Tool(name='init_physics', description='Initialize physics engine',
         inputSchema={'type':'object','properties':{}}),
    Tool(name='add_physics_body', description='Add physics body to an entity',
         inputSchema={'type':'object','properties':{
             'entity_id':{'type':'string'},'shape':{'type':'string','default':'box'},
             'width':{'type':'number','default':32},'height':{'type':'number','default':32},
             'mass':{'type':'number','default':1.0},'dynamic':{'type':'boolean','default':True},
             'friction':{'type':'number','default':0.5},'elasticity':{'type':'number','default':0.2},
         },'required':['entity_id']}),
    Tool(name='remove_physics_body', description='Remove physics body from entity',
         inputSchema={'type':'object','properties':{'entity_id':{'type':'string'}},'required':['entity_id']}),
    Tool(name='apply_force', description='Apply force to a physics body',
         inputSchema={'type':'object','properties':{
             'entity_id':{'type':'string'},'fx':{'type':'number','default':0},'fy':{'type':'number','default':0},
         },'required':['entity_id']}),
    Tool(name='set_gravity', description='Set world gravity',
         inputSchema={'type':'object','properties':{'gx':{'type':'number','default':0},'gy':{'type':'number','default':980}}}),
    Tool(name='ray_cast', description='Cast a ray and find first hit entity',
         inputSchema={'type':'object','properties':{
             'start_x':{'type':'number'},'start_y':{'type':'number'},
             'end_x':{'type':'number'},'end_y':{'type':'number'},
         },'required':['start_x','start_y','end_x','end_y']}),
    Tool(name='get_physics_info', description='Get physics body info for an entity',
         inputSchema={'type':'object','properties':{'entity_id':{'type':'string'}},'required':['entity_id']}),
    # ========== V2 Tools: Audio ==========
    Tool(name='init_audio', description='Initialize audio engine',
         inputSchema={'type':'object','properties':{}}),
    Tool(name='load_sound', description='Register a sound file for AI access',
         inputSchema={'type':'object','properties':{'name':{'type':'string'},'file_path':{'type':'string'}},'required':['name','file_path']}),
    Tool(name='play_sound', description='Play a registered sound effect',
         inputSchema={'type':'object','properties':{
             'name':{'type':'string'},'volume':{'type':'number','default':1.0},
             'loops':{'type':'integer','default':0},'pan':{'type':'number','default':0},
         },'required':['name']}),
    Tool(name='play_music', description='Play background music with optional crossfade',
         inputSchema={'type':'object','properties':{
             'name':{'type':'string'},'file_path':{'type':'string','default':''},
             'volume':{'type':'number','default':0.7},'loop':{'type':'boolean','default':True},
             'fade_ms':{'type':'integer','default':0},
         },'required':['name']}),
    Tool(name='stop_music', description='Stop background music',
         inputSchema={'type':'object','properties':{'fade_ms':{'type':'integer','default':0}}}),
    Tool(name='set_audio_volume', description='Set audio volume levels',
         inputSchema={'type':'object','properties':{
             'master':{'type':'number','default':0.8},'music':{'type':'number','default':0.7},'sfx':{'type':'number','default':1.0}}}),
    Tool(name='get_audio_state', description='Get audio engine status',
         inputSchema={'type':'object','properties':{}}),
    # ========== V2 Tools: 3D ==========
    Tool(name='set_3d_mesh', description='Set 3D mesh for an entity',
         inputSchema={'type':'object','properties':{
             'entity_id':{'type':'string'},'geometry':{'type':'string','default':'box'},
             'color':{'type':'string','default':'#888888'},'texture':{'type':'string','default':''},
             'emissive':{'type':'string','default':'#000000'},'metalness':{'type':'number','default':0},
             'roughness':{'type':'number','default':0.8},'opacity':{'type':'number','default':1.0},
             'wireframe':{'type':'boolean','default':False},
         },'required':['entity_id']}),
    Tool(name='set_3d_transform', description='Set 3D transform (position, rotation, scale)',
         inputSchema={'type':'object','properties':{
             'entity_id':{'type':'string'},'x':{'type':'number','default':0},'y':{'type':'number','default':0},'z':{'type':'number','default':0},
             'rx':{'type':'number','default':0},'ry':{'type':'number','default':0},'rz':{'type':'number','default':0},
             'sx':{'type':'number','default':1},'sy':{'type':'number','default':1},'sz':{'type':'number','default':1},
         },'required':['entity_id']}),
    Tool(name='add_3d_light', description='Add a light to the 3D scene',
         inputSchema={'type':'object','properties':{
             'light_type':{'type':'string','default':'directional'},'color':{'type':'string','default':'#ffffff'},
             'intensity':{'type':'number','default':1.0},'px':{'type':'number','default':0},'py':{'type':'number','default':10},'pz':{'type':'number','default':10},
             'shadow':{'type':'boolean','default':False}}}),
    Tool(name='set_3d_camera', description='Set 3D camera',
         inputSchema={'type':'object','properties':{
             'px':{'type':'number','default':0},'py':{'type':'number','default':0},'pz':{'type':'number','default':10},
             'tx':{'type':'number','default':0},'ty':{'type':'number','default':0},'tz':{'type':'number','default':0},
             'fov':{'type':'number','default':60},'orthographic':{'type':'boolean','default':False}}}),
    Tool(name='get_3d_state', description='Get full 3D scene state for rendering',
         inputSchema={'type':'object','properties':{}}),
    # ========== V2 Tools: AI Image Gen ==========
    Tool(name='init_image_gen', description='Initialize AI image generation (anything-v5 / SD)',
         inputSchema={'type':'object','properties':{}}),
    Tool(name='generate_image', description='Generate image from text prompt',
         inputSchema={'type':'object','properties':{
             'prompt':{'type':'string'},'negative_prompt':{'type':'string','default':''},
             'width':{'type':'integer','default':512},'height':{'type':'integer','default':512},
             'steps':{'type':'integer','default':20},'guidance_scale':{'type':'number','default':7.5},
         },'required':['prompt']}),
    Tool(name='generate_texture', description='Generate a texture for game assets',
         inputSchema={'type':'object','properties':{
             'prompt':{'type':'string'},'entity_type':{'type':'string','default':'object'},
             'style':{'type':'string','default':'realistic'},'width':{'type':'integer','default':512},'height':{'type':'integer','default':512},
         },'required':['prompt']}),
    # ========== V2 Tools: AI Music Gen ==========
    Tool(name='init_music_gen', description='Initialize AI music generation',
         inputSchema={'type':'object','properties':{}}),
    Tool(name='generate_music', description='Generate music from text description',
         inputSchema={'type':'object','properties':{
             'description':{'type':'string'},'duration':{'type':'number','default':8.0},
         },'required':['description']}),
    Tool(name='generate_sound_effect', description='Generate sound effect from text description',
         inputSchema={'type':'object','properties':{
             'description':{'type':'string'},'duration':{'type':'number','default':2.0},
         },'required':['description']}),
    # ========== V2 Tools: Utility ==========
    Tool(name='list_generated_assets', description='List all AI-generated image and music assets',
         inputSchema={'type':'object','properties':{}}),
    Tool(name='get_engine_info', description='Get full engine status with all subsystems',
         inputSchema={'type':'object','properties':{}}),

    # ========== V2 Tools: Model Selection ==========
    Tool(name='list_image_models', description='List all available image generation models (local + HF cache + known)',
         inputSchema={'type':'object','properties':{}}),
    Tool(name='select_image_model', description='Switch image generation model by name or path. Examples: anything-v5, sdxl, D:/models/my-sd',
         inputSchema={'type':'object','properties':{
             'name_or_path':{'type':'string'},
         },'required':['name_or_path']}),
    Tool(name='list_music_models', description='List all available music generation models (local + HF cache + known)',
         inputSchema={'type':'object','properties':{}}),
    Tool(name='select_music_model', description='Switch music generation model by name or path. Examples: musicgen-medium, musicgen-large',
         inputSchema={'type':'object','properties':{
             'name_or_path':{'type':'string'},
         },'required':['name_or_path']}),

]

# ??? Tool dispatch ??????????????????????????????????????????

# Startup validation: ensure all TOOL_DEFS have implementations
SPECIAL_HANDLERS = {'load_demo', 'run_tests', 'execute_workflow'}
missing = [t.name for t in TOOL_DEFS if not hasattr(engine, t.name) and t.name not in SPECIAL_HANDLERS]
if missing:
    raise RuntimeError(f"Missing tool implementations: {missing}")
TOOL_MAP = {t.name: getattr(engine, t.name) for t in TOOL_DEFS if t.name not in SPECIAL_HANDLERS}
# ??? Special handlers ???????????????????????????????????????

async def handle_load_demo():
    ok = demo_setup(engine)
    return {'success': True, 'loaded': ok, 'summary': world.summary}

async def handle_run_tests():
    from aetherforge.test.test_runner import TestRunner
    from aetherforge.runtime.game_loop import GameRuntime
    rt = GameRuntime(world)
    runner = TestRunner(engine, rt)
    result = runner.run_all()
    return result.to_dict()

async def handle_execute_workflow(steps=None, auto_recover=True):
    if not steps:
        return {'success': False, 'error': 'No steps provided'}
    results = []
    world._checkpoint()
    for i, step in enumerate(steps):
        tn = step.get('tool')
        args = step.get('args', {})
        critical = step.get('critical', False)
        fn = TOOL_MAP.get(tn)
        if not fn:
            results.append({'step': i, 'tool': tn, 'success': False, 'error': 'Unknown tool', 'critical': critical})
            if critical and auto_recover:
                world.rollback()
                results.append({'step': i, 'action': 'rollback', 'success': True})
                break
            continue
        try:
            r = fn(**args)
            ok = r.success if hasattr(r, 'success') else True
            entry = {'step': i, 'tool': tn, 'success': ok, 'critical': critical}
            if hasattr(r, 'error') and r.error:
                entry['error'] = r.error
            if hasattr(r, 'data'):
                entry['data'] = str(r.data)[:100]
            results.append(entry)
            if not ok and critical and auto_recover:
                world.rollback()
                results.append({'step': i, 'action': 'rollback', 'success': True, 'reason': 'Critical step failed'})
                break
        except Exception as ex:
            results.append({'step': i, 'tool': tn, 'success': False, 'error': str(ex), 'critical': critical})
            if critical and auto_recover:
                world.rollback()
                results.append({'step': i, 'action': 'rollback', 'success': True, 'reason': str(ex)})
                break
    return {'success': True, 'steps_completed': len(results), 'results': results}

# MCP handlers?????????????????

@server.list_tools()
async def handle_list_tools():
    return TOOL_DEFS

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict):
    args = arguments or {}
    try:
        HEAVY_TOOLS = {'generate_image', 'generate_music', 'generate_texture'}
        if name == 'load_demo':
            result = await handle_load_demo()
        elif name == 'run_tests':
            result = await handle_run_tests()
        elif name == 'execute_workflow':
            result = await handle_execute_workflow(**args)
        elif name in TOOL_MAP:
            if name in HEAVY_TOOLS:
                result = await asyncio.to_thread(TOOL_MAP[name], **args)
            else:
                result = TOOL_MAP[name](**args)
            result = result.to_dict() if hasattr(result, 'to_dict') else result
        else:
            result = {'success': False, 'error': 'Unknown tool: ' + name}
        text = json.dumps(result, indent=2, ensure_ascii=False)
        return CallToolResult(content=[TextContent(type='text', text=text)])
    except Exception as ex:
        traceback.print_exc()
        return CallToolResult(content=[TextContent(type='text', text=json.dumps({'success': False, 'error': str(ex)}, indent=2))])

@server.list_resources()
async def handle_list_resources():
    return [
        Resource(uri='aetherforge://world/summary', name='World Summary', mimeType='application/json'),
        Resource(uri='aetherforge://world/snapshot', name='World Snapshot', mimeType='application/json'),
        Resource(uri='aetherforge://world/entities', name='All Entities', mimeType='application/json'),
        Resource(uri='aetherforge://world/rules', name='All Rules', mimeType='application/json'),
        Resource(uri='aetherforge://world/quests', name='All Quests', mimeType='application/json'),
    ]

@server.read_resource()
async def handle_read_resource(uri: str):
    m = {
        'aetherforge://world/summary': lambda: json.dumps(world.summary, indent=2, ensure_ascii=False),
        'aetherforge://world/snapshot': lambda: world.to_json(),
        'aetherforge://world/entities': lambda: json.dumps(
            {eid: e.to_dict() for eid, e in world.entities.items()}, indent=2, ensure_ascii=False),
        'aetherforge://world/rules': lambda: json.dumps(
            [r.to_dict() for r in world.rules.values()], indent=2, ensure_ascii=False),
        'aetherforge://world/quests': lambda: json.dumps(
            [q.to_dict() for q in world.quests.values()], indent=2, ensure_ascii=False),
    }
    fn = m.get(uri)
    if not fn:
        raise ValueError('Unknown resource: ' + uri)
    return TextResourceContents(uri=uri, mimeType='application/json', text=fn())

async def main():
    print('AetherForge MCP Server v2.0.0 started - waiting for MCP client...', flush=True)
    async with mcp.server.stdio.stdio_server() as (rs, ws):
        await server.run(rs, ws,
            mcp.server.models.InitializationOptions(
                server_name='aetherforge-engine',
                server_version=get_config().version,
                capabilities={},
            ),
        )

if __name__ == '__main__':
    asyncio.run(main())

