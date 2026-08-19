#!/usr/bin/env python3
"""Create non-destructive lesson scaffolds for the Agent course repository."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


SKILL_ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = SKILL_ROOT / "references" / "course-plan.json"
SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
MAX_SLUG_LENGTH = 80
MAX_CATALOG_TEXT_LENGTH = 240


class ScaffoldError(ValueError):
    """Raised for invalid input or an unsafe repository layout."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create missing lesson files without overwriting existing files."
    )
    parser.add_argument(
        "--repo-root",
        required=True,
        help="Absolute or relative path to the repository root.",
    )
    parser.add_argument("--week", type=int, help="Week number from 1 to 24.")
    parser.add_argument("--lesson", type=int, help="Lesson number within the week: 1 or 2.")
    parser.add_argument(
        "--all-lessons",
        action="store_true",
        help="Create both catalog lessons for --week.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Create all 48 catalog lesson scaffolds.",
    )
    parser.add_argument(
        "--slug",
        help="Optional safe slug override for one selected lesson.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned changes without writing files.",
    )
    return parser.parse_args()


def fail(message: str) -> None:
    raise ScaffoldError(message)


def validate_slug(slug: str) -> str:
    if len(slug) > MAX_SLUG_LENGTH or not SLUG_PATTERN.fullmatch(slug):
        fail(
            "slug 只能包含小写字母、数字和单个连字符分隔的片段，"
            f"且长度不能超过 {MAX_SLUG_LENGTH}。"
        )
    return slug


def load_catalog() -> list[dict[str, Any]]:
    try:
        with CATALOG_PATH.open("r", encoding="utf-8") as catalog_file:
            payload = json.load(catalog_file)
    except (OSError, json.JSONDecodeError) as error:
        fail(f"无法读取课程目录 {CATALOG_PATH}: {error}")

    if not isinstance(payload, dict) or not isinstance(payload.get("lessons"), list):
        fail("课程目录格式无效：lessons 必须是数组。")

    lessons: list[dict[str, Any]] = []
    for entry in payload["lessons"]:
        if not isinstance(entry, dict):
            fail("课程目录格式无效：每个 lesson 必须是对象。")
        required = ("week", "lesson", "title", "slug", "focus")
        if any(key not in entry for key in required):
            fail("课程目录格式无效：lesson 缺少必要字段。")
        if (
            not isinstance(entry["week"], int)
            or not 1 <= entry["week"] <= 24
            or not isinstance(entry["lesson"], int)
            or entry["lesson"] not in (1, 2)
        ):
            fail("课程目录格式无效：week/lesson 超出允许范围。")
        for key in ("title", "slug", "focus"):
            if not isinstance(entry[key], str) or not entry[key].strip():
                fail(f"课程目录格式无效：{key} 必须是非空字符串。")
            if len(entry[key]) > MAX_CATALOG_TEXT_LENGTH or any(
                character in entry[key] for character in ("\x00", "\r", "\n")
            ):
                fail(f"课程目录格式无效：{key} 超出长度或包含控制字符。")
        validate_slug(entry["slug"])
        lessons.append(entry)

    if len(lessons) != 48 or len({(item["week"], item["lesson"]) for item in lessons}) != 48:
        fail("课程目录格式无效：必须包含唯一的 48 节课。")
    return lessons


def resolve_repo_root(raw_root: str) -> Path:
    root = Path(raw_root).expanduser().resolve()
    if not root.is_dir():
        fail(f"repo root 不是目录：{root}")
    courses_root = (root / "courses").resolve()
    if not courses_root.is_dir():
        fail(f"repo root 下不存在 courses/ 目录：{courses_root}")
    try:
        courses_root.relative_to(root)
    except ValueError:
        fail("courses/ 目录解析后不在 repo root 内，已停止写入。")
    return root


def safe_path(base: Path, *parts: str) -> Path:
    candidate = base.joinpath(*parts).resolve()
    try:
        candidate.relative_to(base.resolve())
    except ValueError:
        fail(f"拒绝写入 repo root 外部路径：{candidate}")
    return candidate


