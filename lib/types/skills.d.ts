import type { SkillRegistration } from '@deepseek-ai/dsh-skill';
import type { ForeignSessionProvider } from './reader.ts';
export interface ResumeSkillSpec {
    readonly name: `resume-${string}`;
    readonly provider: ForeignSessionProvider;
    readonly product: string;
    readonly description: string;
}
export declare const RESUME_SKILL_SPECS: readonly [{
    readonly name: "resume-codex";
    readonly provider: "codex";
    readonly product: "Codex";
    readonly description: "继续当前工作目录中的 Codex 会话；可附会话 ID、记录路径或标题关键词。";
}, {
    readonly name: "resume-claude";
    readonly provider: "claude";
    readonly product: "Claude Code";
    readonly description: "继续当前工作目录中的 Claude Code 会话；可附会话 ID、记录路径或标题关键词。";
}, {
    readonly name: "resume-cursor";
    readonly provider: "cursor";
    readonly product: "Cursor";
    readonly description: "继续当前工作目录中的 Cursor 会话；可附会话 ID、记录路径或标题关键词。";
}];
/** One source of truth for all three user-only slash skills. */
export declare function skillRegistration(spec: ResumeSkillSpec): SkillRegistration;
export declare function resumeSkillContent(spec: ResumeSkillSpec): string;
//# sourceMappingURL=skills.d.ts.map