import { randomUUID } from "node:crypto";

export type MessageRole = "system" | "user" | "assistant" | "tool";

export interface ToolCall {
  readonly id: string;
  readonly name: string;
  readonly arguments: unknown;
}

export interface Message {
  readonly role: MessageRole;
  readonly content: string;
  readonly toolCallId?: string;
  readonly toolCalls?: readonly ToolCall[];
}

export interface ToolSpec {
  readonly name: string;
  readonly description: string;
  readonly sideEffect: "read" | "write";
  readonly inputSchema: object;
}

export interface ModelRequest {
  readonly messages: readonly Message[];
  readonly tools: readonly ToolSpec[];
  readonly signal?: AbortSignal | undefined;
}

export type ModelDecision =
  | {
      readonly type: "final";
      readonly text: string;
    }
  | {
      readonly type: "tool_calls";
      readonly calls: readonly ToolCall[];
    };

export interface ModelGateway {
  complete(request: ModelRequest): Promise<ModelDecision>;
}

export interface ToolRegistry {
  list(): readonly ToolSpec[];
}

export interface ContextBuilder {
  build(state: AgentState): readonly Message[];
}

export interface AgentState {
  readonly runId: string;
  readonly status: "running" | "waiting_tool" | "completed" | "failed";
  readonly step: number;
  readonly messages: Message[];
}

export type AgentEvent =
  | {
      readonly type: "run.started";
      readonly runId: string;
      readonly inputLength: number;
      readonly occurredAt: number;
    }
  | {
      readonly type: "model.decision";
      readonly runId: string;
      readonly decisionType: ModelDecision["type"];
      readonly toolNames?: readonly string[];
      readonly occurredAt: number;
    }
  | {
      readonly type: "run.failed";
      readonly runId: string;
      readonly name: string;
      readonly message: string;
      readonly occurredAt: number;
    }
  | {
      readonly type: "run.completed";
      readonly runId: string;
      readonly resultType: "final";
      readonly occurredAt: number;
    }
  | {
      readonly type: "run.cancelled",
      readonly runId: string;
      readonly occurredAt: number;
  }


export interface EventSink {
  emit(event: AgentEvent): Promise<void>;
}


export class AgentRuntimeError extends Error {
  runId: string;
  override name: 'ToolExecutor' | 'ToolContract' | 'ModelDecision' | 'Aborted' | 'Unknown';
  occurredAt: number;

  constructor(runId: AgentRuntimeError['runId'], name: AgentRuntimeError['name'], message: AgentRuntimeError['message']) {
    super(redactSensitiveMessage(message));
    this.runId = runId;
    this.name = name;
    this.occurredAt = Date.now();
  }
}

function redactSensitiveMessage(message: string): string {
  return message
    .replace(
      /\bcookie\b\s*[:=]\s*("[^"]*"|'[^']*'|[^\r\n]+)/gi,
      "cookie=**",
    )
    .replace(
      /\b(api[_-]?key|access[_-]?token|refresh[_-]?token|client[_-]?secret|secret|password|passwd|token|authorization|session(?:id)?|private[_-]?key)\b\s*[:=]\s*("[^"]*"|'[^']*'|Bearer\s+[A-Za-z0-9._~+/=-]+|[^\s,;]+)/gi,
      (_match, key: string) => `${key}=**`,
    )
    .replace(/\bBearer\s+[A-Za-z0-9._~+/=-]+/gi, "Bearer **");
}

function getSafeErrorName(error: unknown): AgentRuntimeError["name"] {
  if (!(error instanceof AgentRuntimeError)) {
    return "Unknown";
  }

  switch (error.name) {
    case "ToolExecutor":
    case "ToolContract":
    case "ModelDecision":
    case "Aborted":
    case "Unknown":
      return error.name;
    default:
      return "Unknown";
  }
}

export interface RuntimeDependencies {
  readonly model: ModelGateway;
  readonly tools: ToolRegistry;
  readonly context: ContextBuilder;
  readonly events: EventSink;
}

