"""Tests for tools/security.py"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

def test_security_checklist():
    from aetherforge.tools.security import security_checklist
    cl = security_checklist()
    assert "code" in cl
    assert "model" in cl
    assert "network" in cl
    assert "agent" in cl
    assert len(cl["code"]) >= 5
    print("  [PASS] test_security_checklist")

def test_validate_model_source_allowed():
    from aetherforge.tools.security import validate_model_source
    result = validate_model_source("https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0")
    assert result["safe"], str(result)
    print("  [PASS] test_validate_model_source_allowed")

def test_validate_model_source_blocked():
    from aetherforge.tools.security import validate_model_source
    result = validate_model_source("unknown-site.com/malicious-model")
    assert not result["safe"]
    assert len(result["issues"]) > 0
    print("  [PASS] test_validate_model_source_blocked")

def test_generate_security_report():
    from aetherforge.tools.security import generate_security_report
    report = generate_security_report({"check1": True, "check2": False})
    assert report["passed"] == 1
    assert report["failed"] == 1
    assert not report["all_passed"]
    print("  [PASS] test_generate_security_report")

if __name__ == "__main__":
    tests = [test_security_checklist, test_validate_model_source_allowed,
             test_validate_model_source_blocked, test_generate_security_report]
    passed = 0
    for t in tests:
        try:
            t()
            passed += 1
        except Exception as e:
            print(f"  [FAIL] {t.__name__}: {e}")
    print(f"\nResult: {passed}/{len(tests)} passed")
