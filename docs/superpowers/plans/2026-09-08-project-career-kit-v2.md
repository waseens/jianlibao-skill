# `project-career-kit` V2 实施计划

> **历史文档，已废弃：** 本文保留旧版审计模型的实施记录，不能作为当前实现或验收依据。请以 [`2026-09-07-project-career-kit-v2-design.md`](../specs/2026-09-07-project-career-kit-v2-design.md) 和 [`project-career-kit/references/output-contract.md`](../../../project-career-kit/references/output-contract.md) 为准。

> **供智能代理执行：** 必须逐项使用 `superpowers:subagent-driven-development`（推荐）或 `superpowers:executing-plans`。每个步骤使用复选框追踪。

**目标：** 将 `project-career-kit` 升级为 V2 契约：只生成四个中文文件，用图内 Mermaid 证据注释表达项目流程，并以项目开发视角书写经验证的学习/实验项目定位。

**架构：** `project-career-kit/SKILL.md` 负责触发、扫描边界、生成顺序和最终 QA；`references/output-contract.md` 保存四个产物的精确模板、Mermaid 映射规则和示例。新增标准库 `unittest` 测试，将 V2 文档契约与现有 inventory 行为分开验证；独立的后端学习项目夹具只用于人工前向评测，不作为运行时依赖。

**技术栈：** Markdown、Mermaid、Python 3 标准库、`unittest`、PowerShell、Codex/Claude 兼容的 Agent Skill 格式。

**规格：** `docs/superpowers/specs/2026-09-07-project-career-kit-v2-design.md`

## 全局约束

- 只改当前 `master` 中的 `project-career-kit/`；不得把 `.worktrees/project-career-kit/` 里未提交、已改名为 `resume-bao` 的分支内容带入本次工作。
- 新运行只生成 `career-kit/简历素材.md`、`career-kit/面试逐字稿.md`、`career-kit/项目流程图.md`、`career-kit/证据索引.md`，不重命名、删除或编辑已有英文产物。
- 保留证据等级、段落级覆盖、隐藏引用、运行时未知项和 `project-career-kit/scripts/project_inventory.py` 的现有行为。
- 不修改 `project-career-kit/agents/openai.yaml`，不修改任何目标项目中已生成的用户材料，不增加 SVG、PNG、外部 Mermaid 渲染器或第五个输出文件。
- 当前工作树中的中文 V2 规格是已确认但尚未提交的修改；执行中保留它，不使用 `git reset`、`git checkout --` 或任何会丢弃它的操作。

## 文件边界

- 修改：`project-career-kit/SKILL.md`，替换输出路径并补充 V2 生成、证据和 QA 规则。
- 修改：`project-career-kit/references/output-contract.md`，替换四文件模板、流程图模板和紧凑示例。
- 创建：`tests/__init__.py`，使测试可用模块路径运行。
- 创建：`tests/test_project_inventory.py`，锁定包内 inventory 的关键安全与边界行为。
- 创建：`tests/test_output_contract_v2.py`，锁定 V2 输出、图内证据和项目开发视角契约。
- 创建：`tests/fixtures/backend-learning-project/README.md`、`pyproject.toml`、`app/main.py`、`app/api/tasks.py`、`app/services/task_service.py`，作为 README 与配置/源码可交叉验证的前向场景。
- 创建：`docs/superpowers/evals/2026-09-08-project-career-kit-v2.md`，记录新鲜上下文前向评测的输入、结构检查和结果。

---

### Task 1: 建立 V2 回归测试与前向评测夹具

**文件：**
- 创建：`tests/__init__.py`
- 创建：`tests/test_project_inventory.py`
- 创建：`tests/test_output_contract_v2.py`
- 创建：`tests/fixtures/backend-learning-project/README.md`
- 创建：`tests/fixtures/backend-learning-project/pyproject.toml`
- 创建：`tests/fixtures/backend-learning-project/app/main.py`
- 创建：`tests/fixtures/backend-learning-project/app/api/tasks.py`
- 创建：`tests/fixtures/backend-learning-project/app/services/task_service.py`