export type RunResult =
  | {
      readonly type: "final";
      readonly runId: string;
      readonly text: string;
    }
  | {
      readonly type: "tool_calls";
      readonly runId: string;
      readonly calls: readonly ToolCall[];
    };

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function assertToolCall(state: AgentState, value: unknown): asserts value is ToolCall {
  if (!isRecord(value)) {
    throw new AgentRuntimeError(state.runId, 'ToolContract', "工具调用格式无效");
  }

  if (
    typeof value.id !== "string" ||
    value.id.length < 1 ||
    value.id.length > 128
  ) {
    throw new AgentRuntimeError(state.runId, 'ToolContract', "工具调用 id 无效");
  }

  if (
    typeof value.name !== "string" ||
    value.name.length < 1 ||
    value.name.length > 100
  ) {
    throw new AgentRuntimeError(state.runId, 'ToolContract', "工具名称无效");
  }

  if (
    !Object.prototype.hasOwnProperty.call(value, "arguments") ||
    (!isRecord(value.arguments) && !Array.isArray(value.arguments))
  ) {
    throw new AgentRuntimeError(state.runId, 'ToolContract', "工具参数必须是对象或数组");
  }
}

export function assertModelDecision(
  state: AgentState,
  value: unknown,
): asserts value is ModelDecision {
  if (!isRecord(value)) {
    throw new AgentRuntimeError(state.runId, 'ModelDecision', "模型返回的数据格式无效");
  }

  if (value.type === "final") {
    if (
      typeof value.text !== "string" ||
      value.text.trim().length === 0 ||
      value.text.length > 12_000
    ) {
      throw new AgentRuntimeError(state.runId, 'ModelDecision', "模型最终文本无效或超出长度限制");
    }

    return;
  }

  if (value.type === "tool_calls") {
    if (!Array.isArray(value.calls) || value.calls.length > 8) {
      throw new AgentRuntimeError(state.runId, 'ToolContract', "模型工具调用数量无效")
    }

    for (const call of value.calls) {
      assertToolCall(state, call);
    }

    return;
  }

  throw new AgentRuntimeError(state.runId, 'Unknown', "未知的模型决策类型");
}

export class LessonOneRuntime {
  private readonly deps: RuntimeDependencies;

  public constructor(deps: RuntimeDependencies) {
    this.deps = deps;
  }

  public async run(
    rawInput: unknown,
    signal?: AbortSignal,
  ): Promise<RunResult> {

    const runId = randomUUID();

    if (typeof rawInput !== "string") {
      throw new AgentRuntimeError(runId, 'Aborted', "用户输入必须是字符串");
    }

    const input = rawInput.trim();

    if (input.length === 0 || input.length > 4_000) {
      throw new AgentRuntimeError(runId, 'Aborted', "用户输入长度无效");
    }

    const state: AgentState = {
      runId,
      status: "running",
      step: 0,
      messages: [
        {
          role: "user",
          content: input,
        },
      ],
    };

    if (signal?.aborted) {
      this.emitSafely({
        type: 'run.cancelled',
        runId: state.runId,
        occurredAt: Date.now()
      })
      throw new AgentRuntimeError(state.runId, 'Aborted', "任务已取消");
    }

    try {
      await this.emitSafely({
        type: "run.started",
        runId: state.runId,
        inputLength: input.length,
        occurredAt: Date.now()
      });

      let decision: ModelDecision;

      const response = await this.deps.model.complete({
          messages: this.deps.context.build(state),
          tools: this.deps.tools.list(),
          signal,
        });

        assertModelDecision(state, response);
        decision = response;

      await this.emitSafely({
        type: "model.decision",
        runId: state.runId,
        occurredAt: Date.now(),
        decisionType: decision.type,
        ...(decision.type === "tool_calls"
          ? { toolNames: decision.calls.map((call) => call.name) }
          : {}),
      });

      if (decision.type === "final") {
        await this.emitSafely({
          type: 'run.completed',
          runId: state.runId,
          occurredAt: Date.now(),
          resultType: 'final'
        })
        return {
          type: "final",
          runId: state.runId,
          text: decision.text,
        };
      }

      return {
        type: "tool_calls",
        runId: state.runId,
        calls: decision.calls,
      };
    } catch (error) {
      await this.emitSafely({
        type: 'run.failed',
        runId: state.runId,
        name: getSafeErrorName(error),
        message: "任务执行失败",
        occurredAt: Date.now()
      })
      throw error;
    }
  }

  private async emitSafely(event: AgentEvent): Promise<void> {
    try {
      await this.deps.events.emit(event);
    } catch {
      // 事件写入失败不应泄露原始错误内容或敏感数据。
      console.warn("agent_event_sink_failed", {
        eventType: event.type,
      });
    }
  }
}
