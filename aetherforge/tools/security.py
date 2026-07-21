# -*- coding: utf-8 -*-
"""Security review module for AetherForge.

Provides code review checklists, model security validation,
and safety checks per the ai-code-framework guidelines.
"""
import os, re, json
from typing import Dict, List, Optional, Any
from pathlib import Path


def security_checklist() -> Dict[str, List[str]]:
    """Return the full security review checklist."""
    return {
        "code": [
            "Hardcoded secrets / API keys?",
            "SQL injection risk?",
            "User input validated and sanitized?",
            "Path traversal protection?",
            "Remote code execution risk?",
            "Dangerous eval/exec usage?",
        ],
        "model": [
            "Model source allowed?",
            "trust_remote_code=False?",
            "Safetensors format preferred?",
            "NSFW or unknown model warning?",
            "License checked?",
        ],
        "network": [
            "HTTPS only?",
            "Certificate verification enabled?",
            "Proxy credentials not in config file?",
            "Download size limits enforced?",
        ],
        "agent": [
            "Builder cannot commit?",
            "Evidence not forged by model?",
            "Verifier re-reads world state?",
            "Critic has independent context?",
        ],
    }


def validate_model_source(model_id: str) -> Dict:
    """Validate that a model source is trusted."""
    allowed_sources = {"huggingface.co", "hf-mirror.com"}
    blocked_patterns = [r"\.exe$", r"\.bat$", r"\.cmd$", r"\.dll$", r"\.so$", r"\.sh$"]

    is_allowed = any(src in model_id for src in allowed_sources)
    has_blocked = any(re.search(p, model_id) for p in blocked_patterns)

    issues = []
    if not is_allowed:
        issues.append("Model source not in allowed list: " + model_id)
    if has_blocked:
        issues.append("Model ID contains blocked extension pattern")

    return {
        "safe": is_allowed and not has_blocked,
        "issues": issues,
        "warnings": ["Use trust_remote_code=False when loading"] if is_allowed else [],
    }


def validate_file_security(file_path: str) -> Dict:
    """Check a downloaded file for security concerns."""
    path = Path(file_path)
    if not path.exists():
        return {"safe": False, "issues": ["File not found"]}

    suspicious_extensions = {".exe", ".bat", ".cmd", ".dll", ".so", ".dylib", ".sh", ".pyc"}
    ext = path.suffix.lower()

    issues = []
    if ext in suspicious_extensions:
        issues.append("Suspicious extension: " + ext)
    if path.stat().st_size > 30 * 1024 * 1024 * 1024:
        issues.append("File exceeds max size: " + str(path.stat().st_size) + " bytes")

    return {
        "safe": len(issues) == 0,
        "issues": issues,
        "size_bytes": path.stat().st_size,
        "extension": ext,
    }


def generate_security_report(checks: Dict[str, bool]) -> Dict:
    """Generate a structured security report."""
    passed = sum(1 for v in checks.values() if v)
    failed = sum(1 for v in checks.values() if not v)
    return {
        "passed": passed,
        "failed": failed,
        "total": len(checks),
        "checks": {k: {"passed": v} for k, v in checks.items()},
        "all_passed": failed == 0,
    }
