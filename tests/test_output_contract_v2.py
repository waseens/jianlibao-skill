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


def section(text: str, start: str, end: str) -> str:
    start_index = text.index(start)
    end_index = text.index(end, start_index + len(start))
    return text[start_index:end_index]


def output_paths_outside_compatibility(text: str) -> set[str]:
    paths = set()
    for paragraph in re.split(r"\n\s*\n", text):
        is_compatibility_note = (
            "不得重命名、删除或编辑" in paragraph
            or "保留旧产物" in paragraph
            or bool(re.search(r"(?:保留|兼容).*(?:旧|早期|已有)", paragraph))
        )
        for path in re.findall(r"`(career-kit/[^`]+\.md)`", paragraph):
            if path not in LEGACY_OUTPUTS or not is_compatibility_note:
                paths.add(path)
    return paths


class OutputContractV2Tests(unittest.TestCase):
    def setUp(self):
        self.skill = SKILL_PATH.read_text(encoding="utf-8")
        self.contract = CONTRACT_PATH.read_text(encoding="utf-8")

    def test_current_output_list_is_exactly_the_four_chinese_files(self):
        output_block = section(self.contract, "## 生成文件", "## 证据工作流")
        listed = re.findall(r"(?m)^- `([^`]+\.md)`$", output_block)
        self.assertEqual(listed, EXPECTED_OUTPUTS)
        self.assertEqual(output_paths_outside_compatibility(self.skill), set(EXPECTED_OUTPUTS))
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
            r"^\s*(?:[A-Za-z_][A-Za-z0-9_]*\s*(?:\[|\(|\{)|[A-Za-z_][A-Za-z0-9_]*\s*(?:--.*>|==>|-.->))"
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
        visible_legend_entries = re.findall(
            r"(?m)^-\s+`?[^：:\n`]{1,40}`?\s*[：:]",
            flow_template,
        )
        self.assertLess(len(visible_legend_entries), 4)

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
