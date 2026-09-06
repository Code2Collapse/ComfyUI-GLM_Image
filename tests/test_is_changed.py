"""IS_CHANGED and tensor validation regression tests for ComfyUI-GLM_Image."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _load_util():
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    spec = importlib.util.spec_from_file_location("glm_is_changed_util", ROOT / "_is_changed_util.py")
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _load_separate_nodes():
    """Load separate_nodes AS PART OF THE PACKAGE, the way ComfyUI does.

    This used to do `sys.path.insert(ROOT); import separate_nodes` — loading the
    module standalone. That is precisely the anti-pattern that let the pack ship
    registering ZERO nodes: standalone loading makes an absolute sibling import
    (`from _is_changed_util import ...`) resolve, so the test passed against an
    import path production never uses. Sibling imports are relative now, which a
    standalone load cannot satisfy at all.

    Skipping is reserved for genuinely absent third-party weights/libraries
    (diffusers, transformers). An ImportError from OUR OWN modules must fail.
    """
    pkg_name = str(ROOT).replace(".", "_x_")
    if pkg_name not in sys.modules:
        spec = importlib.util.spec_from_file_location(
            pkg_name, ROOT / "__init__.py", submodule_search_locations=[str(ROOT)]
        )
        assert spec and spec.loader
        pkg = importlib.util.module_from_spec(spec)
        sys.modules[pkg_name] = pkg  # BEFORE exec_module
        try:
            spec.loader.exec_module(pkg)
        except ModuleNotFoundError as exc:
            missing = (exc.name or "").split(".")[0]
            if missing in {"diffusers", "transformers", "accelerate", "sentencepiece"}:
                pytest.skip(f"optional dependency missing: {missing}")
            raise
    return importlib.import_module(f"{pkg_name}.separate_nodes")


def test_hash_args_and_kwargs_stable_for_scalars():
    util = _load_util()
    a = util.hash_args_and_kwargs(model_id="zai-org/GLM-Image", dtype="bf16", device="cuda")
    b = util.hash_args_and_kwargs(model_id="zai-org/GLM-Image", dtype="bf16", device="cuda")
    assert a == b
    assert len(a) == 32


def test_hash_args_and_kwargs_changes_when_scalar_changes():
    util = _load_util()
    a = util.hash_args_and_kwargs(seed=42, steps=4)
    b = util.hash_args_and_kwargs(seed=43, steps=4)
    assert a != b


@pytest.mark.skipif(
    importlib.util.find_spec("torch") is None,
    reason="torch not installed in this interpreter",
)
def test_hash_args_and_kwargs_tensor_fingerprint():
    import torch

    util = _load_util()
    t1 = torch.zeros(1, 8, 8, 3)
    t2 = torch.ones(1, 8, 8, 3)
    assert util.hash_args_and_kwargs(image=t1) != util.hash_args_and_kwargs(image=t2)


def test_is_changed_pattern_never_returns_nan():
    util = _load_util()

    class _StubNode:
        @classmethod
        def IS_CHANGED(cls, **kwargs):
            return util.hash_args_and_kwargs(**kwargs)

    out = _StubNode.IS_CHANGED(prompt="hello", seed=1, steps=4)
    assert isinstance(out, str)
    assert out == out


def test_loader_nodes_define_is_changed():
    nodes = _load_separate_nodes()
    for name in nodes.SEPARATE_NODE_CLASS_MAPPINGS:
        cls = nodes.SEPARATE_NODE_CLASS_MAPPINGS[name]
        assert hasattr(cls, "IS_CHANGED"), f"{name} missing IS_CHANGED"


@pytest.mark.skipif(
    importlib.util.find_spec("torch") is None,
    reason="torch not installed in this interpreter",
)
def test_require_image_bhwc_rejects_bad_shape():
    import torch

    nodes = _load_separate_nodes()
    with pytest.raises(ValueError, match="4D IMAGE tensor"):
        nodes._require_image_bhwc(torch.zeros(3, 64, 64), "image")
