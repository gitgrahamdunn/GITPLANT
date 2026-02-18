import importlib
import pathlib
import sys


def test_backend_imports_without_mkdir_calls(monkeypatch):
    mkdir_calls: list[pathlib.Path] = []
    original_mkdir = pathlib.Path.mkdir

    def tracking_mkdir(self, *args, **kwargs):
        mkdir_calls.append(self)
        return original_mkdir(self, *args, **kwargs)

    monkeypatch.setattr(pathlib.Path, "mkdir", tracking_mkdir)

    target_modules = [
        "app.config",
        "app.db",
        "app.routers.documents",
        "app.routers.projects",
        "app.routers.health",
        "app.main",
    ]
    for module in target_modules:
        sys.modules.pop(module, None)

    importlib.import_module("app.main")

    assert mkdir_calls == []


def test_default_storage_dir_targets_tmp(monkeypatch):
    monkeypatch.delenv("DATA_DIR", raising=False)
    monkeypatch.delenv("STORAGE_DIR", raising=False)

    import app.config as config

    assert str(config.get_storage_dir(ensure_exists=False)).startswith("/tmp/")
