export declare const FOREIGN_SESSION_PROVIDERS: readonly ["claude", "codex", "cursor", "grok", "pi"];
export type ForeignSessionProvider = typeof FOREIGN_SESSION_PROVIDERS[number];
export declare const FOREIGN_SESSION_ACTIONS: readonly ["show", "list"];
export type ForeignSessionAction = typeof FOREIGN_SESSION_ACTIONS[number];
export declare const SESSION_READER_PATH: string;
export declare const GROK_SESSION_READER_PATH: string;
export interface ReaderRequest {
    readonly provider: ForeignSessionProvider;
    readonly action: ForeignSessionAction;
    readonly cwd: string;
    readonly reference?: string;
    readonly withinMinutes?: number;
    readonly maxToolChars?: number;
    readonly signal?: AbortSignal;
    readonly readerPath?: string;
    readonly maxOutputBytes?: number;
}
/** Build the fixed, shell-free reader argv used by the DSH tool. */
export declare function buildReaderArgs(request: ReaderRequest): string[];
/**
 * Run the read-only Grok-compatible reader wrapper as a bounded child process.
 * Exit 2 is returned as ordinary text because it carries disambiguation
 * candidates the agent must show to the user.
 */
export declare function runSessionReader(request: ReaderRequest): Promise<string>;
//# sourceMappingURL=reader.d.ts.map