**接口：**
- `tests/test_project_inventory.py` 通过 `importlib.util.spec_from_file_location` 加载 `project-career-kit/scripts/project_inventory.py`，并调用 `build_inventory(root, max_files=2000, max_bytes=1_000_000)` 或更小的受测上限。
- `tests/test_output_contract_v2.py` 只读 `project-career-kit/SKILL.md` 与 `project-career-kit/references/output-contract.md`，不执行 Skill，也不修改包内容。
- `backend-learning-project` 的 README 和 `pyproject.toml` 都包含“多智能体协作技术实践”，源码包含可扫描的 FastAPI 入口、任务路由和 service 调用。

- [ ] **Step 1: 创建可交叉验证的后端学习项目夹具**

写入以下固定内容；不要向既有的 no-README 夹具添加 README，二者验证的是不同分支。

```markdown
<!-- tests/fixtures/backend-learning-project/README.md -->
# 多智能体协作练习服务

这是一个用于多智能体协作技术实践的学习项目。
服务提供任务创建接口，并把请求交给任务服务处理。
```

```toml
# tests/fixtures/backend-learning-project/pyproject.toml
[project]
name = "multi-agent-practice"
version = "0.1.0"
description = "用于多智能体协作技术实践的后端服务"
requires-python = ">=3.11"
dependencies = ["fastapi>=0.110"]
```

```python
# tests/fixtures/backend-learning-project/app/main.py
from fastapi import FastAPI

from app.api.tasks import router as tasks_router

app = FastAPI()
app.include_router(tasks_router)
```

```python
# tests/fixtures/backend-learning-project/app/api/tasks.py
from fastapi import APIRouter

from app.services.task_service import TaskService

router = APIRouter(prefix="/tasks")
service = TaskService()


@router.post("")
async def create_task() -> dict[str, str]:
    return service.create()
```

```python
# tests/fixtures/backend-learning-project/app/services/task_service.py
class TaskService:
    def create(self) -> dict[str, str]:
        return {"status": "accepted"}
```

- [ ] **Step 2: 为 inventory 写入独立基线测试**

创建 `tests/test_project_inventory.py`。用动态模块加载避免连字符目录名成为 Python import 名；测试不复制或修改 production 脚本。

```python
import importlib.util
import os
from pathlib import Path
import tempfile
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPOSITORY_ROOT / "project-career-kit" / "scripts" / "project_inventory.py"
MODULE_SPEC = importlib.util.spec_from_file_location("project_inventory_under_test", SCRIPT_PATH)
assert MODULE_SPEC is not None and MODULE_SPEC.loader is not None
INVENTORY_MODULE = importlib.util.module_from_spec(MODULE_SPEC)
MODULE_SPEC.loader.exec_module(INVENTORY_MODULE)
build_inventory = INVENTORY_MODULE.build_inventory


class ProjectInventoryTests(unittest.TestCase):
    def test_discovers_readme_entrypoint_and_route_candidates(self):
        fixture = REPOSITORY_ROOT / "tests" / "fixtures" / "backend-learning-project"
        result = build_inventory(fixture)
        paths = {record["path"] for record in result["files"]}
        categories = {record["category"] for record in result["candidate_files"]}
        self.assertTrue(result["readme_present"])
        self.assertTrue({"README.md", "app/main.py", "app/api/tasks.py"} <= paths)
        self.assertTrue({"manifest", "entrypoint", "route_handler", "service"} <= categories)

    def test_excludes_sensitive_and_generated_content(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            (root / ".env").write_text("TOKEN=not-for-output", encoding="utf-8")
            (root / "node_modules").mkdir()
            (root / "node_modules" / "bundle.js").write_text("ignored", encoding="utf-8")
            (root / "dist").mkdir()
            (root / "dist" / "app.js").write_text("ignored", encoding="utf-8")
            (root / "app.py").write_text("print('kept')", encoding="utf-8")
            paths = {record["path"] for record in build_inventory(root)["files"]}
        self.assertEqual(paths, {"app.py"})

    def test_limit_warning_stops_collection_without_reading_contents(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            (root / "a.py").write_text("a", encoding="utf-8")
            (root / "b.py").write_text("bb", encoding="utf-8")
            result = build_inventory(root, max_bytes=1)
        self.assertEqual([record["path"] for record in result["files"]], ["a.py"])
        self.assertTrue(any("max_bytes" in warning for warning in result["warnings"]))

    def test_ignores_a_file_symlink_when_the_platform_allows_one(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory) / "project"
            external = Path(temporary_directory) / "external.py"
            root.mkdir()
            external.write_text("print('outside')", encoding="utf-8")
            try:
                os.symlink(external, root / "linked.py")
            except OSError as error:
                self.skipTest("file symlink unavailable: %s" % error)
            self.assertEqual(build_inventory(root)["files"], [])
```

