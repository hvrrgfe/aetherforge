'''
Game Runtime - drives the game loop, NPC AI, and physics.
'''
import math, random, sys
from aetherforge.core import BehaviorType

class GameRuntime:
    def __init__(self, world, checkpoint_interval=60):
        self.world = world
        self.paused = False
        self.time_scale = 1.0
        self._input = {'up':False,'down':False,'left':False,'right':False}
        self._npcs = {}
        self._checkpoint_interval = checkpoint_interval  # auto-checkpoint every N ticks
        self._tick_counter = 0

    def start(self):
        self.paused = False
        for eid, b in self.world.behaviors.items():
            self._npcs[eid] = {'target':None,'goal':None,'state':'idle','timer':0.0}

    def tick(self, dt):
        if self.paused:
            return self.world.snapshot()
        dt = dt * self.time_scale
        self.world.tick_world()
        self._tick_counter += 1
        if self._tick_counter % self._checkpoint_interval == 0:
            self.world.commit()
        self._move_player(dt)
        self._process_npcs(dt)
        return self.world.snapshot()

    def _move_player(self, dt):
        pid = self.world.player_entity_id
        if not pid:
            return
        p = self.world.get_entity(pid)
        if not p:
            return
        speed = 120.0
        dx = dy = 0.0
        inp = self._input
        if inp.get('left'): dx -= speed * dt
        if inp.get('right'): dx += speed * dt
        if inp.get('up'): dy -= speed * dt
        if inp.get('down'): dy += speed * dt
        if dx or dy:
            p.position['x'] += dx
            p.position['y'] += dy

    def set_player_input(self, **inputs):
        self._input.update(inputs)

    def player_interact(self):
        pid = self.world.player_entity_id
        if not pid:
            return {'success':False,'error':'No player'}
        p = self.world.get_entity(pid)
        if not p:
            return {'success':False,'error':'Player not found'}
        nearest = None
        nd = 80.0
        for eid, e in self.world.entities.items():
            if eid == pid:
                continue
            if 'interact' in e.capabilities or 'use' in e.capabilities:
                d = math.sqrt((p.position['x']-e.position['x'])**2 + (p.position['y']-e.position['y'])**2)
                if d < nd:
                    nearest, nd = e, d
        if not nearest:
            return {'success':False,'error':'Nothing nearby to interact with'}
        return {'success':True,'target':nearest.entity_id,'target_name':nearest.name}

    def _process_npcs(self, dt):
        for eid, b in self.world.behaviors.items():
            e = self.world.get_entity(eid)
            if not e:
                continue
            rs = self._npcs.setdefault(eid, {'target':None,'goal':None,'state':'idle','timer':0.0})
            if b.behavior_type == BehaviorType.WANDER:
                self._wander(e, b, rs, dt)
            elif b.behavior_type == BehaviorType.GOAL_ORIENTED:
                self._goal_oriented(e, b, rs, dt)

    def _wander(self, e, b, rs, dt):
        rs['timer'] -= dt
        if rs['timer'] <= 0:
            rs['target'] = {'x': e.position['x'] + random.uniform(-100, 100),
                            'y': e.position['y'] + random.uniform(-100, 100)}
            rs['timer'] = random.uniform(2.0, 5.0)
            rs['state'] = 'wandering'
        if rs.get('target'):
            self._move_toward(e, rs['target'], b.speed * 0.5, dt)
            if self._dist(e.position, rs['target']) < 10:
                rs['target'] = None
                rs['state'] = 'idle'

    def _goal_oriented(self, e, b, rs, dt):
        if not b.goals:
            self._wander(e, b, rs, dt)
            return
        if rs.get('goal') is None:
            for g in b.goals:
                cond = g.get('condition','')
                if 'weather.rain == true' in cond and self.world.weather == 'rainy':
                    rs['goal'] = g
                    break
            if rs.get('goal') is None:
                for g in b.goals:
                    if g.get('priority',0) > 0:
                        rs['goal'] = g
                        break
        g = rs.get('goal')
        if g:
            tid = g.get('target_id')
            action = g.get('action','move_to')
            if action == 'seek_shelter':
                shelters = self.world.find_entities(semantic_type='roof')
                if shelters:
                    nearest = min(shelters, key=lambda s: self._dist(e.position, s.position))
                    if self._dist(e.position, nearest.position) > 20:
                        self._move_toward(e, nearest.position, b.speed, dt)
                    else:
                        rs['goal'] = None
                        rs['state'] = 'sheltering'
                else:
                    rs['goal'] = None
            elif tid:
                t = self.world.get_entity(tid)
                if t and self._dist(e.position, t.position) > 20:
                    self._move_toward(e, t.position, b.speed, dt)
                else:
                    rs['goal'] = None
        elif b.fallback_action == 'wander_near_station':
            self._wander(e, b, rs, dt)
        else:
            rs['state'] = b.fallback_action

    def _move_toward(self, e, target, speed, dt):
        dx = target['x'] - e.position['x']
        dy = target['y'] - e.position['y']
        d = math.sqrt(dx*dx + dy*dy)
        if d > 1:
            e.position['x'] += (dx/d) * speed * dt
            e.position['y'] += (dy/d) * speed * dt

    def _dist(self, a, b):
        return math.sqrt((a['x']-b['x'])**2 + (a['y']-b['y'])**2)

    def pause(self):
        self.paused = True

    def resume(self):
        self.paused = False

    def set_time_scale(self, s):
        self.time_scale = max(0.1, min(10.0, s))
