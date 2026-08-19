---
name: create-agent-course-lesson
description: Scaffold or quality-check a lesson in the 24-week, 48-lesson hand-written AI Agent course inside this repository. Use when the user asks to create a lesson directory, week directory, lesson templates, course content, or course quality checks for the Universal Tool Agent Runtime. Do not use it to replace existing lesson content; it creates missing files only and never generates assignment solution code.
---

# Create Agent Course Lesson

This skill creates an idempotent lesson scaffold under `courses/` for the
repository's TypeScript/Node.js AI Agent course. It follows the existing
layout, keeps lesson content separate from directory creation, and applies a
quality gate when lesson content is generated or reviewed.

## When to use

Use this skill when the user asks for any of the following:

- Create a particular lesson, such as Week 3 Lesson 2.
- Create all lessons for a week.
- Create the remaining course lesson directories.
- Prepare a lesson directory before another chat writes the lesson content.

If the user asks for teaching content, use the scaffold first when the target
lesson does not exist, then write the content into the generated files. Do not
regenerate or overwrite a completed lesson.

## Repository contract

The repository root is the current working repository. Lesson directories use
this structure:

```text
courses/
  week-XX/
    README.md
    lesson-YY-topic-slug/
      lesson.md
      assignment.md
      acceptance.md
      answer.md
      implementation/README.md
      tests/README.md
```

The canonical 24-week catalog is in
[`references/course-plan.json`](references/course-plan.json). Read it when the
user asks about lesson numbering, titles, or the next lesson.

## Workflow

1. Confirm the repository root with `git rev-parse --show-toplevel` or the
   current working directory. Do not scaffold into a parent directory or an
   unrelated repository.
2. Read the existing `courses/README.md`, the relevant week README, and one
   nearby lesson before changing a course area. Preserve local conventions.
3. Select a catalog lesson by `week` and `lesson`. The catalog is authoritative
   for the default title and slug.
4. Run the deterministic scaffold script from the repository root:

   ```bash
   python3 .agents/skills/create-agent-course-lesson/scripts/scaffold_lesson.py \
     --repo-root "$PWD" --week 1 --lesson 2
   ```

   For all lessons in one week:

   ```bash
   python3 .agents/skills/create-agent-course-lesson/scripts/scaffold_lesson.py \
     --repo-root "$PWD" --week 1 --all-lessons
   ```

   To scaffold all 48 lessons, use `--all`. This is optional and creates
   placeholders only.
5. Review the script output and `git diff -- courses`. Existing files are
   intentionally skipped; never add a force/overwrite option to this workflow.
6. If the user also requested lesson content, edit only the selected lesson's
   Markdown files. Do not automatically create solution code, test solutions,
   or answer code for the assignment. Keep lesson implementation code under
   that lesson's `implementation/` directory only when the user separately
   asks for an implementation review or coding task.
7. Before reporting a generated lesson as complete, run the quality gate below.
   If any check fails, report the gap and fix the lesson/assignment/acceptance
   relationship before proceeding.

   The structural part can be checked with:

   ```bash
   python3 .agents/skills/create-agent-course-lesson/scripts/audit_lesson.py \
     --repo-root "$PWD" --week 1 --lesson 2
   ```

   This checker validates required files, unfinished placeholders, assignment
   IDs, and acceptance mappings. It cannot judge semantic relevance, so the
   manual review below is still mandatory.

## Course-content quality gate

These are hard requirements, not optional review suggestions.

### Content completeness and assignment relevance

- `lesson.md` must contain a complete explanation of the concepts required by
  the assignment, including the relevant API, data shape, algorithm, pattern,
  or security rule.
- Every assignment requirement must point to a concrete section in `lesson.md`
  using a course-to-assignment mapping table. An assignment must not require a
  library, API, pattern, implementation detail, or security concept that the
  lesson never introduced.
- If an assignment idea is useful but not taught in the lesson, either teach it
  before the assignment or remove it from the assignment. Do not silently add
  new material in the assignment.
- Check for unfinished placeholders such as `TODO`, empty required sections,
  broken internal links, and undefined terms before calling the lesson complete.
- Optional exercises follow the same rule: optional does not mean “new
  knowledge”; the lesson must still introduce everything they require.

### Assignment and acceptance one-to-one mapping

- Give every assignment requirement a stable ID such as `A1`, `A2`, and `A3`.
- `acceptance.md` must map every acceptance item to exactly one assignment ID,
  such as `AC-A1 → A1`. Include the expected evidence for that item.
- Every assignment ID must have one corresponding acceptance item, and every
  acceptance item must point to an assignment ID. No extra acceptance
  requirement may appear only in `acceptance.md`.
- If security, testing, or runtime behavior is required for acceptance, state
  that requirement in `assignment.md` first, then map it in `acceptance.md`.
- Before completion, manually compare the two files line by line and record
  the mapping in `answer.md` or the lesson review notes.

### No automatic assignment solution code

- Directory scaffolding may create `implementation/README.md` and
  `tests/README.md`, but it must not create `.ts`, `.tsx`, `.js`, test solution,
  or answer-code files for the assignment.
- Lesson examples may show small illustrative snippets in `lesson.md`; do not
  turn them into a completed assignment solution.
- Do not fill `answer.md` with the learner's solution. It is a record/template
  for the learner's own work.

## Generated file expectations

The script creates safe placeholders, not fabricated teaching material:

- `lesson.md`: objectives, prerequisites, concepts, implementation notes, and
  review prompts.
- `assignment.md`: numbered exercises (`A1`, `A2`, ...) with a course-to-
  assignment mapping table and a submission checklist.
- `acceptance.md`: acceptance items (`AC-A1`, `AC-A2`, ...) mapped one-to-one to
  the assignment IDs; it must not introduce extra requirements.
- `answer.md`: learner answer template.
- `implementation/README.md` and `tests/README.md`: locations and boundaries
  for lesson code and tests.

When another chat is used to write the actual lesson, it should replace the
placeholders in the selected lesson only and keep the directory names stable.

## Safety rules

- Treat CLI arguments and repository files as untrusted input.
- The script accepts only catalog week/lesson numbers and a constrained slug.
- All generated paths must remain below the repository's `courses/` directory.
- The script must not execute model output, shell fragments, or generated code.
- Never overwrite an existing file. If a path conflicts with the expected file
  or directory type, stop with an error.
- Do not put API keys, access tokens, cookies, private prompts, or user data in
  generated files.
- Keep lesson examples and tests free of `eval`, `new Function`, shell
  execution, raw SQL interpolation, and unsafe path handling.
- Do not generate assignment solution code automatically.

## Completion report

After scaffolding, report:

- The lesson directories created or skipped.
- The exact files created.
- Any path conflict or validation issue.
- The content-quality result: lesson completeness, assignment relevance, and
  assignment-to-acceptance one-to-one mapping.
- The next action, such as opening `lesson.md` in another chat for content
  generation.

Do not claim that lesson content, implementation, or tests are complete when
only the scaffold was created.
