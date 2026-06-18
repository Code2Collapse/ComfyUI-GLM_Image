"""Minimal ComfyUI stubs so separate_nodes imports in CI without a full install."""
from __future__ import annotations

import sys
from types import ModuleType


def _ensure_comfy_stubs() -> None:
    if "folder_paths" not in sys.modules:
        fp = ModuleType("folder_paths")
        fp.get_folder_paths = lambda *_a, **_k: []
        fp.get_filename_list = lambda *_a, **_k: []
        sys.modules["folder_paths"] = fp

    if "comfy" not in sys.modules:
        comfy = ModuleType("comfy")
        sys.modules["comfy"] = comfy
    else:
        comfy = sys.modules["comfy"]

    if "comfy.model_management" not in sys.modules:
        mm = ModuleType("comfy.model_management")
        mm.unload_all_models = lambda: None
        mm.soft_empty_cache = lambda: None
        mm.throw_exception_if_processing_interrupted = lambda: None

        class InterruptProcessingException(Exception):
            pass

        mm.InterruptProcessingException = InterruptProcessingException
        sys.modules["comfy.model_management"] = mm
        comfy.model_management = mm

    if "comfy.utils" not in sys.modules:
        cu = ModuleType("comfy.utils")

        class _ProgressBar:
            def __init__(self, total):
                self.total = total

            def update_absolute(self, *_a, **_k):
                return None

        cu.ProgressBar = _ProgressBar
        sys.modules["comfy.utils"] = cu
        comfy.utils = cu


_ensure_comfy_stubs()
