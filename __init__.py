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

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]
