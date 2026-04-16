# Gemini Project Guidelines

This file defines the foundational mandates for Gemini CLI within this project. These instructions take absolute precedence over general workflows.

## Environment & Setup
- **OS:** Windows 11 (Use PowerShell or Command Prompt syntax as appropriate, but prefer Python-native paths).
- **Venv:** The virtual environment is located in the project root (`Lib/`, `Scripts/`, `Include/`). Always ensure it is active or use the full path to the interpreter if running scripts.
- **Python:** strictly follow **PEP 8**.

## Core Mandates
- **Version Control:** 
  - **Always git commit before making changes.** Create a checkpoint of the current state.
  - **Bump VERSION in `config.py`** on every commit using semantic versioning (patch for fixes, minor for features, major for breaking changes).
  - Use descriptive "why"-focused commit messages.
- **Path Handling:** Use `pathlib.Path` for all file operations to ensure cross-platform compatibility.
- **Code Style:**
  - Follow PEP8
  - Prefer modular files instead of large 1 file type solutions.
  - Snake_case for functions and variables.
  - PascalCase for classes.
  - Use type hints for all function signatures.
  - Organize imports: Standard Library, Third-party, Local (separated by blank lines).
  - Explain the "why" in comments, not just the "what".

## Development Workflow
1. **Research:** Map dependencies across `scene.py`, `shapes.py`, and `main_window.py`.
2. **Strategy:** Define the change and the version bump level (patch/minor/major).
3. **Execution:**
   - Modify code following PEP 8.
   - Update `config.py` version.
   - **Validate:** Test UI changes manually if possible (PyQt5) or via unit tests if present.
4. **Checkpoint:** Commit the changes with the updated version number.

## Key Files
- `main.py`: Entry point.
- `main_window.py`: UI layout and toolbars.
- `scene.py`: Core logic for the drawing canvas and event handling.
- `shapes.py`: Definitions for rectangle, oval, diamond, etc.
- `arrows.py`: Logic for connections and bend points.
- `config.py`: Application metadata and versioning.
