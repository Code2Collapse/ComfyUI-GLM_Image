# WORKLOG — ComfyUI-GLM_Image

**Stage 0 audit, 2026-08-29. Every number below was MEASURED this session, not inherited.**
Regenerate with the commands in the last section. Per R3 this file is the persisted source of
record; a claim that lives only in a chat transcript has now drifted five times.

## 1. Live inventory
| | |
|---|---|
| **Nodes registered (runtime)** | **0** |
| Nodes expected from source | 4 |
| Registration style | V1 `NODE_CLASS_MAPPINGS` |
| `WEB_DIRECTORY` | none |
| **Tests** | **6 passed** |

## 2. Licence
**Apache-2.0.**

## 3. REGISTRATION SMOKE FAILS — THE PACK REGISTERS ZERO NODES

Under the production loader this pack does not load at all:

```
ComfyUI-GLM_Image   LOAD_FAIL   0   ModuleNotFoundError: No module named 'separate_nodes'
```

**Root cause** — `separate_nodes.py:26`:

```python
from _is_changed_util import hash_args_and_kwargs
```

That is an ABSOLUTE import of a sibling module. Under ComfyUI's loader the pack directory is not on
`sys.path`, so it cannot resolve. Proven directly:

```
RELATIVE IMPORT FAILS WITH: ModuleNotFoundError -> No module named '_is_changed_util'
```

**Why the error message lies.** `__init__.py:12` wraps the relative import in `except ImportError`.
`ModuleNotFoundError` is an ImportError subclass, so the real cause is swallowed and the absolute
fallback reports the misleading "No module named 'separate_nodes'" instead. Two bugs stacked: a bad
import, and a guard that hides which import failed.

**And the tests pass anyway.** 6 tests green while the pack is dead in production, because pytest
puts the repo root on `sys.path` and never reproduces ComfyUI's loader. This is the fourth instance
of the green-suite-dead-in-production pattern in this workspace, after the MiniMaxSuite `utils/`
collision, the widget `onExecuted` channel, and the workflow slot drift.

**Fix shape:** make sibling imports relative (`from ._is_changed_util import ...`) and drop the
`except ImportError` fallback so a future breakage reports its own cause. Then add a registration
smoke test using the `nodes.py:2243-2263` harness — without one, this class of bug cannot be caught.

This repo also contains `utils.py`, whose name collides with ComfyUI's own top-level `utils` package.
It is not currently imported by `separate_nodes.py`, but it is a live trap.

## 4. Invariant sweep
| Check | Result |
|---|---|
| `third_party` runtime imports | 0 |
| `IS_CHANGED` -> `float("nan")` | 0 |
| Hardcoded `.cuda()` | 0 |

## 5. Build queue (brief 2.5)
**Nothing until section 3 is fixed.** Batch grid prompts, metadata-preserving save and the
prompt-guide node are all worthless while the pack registers zero nodes.

## 6. Blocked / decisions
None. The fix is unambiguous and small.

## Regeneration commands

```
head -3 LICENSE

# registration smoke, the way ComfyUI loads (third_party/ComfyUI/nodes.py:2243-2263):
#   sys.modules[name] = mod   BEFORE   spec.loader.exec_module(mod)
# Anything less can report healthy for a pack that registers nothing.
python <scratch>/regsmoke.py ComfyUI-GLM_Image

D:/PROJECT/ComfyUI_windows_portable/comfy_env/python.exe -m pytest tests/ -q
```

Shell python has no torch — always use the comfy_env interpreter.
