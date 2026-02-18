"""Vercel entrypoint for FastAPI app."""

from importlib import import_module

_TRIED_IMPORTS = (
    "app.main",
    "main",
    "app.server",
    "server",
)


for _module_path in _TRIED_IMPORTS:
    try:
        app = import_module(_module_path).app
        break
    except (ImportError, AttributeError):
        continue
else:
    tried = ", ".join(f"{module}.app" for module in _TRIED_IMPORTS)
    raise ImportError(
        f"Could not import FastAPI app. Tried: {tried}"
    )
