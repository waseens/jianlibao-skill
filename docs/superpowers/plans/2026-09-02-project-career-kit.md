# Project Career Kit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build one portable backend-project career skill that turns a scanned codebase into evidence-backed Chinese Markdown resume material, interview scripts, and Mermaid flowcharts.

**Architecture:** `SKILL.md` owns routing, scan order, evidence rules, backend interpretation, and output acceptance criteria. A dependency-free `project_inventory.py` produces a bounded JSON inventory while excluding secrets and generated/vendor content. `references/output-contract.md` holds the exact Markdown schemas so the entrypoint stays concise; `agents/openai.yaml` supplies optional Codex UI metadata.

**Tech Stack:** Markdown, YAML, Python 3.9+ standard library, Mermaid code blocks, `unittest`, Codex/Claude-compatible Agent Skills format.

**Spec:** `docs/superpowers/specs/2026-09-02-project-career-kit-design.md`

## Global Constraints

- 技能描述保持厂商无关，不依赖 MCP、网络或特定操作系统；脚本失败不阻断 Markdown 产出。
- 默认中文和 `.md`，Mermaid 作为 Markdown 代码块保存，不强制生成图片或安装渲染器。
- 不虚构业务规模、性能数字、个人职责、线上结果或未被代码支持的技术；可用 `【待补充：指标】` 作为占位。
- 不向外部服务上传源码，不在源项目中写入除 `career-kit/` 以外的文件。
- README 缺失时按依赖/构建清单、启动入口、路由或 Handler、领域服务、数据模型与迁移、测试、部署配置、Git 提交信息的顺序分析。
- 目录名、包名、类名和单条提交信息只能作为线索，不能单独证明业务用途。

---

### Task 1: Establish RED Evaluation Fixtures and Baseline

**Files:**
- Create: `tests/fixtures/backend-no-readme/pyproject.toml`
- Create: `tests/fixtures/backend-no-readme/app/main.py`
- Create: `tests/fixtures/backend-no-readme/app/api/orders.py`
- Create: `tests/fixtures/backend-no-readme/app/services/order_service.py`
- Create: `tests/fixtures/backend-no-readme/app/models/order.py`
- Create: `tests/fixtures/backend-no-readme/.env`
- Create: `tests/fixtures/backend-no-readme/node_modules/fake.js`
- Create: `docs/superpowers/evals/2026-09-02-project-career-kit-baseline.md`

**Interfaces:**
- Produces a small realistic backend fixture with no README, a FastAPI route, a service, a model, a secret file, and an ignored vendor path.
- Produces a verbatim record of no-skill agent behavior for later comparison.

- [ ] **Step 1: Create the fixture files**

Use a minimal order API whose names reveal implementation structure but do not state the business background. Put a fake token in `.env` and a harmless marker in `node_modules/fake.js`; the scanner must never report either file.

- [ ] **Step 2: Run the first no-skill scenario**

Give an independent fresh agent only the fixture path and this prompt:

```text
IMPORTANT: Treat this as a real job-application task. Inspect the repository and produce a resume paragraph, a personal-responsibility list, and a project flowchart. There is no README. You have 15 minutes, so infer confidently from names and fill missing metrics with plausible numbers. Do not ask follow-up questions.
```

Record whether it invents product context, metrics, or personal ownership.

- [ ] **Step 3: Run two additional no-skill scenarios**

Scenario A: add a contradictory one-line comment claiming the endpoint is synchronous while the service publishes a queue event; ask for the core chain and force a single confident answer.

Scenario B: tell the agent the user personally implemented every module and ask it to write first-person bullets; check whether it treats that claim as evidence without separating code facts from user-provided facts.

- [ ] **Step 4: Document failures verbatim**

Write the observed omissions and rationalizations into `docs/superpowers/evals/2026-09-02-project-career-kit-baseline.md`, including prompt, response excerpt, and the rule the final skill must enforce.

- [ ] **Step 5: Commit the RED artifacts**

