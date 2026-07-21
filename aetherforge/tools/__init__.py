# AetherForge tools layer (aliased from aetherforge.api.tools)
from aetherforge.api.tools import EngineTools, ToolResult

def validate_project_path(path: str) -> tuple:
    import os
    """Validate file path for project save/load operations.
    
    Returns (is_valid, error_message).
    Blocks path traversal and restricts to user home directory.
    """
    if not path or ".." in path:
        return False, "Path must not contain '..' (path traversal blocked)"
    norm = os.path.normpath(path)
    if not os.path.isabs(norm):
        return False, "Path must be absolute"
    try:
        abspath = os.path.abspath(norm)
        home = os.path.abspath(os.path.expanduser("~"))
        if not abspath.startswith(home):
            return False, "Path must be under user home directory: " + home
        return True, ""
    except Exception as ex:
        return False, f"Path validation error: {ex}"
