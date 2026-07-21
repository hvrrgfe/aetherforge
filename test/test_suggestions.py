"""Tests for agents/suggestions.py"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

def test_create_suggestion():
    from aetherforge.agents.suggestions import SuggestionManager
    mgr = SuggestionManager()
    sug = mgr.create_suggestion("user", {"type": "scene", "id": "village"}, "Add more NPCs", "improve_atmosphere", ["keep medieval style"])
    assert sug.author == "user"
    assert sug.status.value == "proposed"
    assert len(sug.constraints) == 1
    print("  [PASS] test_create_suggestion")

def test_generate_candidates():
    from aetherforge.agents.suggestions import SuggestionManager
    mgr = SuggestionManager()
    sug = mgr.create_suggestion("user", {"type": "scene", "id": "village"}, "Add market stalls")
    mgr.generate_candidates(sug)
    assert len(sug.candidates) >= 2
    assert any("方案A" in c.label for c in sug.candidates)
    assert any("方案B" in c.label for c in sug.candidates)
    print("  [PASS] test_generate_candidates")

def test_accept_suggestion():
    from aetherforge.agents.suggestions import SuggestionManager
    mgr = SuggestionManager()
    sug = mgr.create_suggestion("user", {"type": "entity"}, "Test")
    result = mgr.accept_suggestion(sug.id)
    assert result["status"] == "accepted"
    print("  [PASS] test_accept_suggestion")

def test_get_all():
    from aetherforge.agents.suggestions import SuggestionManager
    mgr = SuggestionManager()
    mgr.create_suggestion("u1", {}, "S1")
    mgr.create_suggestion("u2", {}, "S2")
    all_sugs = mgr.get_all()
    assert len(all_sugs) == 2
    print("  [PASS] test_get_all")

if __name__ == "__main__":
    for t in [test_create_suggestion, test_generate_candidates, test_accept_suggestion, test_get_all]:
        try:
            t()
        except Exception as e:
            print(f"  [FAIL] {t.__name__}: {e}")