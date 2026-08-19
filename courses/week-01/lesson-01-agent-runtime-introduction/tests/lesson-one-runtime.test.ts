



import assert from "node:assert/strict";
import test from "node:test";

import {
  AgentRuntimeError,
  LessonOneRuntime,
  type AgentEvent,
  type ContextBuilder,
  type EventSink,
  type ModelGateway,
  type RuntimeDependencies,
  type ToolRegistry,
} from "../implementation/lesson-one-runtime.ts";

test("AgentRuntimeError 会过滤疑似 secret", () => {
  const error = new AgentRuntimeError(
    "run-1",
    "Unknown",
    'provider failed api_key=secret-demo Authorization: Bearer bearer-demo password="password-demo"',
  );

  assert.equal(
    error.message,
    "provider failed api_key=** Authorization=** password=**",
  );
  assert.doesNotMatch(error.message, /secret-demo|bearer-demo|password-demo/);
});

function createRuntime(
  model: ModelGateway,
  receivedEvents: AgentEvent[] = [],
): LessonOneRuntime {
  const tools: ToolRegistry = {
    list() {
      return [];
    },
  };

  const context: ContextBuilder = {
    build(state) {
      return state.messages;
    },
  };

  const events: EventSink = {
    async emit(event) {
      receivedEvents.push(event);
    },
  };

  const dependencies: RuntimeDependencies = {
    model,
    tools,
    context,
    events,
  };

  return new LessonOneRuntime(dependencies);
}

test("模型返回 final 时，Runtime 返回最终结果", async () => {
  const runtime = createRuntime({
    async complete() {
      return {
        type: "final",
        text: "这是最终答案",
      };
    },
  });

  const result = await runtime.run("你好");

  assert.equal(result.type, "final");

  if (result.type === "final") {
    assert.equal(result.text, "这是最终答案");
    assert.match(result.runId, /^[0-9a-f-]{36}$/);
  }
});


test("工具id无效", async () => {
  const runtime = createRuntime({
    async complete() {
      return {
        type: "tool_calls",
        calls: [
          {
            id: "",
            name: "searchDocuments",
            arguments: {
              query: "agent runtime",
            },
          },
        ],
      };
    },
  });
  await assert.rejects(
    () => runtime.run("搜索 Agent Runtime 文档"),
    /工具调用 id 无效/,
  );
});



test("工具名称无效", async () => {
  const receivedEvents: AgentEvent[] = [];
  const runtime = createRuntime({
    async complete() {
      return {
        type: "tool_calls",
        calls: [
          {
            id: "call-1",
            name: "",
            arguments: {
              query: "agent runtime",
            },
          },
        ],
      };
    },
  }, receivedEvents);
  await assert.rejects(
    () => runtime.run("搜索 Agent Runtime 文档").catch(error => {
      const events = receivedEvents.map(r => r.type);
      assert.deepEqual(events, ['run.started', 'run.failed'])
      throw error;
    }),
    /工具名称无效/,
  )
});


test("工具调用数据不能超过8个", async () => {
  const runtime = createRuntime({
    async complete() {
      return {
        type: "tool_calls",
        calls: [
          {
            id: "call-1",
            name: "searchDocuments",
            arguments: {
              query: "agent runtime",
            },
          },
          {
            id: "call-1",
            name: "searchDocuments",
            arguments: {
              query: "agent runtime",
            },
          },
          {
            id: "call-1",
            name: "searchDocuments",
            arguments: {
              query: "agent runtime",
            },
          },
          {
            id: "call-1",
            name: "searchDocuments",
            arguments: {
              query: "agent runtime",
            },
          },
          {
            id: "call-1",
            name: "searchDocuments",
            arguments: {
              query: "agent runtime",
            },
          },
          {
            id: "call-1",
            name: "searchDocuments",
            arguments: {
              query: "agent runtime",
            },
          },
          {
            id: "call-1",
            name: "searchDocuments",
            arguments: {
              query: "agent runtime",
            },
          },
          {
            id: "call-1",
            name: "searchDocuments",
            arguments: {
              query: "agent runtime",
            },
          },
          {
            id: "call-1",
            name: "searchDocuments",
            arguments: {
              query: "agent runtime",
            },
          },
        ],
      };
    },
  });
  await assert.rejects(
    () => runtime.run("搜索 Agent Runtime 文档"),
    /模型工具调用数量无效/,
  );
});


