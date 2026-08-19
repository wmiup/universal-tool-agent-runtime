#!/usr/bin/env python3
"""Audit lesson structure without modifying repository files."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from scaffold_lesson import ScaffoldError, load_catalog, resolve_repo_root, safe_path


REQUIRED_LESSON_MARKERS = {
    "学习目标": ("本节学习目标",),
    "前置知识": ("前置知识",),
    "核心概念": ("核心概念", "Agent、Chatbot", "Agent 的最小定义"),
    "架构与实现": ("架构与实现", "我们要手写的 Agent Runtime", "TypeScript 第一版核心接口"),
    "安全边界": ("常见错误与安全边界", "信任边界", "核心架构原则", "安全检查卡"),
}
PLACEHOLDER_PATTERN = re.compile(r"\b(?:TODO|TBD)\b|待补充")
ASSIGNMENT_TABLE_PATTERN = re.compile(r"^\s*\|\s*(A\d+)\s*\|", re.MULTILINE)
ACCEPTANCE_TABLE_PATTERN = re.compile(
    r"^\s*\|\s*AC-(A\d+)\s*\|\s*\1\s*\|", re.MULTILINE
)
ACCEPTANCE_ITEM_PATTERN = re.compile(
    r"^\s*(?:-\s*\[\s*\]\s*AC-(A\d+)\b|##\s+AC-(A\d+)\b)",
    re.MULTILINE,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit lesson completeness and assignment/acceptance mapping."
    )
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--week", type=int)
    parser.add_argument("--lesson", type=int)
    parser.add_argument("--all", action="store_true")
    return parser.parse_args()


def select_targets(args: argparse.Namespace) -> list[tuple[int, int]]:
    if args.all and any(value is not None for value in (args.week, args.lesson)):
        raise ScaffoldError("--all 不能和 --week/--lesson 一起使用。")
    if args.all:
        return [(week, lesson) for week in range(1, 25) for lesson in (1, 2)]
    if args.week is None or args.lesson is None:
        raise ScaffoldError("单节课审计需要同时提供 --week 和 --lesson，或使用 --all。")
    if not 1 <= args.week <= 24 or args.lesson not in (1, 2):
        raise ScaffoldError("--week 必须在 1 到 24 之间，--lesson 必须是 1 或 2。")
    return [(args.week, args.lesson)]


def read_required(path: Path, label: str, errors: list[str]) -> str:
    if not path.exists():
        errors.append(f"缺少 {label}: {path}")
        return ""
    if not path.is_file():
        errors.append(f"{label} 不是文件: {path}")
        return ""
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        errors.append(f"无法读取 {label}: {path} ({error})")
        return ""


def audit_one(root: Path, week: int, lesson: int) -> bool:
    catalog = load_catalog()
    catalog_entry = next(
        (item for item in catalog if item["week"] == week and item["lesson"] == lesson),
        None,
    )
    if catalog_entry is None:
        raise ScaffoldError(f"课程目录中不存在 Week {week} Lesson {lesson}。")

    courses_root = (root / "courses").resolve()
    lesson_dir = safe_path(
        courses_root,
        f"week-{week:02d}",
        f"lesson-{lesson:02d}-{catalog_entry['slug']}",
    )
    errors: list[str] = []
    lesson_text = read_required(lesson_dir / "lesson.md", "lesson.md", errors)
    assignment_text = read_required(
        lesson_dir / "assignment.md", "assignment.md", errors
    )
    acceptance_text = read_required(
        lesson_dir / "acceptance.md", "acceptance.md", errors
    )

    if not errors:
        missing_sections = [
            section
            for section, markers in REQUIRED_LESSON_MARKERS.items()
            if not any(marker in lesson_text for marker in markers)
        ]
        if missing_sections:
            errors.append(f"lesson.md 缺少课程结构：{', '.join(missing_sections)}")

        for label, text in (
            ("lesson.md", lesson_text),
            ("assignment.md", assignment_text),
            ("acceptance.md", acceptance_text),
        ):
            if PLACEHOLDER_PATTERN.search(text):
                errors.append(f"{label} 仍包含未完成占位符（TODO/TBD/待补充）。")

        assignment_ids = ASSIGNMENT_TABLE_PATTERN.findall(assignment_text)
        acceptance_table_ids = ACCEPTANCE_TABLE_PATTERN.findall(acceptance_text)
        acceptance_item_ids = [
            first or second
            for first, second in ACCEPTANCE_ITEM_PATTERN.findall(acceptance_text)
        ]
        expected_ids = sorted(set(assignment_ids), key=lambda item: int(item[1:]))

        if not expected_ids:
            errors.append("assignment.md 没有找到课程—作业映射表中的 A 编号。")
        if sorted(set(acceptance_table_ids), key=lambda item: int(item[1:])) != expected_ids:
            errors.append("acceptance.md 的 AC 映射表没有与 assignment.md 的 A 编号一一对应。")
        if sorted(set(acceptance_item_ids), key=lambda item: int(item[1:])) != expected_ids:
            errors.append("acceptance.md 的验收项没有与 assignment.md 的 A 编号一一对应。")
        if len(acceptance_table_ids) != len(set(acceptance_table_ids)):
            errors.append("acceptance.md 的验收映射表存在重复验收编号。")
        if len(acceptance_item_ids) != len(set(acceptance_item_ids)):
            errors.append("acceptance.md 的验收项存在重复验收编号。")

    if errors:
        print(f"FAIL Week {week:02d} Lesson {lesson:02d}")
        for error in errors:
            print(f"  - {error}")
        return False

    print(f"PASS structure Week {week:02d} Lesson {lesson:02d}")
    print("  - 需要人工确认：每个作业要求都在 lesson.md 中完整介绍，且没有引入新知识。")
    print("  - 需要人工确认：没有自动生成作业解答代码，验收内容只对应作业要求。")
    return True


def main() -> int:
    args = parse_args()
    try:
        root = resolve_repo_root(args.repo_root)
        targets = select_targets(args)
        results = [audit_one(root, week, lesson) for week, lesson in targets]
        return 0 if all(results) else 1
    except (OSError, UnicodeError, ScaffoldError) as error:
        print(f"audit_lesson.py: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
