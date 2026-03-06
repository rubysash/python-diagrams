# Project Guidelines

## Environment
- Windows 11 Pro, Python venv at `D:\v\python\diagrams`
- Activate venv: `Scripts/activate` (bash) or `Scripts\Activate.ps1` (PowerShell)
- Always use forward slashes in shell commands (Unix shell syntax)

## Git Workflow
- **Always git commit before making changes** — create a checkpoint commit of the current state before starting modifications
- Use descriptive commit messages explaining the "why"
- Never force-push or use destructive git operations without explicit approval

## Code Standards
- Follow **PEP 8** style guidelines strictly
- Write **modular code** — break logic into small, focused functions and classes
- Use meaningful variable and function names (snake_case for functions/variables, PascalCase for classes)
- Keep functions short and single-purpose
- Use type hints for function signatures
- Imports should be organized: stdlib, third-party, local (separated by blank lines)
- Include useful comments in all written code — explain the "why", not just the "what"

## Python Best Practices
- Use `pathlib.Path` over `os.path` for file operations
- Use context managers (`with` statements) for resource handling
- Prefer f-strings for string formatting
- Use `if __name__ == "__main__":` guard in scripts
- Handle exceptions specifically, never bare `except:`
- Use virtual environment packages — do not install globally
