# Python Health Report — free-llm-api-keys-python

Generated on 2026-06-25 14:34 by python-health-audit.

## 1. Executive Summary
- Global grade: B
- Reason: Grade B assigned: Ruff has exactly 5 minor findings, 0 E/F complexity hotspots were detected, and the average Maintainability Index is 70.1.

## 2. Dead Code
### 2.1 Local — Ruff
| File | Line | Issue |
|---|---|---|
| `examples/cleanup.py` | 158:12 | F541 f-string without any placeholders |
| `examples/demo.py` | 145:41 | F841 Local variable `exc` is assigned to but never used |
| `examples/demo.py` | 146:18 | F541 f-string without any placeholders |
| `src/free_llm_api_keys/parser.py` | 22:44 | F401 `dataclasses.field` imported but unused |
| `tests/test_health.py` | 7:38 | F401 `free_llm_api_keys.health.HealthState` imported but unused |

### 2.2 Global — Vulture
No finding.

> ⚠️ Vulture produces false positives by construction (global static
> detection). Verify each entry before removal.

## 3. Complexity Hotspots (Radon)
- `src/free_llm_api_keys/client.py`: `FreeLLMClient._resolve_keys` (Rank C)
- `src/free_llm_api_keys/parser.py`: `parse_readme_full` (Rank C)
- `src/free_llm_api_keys/parser.py`: `_build_entry` (Rank C)
- `examples/demo.py`: `_run` (Rank C)

## 4. Code Duplication (Pylint)
- `examples/cleanup.py` (lines 31:49) and `examples/demo.py` (lines 26:44): Duplicate setup and color constants block.

## 5. Recommended Action Plan
1. Extract the duplicate CLI setup and color constants from `examples/cleanup.py` and `examples/demo.py` into a shared `examples/utils.py` module.
2. Fix the 5 minor local issues identified by Ruff (unused variables/imports and unnecessary f-strings).
3. Refactor `FreeLLMClient._resolve_keys` and `parse_readme_full` to reduce their cyclomatic complexity (currently Rank C) and improve their maintainability index.
