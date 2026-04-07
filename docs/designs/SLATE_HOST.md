# スレート ホストの統合 — Research & Design Doc

**日付:** 2026-04-02
**ブランチ:** garrytan/slate-agent-support
**ステータス:** 研究は完了しましたが、ホスト構成リファクタリングでブロックされました
**代替品:** なし

## スレートとは

Slate は、Random Labs が提供する独自のコーディング エージェント CLI です。
インストール: `npm i -g @randomlabs/slate` または `brew install anthropic/tap/slate`。
ライセンス: プロプライエタリ。 85MB のコンパイル済み Bun バイナリ (arm64/x64、darwin/linux/windows)。
npm パッケージ: `@randomlabs/slate@1.0.25` (薄型 8.8KB ランチャー + プラットフォーム固有のオプションの deps)。

マルチモデル: Claude Sonnet/Opus/Haiku とその他のモデルを動的に選択します。
複数時間にわたる長時間のセッションによる「群オーケストレーション」用に構築されています。

## Slate は OpenCode のフォークです

**85MB Mach-O arm64 バイナリのバイナリ文字列分析によって確認**:

- 内部名: `name: "opencode"` (バイナリのリテラル文字列)
- すべての `OPENCODE_*` 環境変数は、同等の `SLATE_*` と一緒に存在します
- OpenCode のツール/スキル アーキテクチャ、LSP 統合、端末管理を共有します。
- 独自のブランディング、API エンドポイント (`api.randomlabs.ai`、`agent-worker-prod.randomlabs.workers.dev`)、および構成パス

これは統合にとって重要です。OpenCode の規約はほとんど適用されますが、Slate では追加が加えられます。
独自のパスと環境変数がその上にあります。

## Skill Discovery (バイナリから確認)

スレートは、スキルについて 4 つのディレクトリ ファミリすべてをスキャンします。バイナリのエラー メッセージは次のことを確認します。

```
"failed .slate directory scan for skills"
"failed .claude directory scan for skills"
"failed .agents directory scan for skills"
"failed .opencode directory scan for skills"
```

**検出パス (スレート ドキュメントの優先順位):**

1. `.slate/skills/<name>/SKILL.md` — プロジェクトレベル、最高の優先度
2. `~/.slate/skills/<name>/SKILL.md` — グローバル
3. `.opencode/skills/`、`.agents/skills/` — 互換性フォールバック
4. `.claude/skills/` — クロードコード互換性フォールバック (最低)
5. `slate.json` 経由のカスタム パス

**グロブ パターン:** `**/SKILL.md` および `{skill,skills}/**/SKILL.md`

**コマンド:** 同じディレクトリ構造ですが、`commands/` サブディレクトリの下にあります:
`/.slate/commands/`、`/.claude/commands/`、`/.agents/commands/`、`/.opencode/commands/`

**スキルのフロントマター:** `name` フィールドと `description` フィールドを含む YAML (スレート ドキュメントごと)。
どちらのフィールドにも長さの制限は文書化されていません。

## プロジェクトの指示

スレートは、プロジェクトの指示として `CLAUDE.md` と `AGENTS.md` の両方を読み取ります。
両方のリテラル文字列がバイナリで確認されました。既存のものを変更する必要はありません
gstack プロジェクト... CLAUDE.md はそのまま動作します。

＃＃ 構成

**設定ファイル:** `slate.json` / `slate.jsonc` (opencode.json ではありません)

**設定オプション (スレートドキュメントより):**
- `privacy` (ブール値) — テレメトリ/ロギングを無効にします
- 権限: ツールごとに `allow`、`ask`、`deny` (`read`、`edit`、`bash`、`grep`、 `webfetch`、`websearch`、`*`)
- モデルスロット: `models.main`、`models.subagent`、`models.search`、`models.reasoning`
- MCP サーバー: カスタム コマンドとヘッダーを備えたローカルまたはリモート
- カスタムコマンド: `/commands` テンプレート付き

