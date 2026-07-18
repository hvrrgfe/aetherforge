'''
Rainy Night Train Station - Demo vertical slice for AetherForge.
'''
def demo_setup(tools):
    results = []
    r = tools.set_weather('rainy'); results.append(r.success)

    w = tools.world
    w._history.clear()

    # Station building
    r = tools.create_entity(semantic_type='building', name='Waiting Room',
        description='Abandoned train station waiting room, door is locked',
        position={'x':500,'y':200}, size={'width':200,'height':180},
        visual={'color':'#5a4a3a','shape':'rectangle'}, capabilities=['enter','inspect'])
    results.append(r.success)
    wr_id = r.data['entity_id']

    # Roof (for shelter)
    r = tools.create_entity(semantic_type='roof', name='Station Eaves',
        description='Eaves outside waiting room, provides shelter from rain',
        position={'x':450,'y':100}, size={'width':300,'height':20},
        visual={'color':'#6a5a4a','shape':'rectangle'}, capabilities=['shelter'])
    results.append(r.success)

    # Locked door
    r = tools.create_entity(semantic_type='locked_door', name='Iron Door',
        description='Rusted iron door blocking entrance to waiting room',
        capabilities=['open','lock','unlock','inspect','interact'],
        requires={'item':'station_key'},
        state={'locked':True,'open':False},
        position={'x':500,'y':300}, size={'width':64,'height':16},
        visual={'color':'#8a7a6a','shape':'rectangle'},
        editable_properties=['position','state','requires'])
    results.append(r.success)
    door_id = r.data['entity_id']

    # Player
    r = tools.create_entity(semantic_type='player', name='Traveler',
        description='A traveler arriving at the abandoned station late at night',
        capabilities=['move','interact','use','inspect','pick_up'],
        state={'inventory':[],'health':100},
        position={'x':200,'y':400}, size={'width':28,'height':32},
        visual={'color':'#4488cc','shape':'rectangle'})
    results.append(r.success)
    pid = r.data['entity_id']
    tools.set_player(pid)

    # Station key
    r = tools.create_entity(semantic_type='key_item', name='Station Key',
        description='Rusted station key that can unlock the waiting room door',
        capabilities=['pick_up','use'], state={'picked_up':False},
        position={'x':100,'y':150}, size={'width':16,'height':16},
        visual={'color':'#ccaa44','shape':'circle'}, tags=['key','important'])
    results.append(r.success)

    # NPC with rain-seeking behavior
    r = tools.create_entity(semantic_type='npc', name='Vagrant',
        description='A homeless person sheltering at the station',
        capabilities=['talk','inspect'], state={'mood':'anxious','has_info':True},
        position={'x':350,'y':380}, size={'width':28,'height':32},
        visual={'color':'#cc8844','shape':'rectangle'})
    results.append(r.success)
    npc_id = r.data['entity_id']

    from aetherforge.core import NPCBehavior, BehaviorType, Rule, RuleTriggerType, Quest, QuestStep
    b = NPCBehavior(entity_id=npc_id, behavior_type=BehaviorType.GOAL_ORIENTED,
        goals=[{'condition':'weather.rain == true','priority':10,
                'action':'seek_shelter','desc':'Find shelter when raining'},
               {'condition':'always','priority':1,'action':'wander',
                'desc':'Wander around when not raining'}],
        fallback_action='wander_near_station', speed=50.0, perception_range=250.0)
    w.set_behavior(b)

    # Game rules
    from aetherforge.core import Rule, RuleTriggerType
    r = tools.create_rule(when=['player.interacts_with(Station Key)'],
        then=['key.pick_up()','player.inventory.add(Station Key)','key.state.picked_up=true'],
        trigger_type='interaction', priority=5)
    results.append(r.success)

    r = tools.create_rule(
        when=['player.interacts_with(Iron Door)','player.inventory.contains(station_key)'],
        then=['door.unlock()','door.open()','quest.find_key.complete()','music.intensity(0.3)'],
        else_actions=['dialogue.play(door_locked)','sound.play(metal_impact)'],
        trigger_type='interaction', priority=10)
    results.append(r.success)

    # Quest
    from aetherforge.core import Quest, QuestStep
    q = Quest(name='Enter the Waiting Room',
        description='Find the station key and open the iron door',
        steps=[QuestStep(step_id='find_key',description='Find the station key',
                         condition='player.inventory.contains(station_key)'),
               QuestStep(step_id='open_door',description='Open the iron door with key',
                         condition='door.state.open == true')],
        rewards=['access_to_waiting_room'])
    w.create_quest(q)

    # Audio config
    w.set_audio_config({'intent':'Atmospheric rainy station music',
        'mood':['lonely','suspenseful'],
        'layers':[{'name':'rain','volume':0.6},{'name':'drone','volume':0.4}]})

    tools.commit_change()

    print(f'  Rainy Station Demo Setup Complete')
    print(f'  Player: {pid} | Door: {door_id} | NPC: {npc_id}')
    all_ok = all(results)
    return all_ok
