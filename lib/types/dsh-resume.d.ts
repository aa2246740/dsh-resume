import type { Context } from '@deepseek-ai/cordis';
export declare const name = "dsh-resume";
export declare const inject: string[];
/** Register one read-only reader tool and three user-only slash skills. */
export declare function apply(ctx: Context): void;
export { buildReaderArgs, runSessionReader, SESSION_READER_PATH } from './reader.ts';
export { RESUME_SKILL_SPECS, resumeSkillContent, skillRegistration } from './skills.ts';
//# sourceMappingURL=dsh-resume.d.ts.map