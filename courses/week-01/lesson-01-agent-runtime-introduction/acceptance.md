# 第 1 节验收标准

## 一一对应映射

本文件只验收 `assignment.md` 中的 A1–A3，不新增作业中没有要求的知识或实现。

| 验收编号 | 作业编号 | 验收证据 |
| --- | --- | --- |
| AC-A1 | A1 | `answer.md` 中的信任边界图、概念回答和停止条件说明。 |
| AC-A2 | A2 | `implementation/lesson-one-runtime.ts`、对应测试和 `npm test` 结果。 |
| AC-A3 | A3 | `answer.md` 中的事件字段/时机/用途说明、TypeScript 类型和安全检查结果。 |

## AC-A1（对应 A1）

- [ ] 能用自己的话解释 Agent 和 Chatbot 的区别。
- [ ] 能解释 Agent 和固定 Workflow 的区别。
- [ ] 能说明模型为什么不能直接执行工具。
- [ ] 能画出 Model Gateway、Runtime、Tool Executor 的关系，并标注决策、执行、权限、状态和验证边界。
- [ ] 能解释 `run.started`、`model.decision` 和 `run.completed` 的触发时机及用途。
- [ ] 能说明公共事件是给 UI、日志和监控消费的观察钩子，不是模型的决策输入。
- [ ] 能说出至少三个 Agent 停止条件，并说明它们防止的问题。

## AC-A2（对应 A2）

- [ ] 工具调用 `id` 是 1–128 个字符的字符串。
- [ ] 工具名称是 1–100 个字符的字符串。
- [ ] 工具调用数组不超过 8 个。
- [ ] `arguments` 不是 `undefined`，并且是对象或数组。
- [ ] 工具调用数组中的每项是对象，不能是数组或 `null`。
- [ ] 使用 `unknown` 表示尚未校验的工具参数，并定义了 `ModelDecision` 联合类型边界。
- [ ] 每条新增校验规则都有对应测试，测试覆盖正常输入和非法输入。
- [ ] 测试不依赖真实模型供应商或真实工具，且 `npm test` 通过。

## AC-A3（对应 A3）

- [ ] 设计了 `run.started`、`model.decision` 和 `run.completed` 三类公共事件。
- [ ] 事件字段、触发时机和用途在 `answer.md` 中有说明，并可用 TypeScript 表达。
- [ ] 事件不包含 API Key、Token、Cookie、完整用户输入、完整工具参数或模型隐藏思维过程。
- [ ] 事件能够被 React UI、日志和监控消费。

自选扩展 `run.cancelled` 不属于本节必选验收；只有提交该扩展时才额外检查其实现和测试。
