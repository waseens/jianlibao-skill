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
LEGACY_OUTPUTS = {
    "career-kit/resume.md",
    "career-kit/interview-script.md",
    "career-kit/flowchart.md",
    "career-kit/evidence.md",
}
AUDIT_METADATA = (
    r"<!--|%%\s*evidence:|\bC[-_:]?\d+[A-Za-z0-9_-]*\b|\bE[1-4]\b|"
    r"来源等级|结论清单|下游材料映射|扫描记录"
)
SOURCE_LOCATION = re.compile(r"`([^`:\\]+(?:/[^`:\\]+)*):(\d+)-(\d+)`")


def section(text: str, start: str, end: str) -> str:
    start_index = text.index(start)
    end_index = text.index(end, start_index + len(start))
    return text[start_index:end_index]


def markdown_template(contract: str, start: str, end: str) -> str:
    template_section = section(contract, start, end)
    match = re.search(r"(?s)~~~~markdown\n(.*?)\n~~~~", template_section)
    if match is None:
        raise AssertionError(f"missing Markdown template in {start}")
    return match.group(1)


def source_locations(text: str) -> list[tuple[str, int, int]]:
    return [
        (path, int(start), int(end))
        for path, start, end in SOURCE_LOCATION.findall(text)
    ]


class OutputContractV2Tests(unittest.TestCase):
    def setUp(self):
        self.skill = SKILL_PATH.read_text(encoding="utf-8")
        self.contract = CONTRACT_PATH.read_text(encoding="utf-8")

    def test_current_output_list_is_exactly_the_four_chinese_files(self):
        output_block = section(self.contract, "## 生成文件", "## 内部事实核验")
        listed = re.findall(r"(?m)^- `([^`]+\.md)`$", output_block)
        self.assertEqual(listed, EXPECTED_OUTPUTS)
        for legacy_path in LEGACY_OUTPUTS:
            self.assertNotIn(legacy_path, self.skill)
        skill_output_paths = set(re.findall(r"career-kit/[^\s`\"'<>]+\.md", self.skill))
        self.assertEqual(skill_output_paths, set(EXPECTED_OUTPUTS))
        self.assertIn("不得重命名、删除或编辑", self.skill)

    def test_evidence_index_is_a_two_section_input_checklist(self):
        template = markdown_template(
            self.contract,
            "## career-kit/证据索引.md",
            "## 后端项目核验重点",
        )
        headings = re.findall(r"(?m)^## (.+)$", template)
        self.assertEqual(headings, ["输入与默认值", "待用户确认"])
        self.assertIn("目标岗位", template)
        self.assertIn("语言与格式", template)
        self.assertIn("本人参与范围", template)
        self.assertIn("个人职责", template)
        self.assertNotRegex(template, AUDIT_METADATA)
        for prohibited in ("扫描记录", "冲突与未知", "证据等级", "确定性"):
            self.assertNotIn(prohibited, template)

    def test_learning_materials_hide_audit_metadata_and_keep_learning_locations(self):
        resume = markdown_template(
            self.contract,
            "## career-kit/简历素材.md",
            "## career-kit/面试逐字稿.md",
        )
        interview = markdown_template(
            self.contract,
            "## career-kit/面试逐字稿.md",
            "## career-kit/项目流程图.md",
        )
        flow = markdown_template(
            self.contract,
            "## career-kit/项目流程图.md",
            "## career-kit/证据索引.md",
        )
        for artifact, template in {
            "简历素材.md": resume,
            "面试逐字稿.md": interview,
            "项目流程图.md": flow,
        }.items():
            with self.subTest(artifact=artifact):
                self.assertNotRegex(template, AUDIT_METADATA)
                self.assertNotRegex(
                    template,
                    r"(?m)^\|.*(?:来源|证据|映射|扫描).*\|\s*$",
                )

        self.assertIn("源码定位（备查）", interview)
        self.assertRegex(interview, r"`<相对路径>:<起始行>-<结束行>`")
        self.assertNotRegex(resume, SOURCE_LOCATION)
        self.assertIn("## 学习导航", flow)
        self.assertRegex(flow, r"`<相对路径>:<起始行>-<结束行>`")

    def test_source_locations_are_limited_to_key_learning_sections(self):
        resume = markdown_template(
            self.contract,
            "## career-kit/简历素材.md",
            "## career-kit/面试逐字稿.md",
        )
        interview = markdown_template(
            self.contract,
            "## career-kit/面试逐字稿.md",
            "## career-kit/项目流程图.md",
        )
        index = markdown_template(
            self.contract,
            "## career-kit/证据索引.md",
            "## 后端项目核验重点",
        )
        sixty_seconds = section(interview, "## 60 秒概述", "## 3 分钟概述")
        three_minutes = section(interview, "## 3 分钟概述", "## 核心链路说明")
        core_chain = section(interview, "## 核心链路说明", "## 难点与亮点回答")
        highlights = section(interview, "## 难点与亮点回答", "## 技术取舍说明")

        for material in (resume, index, sixty_seconds, three_minutes):
            self.assertNotRegex(material, SOURCE_LOCATION)
        self.assertRegex(core_chain, r"(?s)> 源码定位（备查）：.*<相对路径>")
        self.assertRegex(highlights, r"(?s)> 源码定位（备查）：.*<相对路径>")

    def test_skill_allows_learning_source_locations_while_banning_audit_provenance(self):
        self.assertIn("源码定位（备查）", self.skill)
        self.assertNotIn("四个交付文件中都不得出现 HTML evidence 注释、`%% evidence:`、编号化证据、来源等级、来源定位", self.skill)

    def test_user_material_rules_keep_scan_narration_internal(self):
        rule = "不在求职材料中叙述本次扫描、已读或已检查范围"
        self.assertIn(rule, self.skill)
        self.assertIn(rule, self.contract)

    def test_spoken_summaries_do_not_narrate_cross_validation(self):
        rule = "不得在口播中叙述 README、配置或源码的交叉验证过程"
        self.assertIn(rule, self.skill)
        self.assertIn(rule, self.contract)

    def test_compact_flow_uses_fixture_initialization_order(self):
        example = self.contract[self.contract.index("## 紧凑示例（fixture）") :]
        graph = re.search(r"(?s)~~~mermaid\n(.*?)\n~~~", example).group(1)
        self.assertIn("bindTaskService --> defineTaskRoute", graph)
        self.assertNotIn("defineTaskRoute --> bindTaskService", graph)

    def test_flow_template_has_a_clean_mermaid_graph_and_learning_navigation(self):
        template = markdown_template(
            self.contract,
            "## career-kit/项目流程图.md",
            "## career-kit/证据索引.md",
        )
        mermaid = re.search(r"(?s)~~~mermaid\n(.*?)\n~~~", template)
        self.assertIsNotNone(mermaid)
        graph = mermaid.group(1)
        self.assertTrue(graph.splitlines()[0].startswith("flowchart"))
        self.assertNotRegex(graph, r"(?m)^\s*%%")
        meaningful = re.compile(
            r"^\s*(?:[A-Za-z_][A-Za-z0-9_]*\s*(?:\[|\(|\{)|"
            r"[A-Za-z_][A-Za-z0-9_]*\s*(?:--.*>|==>|-.->))"
        )
        self.assertGreaterEqual(
            sum(bool(meaningful.match(line)) for line in graph.splitlines()),
            4,
        )
        navigation = template[mermaid.end() :]
        self.assertRegex(navigation, r"(?m)^## 学习导航$")
        self.assertRegex(navigation, r"(?m)^- .+：`<相对路径>:<起始行>-<结束行>`$")

    def test_compact_example_uses_learning_locations_without_audit_metadata(self):
        example = self.contract[self.contract.index("## 紧凑示例（fixture）") :]
        self.assertNotRegex(example, AUDIT_METADATA)
        self.assertNotRegex(
            example,
            r"(?m)^\|.*(?:来源|证据|映射|扫描).*\|\s*$",
        )
        self.assertIn("源码定位（备查）", example)
        self.assertIn("## 学习导航", example)
        self.assertGreaterEqual(len(source_locations(example)), 3)
        fixture_root = REPOSITORY_ROOT / "tests" / "fixtures" / "backend-learning-project"
        for relative_path, start, end in source_locations(example):
            with self.subTest(path=relative_path, start=start, end=end):
                self.assertGreaterEqual(start, 1)
                self.assertGreaterEqual(end, start)
                source_file = fixture_root / relative_path
                self.assertTrue(source_file.is_file(), source_file)
                self.assertGreaterEqual(
                    len(source_file.read_text(encoding="utf-8").splitlines()),
                    end,
                )

    def test_project_framing_requires_cross_validation_and_blocks_unconfirmed_ownership(self):
        instructions = self.skill + "\n" + self.contract
        self.assertRegex(instructions, r"README.*(?:源码|配置).*交叉验证")
        self.assertIn("这是一个用于", instructions)
        self.assertIn("不得写成“README 将其描述为", instructions)
        self.assertIn("不得写“我设计”或“我实现”", instructions)
        self.assertNotRegex(instructions, r"\bE[1-4]\b")

    def test_learning_fixture_cross_validates_its_positioning(self):
        root = REPOSITORY_ROOT / "tests" / "fixtures" / "backend-learning-project"
        purpose = "多智能体协作技术实践"
        self.assertIn(purpose, (root / "README.md").read_text(encoding="utf-8"))
        self.assertIn(purpose, (root / "pyproject.toml").read_text(encoding="utf-8"))
        route = (root / "app" / "api" / "tasks.py").read_text(encoding="utf-8")
        self.assertIn("APIRouter", route)
        self.assertIn("TaskService", route)
