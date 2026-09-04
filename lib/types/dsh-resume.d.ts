import type { Context } from '@deepseek-ai/cordis';
export declare const name = "dsh-resume";
export declare const inject: string[];
/** Register one read-only reader tool and five user-only slash skills. */
export declare function apply(ctx: Context): void;
export { buildReaderArgs, GROK_SESSION_READER_PATH, runSessionReader, SESSION_READER_PATH, slashReferenceFromSession, slashReferenceFromUserText, } from './reader.ts';
export { RESUME_SKILL_SPECS, resumeSkillContent, skillRegistration } from './skills.ts';
//# sourceMappingURL=dsh-resume.d.ts.map