セットアップ スクリプトは `slate.json` を作成しないでください。ユーザーは独自の権限を構成します。

## CLI フラグ (ヘッドレス モード)

```
--stream-json / --output-format stream-json  — JSONL output, "compatible with Anthropic Claude Code SDK"
--dangerously-skip-permissions               — bypass all permission checks (CI/automation)
--input-format stream-json                   — programmatic input
-q                                           — non-interactive mode
-w <dir>                                     — workspace directory
--output-format text                         — plain text output (default)
```

**ストリーム-JSON 形式:** スレートのドキュメントでは、「Anthropic Claude Code SDK と互換性がある」と主張しています。
まだ実証的に検証されていません。 OpenCode の伝統を考慮すると、おそらく Claude Code のものと一致します。
NDJSON イベント スキーマ (タイプ: "assistant"、タイプ: "tool_result"、タイプ: "result")。

**確認が必要です:** 有効なクレジットを使用して `slate -q "hello" --stream-json` を実行し、
セッション ランナー パーサーを構築する前に、実際の JSONL イベントをキャプチャします。



### スレート固有
```
SLATE_API_KEY                              — API key
SLATE_AGENT                                — agent selection
SLATE_AUTO_SHARE                           — auto-share setting
SLATE_CLIENT                               — client identifier
SLATE_CONFIG                               — config override
SLATE_CONFIG_CONTENT                       — inline config
SLATE_CONFIG_DIR                           — config directory
SLATE_DANGEROUSLY_SKIP_PERMISSIONS         — bypass permissions
SLATE_DIR                                  — data directory override
SLATE_DISABLE_AUTOUPDATE                   — disable auto-update
SLATE_DISABLE_CLAUDE_CODE                  — disable Claude Code integration entirely
SLATE_DISABLE_CLAUDE_CODE_PROMPT           — disable Claude Code prompt loading
SLATE_DISABLE_CLAUDE_CODE_SKILLS           — disable .claude/skills/ loading
SLATE_DISABLE_DEFAULT_PLUGINS              — disable default plugins
SLATE_DISABLE_FILETIME_CHECK               — disable file time checks
SLATE_DISABLE_LSP_DOWNLOAD                 — disable LSP auto-download
SLATE_DISABLE_MODELS_FETCH                 — disable models config fetch
SLATE_DISABLE_PROJECT_CONFIG               — disable project-level config
SLATE_DISABLE_PRUNE                        — disable session pruning
SLATE_DISABLE_TERMINAL_TITLE               — disable terminal title updates
SLATE_ENABLE_EXA                           — enable Exa search
SLATE_ENABLE_EXPERIMENTAL_MODELS           — enable experimental models
SLATE_EXPERIMENTAL                         — enable experimental features
SLATE_EXPERIMENTAL_BASH_DEFAULT_TIMEOUT_MS — bash timeout override
SLATE_EXPERIMENTAL_DISABLE_COPY_ON_SELECT  — disable copy on select
SLATE_EXPERIMENTAL_DISABLE_FILEWATCHER     — disable file watcher
SLATE_EXPERIMENTAL_EXA                     — Exa search (alt flag)
SLATE_EXPERIMENTAL_FILEWATCHER             — enable file watcher
SLATE_EXPERIMENTAL_ICON_DISCOVERY          — icon discovery
SLATE_EXPERIMENTAL_LSP_TOOL               — LSP tool
SLATE_EXPERIMENTAL_LSP_TY                 — LSP type checking
SLATE_EXPERIMENTAL_MARKDOWN               — markdown mode
SLATE_EXPERIMENTAL_OUTPUT_TOKEN_MAX       — output token limit
SLATE_EXPERIMENTAL_OXFMT                  — oxfmt integration
SLATE_EXPERIMENTAL_PLAN_MODE              — plan mode
SLATE_FAKE_VCS                            — fake VCS for testing
SLATE_GIT_BASH_PATH                       — git bash path (Windows)
SLATE_MODELS_URL                          — models config URL
SLATE_PERMISSION                          — permission override
SLATE_SERVER_PASSWORD                     — server auth
SLATE_SERVER_USERNAME                     — server auth
SLATE_TELEMETRY_DISABLED                  — disable telemetry
SLATE_TEST_HOME                           — test home directory
SLATE_TOKEN_DIR                           — token storage directory
```