test("工具调用参数校验", async () => {
  const runtime = createRuntime({
    async complete() {
      return {
        type: "tool_calls",
        calls: [
          {
            id: "call-1",
            name: "searchDocuments",
            arguments: null,
          },
        ],
      };
    },
  });

  await assert.rejects(
    () => runtime.run("搜索 Agent Runtime 文档"),
    /工具参数必须是对象或数组/,
  );
});



test("工具调用参数校验", async () => {
  const runtime = createRuntime({
    async complete() {
      return {
        type: "tool_calls",
        calls: [
          {
            id: "call-1",
            name: "searchDocuments",
            arguments: undefined,
          },
        ],
      };
    },
  });

  await assert.rejects(
    () => runtime.run("搜索 Agent Runtime 文档"),
    /工具参数必须是对象或数组/,
  );
});



test("工具格式校验", async () => {
  const runtime = createRuntime({
    async complete() {
      return {
        type: "tool_calls",
        calls: [
          [
            {
              id: "call-1",
              name: "searchDocuments",
              arguments: undefined,
            }
          ] as any
        ],
      };
    },
  });

  await assert.rejects(
    () => runtime.run("搜索 Agent Runtime 文档"),
    /工具调用格式无效/,
  );
});


test("工具格式校验", async () => {
  const runtime = createRuntime({
    async complete() {
      return {
        type: "tool_calls",
        calls: [
          null as any
        ],
      };
    },
  });

  await assert.rejects(
    () => runtime.run("搜索 Agent Runtime 文档"),
    /工具调用格式无效/,
  );
});



test("模型返回工具调用时，Runtime 返回待执行调用", async () => {
  const runtime = createRuntime({
    async complete() {
      return {
        type: "tool_calls",
        calls: [
          {
            id: "call-1",
            name: "searchDocuments",
            arguments: {
              query: "agent runtime",
            },
          },
        ],
      };
    },
  });

  const result = await runtime.run("搜索 Agent Runtime 文档");

  assert.equal(result.type, "tool_calls");

  if (result.type === "tool_calls") {
    assert.equal(result.calls[0]?.name, "searchDocuments");
  }
});

test("空输入应该被拒绝", async () => {
  const runtime = createRuntime({
    async complete() {
      throw new Error("不应调用模型");
    },
  });

  await assert.rejects(
    () => runtime.run("   "),
    /用户输入长度无效/,
  );
});

test("超长输入应该被拒绝且不能调用模型", async () => {
  let modelCalled = false;
  const runtime = createRuntime({
    async complete() {
      modelCalled = true;
      throw new Error("不应调用模型");
    },
  });

  await assert.rejects(
    () => runtime.run("a".repeat(4_001)),
    /用户输入长度无效/,
  );

  assert.equal(modelCalled, false);
});

test("工具调用 id 超过128个字符应该被拒绝", async () => {
  const runtime = createRuntime({
    async complete() {
      return {
        type: "tool_calls",
        calls: [
          {
            id: "a".repeat(129),
            name: "searchDocuments",
            arguments: {},
          },
        ],
      };
    },
  });

  await assert.rejects(
    () => runtime.run("搜索文档"),
    /工具调用 id 无效/,
  );
});

