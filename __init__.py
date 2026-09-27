"""GLM-Image custom nodes — separate-loader architecture only.

Legacy monolithic pipeline loader and pipeline-extract nodes were removed
on 2026-05-01 per user request ("Remove legacy. Add I2I support.").
"""

# Relative import only, and deliberately unguarded.
#
# This used to fall back to `from separate_nodes import ...` under
# `except ImportError`. ModuleNotFoundError is an ImportError subclass, so when
# separate_nodes.py failed on its own absolute sibling import
# (`from _is_changed_util import ...` — unresolvable because ComfyUI does not put
# the pack directory on sys.path), the real cause was swallowed and the fallback
# reported the misleading "No module named 'separate_nodes'". The pack registered
# ZERO nodes in production while its test suite stayed green.
#
# A failure here must be loud and must name the module that actually failed.
from .separate_nodes import (
    SEPARATE_NODE_CLASS_MAPPINGS,
    SEPARATE_NODE_DISPLAY_NAME_MAPPINGS,
)

NODE_CLASS_MAPPINGS = dict(SEPARATE_NODE_CLASS_MAPPINGS)
NODE_DISPLAY_NAME_MAPPINGS = dict(SEPARATE_NODE_DISPLAY_NAME_MAPPINGS)

# The pack had no front-end; this directory carries only the house brand
# (_c2c_brand.js), so its nodes share the Code2Collapse look on the canvas.
WEB_DIRECTORY = "./web"

# ── One menu root for every Code2Collapse pack ─────────────────────────────
# Every node lands under "🐺 C2C/<pack>/<family>" in the Add Node menu and the
# node library (see _c2c_menu.py). Node ids are untouched, so saved workflows
# are unaffected. Guarded: a menu placement must never cost the pack its nodes.
try:
    from ._c2c_menu import rebrand_v1 as _c2c_menu_rebrand

    _c2c_menu_rebrand(
        NODE_CLASS_MAPPINGS, "\U0001F5BC\uFE0F GLM Image",
        strip=("GLMImage",),
        rename={"loaders": "Loaders", "sampling": "Sampling"},
    )
except Exception as _c2c_menu_exc:  # noqa: BLE001
    import logging as _c2c_menu_log

    _c2c_menu_log.getLogger(__name__).warning("C2C menu root not applied: %s", _c2c_menu_exc)


__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