def select_lessons(
    catalog: list[dict[str, Any]], args: argparse.Namespace
) -> list[dict[str, Any]]:
    if args.all and any(value is not None for value in (args.week, args.lesson)):
        fail("--all 不能和 --week/--lesson 一起使用。")
    if args.all and (args.all_lessons or args.slug):
        fail("--all 不能和 --all-lessons/--slug 一起使用。")
    if args.all_lessons and args.lesson is not None:
        fail("--all-lessons 不能和 --lesson 一起使用。")
    if args.slug and (args.all_lessons or args.all or args.lesson is None):
        fail("--slug 只能用于单节课，并且必须同时提供 --week 和 --lesson。")

    if args.all:
        return catalog
    if args.week is None:
        fail("必须提供 --week，或使用 --all。")
    if not 1 <= args.week <= 24:
        fail("--week 必须在 1 到 24 之间。")
    if args.all_lessons:
        return [item for item in catalog if item["week"] == args.week]
    if args.lesson is None:
        fail("单节课需要同时提供 --lesson，或使用 --all-lessons。")
    if args.lesson not in (1, 2):
        fail("--lesson 必须是 1 或 2。")
    selected = [
        item
        for item in catalog
        if item["week"] == args.week and item["lesson"] == args.lesson
    ]
    if not selected:
        fail("找不到指定课程。")
    if args.slug:
        selected[0] = {**selected[0], "slug": validate_slug(args.slug)}
    return selected


def render_files(lesson: dict[str, Any]) -> dict[str, str]:
    week = lesson["week"]
    number = lesson["lesson"]
    title = lesson["title"]
    focus = lesson["focus"]
    return {
        "lesson.md": f"""# 第 {week} 周 · 第 {number} 节：{title}

> 状态：待授课
> 主题：{focus}

## 1. 本节学习目标

- TODO：补充本节完成后必须掌握的知识和能力。

## 2. 前置知识

- TODO：列出本节需要的前置知识。

## 3. 核心概念

- TODO：由课程内容对话补充概念讲解。

## 4. 架构与实现

- TODO：补充本节架构图、数据流和 TypeScript 实现。

## 5. 常见错误与安全边界

- TODO：记录失败案例、输入校验、权限和数据暴露风险。

## 6. 课后复盘

- TODO：记录本节学到的内容和未解决问题。
""",
        "assignment.md": f"""# 第 {week} 周 · 第 {number} 节课后作业

## 作业目标

围绕“{title}”完成一个最小、可测试的实现。

## 课程—作业映射

| 作业编号 | 对应课程章节 | 作业要求 |
| --- | --- | --- |
| A1 | TODO：填写 `lesson.md` 的章节 | TODO：概念理解任务 |
| A2 | TODO：填写 `lesson.md` 的章节 | TODO：TypeScript/Node.js 编码任务 |
| A3 | TODO：填写 `lesson.md` 的章节 | TODO：失败场景或安全场景测试 |

每个作业要求都必须能在 `lesson.md` 找到完整介绍。不能在作业中引入课程没有讲过的新 API、库、模式或安全概念。

## 练习

### A1：概念练习

TODO：补充与课程内容直接相关的概念练习。

### A2：编码练习

TODO：补充与课程示例和接口直接相关的编码练习。这里只写任务要求，不生成解答代码。

### A3：失败或安全场景

TODO：补充课程中已经介绍过的失败处理或安全场景测试。

## 提交内容

- [ ] 更新 `lesson.md` 中需要补充的复盘内容。
- [ ] 完成 A1 概念练习。
- [ ] 完成 A2 编码练习；解答代码由学习者自行编写。
- [ ] 完成 A3 失败或安全场景测试。
- [ ] 在 `answer.md` 中记录设计决策和测试结果。

不要提交 API Key、访问 Token、Cookie、真实用户数据或生产日志。
""",
        "acceptance.md": f"""# 第 {week} 周 · 第 {number} 节验收标准

## 一一对应映射

验收标准必须与 `assignment.md` 的 A1–A3 一一对应。不得在本文件新增作业中没有要求的内容。

| 验收编号 | 作业编号 | 验收证据 |
| --- | --- | --- |
| AC-A1 | A1 | TODO：填写概念回答或设计说明的位置 |
| AC-A2 | A2 | TODO：填写实现文件、运行结果或演示证据 |
| AC-A3 | A3 | TODO：填写失败/安全测试及结果 |

## 验收标准

- [ ] AC-A1（对应 A1）：TODO：只能验收 A1 已明确要求的内容。
- [ ] AC-A2（对应 A2）：TODO：只能验收 A2 已明确要求的内容。
- [ ] AC-A3（对应 A3）：TODO：只能验收 A3 已明确要求的内容。

""",
        "answer.md": f"""# 第 {week} 周 · 第 {number} 节作业记录

## 我的理解

TODO：用自己的话总结“{title}”。

## 设计决策

TODO：记录关键接口、数据流和取舍。

## 测试结果

TODO：记录运行的命令、通过数量和失败分析。

## 未解决问题

TODO：记录需要下一节课或后续复习的问题。
""",
        "implementation/README.md": """# Implementation

本目录存放本节课新增或演示的最小 TypeScript 实现。

- 代码必须保持可读、可测试。
- 脚手架不会自动生成作业解答代码；作业实现由学习者自行完成。
- 不要提交 API Key、Token、Cookie 或真实用户数据。
- 完整 Runtime 模块成熟后，再按课程安排迁移到仓库根目录 `src/`。
""",
        "tests/README.md": """# Tests

本目录存放本节课的单元测试和集成测试。

测试任务由 `assignment.md` 定义，脚手架不会自动生成作业测试解答。至少覆盖作业要求的正常场景和非法输入或失败场景；测试不应依赖真实模型供应商、网络服务或生产凭证。
""",
    }