### OpenCode レガシー (まだ機能)
```
OPENCODE_DISABLE_LSP_DOWNLOAD
OPENCODE_EXPERIMENTAL_DISABLE_FILEWATCHER
OPENCODE_EXPERIMENTAL_FILEWATCHER
OPENCODE_EXPERIMENTAL_ICON_DISCOVERY
OPENCODE_EXPERIMENTAL_LSP_TY
OPENCODE_EXPERIMENTAL_OXFMT
OPENCODE_FAKE_VCS
OPENCODE_GIT_BASH_PATH
OPENCODE_LIBC
OPENCODE_TERMINAL
```

### gstack 統合のための重要な環境変数

**`SLATE_DISABLE_CLAUDE_CODE_SKILLS`** — 設定すると、`.claude/skills/` の読み込みが無効になります。
これにより、`.slate/skills/` への公開が単なる最適化ではなく、負荷に耐えるようになります。
ネイティブ `.slate/` を公開しないと、このフラグが設定されると gstack スキルが失われます。

**`SLATE_TEST_HOME`** — E2E テストに役立ちます。スレートのホームディレクトリをリダイレクトできる
Codex テストが一時 HOME を使用する方法と同様に、分離された一時ディレクトリにコピーされます。

**`SLATE_DANGEROUSLY_SKIP_PERMISSIONS`** — ヘッドレス E2E テストに必要です。

## モデル参照 (バイナリから)

```
anthropic/claude-sonnet-4.6
anthropic/claude-opus-4
anthropic/claude-haiku-4
anthropic/slate              — Slate's own model routing
openai/gpt-5.3-codex
google/nano-banana
randomlabs/fast-default-alpha
```

## API エンドポイント (バイナリから)

```
https://api.randomlabs.ai                          — main API
https://api.randomlabs.ai/exaproxy                 — Exa search proxy
https://agent-worker-prod.randomlabs.workers.dev   — production worker
https://agent-worker-dev.randomlabs.workers.dev    — dev worker
https://dashboard.randomlabs.ai                    — dashboard
https://docs.randomlabs.ai                         — documentation
https://randomlabs.ai/config.json                  — remote config
```

醸造タップ: `anthropic/tap/slate` (注目すべき点: Random Labs ではなく Anthropic のタップの下)

## npm パッケージ構造

```
@randomlabs/slate (8.8 kB, thin launcher)
├── bin/slate           — Node.js launcher (finds platform binary in node_modules)
├── bin/slate1          — Bun launcher (same logic, import.meta.filename)
├── postinstall.mjs     — Verifies platform binary exists, symlinks if needed
└── package.json        — Declares optionalDependencies for all platforms

Platform packages (85MB each):
├── @randomlabs/slate-darwin-arm64
├── @randomlabs/slate-darwin-x64
├── @randomlabs/slate-linux-arm64
├── @randomlabs/slate-linux-x64
├── @randomlabs/slate-linux-x64-musl
├── @randomlabs/slate-linux-arm64-musl
├── @randomlabs/slate-linux-x64-baseline
├── @randomlabs/slate-linux-x64-baseline-musl
├── @randomlabs/slate-darwin-x64-baseline
├── @randomlabs/slate-windows-x64
└── @randomlabs/slate-windows-x64-baseline
```

バイナリ オーバーライド: `SLATE_BIN_PATH` 環境変数はすべての検出をスキップし、指定されたバイナリを直接実行します。

## 現在すでに機能しているもの

gstack スキルは、`.claude/skills/` フォールバック パスを介してスレートですでに機能しています。
基本的な機能に変更は必要ありません。クロードコード用に gstack をインストールするユーザー
また、Slate を使用すると、両方のエージェントで利用可能なスキルが見つかります。