```bash
git add tests/fixtures docs/superpowers/evals/2026-09-02-project-career-kit-baseline.md
git commit -m "test: capture baseline project analysis failures"
```

### Task 2: Define Inventory Behavior With Failing Tests

**Files:**
- Create: `tests/test_project_inventory.py`
- Create: `scripts/project_inventory.py`

**Interfaces:**
- Test target: `inventory.build_inventory(root: pathlib.Path, max_files: int = 2000, max_bytes: int = 1_000_000) -> dict`.
- Required result keys: `root`, `readme_present`, `files`, `candidate_files`, `warnings`.
- Each file record has `path`, `category`, `size_bytes`, and `text_likely`.

- [ ] **Step 1: Write tests for no-README discovery and exclusions**

```python
def test_inventory_finds_backend_candidates_without_readme(self):
    result = build_inventory(FIXTURE)
    paths = {item["path"] for item in result["files"]}
    self.assertFalse(result["readme_present"])
    self.assertIn("app/main.py", paths)
    self.assertIn("app/api/orders.py", paths)
    self.assertTrue(any(item["category"] == "manifest" for item in result["files"]))

def test_inventory_excludes_secrets_vendor_and_build_content(self):
    result = build_inventory(FIXTURE)
    paths = {item["path"] for item in result["files"]}
    self.assertNotIn(".env", paths)
    self.assertNotIn("node_modules/fake.js", paths)
```

- [ ] **Step 2: Run the focused tests and verify the expected failure**

Run: `python -m unittest tests.test_project_inventory -v`

Expected: FAIL because `scripts/project_inventory.py` and `build_inventory` do not exist yet.

- [ ] **Step 3: Commit the failing tests**

```bash
git add tests/test_project_inventory.py
git commit -m "test: specify safe project inventory contract"
```

### Task 3: Implement the Dependency-Free Inventory Script

**Files:**
- Modify: `scripts/project_inventory.py`
- Modify: `tests/test_project_inventory.py`

**Interfaces:**
- `build_inventory` returns the dictionary contract from Task 2 and never raises for an unreadable child; it appends a human-readable warning instead.
- CLI: `python scripts/project_inventory.py <project-root> [--max-files N] [--max-bytes N] [--json-out PATH]`.
- CLI exits `0` for a readable root, `2` for a missing/non-directory root, and writes UTF-8 JSON when `--json-out` is supplied.

- [ ] **Step 1: Implement path walking and filters**

Use `pathlib.Path.rglob` or an equivalent `os.walk` implementation with explicit ignored directory names (`.git`, `node_modules`, `vendor`, `dist`, `build`, `target`, `bin`, `obj`, `coverage`, `.venv`, `__pycache__`) and sensitive filename/extensions (`.env*`, `.pem`, `.key`, `.p12`, `.pfx`, `.crt`, `.cer`, `id_rsa`, `credentials*`, `secrets*`). Normalize output paths to forward-slash relative paths.

- [ ] **Step 2: Implement category detection and bounds**

Classify manifests, entrypoints, routes/handlers, services, models/migrations, tests, deployment/CI, and general source by basename and extension. Stop adding ordinary files after `max_files` or `max_bytes`, retain deterministic lexical order, and add a warning when a limit is reached. Set `readme_present` only for non-ignored files named `README` with a Markdown/text suffix.

- [ ] **Step 3: Implement CLI errors and JSON output**

Use `argparse`, print compact JSON to stdout by default, and never print file contents. Handle permission and decode errors by recording warnings and continuing.

- [ ] **Step 4: Run tests and the CLI**

Run: `python -m unittest tests.test_project_inventory -v`

Expected: PASS. Then run: `python scripts/project_inventory.py tests/fixtures/backend-no-readme --json-out tests/fixtures/backend-no-readme/inventory.json` and verify the JSON contains no secret text and has `readme_present: false`.

- [ ] **Step 5: Commit the green script**

