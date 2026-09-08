# Project Career Kit V2 Forward Evaluation

- Date: 2026-09-08
- Fixture: `tests/fixtures/backend-learning-project`
- Isolated forward copy: `C:\Users\Administrator\AppData\Local\Temp\backend-learning-project-v2-d7124c13a03f4cc280a243cafc6bebac`
- Generated directory: `career-kit/` beneath the isolated forward copy

## User Request

```text
请使用 project-career-kit 只读扫描这个后端项目，为后端开发岗位生成默认中文 Markdown 求职材料。
```

The generation agent received only the Skill path, isolated project path, and request above. It did not receive the implementation plan, tests, expected graph nodes, evidence IDs, expected material contents, or known failures.

## Generation Boundary

- Generated files: `简历素材.md`, `面试逐字稿.md`, `项目流程图.md`, and `证据索引.md`.
- The generation agent reported no project execution, dependency installation, or network access.
- The five source files in the isolated copy (`README.md`, `pyproject.toml`, `app/main.py`, `app/api/tasks.py`, and `app/services/task_service.py`) matched their fixture counterparts by SHA-256: PASS (5/5).

## Mechanical Acceptance

The complete Task 4 Step 3 PowerShell acceptance script was rerun against the isolated copy on 2026-09-08. It exited with code 0 and produced `V2 forward acceptance: PASS`.

- File-set check: PASS; exactly the four required Chinese Markdown files were present.
- Evidence records parsed: 17 (`C001` through `C017`).
- Mermaid: a `flowchart` was present; its five substantive node/edge lines each had a directly preceding `%% evidence:` annotation. The unique referenced IDs were `C004` and `C005`, both present in `证据索引.md`.
- README E2 source record: PASS.
- Project-purpose wording: PASS; the prose contains `多智能体协作技术实践` and uses direct project language in the `这是一个/该项目 ... 用于` form.
- Attribution and source-summary checks: PASS; it contains neither `README 将其描述` nor `我设计`/`我实现`.

## Independent Semantic Review

The completed independent read-only review found no Critical or Important issue. It confirmed that graph labels and edges are directly supported by their evidence comments; static declarations are not represented as observed runtime behavior; the README learning-project positioning is cross-validated by source/configuration; and no first-person ownership claim appears without E3 confirmation. Unconfirmed participation scope and responsibilities remain marked as pending confirmation.

## Frozen Boundary

`git diff --quiet master...HEAD -- project-career-kit/scripts/project_inventory.py` exited 0 during this evaluation: `project_inventory.py` is unchanged relative to `master`.
