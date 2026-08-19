# universal-tool-agent-runtime

A vendor-neutral Universal Tool Agent Runtime built from scratch with TypeScript and Node.js, including lessons, exercises, tests, and a React streaming UI.

## Repository layout

```text
courses/
  week-01/
    lesson-01-agent-runtime-introduction/
      lesson.md
      assignment.md
      acceptance.md
      answer-template.md
      implementation/
      tests/

src/       # final Runtime implementation, introduced incrementally
tests/     # cross-module and final-project tests
```

The `courses/` directory is the learning record. Each lesson is self-contained: it has the lesson notes, exercises, acceptance criteria, and the code/tests introduced in that lesson.

The final Runtime will live under `src/` and will be built incrementally from the lesson implementations. Lesson code is intentionally small and may be replaced by the corresponding production-oriented module later.

## Current progress

- [x] Week 1 / Lesson 1: content and starter implementation added
- [ ] Week 1 / Lesson 1: learner exercises completed

## Local development

This repository currently uses Node.js native TypeScript type stripping for the first lesson, so no Agent framework or runtime abstraction is required.

```bash
npm test
```

Do not commit API keys, access tokens, private prompts, or production user data. Use environment variables or a local secret manager for provider credentials.

## Lesson scaffolding

This repository includes the `$create-agent-course-lesson` skill. Ask Codex to
create a specific lesson or invoke the deterministic script directly from the
repository root:

```bash
python3 .agents/skills/create-agent-course-lesson/scripts/scaffold_lesson.py \
  --repo-root "$PWD" --week 1 --lesson 2
```

The script creates only missing lesson files and preserves existing lesson
content. Use `--all-lessons` for one week or `--all` for all 48 lesson
scaffolds.

完成课程内容后，运行结构审计：

```bash
python3 .agents/skills/create-agent-course-lesson/scripts/audit_lesson.py \
  --repo-root "$PWD" --week 1 --lesson 1
```

审计通过后，仍需人工确认：作业要求都已在课程中讲解，且验收标准与作业编号一一对应。
