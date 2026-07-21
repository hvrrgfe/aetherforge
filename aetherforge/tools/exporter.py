"""Project Exporter — package AetherForge projects for distribution."""
import os
import json
import shutil
import zipfile
import tempfile
from datetime import datetime


def export_project(project_root, output_path=None, include_viewer=False):
    """
    Export a project into a distributable package.
    项目文件在 zip 中以根目录存放，不包含多余的父路径前缀。
    """
    project_root = os.path.normpath(project_root)
    if not os.path.isdir(project_root):
        return {"success": False, "error": "Directory not found: " + project_root}

    project_json = os.path.join(project_root, "project.json")
    if not os.path.isfile(project_json):
        return {"success": False, "error": "No project.json found in directory"}

    try:
        with open(project_json, "r", encoding="utf-8") as f:
            meta = json.load(f)
        name = meta.get("name", os.path.basename(project_root))
    except Exception:
        name = os.path.basename(project_root)

    if not output_path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(os.path.dirname(project_root), name + "_" + timestamp + ".zip")
    output_path = os.path.normpath(output_path)

    file_count = 0
    try:
        with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
            # Walk project_root and add files with arcname rooted at project_root
            for root, dirs, files in os.walk(project_root):
                dirs[:] = [d for d in dirs if not d.startswith('.')]
                for file in files:
                    if file.startswith('.'):
                        continue
                    full = os.path.join(root, file)
                    # arcname is relative to the project_root's PARENT,
                    # so the project folder becomes the zip root
                    arcname = os.path.relpath(full, project_root)
                    zf.write(full, arcname)
                    file_count += 1

            if include_viewer:
                _bundle_viewer(zf, project_root)

    except Exception as ex:
        return {"success": False, "error": str(ex)}

    size = os.path.getsize(output_path)
    return {
        "success": True,
        "path": output_path,
        "size": size,
        "file_count": file_count,
        "name": name,
    }


def build_project(project_root, output_path=None):
    """Build standalone package with embedded viewer."""
    return export_project(project_root, output_path, include_viewer=True)


def _bundle_viewer(zf, project_root):
    """Find and bundle the viewer JAR and launcher scripts."""
    import aetherforge
    pkg_dir = os.path.dirname(aetherforge.__file__)
    # Search for JAR relative to the aetherforge package
    jar_candidates = [
        os.path.normpath(os.path.join(pkg_dir, "..", "AetherForgeStudio-fat.jar")),
        os.path.normpath(os.path.join(pkg_dir, "..", "..", "AetherForgeStudio-fat.jar")),
    ]
    # Also search relative to project_root
    jar_candidates.append(os.path.normpath(os.path.join(project_root, "..", "AetherForgeStudio-fat.jar")))

    jar_found = None
    for p in jar_candidates:
        if os.path.isfile(p):
            jar_found = p
            break

    if jar_found:
        zf.write(jar_found, "_viewer/AetherForgeStudio-fat.jar")
    else:
        # Last resort: search PATH
        for base in [os.getcwd(), os.path.expanduser("~"), pkg_dir]:
            candidate = os.path.join(base, "AetherForgeStudio-fat.jar")
            if os.path.isfile(candidate):
                zf.write(candidate, "_viewer/AetherForgeStudio-fat.jar")
                jar_found = candidate
                break

    _add_launcher_scripts(zf, os.path.basename(project_root))
    return jar_found is not None


def _add_launcher_scripts(zf, project_name):
    """Add platform launcher scripts."""
    win = ("@echo off\r\nchcp 65001 >nul\r\n"
           "set JAR=%~dp0_viewer\\AetherForgeStudio-fat.jar\r\n"
           "if not exist \"%JAR%\" (\r\n"
           "    echo [ERROR] Viewer JAR not found!\r\n"
           "    pause & exit /b 1\r\n"
           ")\r\n"
           "echo === " + project_name + " ===\r\n"
           "java -cp \"%JAR%\" com.aetherforge.ui.GameViewer \"%~dp0project.json\"\r\n"
           "if errorlevel 1 pause\r\n")
    zf.writestr("run.bat", win)

    ps = ("$jar = Join-Path $PSScriptRoot \"_viewer\" \"AetherForgeStudio-fat.jar\"\r\n"
          "if (-not (Test-Path $jar)) {\r\n"
          "    Write-Host \"ERROR: Viewer JAR not found!\" -ForegroundColor Red\r\n"
          "    Read-Host \"Press Enter\" & exit 1\r\n"
          "}\r\n"
          "$proj = Join-Path $PSScriptRoot \"project.json\"\r\n"
          "Write-Host \"=== " + project_name + " ===\" -ForegroundColor Cyan\r\n"
          "java -cp $jar com.aetherforge.ui.GameViewer $proj\r\n"
          "if (-not $?) { Read-Host \"Press Enter\" }\r\n")
    zf.writestr("run.ps1", ps)

    sh = ("#!/bin/bash\n"
          "DIR=\"$(cd \"$(dirname \"$0\")\" && pwd)\"\n"
          "echo \"=== " + project_name + " ===\"\n"
          "JAR=\"$DIR/_viewer/AetherForgeStudio-fat.jar\"\n"
          'if [ ! -f "$JAR" ]; then\n'
          "    echo \"ERROR: Viewer JAR not found!\"\n"
          "    read -p \"Press Enter\"\n"
          "    exit 1\n"
          "fi\n"
          'java -cp "$JAR" com.aetherforge.ui.GameViewer "$DIR/project.json"\n')
    zf.writestr("run.sh", sh)