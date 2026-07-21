class WorldSnapshot:
    """A point-in-time snapshot of world state."""
    def __init__(self, revision=0, tick=0, entities=None, rules=None, quests=None, evidence_ids=None, timestamp=None):
        import time
        self.revision = revision
        self.tick = tick
        self.entities = entities or {}
        self.rules = rules or []
        self.quests = quests or []
        self.evidence_ids = evidence_ids or []
        self.timestamp = timestamp or time.time()


def diff_snapshots(snap_a, snap_b):
    """Compare two snapshot dicts, return structured diff."""
    if not snap_a or not snap_b:
        return {"entities_created": [], "entities_modified": []}
    created = [eid for eid in snap_b["entities"] if eid not in snap_a["entities"]]
    modified = [eid for eid in snap_b["entities"]
                if eid in snap_a["entities"] and snap_a["entities"][eid] != snap_b["entities"][eid]]
    return {"entities_created": created, "entities_modified": modified}


class SnapshotManager:
    """Manages world snapshots with auto-cleanup."""

    def __init__(self, max_snapshots=20):
        self._lock = __import__("threading").Lock()
        self._snapshots = []
        self._max_snapshots = max_snapshots

    def take(self, world):
        snapshot = {
            "revision": getattr(world, "revision", 0),
            "tick": getattr(world, "tick", 0),
            "entities": __import__("copy").deepcopy(getattr(world, "entities", {})),
            "rules": __import__("copy").deepcopy(getattr(world, "rules", {})),
            "quests": __import__("copy").deepcopy(getattr(world, "quests", {})),
            "timestamp": __import__("time").time(),
        }
        with self._lock:
            self._snapshots.append(snapshot)
            if len(self._snapshots) > self._max_snapshots:
                self._snapshots = self._snapshots[-self._max_snapshots:]
        return WorldSnapshot(**snapshot)

    def get_snapshot(self, revision):
        with self._lock:
            for s in reversed(self._snapshots):
                if s["revision"] == revision:
                    return s
        return None

    def diff(self, rev_a, rev_b):
        a = self.get_snapshot(rev_a)
        b = self.get_snapshot(rev_b)
        if not a or not b:
            return {"error": "Snapshot not found"}
        created = [eid for eid in b["entities"] if eid not in a["entities"]]
        modified = [eid for eid in b["entities"]
                    if eid in a["entities"] and a["entities"][eid] != b["entities"][eid]]
        return {"entities_created": created, "entities_modified": modified,
                "revision_a": rev_a, "revision_b": rev_b}

    def cleanup(self, keep_last=None):
        keep = keep_last or self._max_snapshots
        with self._lock:
            before = len(self._snapshots)
            if len(self._snapshots) > keep:
                self._snapshots = self._snapshots[-keep:]
            return before - len(self._snapshots)