- [ ] **Step 3: 编写会在旧契约上失败的 V2 输出契约测试**

创建 `tests/test_output_contract_v2.py`。该测试刻意只检查当前生成契约，不全局禁止英文旧文件名，因为兼容性规则允许在“保留旧产物”的文字中提及它们。

```python
import re
from pathlib import Path
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = REPOSITORY_ROOT / "project-career-kit"
SKILL_PATH = PACKAGE_ROOT / "SKILL.md"
CONTRACT_PATH = PACKAGE_ROOT / "references" / "output-contract.md"
EXPECTED_OUTPUTS = [
    "career-kit/简历素材.md",
    "career-kit/面试逐字稿.md",
    "career-kit/项目流程图.md",
    "career-kit/证据索引.md",
]


def section(text: str, start: str, end: str) -> str:
    start_index = text.index(start)
    end_index = text.index(end, start_index + len(start))
    return text[start_index:end_index]


class OutputContractV2Tests(unittest.TestCase):
    def setUp(self):
        self.skill = SKILL_PATH.read_text(encoding="utf-8")
        self.contract = CONTRACT_PATH.read_text(encoding="utf-8")

    def test_current_output_list_is_exactly_the_four_chinese_files(self):
        output_block = section(self.contract, "## 生成文件", "## 证据工作流")
        listed = re.findall(r"(?m)^- `([^`]+\.md)`$", output_block)
        self.assertEqual(listed, EXPECTED_OUTPUTS)
        for output_path in EXPECTED_OUTPUTS:
            self.assertIn("`" + output_path + "`", self.skill)
        self.assertNotRegex(self.skill, r"创建 `career-kit/(resume|interview-script|flowchart|evidence)\.md`")
        self.assertIn("不得重命名、删除或编辑", self.skill)

    def test_flow_template_places_evidence_comments_immediately_before_content(self):
        flow_template = section(
            self.contract,
            "## career-kit/项目流程图.md",
            "## career-kit/证据索引.md",
        )
        mermaid = re.search(r"(?s)~~~mermaid\n(.*?)\n~~~", flow_template)
        self.assertIsNotNone(mermaid)
        lines = mermaid.group(1).splitlines()
        self.assertTrue(lines[0].startswith("flowchart"))
        meaningful = re.compile(
            r"^\s*(?:[A-Za-z_][A-Za-z0-9_]*\s*\[|[A-Za-z_][A-Za-z0-9_]*\s*--.*>)"
        )
        comments = re.compile(r"^\s*%% evidence:C\d{3,}(?:,C\d{3,})*\s*$")
        checked = 0
        for index, line in enumerate(lines):
            if meaningful.match(line):
                checked += 1
                self.assertGreater(index, 0)
                self.assertRegex(lines[index - 1], comments)
        self.assertGreaterEqual(checked, 4)
        self.assertNotRegex(mermaid.group(1), r"(?m)^\s*[A-D]\s*\[")
        self.assertNotIn("## 图例与边界", flow_template)

    def test_project_framing_requires_cross_validation_and_blocks_unconfirmed_ownership(self):
        instructions = self.skill + "\n" + self.contract
        self.assertRegex(instructions, r"README.*(?:源码|配置).*交叉验证")
        self.assertIn("这是一个用于", instructions)
        self.assertIn("不得写成“README 将其描述为", instructions)
        self.assertRegex(instructions, r"E3[\s\S]{0,160}(?:我设计|我实现)")

    def test_learning_fixture_cross_validates_its_positioning(self):
        root = REPOSITORY_ROOT / "tests" / "fixtures" / "backend-learning-project"
        purpose = "多智能体协作技术实践"
        self.assertIn(purpose, (root / "README.md").read_text(encoding="utf-8"))
        self.assertIn(purpose, (root / "pyproject.toml").read_text(encoding="utf-8"))
        route = (root / "app" / "api" / "tasks.py").read_text(encoding="utf-8")
        self.assertIn("APIRouter", route)
        self.assertIn("TaskService", route)
```

- [ ] **Step 4: 运行 RED/GREEN 前的基线**

运行 inventory 测试并确认它通过；然后只运行 V2 契约测试，确认它因当前英文产物名、A/B/C 图例或缺少图内 `%% evidence:` 注释而失败。

```powershell
python -X utf8 -m unittest tests.test_project_inventory -v
python -X utf8 -m unittest tests.test_output_contract_v2 -v
```

预期：第一条命令通过；第二条命令至少有一项失败。保留失败输出，不要修改 inventory 脚本来让文档测试通过。

- [ ] **Step 5: 提交测试和夹具基线**

```powershell
git add tests docs/superpowers/specs/2026-09-07-project-career-kit-v2-design.md
git commit -m "test: define project career kit v2 contract"
```

### Task 2: 更新可分发 Skill 与输出契约

**文件：**
- 修改：`project-career-kit/SKILL.md`
- 修改：`project-career-kit/references/output-contract.md`
- 测试：`tests/test_output_contract_v2.py`

**接口：**
- 目标项目的当前产物集合严格等于 Task 1 的 `EXPECTED_OUTPUTS`。
- `career-kit/证据索引.md` 是唯一持久证据源；文本段落/列表继续使用 `<!-- evidence:C... -->`，Mermaid 节点和有意义的边改用紧邻前置的 `%% evidence:C...`。
- `项目流程图.md` 至少有一个 `flowchart`，直接承载最小已验证链路；内部 ID 有描述性，用户可见标签为简洁中文。

- [ ] **Step 1: 在 `SKILL.md` 中替换产物路径和证据文件名**

把所有“当前生成目标”替换为以下路径，并在工作边界紧接输出规则处加入兼容性句：

```markdown
- 只在用户提供或明确接受的项目根目录创建 `career-kit/简历素材.md`、`career-kit/面试逐字稿.md`、`career-kit/项目流程图.md`、`career-kit/证据索引.md`。新一轮运行只写入这四个中文文件；不得重命名、删除或编辑此前生成的英文文件名产物，也不得生成其他项目文件。
```

将 `evidence.md` 的“唯一证据源”规则、所有输出清单、QA 条目和最终回复路径全部改为 `证据索引.md`。将 `resume.md`、`interview-script.md`、`flowchart.md` 的当前输出引用分别改为 `简历素材.md`、`面试逐字稿.md`、`项目流程图.md`；仅兼容性说明可提及旧英文文件名。

- [ ] **Step 2: 将 Mermaid 证据规则从可见图例迁移至图内注释**

在 `SKILL.md` 的段落级覆盖、流程图与最终 QA 规则中使用以下明确分界：文本事实段落和完整列表项仍在末尾保留一个隐藏 HTML 引用；Mermaid 图内的每个实质节点声明及有意义边则紧邻前置一条 Mermaid 注释。删除“每个节点/边都必须有可见图例”的要求。

```markdown
- Mermaid 图内的每个实质节点声明及有意义边，紧邻前一行必须是 `%% evidence:C001,C002` 形式的注释；该 ID 集合直接指向 `证据索引.md` 中覆盖该节点或边的证据陈述。不能用图外图例、来源定位或相邻节点的引用代替该注释。
- `项目流程图.md` 的核心 `flowchart` 必须在图中直接表达最小已验证链路。节点标签使用简洁中文；内部 ID 使用描述性名称而不显示为用户标签。不得使用 A/B/C 通用占位节点后再用可见长图例补述真实链路。
- 可见文字只允许按需提供一条简短边界说明，且只说明有证据支持的运行时未知项或 Mermaid 兼容性限制；不得写节点/边的长篇图例。
```

保留 Skill 自己“快速决策”流程图，它不是目标项目生成的 `项目流程图.md`，不属于 V2 禁止的用户产物图例模式。

- [ ] **Step 3: 在 `SKILL.md` 中加入项目开发视角规则**

紧接 README 交叉验证和第一人称归属规则，加入下列约束：

```markdown
- README 只有在与源码或配置完成必要交叉验证后才能确定项目定位。在 `简历素材.md` 和 `面试逐字稿.md` 中，把已验证定位写成直接项目语言，例如“这是一个用于多智能体协作技术实践的项目”；不得写成“README 将其描述为……”。`证据索引.md` 仍将 README 作为 E2 来源记录。
- 没有 E3 用户确认时，简历和面试材料只以“项目”或“代码”为主语，不得写“我设计”或“我实现”。
```

- [ ] **Step 4: 重写 `output-contract.md` 的生成清单和四份模板**

将现有 `## Evidence Workflow` 标题改为 `## 证据工作流`。在此标题之前建立结构可测试的当前产物清单，标题必须是 `## 生成文件`，并保持下列顺序：

```markdown
## 生成文件

- `career-kit/简历素材.md`
- `career-kit/面试逐字稿.md`
- `career-kit/项目流程图.md`
- `career-kit/证据索引.md`
```

在该清单后写明“新一轮运行只生成以上四个中文文件；不重命名、删除或编辑已有英文文件名产物”。将所有模板标题替换为对应的中文文件路径，将证据源引用替换为 `证据索引.md`。在简历和逐字稿模板中加入 README 已交叉验证后的直接项目语言及无 E3 时禁止第一人称的规则。

- [ ] **Step 5: 用图内证据注释替换流程图模板和紧凑示例**

把 `## career-kit/项目流程图.md` 模板写成下列形态。示例节点展示格式，真正生成时必须按证据替换为项目专属标签和 ID；不要保留 `## 图例与边界` 标题或 A/B/C/D 长图例。

```markdown
## career-kit/项目流程图.md

~~~~markdown
# 项目流程图：订单路由接口

## 核心流程
~~~mermaid
flowchart TD
    %% evidence:C003
    createOrderRoute["代码定义创建订单接口<br/>POST /orders"]
    %% evidence:C004
    validateOrderPayload["校验 sku 与 quantity"]
    %% evidence:C003,C005
    callOrderService["调用订单服务"]
    %% evidence:C005
    returnCreatedStatus["返回 created 状态"]
    %% evidence:C003,C004
    createOrderRoute --> validateOrderPayload
    %% evidence:C003,C004,C005
    validateOrderPayload --> callOrderService
    %% evidence:C005
    callOrderService --> returnCreatedStatus
~~~

## 边界说明（仅在需要时）
在本次已读 handler、service 与 publisher 源码范围内，真实运行时响应为【未知】。 <!-- evidence:C011 -->
~~~~
```

对可选的 `sequenceDiagram` 或架构图也应用同样的“实质节点/有意义边紧邻 `%% evidence:`”规则；不满足复杂图条件时保留非项目事实 HTML 注释，不列举未经证据支持的缺失能力。将紧凑 FastAPI 示例中的 A/B/C/D 图和可见图例替换为项目专属订单链路及对应注释。

- [ ] **Step 6: 运行 V2 契约测试并修正已观察到的失败**

```powershell
python -X utf8 -m unittest tests.test_output_contract_v2 -v
```

预期：所有 V2 契约测试通过。若失败，只修改 `SKILL.md` 或 `references/output-contract.md` 中与失败断言直接对应的规则或示例；不要改变测试来接受旧英文文件名、A/B/C 图例或 README 资料摘要式表述。

- [ ] **Step 7: 提交 V2 可分发契约**

```powershell
git add project-career-kit/SKILL.md project-career-kit/references/output-contract.md
git commit -m "feat: upgrade project career kit output contract"
```

### Task 3: 运行全量静态、脚本与包结构验证

**文件：**
- 不新增 production 文件。
- 可能修改：`project-career-kit/SKILL.md` 或 `project-career-kit/references/output-contract.md`，仅当本任务的具体失败证明需要收窄规则时。

**接口：**
- inventory 测试、V2 契约测试和 `unittest discover` 都以退出码 `0` 完成。
- Skill 校验器接受 `project-career-kit/` 的 frontmatter 和资源结构。
- inventory CLI 可以安全盘点 V2 学习项目夹具，且不读取源码正文。

- [ ] **Step 1: 运行完整 Python 测试集**

```powershell
python -X utf8 -m unittest discover -s tests -v
```

预期：全部测试通过；若文件符号链接权限在当前 Windows 环境不可用，只有该单个测试可显示 `skipped`，不得把其他失败标记为跳过。

- [ ] **Step 2: 对夹具运行包内 inventory CLI**

```powershell
$inventory = python -X utf8 project-career-kit/scripts/project_inventory.py tests/fixtures/backend-learning-project | ConvertFrom-Json
if (-not $inventory.readme_present) { throw 'learning fixture README was not detected' }
if (-not ($inventory.files.path -contains 'app/api/tasks.py')) { throw 'task route was not inventoried' }
if (-not ($inventory.candidate_files.category -contains 'route_handler')) { throw 'task route category was not detected' }
'inventory smoke test: PASS'
```

预期：输出 `inventory smoke test: PASS`，且不运行目标项目、不安装依赖。

- [ ] **Step 3: 校验 Skill 包和未触及的边界文件**

```powershell
python -X utf8 C:\Users\Administrator\.codex\skills\.system\skill-creator\scripts\quick_validate.py project-career-kit
git diff --exit-code -- project-career-kit/agents/openai.yaml project-career-kit/scripts/project_inventory.py
git diff --check
```

预期：校验器退出码为 `0`；两个排除文件没有 diff；没有空白错误。

- [ ] **Step 4: 仅在真实失败后进行最小修复并重跑完整验证**

当且仅当 Step 1、2 或 3 失败时，保存失败命令、失败文本和根因。只修改能解释该失败的测试、Skill 契约或评测文档，随后依次重跑 Step 1、2、3；不要为假设性模型行为补充全局规则。

- [ ] **Step 5: 提交验证工件**

```powershell
git add tests
git commit -m "test: verify project career kit v2 contract"
```

### Task 4: 执行新鲜上下文的前向场景并记录结果

**文件：**
- 创建：`docs/superpowers/evals/2026-09-08-project-career-kit-v2.md`
- 在系统临时目录生成：名称以 `backend-learning-project-v2-` 开头、以随机 GUID 结尾的 `career-kit/`；不得在仓库夹具内生成用户产物。

**接口：**
- 输入是 Task 1 的 `backend-learning-project` 副本与 V2 Skill。
- 输出严格包含四个中文 Markdown 文件；图内证据 ID 全部存在于 `证据索引.md`；学习定位使用项目语言且不声称第一人称归属。

- [ ] **Step 1: 创建与仓库隔离的前向项目副本**

```powershell
$forwardRoot = Join-Path ([IO.Path]::GetTempPath()) ('backend-learning-project-v2-' + [guid]::NewGuid().ToString('N'))
Copy-Item -LiteralPath 'tests/fixtures/backend-learning-project' -Destination $forwardRoot -Recurse
$forwardRoot
```

预期：打印独立目录路径；后续所有 `career-kit/` 输出只写入该目录。

- [ ] **Step 2: 用新鲜上下文执行真实用户请求**

向未获此前结论的新鲜代理仅提供 Skill 路径、`$forwardRoot` 路径和以下请求：

```text
请使用 project-career-kit 只读扫描这个后端项目，为后端开发岗位生成默认中文 Markdown 求职材料。
```

不得提供预期节点名、证据 ID、预期文件内容或已知失败；代理应按 Skill 自行生成 `$forwardRoot/career-kit/`。

- [ ] **Step 3: 对生成结果运行机械验收**

```powershell
$kit = Join-Path $forwardRoot 'career-kit'
$expected = @('简历素材.md', '面试逐字稿.md', '项目流程图.md', '证据索引.md') | Sort-Object
$actual = Get-ChildItem -LiteralPath $kit -File | ForEach-Object Name | Sort-Object
$errors = [System.Collections.Generic.List[string]]::new()
if (Compare-Object $expected $actual) { $errors.Add('输出文件集合不是四个中文文件') }

$evidence = Get-Content -Raw -LiteralPath (Join-Path $kit '证据索引.md')
$knownIds = [System.Collections.Generic.HashSet[string]]::new([string[]]([regex]::Matches($evidence, '(?m)^\|\s*(C\d{3,})\s*\|') | ForEach-Object { $_.Groups[1].Value }))
$flow = Get-Content -Raw -LiteralPath (Join-Path $kit '项目流程图.md')
$block = [regex]::Match($flow, '(?s)```mermaid\s*(flowchart\s+.*?)(?:\r?\n)```')
if (-not $block.Success) { $errors.Add('没有 Mermaid flowchart') }
if ($flow -match '## 图例与边界') { $errors.Add('仍包含可见长图例标题') }
if ($flow -match '(?m)^\s*[A-D]\s*\[') { $errors.Add('仍使用 A/B/C/D 通用节点') }
if ($block.Success) {
    $lines = $block.Groups[1].Value -split "\r?\n"
    for ($index = 1; $index -lt $lines.Count; $index++) {
        $line = $lines[$index]
        if ($line -match '^\s*(?:[A-Za-z_][A-Za-z0-9_]*\s*\[|[A-Za-z_][A-Za-z0-9_]*\s*--.*>)') {
            if ($lines[$index - 1] -notmatch '^\s*%% evidence:(C\d{3,}(?:,C\d{3,})*)\s*$') {
                $errors.Add('节点或边前缺少紧邻证据注释: ' + $line)
            } else {
                foreach ($id in $Matches[1].Split(',')) {
                    if (-not $knownIds.Contains($id)) { $errors.Add('Mermaid 引用了不存在的证据 ID: ' + $id) }
                }
            }
        }
    }
}

$prose = (Get-Content -Raw -LiteralPath (Join-Path $kit '简历素材.md')) + "`n" + (Get-Content -Raw -LiteralPath (Join-Path $kit '面试逐字稿.md'))
if ($prose -notmatch '多智能体协作技术实践') { $errors.Add('未写出经交叉验证的学习项目用途') }
if ($prose -notmatch '(这是一个|该项目).{0,24}用于') { $errors.Add('学习项目用途没有用直接项目语言表述') }
if ($prose -match 'README\s*将其描述') { $errors.Add('出现 README 资料摘要式表述') }
if ($prose -match '我(?:设计|实现)') { $errors.Add('无 E3 确认时出现第一人称归属') }
if ($evidence -notmatch '(?s)README.*?\|\s*E2\s*\|') { $errors.Add('证据索引没有将 README 作为 E2 来源保留') }

if ($errors.Count) { $errors | ForEach-Object { Write-Error $_ }; exit 1 }
'V2 forward acceptance: PASS'
```

预期：命令输出 `V2 forward acceptance: PASS` 且退出码为 `0`。若失败，保留临时目录用于核对，只针对已观察到的失败修改契约，再从 Step 1 重跑。

- [ ] **Step 4: 进行独立语义审查**

让第二个只读审查者读取夹具源码、四个生成文件、`SKILL.md` 和 `output-contract.md`。要求它只报告以下问题，并给出文件和行号：图内标签或边不能由其 `%% evidence:` 引用的证据陈述直接支持；图把静态代码声明说成已发生的运行时行为；README 学习定位缺少源码/配置交叉验证；没有 E3 却出现第一人称归属。

预期：没有严重或重要问题。若有问题，按其对应的证据或表述缺口进行最小修复，再重跑 Step 1 至 Step 4。

- [ ] **Step 5: 记录评测证据并提交**

在 `docs/superpowers/evals/2026-09-08-project-career-kit-v2.md` 记录：夹具相对路径、用户请求、临时目录、生成文件集合、Mermaid 节点/边检查结果、解析到的证据 ID 数量、README E2 记录、项目用途表述、第一人称检查、独立审查结论和未修改 inventory 脚本的证明。不要复制敏感值或完整生成材料。

```powershell
git add docs/superpowers/evals/2026-09-08-project-career-kit-v2.md
git commit -m "test: record project career kit v2 forward evaluation"
```

### Task 5: 最终复核与交付准备

**文件：**
- 不新增 source 文件；仅在审查发现严重或重要问题时修改对应的测试或包内 Markdown。

**接口：**
- V2 文档、测试和评测记录都与确认的中文规格一致。
- 工作树不包含由本任务引入的未提交产物；不推送远程仓库，除非用户另行要求。

- [ ] **Step 1: 请求独立代码审查**

让只读审查者以 `master` 的实施前基线为比较对象，检查 `project-career-kit/SKILL.md`、`references/output-contract.md`、`tests/` 和 V2 规格。重点检查中文文件集合、旧英文产物兼容、图内注释紧邻性、可见图例移除、README 表述、E3 归属限制以及未修改的 `agents/openai.yaml` 和 inventory 脚本。

- [ ] **Step 2: 修复真实审查问题并运行完整验证**

对每个严重或重要问题，先补充能够复现它的断言或保留前向输出，再做最小修复。随后依次运行：

```powershell
python -X utf8 -m unittest discover -s tests -v
python -X utf8 C:\Users\Administrator\.codex\skills\.system\skill-creator\scripts\quick_validate.py project-career-kit
git diff --exit-code -- project-career-kit/agents/openai.yaml project-career-kit/scripts/project_inventory.py
git diff --check
git status --short --branch
```

预期：测试和校验命令退出码为 `0`；排除文件没有 diff；状态中不出现目标项目的临时 `career-kit/` 输出。若 Git 暂存/提交受权限策略阻止，保留验证输出并报告阻塞原因，不使用绕过性文件系统操作。

- [ ] **Step 3: 提交最终修复（仅在 Step 2 修改文件时）**

```powershell
git add project-career-kit tests docs/superpowers/evals docs/superpowers/specs
git commit -m "fix: finalize project career kit v2"
```

- [ ] **Step 4: 向用户交付**

报告四个新产物名称、V2 规格与计划路径、测试/校验命令的实际结果、前向评测结论，以及没有推送远程仓库这一事实。
