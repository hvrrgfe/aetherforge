'''
Rule Engine - evaluates declarative rules.
'''
from . import RuleTriggerType

class RuleEngine:
    def __init__(self, world):
        self.world = world
        self._cooldowns = {}

    def evaluate(self, event_type, event_data):
        tt = {
            'interaction': RuleTriggerType.INTERACTION,
            'proximity': RuleTriggerType.PROXIMITY,
            'state_change': RuleTriggerType.STATE_CHANGE,
            'quest_event': RuleTriggerType.QUEST_EVENT,
        }.get(event_type, RuleTriggerType.CUSTOM)
        matched = [r for r in self.world.rules.values()
                   if r.trigger_type == tt and r.enabled]
        matched.sort(key=lambda r: r.priority, reverse=True)
        results = []
        for rule in matched:
            if rule.cooldown > 0:
                last = self._cooldowns.get(rule.rule_id, -999.0)
                if (self.world.game_time - last) < rule.cooldown:
                    continue
            if self._all_true(rule.when, event_data):
                actions = rule.then
            elif rule.else_then:
                actions = rule.else_then
            else:
                continue
            results.append({'rule_id': rule.rule_id, 'actions': actions})
            if rule.cooldown > 0:
                self._cooldowns[rule.rule_id] = self.world.game_time
        return results

    def _all_true(self, conds, edata):
        if not conds:
            return True
        for c in conds:
            if not self._cond_true(c, edata):
                return False
        return True

    def _cond_true(self, c, edata):
        if '.interacts_with(' in c:
            pts = c.split('.interacts_with(')
            s, t = pts[0].strip(), pts[1].rstrip(')').strip().strip(chr(39))
            return edata.get('source') == s and edata.get('target') == t
        if '.inventory.contains(' in c:
            pts = c.split('.inventory.contains(')
            item = pts[1].rstrip(')').strip().strip(chr(39))
            ent = self.world.get_entity(pts[0].strip())
            return bool(ent and item in ent.state.get('inventory', []))
        if ' == ' in c:
            lhs, rhs = c.split(' == ', 1)
            lhs, rhs = lhs.strip(), rhs.strip().strip(chr(39))
            if '.state.' in lhs:
                eid, sk = lhs.split('.state.', 1)
                ent = self.world.get_entity(eid.strip())
                return bool(ent and str(ent.state.get(sk.strip())) == rhs)
        if ' == true' in c or ' == false' in c:
            lhs, rhs = c.split(' == ', 1)
            want = rhs.strip() == 'true'
            if '.state.' in lhs:
                eid, sk = lhs.split('.state.', 1)
                ent = self.world.get_entity(eid.strip())
                return bool(ent and ent.state.get(sk.strip()) == want)
        return True