## ファーストクラスのサポートが追加するもの

1. **信頼性** — `.slate/skills/` は、Slate の最も優先度の高いパスです。に対する免疫
   `SLATE_DISABLE_CLAUDE_CODE_SKILLS`。
2. **最適化されたフロントマター** — クロード固有のフィールド (許可されたツール、フック、バージョン) を削除します。
   スレートは使用しません。 `name` と `description` のみを保持してください。
3. **セットアップ スクリプト** — `slate` バイナリを自動検出し、スキルを `~/.slate/skills/` にインストールします。
4. **E2E テスト** — スレートによって直接呼び出された場合にスキルが機能することを確認します。

## ブロックされています: ホスト構成のリファクタリング

Codex の外部の声によるレビューでは、Slate を 4 番目のホスト (Claude に続いて) として追加することが特定されました。
Codex、Factory) は、「パス エイリアスのホスト爆発」です。現在のアーキテクチャには次のものがあります。

- `type Host = 'claude' | 'codex' | 'factory'` のハードコーディングされたホスト名
- ほぼ重複したロジックを使用した `transformFrontmatter()` のホストごとのブランチ
- 同様のパターンを使用した `EXTERNAL_HOST_CONFIG` のホストごとの構成
- セットアップ スクリプトのホストごとの関数 (`create_codex_runtime_root`、`link_codex_skill_dirs`)
・`bin/gstack-platform-detect`、`bin/gstack-uninstall`、`bin/dev-setup`でホスト名が重複している

スレートを追加するということは、これらのパターンをすべて再度コピーすることを意味します。ホストを作成するためのリファクタリング
データ駆動型 (if/else ブランチの代わりに構成オブジェクト) によりスレート統合が行われます。
簡単であり、将来のホスト (新しい OpenCode フォーク、新しいエージェント) の労力はゼロになります。

### 計画に欠落しています (Codex によって特定)

- `lib/worktree.ts` は `.slate/` ではなく、`.agents/` のみをコピーします — ワークツリー内の E2E テストは実行されません
  スレートスキルを持っている
- `bin/gstack-uninstall` は `.slate/` について知りません
- `bin/dev-setup` は `.slate/` をコントリビューター開発モードに接続しません
- `bin/gstack-platform-detect` はスレートを検出しません
- E2E テストでは、`.slate/` パスを証明するために `SLATE_DISABLE_CLAUDE_CODE_SKILLS=1` を設定する必要があります
  実際に動作します (`.claude/` にフォールバックするだけではありません)

## セッション ランナーのデザイン (後で使用)

JSONL 形式が検証されたら、セッション ランナーは次のことを行う必要があります。

- スポーン: `slate -q "<prompt>" --stream-json --dangerously-skip-permissions -w <dir>`
- 解析: Claude Code SDK 互換の NDJSON (想定、要検証)
- スキル: テストフィクスチャの `.slate/skills/` にインストールします (`.claude/skills/` ではありません)
- 認証: `SLATE_API_KEY` または既存の `~/.slate/` 資格情報を使用します。
- 分離: ホームディレクトリの分離には `SLATE_TEST_HOME` を使用します
- タイムアウト: デフォルトは 300 秒 (Codex と同じ)

```typescript
export interface SlateResult {
  output: string;
  toolCalls: string[];
  tokens: number;
  exitCode: number;
  durationMs: number;
  sessionId: string | null;
  rawLines: string[];
  stderr: string;
}
```

## ドキュメントの参照

- スレート ドキュメント: https://docs.randomlabs.ai
- クイックスタート: https://docs.randomlabs.ai/en/getting-started/quickstart
- スキル: https://docs.randomlabs.ai/en/using-slate/skills
- 構成: https://docs.randomlabs.ai/en/using-slate/configuration
- ホットキー: https://docs.randomlabs.ai/en/using-slate/hotkey_reference