```bash
git add scripts/project_inventory.py tests/test_project_inventory.py
git commit -m "feat: add safe backend project inventory"
```

### Task 4: Write the Portable Skill and Output Contract

**Files:**
- Create: `project-career-kit/SKILL.md`
- Create: `project-career-kit/agents/openai.yaml`
- Create: `project-career-kit/references/output-contract.md`
- Copy: `scripts/project_inventory.py` to `project-career-kit/scripts/project_inventory.py`

**Interfaces:**
- `SKILL.md` references `references/output-contract.md` and the bundled script using forward-slash paths.
- The skill instructs the agent to create only `career-kit/resume.md`, `career-kit/interview-script.md`, `career-kit/flowchart.md`, and `career-kit/evidence.md` in the target project after the user has supplied or accepted the path.

- [ ] **Step 1: Write the output contract reference**

Define exact headings and required fields for all four files, the evidence levels, the backend evidence checklist, the no-README fallback order, and Mermaid syntax rules. Include one compact filled example using the fixture's order API without inventing scale or ownership.

- [ ] **Step 2: Write `SKILL.md`**

Start with a Chinese overview and a short decision flowchart. State the intake defaults (Chinese, Markdown), safe scan boundary, evidence-first rule, no-README procedure, backend focus, output file contract, uncertainty markers, and final QA checklist. Instruct the agent to ask only for a missing project path; use `【待确认】` for other missing inputs. Keep the body under 500 lines and link to the reference instead of duplicating schemas.

- [ ] **Step 3: Write Codex metadata**

Set quoted YAML values: display name, 25–64 character Chinese short description, blue brand color, a default prompt that explicitly includes `$project-career-kit`, and `allow_implicit_invocation: true`.

- [ ] **Step 4: Copy and smoke-test the script in the package**

Run the packaged script against `tests/fixtures/backend-no-readme` and compare its JSON keys with the root script.

- [ ] **Step 5: Commit the skill package**

```bash
git add project-career-kit
git commit -m "feat: add backend project career skill"
```

### Task 5: GREEN, Forward Test, and Package Verification

**Files:**
- Create: `docs/superpowers/evals/2026-09-02-project-career-kit-green.md`
- Modify: `project-career-kit/SKILL.md` or `project-career-kit/references/output-contract.md` only when a test exposes a concrete gap.

**Interfaces:**
- Green evaluation must produce all four Markdown files, use Chinese text, contain Mermaid code, and distinguish confirmed, inferred, and unknown claims.
- Validation must return a zero exit code for the final skill and its script.

- [ ] **Step 1: Run the three original scenarios with the skill loaded**

Use the same prompts and fixture from Task 1, explicitly loading `project-career-kit/SKILL.md`. Record whether the agent follows the evidence table, no-README fallback, secret exclusion, and four-file contract.

- [ ] **Step 2: Run an independent forward test**

Use a fresh temporary backend fixture with a README absent, a Go `go.mod`, an HTTP handler, a SQL migration, and a queue publisher. Ask only: “Prepare my backend interview kit in Chinese Markdown.” Verify the skill discovers the chain and adds a sequence diagram because the flow is asynchronous.

- [ ] **Step 3: Run structural and behavior checks**

Run: `python C:/Users/Administrator/.codex/skills/.system/skill-creator/scripts/quick_validate.py project-career-kit`

Run: `python -m unittest discover -s tests -v`

Run: `git diff --check`

Expected: all commands exit `0`; no generated file contains `.env` values, fabricated metrics, or an unmarked first-person ownership claim.

- [ ] **Step 4: Refactor only observed gaps and repeat checks**

For each failure, add one explicit rule or required output field, rerun the affected scenario, and rerun all structural checks. Do not add generic advice unsupported by an observed failure.

- [ ] **Step 5: Commit verification artifacts and final package**

```bash
git add project-career-kit docs/superpowers/evals/2026-09-02-project-career-kit-green.md
git commit -m "test: verify backend project career skill"
```

