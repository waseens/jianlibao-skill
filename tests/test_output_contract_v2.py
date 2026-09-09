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


class OutputContractV2Tests(unittest.TestCase):
    def setUp(self):
        self.skill = SKILL_PATH.read_text(encoding="utf-8")
        self.contract = CONTRACT_PATH.read_text(encoding="utf-8")

    def test_current_output_list_is_exactly_the_four_chinese_files(self):
        output_block = section(self.contract, "## 生成文件", "## 证据工作流")
        listed = re.findall(r"(?m)^- `([^`]+\.md)`$", output_block)
        self.assertEqual(listed, EXPECTED_OUTPUTS)
        for legacy_path in LEGACY_OUTPUTS:
            self.assertNotIn(legacy_path, self.skill)
        skill_output_paths = set(re.findall(r"career-kit/[^\s`\"'<>]+\.md", self.skill))
        self.assertEqual(skill_output_paths, set(EXPECTED_OUTPUTS))
        self.assertIn("不得重命名、删除或编辑", self.skill)

    def test_flow_template_places_evidence_comments_immediately_before_content(self):
        flow_template = section(
            self.contract,
            "## career-kit/项目流程图.md",
            "## career-kit/证据索引.md",
        )
        markdown_template = re.search(r"(?s)~~~~markdown\n(.*?)\n~~~~", flow_template)
        self.assertIsNotNone(markdown_template)
        template_body = markdown_template.group(1)
        mermaid_blocks = re.findall(r"(?s)~~~mermaid\n(.*?)\n~~~", template_body)
        self.assertEqual(len(mermaid_blocks), 1)
        mermaid = re.search(r"(?s)~~~mermaid\n(.*?)\n~~~", template_body)
        self.assertIsNotNone(mermaid)
        self.assertEqual(
            template_body[:mermaid.start()],
            "# 项目流程图：<项目/模块名>\n\n## 核心流程\n",
        )
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
        self.assertNotIn("图例", template_body)
        self.assertNotRegex(template_body, r"(?m)^\s*(?:[-*+]\s+|\d+[.)]\s+|\|)")
        after_mermaid = template_body[mermaid.end():].strip()
        self.assertRegex(
            after_mermaid,
            r"\A(?:|## 边界说明（仅在需要时）\n[^\n]+\s+<!-- evidence:C\d{3,}(?:,C\d{3,})* -->)\Z",
        )

    def test_route_to_payload_edges_cite_field_constraint_evidence(self):
        examples = {
            "full template": section(
                self.contract,
                "## career-kit/项目流程图.md",
                "## career-kit/证据索引.md",
            ),
            "compact example": self.contract[
                self.contract.index("## Compact Example (fixture)") :
            ],
        }
        edge = "defineOrderRoute --> receiveCreateOrderPayload"
        for name, example in examples.items():
            with self.subTest(example=name):
                lines = example.splitlines()
                edge_index = lines.index(next(line for line in lines if edge in line))
                self.assertEqual(
                    lines[edge_index - 1].strip(),
                    "%% evidence:C003,C004",
                )

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
