import type { SkillRegistration } from '@deepseek-ai/dsh-skill';
import type { ForeignSessionProvider } from './reader.ts';
export interface ResumeSkillSpec {
    readonly name: `resume-${string}`;
    readonly provider: ForeignSessionProvider;
    readonly product: string;
    readonly description: string;
    readonly recoveryBoundary: string;
}
export declare const RESUME_SKILL_SPECS: readonly [{
    readonly name: "resume-codex";
    readonly provider: "codex";
    readonly product: "Codex";
    readonly description: "继续当前工作目录中的 Codex 会话；可附会话 ID、记录路径或标题关键词。";
    readonly recoveryBoundary: "The reader excludes Codex system, developer, reasoning, world-state, and inter-agent records.";
}, {
    readonly name: "resume-claude";
    readonly provider: "claude";
    readonly product: "Claude Code";
    readonly description: "继续当前工作目录中的 Claude Code 会话；可附会话 ID、记录路径或标题关键词。";
    readonly recoveryBoundary: "The reader follows the recoverable Claude session branch and excludes private or replaced content.";
}, {
    readonly name: "resume-cursor";
    readonly provider: "cursor";
    readonly product: "Cursor";
    readonly description: "继续当前工作目录中的 Cursor 会话；可附会话 ID、记录路径或标题关键词。";
    readonly recoveryBoundary: "The reader imports only supported Cursor transcript or store records and never replays stored calls.";
}, {
    readonly name: "resume-grok";
    readonly provider: "grok";
    readonly product: "Grok";
    readonly description: "继续当前工作目录中的 Grok 会话；可附会话 ID、会话目录、记录路径或标题关键词。";
    readonly recoveryBoundary: "The reader uses Grok's visible updates.jsonl stream only; it never reads raw chat_history.jsonl model context.";
}, {
    readonly name: "resume-pi";
    readonly provider: "pi";
    readonly product: "Pi";
    readonly description: "继续当前工作目录中的 Pi 会话；可附会话 ID、JSONL 路径或标题关键词。";
    readonly recoveryBoundary: "The reader follows Pi's current active leaf only and excludes thinking, hooks, system messages, and extension-injected records.";
}, {
    readonly name: "resume-zcode";
    readonly provider: "zcode";
    readonly product: "ZCode";
    readonly description: "继续当前工作目录中的 ZCode 会话；可附会话 ID、记录路径或标题关键词。";
    readonly recoveryBoundary: "The reader uses the ZCode sqlite store at cli/db/db.sqlite and does not replay calls or revive the CLI. Abandoned v2 sessions and cli/rollout JSONL are ignored. Projects JSONL is a warned fallback only when sqlite is absent. Compaction is a summary marker; older rows still stored are kept.";
}, {
    readonly name: "resume-trae";
    readonly provider: "trae";
    readonly product: "Trae";
    readonly description: "继续当前工作目录中的 Trae 会话；可附会话 ID、记录路径或标题关键词。";
    readonly recoveryBoundary: "The reader uses Trae's SQLCipher 4 store at ModularData/ai-agent/database.db (TRAE_HOME or TRAE_AGENT_DIR). It decrypts a private snapshot only and never writes back, replays calls, or revives Trae. Hidden thought/reasoning is excluded. ~/.trae, TinyStorage, Chromium Session Storage, and state.vscdb are not transcript sources.";
}];
/** One source of truth for all seven user-only slash skills. */
export declare function skillRegistration(spec: ResumeSkillSpec): SkillRegistration;
export declare function resumeSkillContent(spec: ResumeSkillSpec): string;
//# sourceMappingURL=skills.d.ts.map