test("工具名称超过100个字符应该被拒绝", async () => {
  const runtime = createRuntime({
    async complete() {
      return {
        type: "tool_calls",
        calls: [
          {
            id: "call-1",
            name: "a".repeat(101),
            arguments: {},
          },
        ],
      };
    },
  });

  await assert.rejects(
    () => runtime.run("搜索文档"),
    /工具名称无效/,
  );
});

test("工具调用 id 和名称的最大长度应该允许通过校验", async () => {
  const runtime = createRuntime({
    async complete() {
      return {
        type: "tool_calls",
        calls: [
          {
            id: "a".repeat(128),
            name: "a".repeat(100),
            arguments: {},
          },
        ],
      };
    },
  });

  const result = await runtime.run("搜索文档");

  assert.equal(result.type, "tool_calls");
});

test("非法模型决策应该被拒绝并记录失败事件", async () => {
  const events: AgentEvent[] = [];
  const runtime = createRuntime(
    {
      async complete() {
        return {
          type: "tool_calls",
          calls: [
            {
              id: "call-1",
              name: "readFile",
              arguments: undefined,
            },
          ],
        } as never;
      },
    },
    events,
  );

  await assert.rejects(
    () => runtime.run("读取文件"),
    /工具参数必须是对象或数组/,
  );

  assert.equal(events.at(-1)?.type, "run.failed");
});

test("依赖错误信息不会进入 run.failed 事件", async () => {
  const receivedEvents: AgentEvent[] = [];
  const sensitiveMessage = "provider failed: API_KEY=secret-demo";
  const runtime = createRuntime({
    async complete() {
      throw new Error(sensitiveMessage);
    },
  }, receivedEvents);

  await assert.rejects(
    () => runtime.run("你好"),
    (error: unknown) =>
      error instanceof Error && error.message === sensitiveMessage,
  );

  const failedEvent = receivedEvents.find((event) => event.type === "run.failed");
  assert.ok(failedEvent);
  if (failedEvent.type === "run.failed") {
    assert.equal(failedEvent.message, "任务执行失败");
    assert.doesNotMatch(failedEvent.message, /API_KEY|secret-demo/);
  }
});

test("任务在进入模型前被取消", async () => {
  const controller = new AbortController();
  controller.abort();

  const runtime = createRuntime({
    async complete() {
      throw new Error("不应调用模型");
    },
  });

  await assert.rejects(
    () => runtime.run("执行任务", controller.signal),
    (error: unknown) =>
      error instanceof Error && error.name === "Aborted",
  );
});



test("测试run.started", async () => {
  const receivedEvents: AgentEvent[] = [];
  const runtime = createRuntime({
    async complete() {
      return {
        type: "tool_calls",
        calls: [
          {
            id: "call-1",
            name: "",
            arguments: {
              query: "agent runtime",
            },
          },
        ],
      };
    },
  }, receivedEvents);

  try {
    await runtime.run("你好")
  } catch (error) {
    const events = receivedEvents.map(r => r.type);
    assert.deepEqual(events, ["run.started", "run.failed"])
  }
});

test("final 决策按 started、decision、completed 顺序发事件", async () => {
  const receivedEvents: AgentEvent[] = [];
  const runtime = createRuntime({
    async complete() {
      return {
        type: "final",
        text: "这是最终答案",
      };
    },
  }, receivedEvents);

  await runtime.run("你好");

  const events = receivedEvents.map((event) => event.type);
  assert.deepEqual(events, ["run.started", "model.decision", "run.completed"]);
});

test("工具调用决策不应发出 run.completed", async () => {
  const receivedEvents: AgentEvent[] = [];
  const runtime = createRuntime({
    async complete() {
      return {
        type: "tool_calls",
        calls: [
          {
            id: "call-1",
            name: "searchDocuments",
            arguments: {
              query: "agent runtime",
            },
          },
        ],
      };
    },
  }, receivedEvents);

  await runtime.run("搜索文档");

  const events = receivedEvents.map((event) => event.type);
  assert.deepEqual(events, ["run.started", "model.decision"]);
});
