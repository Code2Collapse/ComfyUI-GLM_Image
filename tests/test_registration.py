"""R11 — registration smoke under ComfyUI's real loader.

This pack registered ZERO nodes in production while its other tests stayed green.
`separate_nodes.py` imported a sibling absolutely (`from _is_changed_util import ...`),
which only resolves when the pack directory happens to be on sys.path. pytest puts
the repo root on sys.path; ComfyUI does not. So every existing test passed against
an import path that production never uses.

The only way to catch that is to load the pack exactly the way ComfyUI does.
`third_party/ComfyUI/nodes.py:2243-2263`:

    sys_module_name = module_path.replace(".", "_x_")          # :2250
    module_spec = importlib.util.spec_from_file_location(sys_module_name, .../__init__.py)
    module = importlib.util.module_from_spec(module_spec)
    sys.modules[sys_module_name] = module                      # :2262  <-- BEFORE exec
    module_spec.loader.exec_module(module)                     # :2263

The `sys.modules` assignment BEFORE `exec_module` is the load-bearing part: without
it the package's own relative imports cannot resolve. Reproducing it faithfully is
what makes this test able to fail.
"""

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

EXPECTED_NODE_COUNT = 4
EXPECTED_NODE_IDS = {
    "GLMImageVAELoader",
    "GLMImageCLIPLoader",
    "GLMImageModelLoader",
    "GLMImageSeparateSampler",
}


def _load_pack_like_comfyui():
    """Load with the pack directory REMOVED from sys.path.

    ComfyUI never puts a custom-node directory on sys.path. pytest does, and so
    does any sibling test that inserts it — which means an absolute sibling import
    resolves during a test run and the pack looks healthy. Verified: with the bug
    deliberately reintroduced, this test PASSED until the strip below was added,
    because an earlier test in the same process had already inserted ROOT.

    Stripping it is what makes this test able to fail.
    """
    module_path = str(ROOT)
    sys_module_name = module_path.replace(".", "_x_")

    saved_path = list(sys.path)
    saved_modules = {k: v for k, v in sys.modules.items() if k == sys_module_name}
    root_str = str(ROOT)
    sys.path[:] = [p for p in sys.path if Path(p or ".").resolve() != ROOT]
    sys.modules.pop(sys_module_name, None)
    try:
        spec = importlib.util.spec_from_file_location(
            sys_module_name, ROOT / "__init__.py", submodule_search_locations=[root_str]
        )
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        sys.modules[sys_module_name] = module  # BEFORE exec_module — see docstring
        spec.loader.exec_module(module)
        return module
    finally:
        sys.path[:] = saved_path
        sys.modules.update(saved_modules)


def test_pack_registers_nodes_under_the_real_loader():
    """A pack that registers 0 must fail here, not ship."""
    pack = _load_pack_like_comfyui()
    mappings = getattr(pack, "NODE_CLASS_MAPPINGS", None)
    assert mappings is not None, "__init__.py exposes no NODE_CLASS_MAPPINGS"
    assert len(mappings) == EXPECTED_NODE_COUNT, (
        f"registered {len(mappings)} nodes, expected {EXPECTED_NODE_COUNT}: "
        f"{sorted(mappings)}"
    )
    assert set(mappings) == EXPECTED_NODE_IDS


def test_no_absolute_sibling_imports():
    """The specific bug: a sibling imported absolutely resolves only under pytest.

    Kept as a source check rather than folded into the loader test, because it
    names the defect directly instead of reporting a downstream import error.
    """
    siblings = {
        p.stem for p in ROOT.glob("*.py") if p.stem not in ("__init__",)
    }
    offenders: list[str] = []
    for py in ROOT.glob("*.py"):
        for n, line in enumerate(py.read_text(encoding="utf-8").splitlines(), 1):
            stripped = line.strip()
            for sib in siblings:
                if stripped.startswith(f"from {sib} import") or stripped == f"import {sib}":
                    offenders.append(f"{py.name}:{n}: {stripped}")
    assert not offenders, (
        "sibling modules must be imported relatively (`from .x import y`); "
        "absolute form breaks under ComfyUI's loader:\n  " + "\n  ".join(offenders)
    )


def test_no_module_named_utils():
    """`utils.py` here would shadow ComfyUI's own top-level `utils` package.

    ComfyUI imports its `utils` at startup, before custom nodes load, so once
    sys.modules['utils'] is taken, a same-named module here is unreachable and any
    import of it fails. The file was renamed to glm_utils.py; this stops it coming back.
    """
    for banned in ("utils.py", "nodes.py"):
        assert not (ROOT / banned).exists(), (
            f"{banned} collides with a ComfyUI top-level name and will not import "
            f"in production; rename it (e.g. glm_{banned})"
        )


def test_init_does_not_swallow_import_errors():
    """The fallback that hid the real cause must not return.

    `except ImportError` also catches ModuleNotFoundError, so the original failure
    was reported as the wrong module entirely.
    """
    code_lines = [
        ln
        for ln in (ROOT / "__init__.py").read_text(encoding="utf-8").splitlines()
        if not ln.lstrip().startswith("#")  # the comment ABOUT the bug is not the bug
    ]
    offenders = [ln.strip() for ln in code_lines if "except ImportError" in ln]
    assert not offenders, (
        "__init__.py must not guard its imports with `except ImportError` — that "
        f"swallows ModuleNotFoundError and misreports which module failed: {offenders}"
    )
