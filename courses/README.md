# Courses

课程资料、作业和每节课产生的最小实现都放在这里。

## 目录约定

```text
courses/
  week-XX/
    lesson-YY-topic-name/
      lesson.md             # 本节课程内容
      assignment.md         # 课后作业
      acceptance.md         # 验收标准
      answer-template.md    # 作业答题模板，可选
      implementation/       # 本节新增或演示的代码
      tests/                # 本节测试
```

每节课只引入一个主要主题。课程示例优先保持可读、可测试；随着 Runtime 的核心模块成熟，最终实现会逐步迁移到仓库根目录的 `src/`。

## 学习记录

- `week-01/lesson-01-agent-runtime-introduction/`：Agent 是什么，以及 Runtime 的核心边界
