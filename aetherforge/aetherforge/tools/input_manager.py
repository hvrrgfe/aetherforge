"""
Input Manager — unified input binding system for AetherForge.
"""
import json


class InputManager:
    """Manages action-to-key bindings and input state."""

    def __init__(self):
        self._bindings = {}
        self._state = {}
        self._keys_down = set()

    def bind(self, action, keys):
        if isinstance(keys, str):
            keys = [keys]
        self._bindings[action] = keys

    def unbind(self, action):
        self._bindings.pop(action, None)
        self._state.pop(action, None)

    def press(self, key):
        self._keys_down.add(key)
        self._update_state()

    def release(self, key):
        self._keys_down.discard(key)
        self._update_state()

    def _update_state(self):
        for action, keys in self._bindings.items():
            self._state[action] = any(k in self._keys_down for k in keys)

    def is_action_pressed(self, action):
        return self._state.get(action, False)

    def get_state(self):
        return dict(self._state)

    def to_dict(self):
        return {'bindings': dict(self._bindings), 'state': dict(self._state)}

    @classmethod
    def from_dict(cls, d):
        mgr = cls()
        mgr._bindings = dict(d.get('bindings', {}))
        return mgr