def append_week_index(week_dir: Path, lesson: dict[str, Any], dry_run: bool) -> str:
    week = lesson["week"]
    number = lesson["lesson"]
    slug = lesson["slug"]
    title = lesson["title"]
    readme_path = week_dir / "README.md"
    entry = f"- [ ] Lesson {number:02d}: [{title}](./lesson-{number:02d}-{slug}/)"

    if readme_path.exists():
        if not readme_path.is_file():
            fail(f"预期是文件但实际不是文件：{readme_path}")
        current = readme_path.read_text(encoding="utf-8")
        if entry in current:
            return "skipped existing index entry"
        return "skipped existing week README"

    content = f"# Week {week:02d}\n\n## 课程目录\n\n{entry}\n"
    if not dry_run:
        readme_path.write_text(content, encoding="utf-8")
    return "created week index"


def scaffold_one(root: Path, lesson: dict[str, Any], dry_run: bool) -> list[str]:
    week = lesson["week"]
    number = lesson["lesson"]
    slug = validate_slug(lesson["slug"])
    courses_root = (root / "courses").resolve()
    week_dir = safe_path(courses_root, f"week-{week:02d}")
    lesson_dir = safe_path(week_dir, f"lesson-{number:02d}-{slug}")

    if week_dir.exists() and not week_dir.is_dir():
        fail(f"预期是目录但实际不是目录：{week_dir}")
    if lesson_dir.exists() and not lesson_dir.is_dir():
        fail(f"预期是目录但实际不是目录：{lesson_dir}")

    planned: list[str] = []
    if not week_dir.exists():
        planned.append(f"create directory {week_dir.relative_to(root)}")
        if not dry_run:
            week_dir.mkdir(parents=False, exist_ok=False)
    if not lesson_dir.exists():
        planned.append(f"create directory {lesson_dir.relative_to(root)}")
        if not dry_run:
            lesson_dir.mkdir(parents=False, exist_ok=False)

    for relative_path, content in render_files(lesson).items():
        file_path = safe_path(lesson_dir, *Path(relative_path).parts)
        if file_path.exists():
            if not file_path.is_file():
                fail(f"预期是文件但实际不是文件：{file_path}")
            planned.append(f"skip existing {file_path.relative_to(root)}")
            continue
        planned.append(f"create file {file_path.relative_to(root)}")
        if not dry_run:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding="utf-8")

    index_result = append_week_index(week_dir, lesson, dry_run)
    planned.append(f"{index_result} {week_dir.relative_to(root)}/README.md")
    return planned


def main() -> int:
    args = parse_args()
    try:
        root = resolve_repo_root(args.repo_root)
        catalog = load_catalog()
        lessons = select_lessons(catalog, args)
        for lesson in lessons:
            print(f"Lesson {lesson['week']:02d}/{lesson['lesson']:02d}: {lesson['title']}")
            for action in scaffold_one(root, lesson, args.dry_run):
                print(f"  - {action}")
        if args.dry_run:
            print("Dry run completed; no files were written.")
        else:
            print(f"Scaffold completed for {len(lessons)} lesson(s); existing files were preserved.")
        return 0
    except (OSError, UnicodeError, ScaffoldError) as error:
        print(f"scaffold_lesson.py: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
