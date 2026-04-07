# gstack に貢献する

Thanks for wanting to make gstack better.スキル プロンプトのタイプミスを修正する場合でも、まったく新しいワークフローを構築する場合でも、このガイドを読めばすぐに使い始めることができます。

## クイックスタート

gstack スキルは、Claude Code が `skills/` ディレクトリから検出する Markdown ファイルです。通常、これらは `~/.claude/skills/gstack/` (グローバル インストール) に存在します。しかし、gstack 自体を開発しているときは、Claude Code が *作業ツリー* 内のスキルを使用できるようにする必要があります。そのため、何もコピーしたりデプロイしたりすることなく、編集内容が即座に有効になります。

それが開発モードの機能です。リポジトリをローカルの `.claude/skills/` ディレクトリにシンボリックリンクするので、Claude Code はチェックアウトから直接スキルを読み取ります。

```bash
git clone <repo> && cd gstack
bun install                    # install dependencies
bin/dev-setup                  # activate dev mode
```

次に、任意の `SKILL.md` を編集し、クロード コード (例: `/review`) で呼び出し、変更をライブで確認します。 When you're done developing:

```bash
bin/dev-teardown               # deactivate — back to your global install
```

## 運用上の自己改善

gstack は失敗から自動的に学習します。すべてのスキル セッションの終了時に、エージェントは
何がうまくいかなかったのか (CLI エラー、間違ったアプローチ、プロジェクトの癖) を反映し、ログに記録します。
`~/.gstack/projects/{slug}/learnings.jsonl` までの運用学習。今後のセッション
これらの学習を自動的に表面化するため、gstack は時間の経過とともにコードベースでより賢くなります。

セットアップは必要ありません。学習内容は自動的に記録されます。 `/learn` でご覧ください。



1. **gstack を通常どおり使用します** — 運用学習は自動的にキャプチャされます
2. **学習内容を確認します:** `/learn` または `ls ~/.gstack/projects/*/learnings.jsonl`
3. **gstack をフォークしてクローンを作成** (まだ行っていない場合)
4. **バグが発生したプロジェクトにフォークをシンボリックリンクします:**
   ```bash
   # In your core project (the one where gstack annoyed you)
   ln -sfn /path/to/your/gstack-fork .claude/skills/gstack
   cd .claude/skills/gstack && bun install && bun run build && ./setup
   ```
   セットアップにより、内部に SKILL.md シンボリックリンクを含むスキルごとのディレクトリが作成されます (`qa/SKILL.md -> gstack/qa/SKILL.md`)
   そしてプレフィックスの好みを尋ねます。プロンプトをスキップして短い名前を使用するには、`--no-prefix` を渡します。
5. **問題を修正** — 変更はこのプロジェクトですぐに反映されます
6. **実際に gstack を使用してテストします** — イライラすることを実行し、修正されていることを確認します
7. **フォークから PR を開きます**

これが貢献するための最良の方法です。実際の作業をしながら gstack を修正します。
実際に痛みを感じたプロジェクト。

### セッションの認識

3 つ以上の gstack セッションが同時に開いている場合、すべての質問によって、どのプロジェクト、どのブランチ、何が起こっているかがわかります。 「待って、これはどのウィンドウですか?」と考えて質問を見つめる必要はもうありません。形式はすべてのスキルにわたって一貫しています。

## gstack リポジトリ内で gstack を操作する

gstack スキルを編集していて、実際に gstack を使用してテストしたい場合
同じリポジトリ内で、`bin/dev-setup` がこれを接続します。 `.claude/skills/` を作成します
シンボリックリンク (gitignored) は作業ツリーを指すため、クロード コードは次のように使用します。
グローバルインストールではなくローカル編集します。

```
gstack/                          <- your working tree
├── .claude/skills/              <- created by dev-setup (gitignored)
│   ├── gstack -> ../../         <- symlink back to repo root
│   ├── review/                  <- real directory (short name, default)
│   │   └── SKILL.md -> gstack/review/SKILL.md
│   ├── ship/                    <- or gstack-review/, gstack-ship/ if --prefix
│   │   └── SKILL.md -> gstack/ship/SKILL.md
│   └── ...                      <- one directory per skill
├── review/
│   └── SKILL.md                 <- edit this, test with /review
├── ship/
│   └── SKILL.md
├── browse/
│   ├── src/                     <- TypeScript source
│   └── dist/                    <- compiled binary (gitignored)
└── ...
```

セットアップは SKILL.md を使用して最上位に実際のディレクトリ (シンボリックリンクではない) を作成します。
内部のシンボリックリンク。これにより、クロードはそれらをネストされたものではなく、トップレベルのスキルとして検出できるようになります。
`gstack/` の下。名前はプレフィックス設定 (`~/.gstack/config.yaml`) によって異なります。
短縮名 (`/review`、`/ship`) がデフォルトです。次の場合は、`./setup --prefix` を実行してください
名前空間付きの名前 (`/gstack-review`、`/gstack-ship`) を優先します。

## 日常のワークフロー

```bash
# 1. Enter dev mode
bin/dev-setup

# 2. Edit a skill
vim review/SKILL.md

# 3. Test it in Claude Code — changes are live
#    > /review

# 4. Editing browse source? Rebuild the binary
bun run build

# 5. Done for the day? Tear down
bin/dev-teardown
```

## テストと評価

＃＃＃ 設定

```bash
# 1. Copy .env.example and add your API key
cp .env.example .env
# Edit .env → set ANTHROPIC_API_KEY=sk-ant-...

# 2. Install deps (if you haven't already)
bun install
```

Bun は `.env` を自動ロードします — 追加の設定は必要ありません。 Conductor ワークスペースは、メイン ワークツリーから `.env` を自動的に継承します (下記の「Conductor ワークスペース」を参照)。

### テスト層

|階層 |コマンド |コスト |テスト内容 |
|------|---------|------|---------------|
| 1 — 静的 | `bun test` |無料 |コマンド検証、スナップショット フラグ、SKILL.md の正確性、TODOS-format.md ref、可観測性単体テスト |
| 2 — E2E | `bun run test:e2e` | ~$3.85 | `claude -p` サブプロセス経由の完全なスキルの実行 |
| 3 — LLM 評価 | `bun run test:evals` | ~$0.15 スタンドアロン |生成された SKILL.md ドキュメントの LLM による審査員スコアリング |
| 2+3 | `bun run test:evals` |合計 $4 | E2E + LLM-as-judge (runs both) |

```bash
bun test                     # Tier 1 only (runs on every commit, <5s)
bun run test:e2e             # Tier 2: E2E only (needs EVALS=1, can't run inside Claude Code)
bun run test:evals           # Tier 2 + 3 combined (~$4/run)
```



Runs automatically with `bun test`. API キーは必要ありません。

- **Skill parser tests** (`test/skill-parser.test.ts`) — Extracts every `$B` command from SKILL.md bash code blocks and validates against the command registry in `browse/src/commands.ts`. Catches typos, removed commands, and invalid snapshot flags.
- **Skill validation tests** (`test/skill-validation.test.ts`) — Validates that SKILL.md files reference only real commands and flags, and that command descriptions meet quality thresholds.
- **Generator tests** (`test/gen-skill-docs.test.ts`) — Tests the template system: verifies placeholders resolve correctly, output includes value hints for flags (e.g. `-d <N>` not just `-d`), enriched descriptions for key commands (e.g. `is` lists valid states, `press` lists key examples).

### Tier 2: E2E via `claude -p` (~$3.85/run)

`--output-format stream-json --verbose` のサブプロセスとして `claude -p` を生成し、NDJSON をストリーミングしてリアルタイムの進行状況を確認し、ブラウズ エラーをスキャンします。これは、「このスキルは実際にエンドツーエンドで機能するか?」に最も近いものです。

```bash
# Must run from a plain terminal — can't nest inside Claude Code or Conductor
EVALS=1 bun test test/skill-e2e-*.test.ts
```

- `EVALS=1` 環境変数によってゲートされます (偶発的な高コストの実行を防止します)
- クロード コード内で実行している場合は自動スキップ (`claude -p` はネストできません)
- API 接続事前チェック — 予算を消費する前に ConnectionRefused ですぐに失敗します
- Real-time progress to stderr: `[Ns] turn T tool #C: Name(...)`
- デバッグ用に完全な NDJSON トランスクリプトと失敗した JSON を保存します
- テストは `test/skill-e2e-*.test.ts` (カテゴリごとに分割) にあり、ランナー ロジックは `test/helpers/session-runner.ts` にあります。

### E2E observability

When E2E tests run, they produce machine-readable artifacts in `~/.gstack-dev/`:

|アーティファクト |パス |目的 |
|----------|------|----------|
|ハートビート | `e2e-live.json` |現在のテスト ステータス (ツール呼び出しごとに更新) |
|部分的な結果 | `evals/_partial-e2e.json` |完了したテスト (キルしても生き残る) |
|進捗ログ | `e2e-runs/{runId}/progress.log` |追加専用のテキスト ログ |
| NDJSON トランスクリプト | `e2e-runs/{runId}/{test}.ndjson` |テストごとの生の `claude -p` 出力 |
|失敗した JSON | `e2e-runs/{runId}/{test}-failure.json` |障害時の診断データ |

**ライブ ダッシュボード:** 2 番目のターミナルで `bun run eval:watch` を実行すると、完了したテスト、現在実行中のテスト、およびコストを示すライブ ダッシュボードが表示されます。 `--tail` を使用して、progress.log の最後の 10 行も表示します。

**Eval history tools:**

```bash
bun run eval:list            # list all eval runs (turns, duration, cost per run)
bun run eval:compare         # compare two runs — shows per-test deltas + Takeaway commentary
bun run eval:summary         # aggregate stats + per-test efficiency averages across runs
```

**評価比較の解説:** `eval:compare` は、実行間で何が変わったかを解釈する自然言語の要点セクションを生成します。つまり、回帰にフラグを立て、改善に注目し、効率の向上 (ターン数が少なく、速く、安く) を指摘し、全体的な概要を生成します。これは、`eval-store.ts` の `generateCommentary()` によって駆動されます。

アーティファクトはクリーンアップされることはなく、事後のデバッグや傾向分析のために `~/.gstack-dev/` に蓄積されます。

### Tier 3: 裁判官としての LLM (~$0.15/実行)

Claude Sonnet を使用して、生成された SKILL.md ドキュメントを 3 つの次元でスコア付けします。

- **明瞭さ** — AI エージェントは曖昧さなく指示を理解できますか?
- **完全性** — すべてのコマンド、フラグ、使用パターンは文書化されていますか?
- **Actionability** — Can the agent execute tasks using only the information in the doc?

各次元には 1 ～ 5 のスコアが付けられます。しきい値: すべてのディメンションのスコアが **≥ 4** である必要があります。生成されたドキュメントを `origin/main` から手動で管理されたベースラインと比較する回帰テストもあります。生成されたドキュメントは同等以上のスコアを取得する必要があります。

```bash
# Needs ANTHROPIC_API_KEY in .env — included in bun run test:evals
```

- スコアの安定性のために `claude-sonnet-4-6` を使用します
- テストは `test/skill-llm-eval.test.ts` にあります
- Anthropic API を (`claude -p` ではなく) 直接呼び出すため、クロード コード内を含むどこからでも機能します

###CI

GitHub アクション (`.github/workflows/skill-docs.yml`) は、プッシュと PR ごとに `bun run gen:skill-docs --dry-run` を実行します。生成された SKILL.md ファイルがコミットされたものと異なる場合、CI は失敗します。これにより、古いドキュメントがマージされる前に検出されます。

テストはブラウズ バイナリに対して直接実行されます。開発モードは必要ありません。



SKILL.md ファイルは、`.tmpl` テンプレートから**生成**されます。 `.md` を直接編集しないでください。変更内容は次のビルドで上書きされます。

```bash
# 1. Edit the template
vim SKILL.md.tmpl              # or browse/SKILL.md.tmpl

# 2. Regenerate for both hosts
bun run gen:skill-docs
bun run gen:skill-docs --host codex

# 3. Check health (reports both Claude and Codex)
bun run skill:check

# Or use watch mode — auto-regenerates on save
bun run dev:skill
```

テンプレート作成のベスト プラクティス (bash-ism よりも自然言語、動的分岐検出、`{{BASE_BRANCH_DETECT}}` の使用法) については、CLAUDE.md の「Writing SKILL templates」セクションを参照してください。

参照コマンドを追加するには、`browse/src/commands.ts` に追加します。スナップショットフラグを追加するには、`browse/src/snapshot.ts`の`SNAPSHOT_FLAGS`に追加します。その後、再構築します。

## デュアルホスト開発 (Claude + Codex)

gstack は、**Claude** (`.claude/skills/`) と **Codex** (`.agents/skills/`) の 2 つのホスト用の SKILL.md ファイルを生成します。すべてのテンプレート変更は両方に対して生成する必要があります。

### 両方のホストに対して生成中

```bash
# Generate Claude output (default)
bun run gen:skill-docs

# Generate Codex output
bun run gen:skill-docs --host codex
# --host agents is an alias for --host codex

# Or use build, which does both + compiles binaries
bun run build
```

### ホスト間での変更点

|側面 |クロード |コーデックス |
|----------|----------|----------|
|出力ディレクトリ | `{skill}/SKILL.md` | `.agents/skills/gstack-{skill}/SKILL.md` (セットアップ時に生成され、gitignored) |
|フロントマター |フル (名前、説明、音声トリガー、許可されたツール、フック、バージョン) |最小限 (名前と説明のみ) |
|パス | `~/.claude/skills/gstack` | `$GSTACK_ROOT` (リポジトリ内では `.agents/skills/gstack`、それ以外の場合は `~/.codex/skills/gstack`) |
|フックスキル | `hooks:` フロントマター (クロードによって強制) |インライン安全勧告散文 (勧告のみ) |
| `/codex` スキル |含まれています (Claude は codex exec をラップします) |除外 (自己参照) |

### Codex 出力のテスト

```bash
# Run all static tests (includes Codex validation)
bun test

# Check freshness for both hosts
bun run gen:skill-docs --dry-run
bun run gen:skill-docs --host codex --dry-run

# Health dashboard covers both hosts
bun run skill:check
```

### .agents/ の開発セットアップ

`bin/dev-setup` を実行すると、`.claude/skills/` と `.agents/skills/` (該当する場合) の両方にシンボリックリンクが作成されるため、Codex 互換エージェントも開発スキルを検出できます。 `.agents/` ディレクトリは、セットアップ時に `.tmpl` テンプレートから生成されます。これは gitignore され、コミットされません。



新しいスキル テンプレートを追加すると、両方のホストがそれを自動的に取得します。
1. Create `{skill}/SKILL.md.tmpl`
2. `bun run gen:skill-docs` (クロード出力) および `bun run gen:skill-docs --host codex` (コーデックス出力) を実行します。
3. 動的テンプレート検出がそれを選択します - 更新する静的リストはありません
4. `{skill}/SKILL.md` をコミットします — `.agents/` はセットアップ時に生成され、無視されます



[Conductor](https://conductor.build) を使用して複数のクロード コード セッションを並行して実行している場合、`conductor.json` はワークスペースのライフサイクルを自動的に調整します。

|フック |スクリプト |何をするのか |
|------|--------|---------------|
| `setup` | `bin/dev-setup` |メインワークツリーから `.env` をコピーし、deps とシンボリックリンクのスキルをインストールします。
| `archive` | `bin/dev-teardown` |スキルのシンボリックリンクを削除し、`.claude/` ディレクトリをクリーンアップします。

Conductor が新しいワークスペースを作成すると、`bin/dev-setup` が自動的に実行されます。メインのワークツリーを (`git worktree list` 経由で) 検出し、API キーが引き継がれるように `.env` をコピーし、開発モードを設定します。手動の手順は必要ありません。

**初回セットアップ:** `ANTHROPIC_API_KEY` をメイン リポジトリの `.env` に配置します (`.env.example` を参照)。すべての Conductor ワークスペースはこれを自動的に継承します。

## 知っておくべきこと

- **SKILL.md ファイルが生成されます。** `.md` ではなく、`.tmpl` テンプレートを編集します。 `bun run gen:skill-docs` を実行して再生成します。
- **TODOS.md は統合されたバックログです。** P0 ～ P4 の優先順位を持つスキル/コンポーネントごとに編成されています。 `/ship` は完了したアイテムを自動検出します。計画/レビュー/レトロなスキルを持つ人は、文脈を理解するためにこの文書を読んでください。
- **ソースの変更を参照するには再構築が必要です。** `browse/src/*.ts` をタッチした場合は、`bun run build` を実行します。
- **開発モードはグローバル インストールをシャドウします。** プロジェクトのローカル スキルが `~/.claude/skills/gstack` よりも優先されます。 `bin/dev-teardown` はグローバルなものを復元します。
- **Conductor ワークスペースは独立しています。** 各ワークスペースは独自の git ワークツリーです。 `bin/dev-setup` は `conductor.json` を介して自動的に実行されます。
- **`.env` はワークツリー全体に伝播します。** メイン リポジトリで一度設定すると、すべての Conductor ワークスペースがそれを取得します。
- **`.claude/skills/` は gitignored です。** シンボリックリンクはコミットされません。

## 実際のプロジェクトで変更をテストする

**This is the recommended way to develop gstack.** Symlink your gstack checkout
into the project where you actually use it, so your changes are live while you
本当の仕事をする。

### ステップ 1: チェックアウトをシンボリックリンクする

```bash
# In your core project (not the gstack repo)
ln -sfn /path/to/your/gstack-checkout .claude/skills/gstack
```

### ステップ 2: セットアップを実行してスキルごとのシンボリックリンクを作成する

`gstack` シンボリックリンクだけでは十分ではありません。クロード・コードは次のようなスキルを発見します
個々の最上位ディレクトリ (`qa/SKILL.md`、`ship/SKILL.md` など)、経由ではなく
`gstack/` ディレクトリ自体。 `./setup` を実行して作成します。

```bash
cd .claude/skills/gstack && bun install && bun run build && ./setup
```

セットアップでは、短縮名 (`/qa`) または名前空間付き (`/gstack-qa`) のどちらを使用するかを尋ねられます。
選択内容は `~/.gstack/config.yaml` に保存され、今後の実行のために記憶されます。
プロンプトをスキップするには、`--no-prefix` (短縮名) または `--prefix` (名前空間あり) を渡します。

### ステップ 3: 開発する

テンプレートを編集し、`bun run gen:skill-docs` を実行し、次の `/review` または `/qa` を実行します。
電話するとすぐに出ます。再起動は必要ありません。

### 安定したグローバル インストールに戻る

プロジェクトローカルのシンボリックリンクを削除します。クロード コードは `~/.claude/skills/gstack/` にフォールバックします。

```bash
rm .claude/skills/gstack
```

スキルごとのディレクトリ (`qa/`、`ship/` など) には、以下をポイントする SKILL.md シンボリックリンクが含まれています。
`gstack/...` に変更すると、グローバル インストールが自動的に解決されます。

### プレフィックスモードの切り替え

1 つのプレフィックス設定で gstack をベンダー化しており、切り替える場合:

```bash
cd .claude/skills/gstack && ./setup --no-prefix   # switch to /qa, /ship
cd .claude/skills/gstack && ./setup --prefix       # switch to /gstack-qa, /gstack-ship
```

セットアップは古いシンボリックリンクを自動的にクリーンアップします。手動によるクリーンアップは必要ありません。

### 代替案: グローバル インストールをブランチに指定します

プロジェクトごとのシンボリックリンクが不要な場合は、グローバル インストールを切り替えることができます。

```bash
cd ~/.claude/skills/gstack
git fetch origin
git checkout origin/<branch>
bun install && bun run build && ./setup
```

これはすべてのプロジェクトに影響します。元に戻すには: `git checkout main && git pull && bun run build && ./setup`。

## コミュニティ PR トリアージ (ウェーブ プロセス)

コミュニティ PR が蓄積されたら、テーマ別の Wave にまとめます。

1. **分類** — テーマごとにグループ化します (セキュリティ、機能、インフラ、ドキュメント)
2. **重複排除** — 2 つの PR が同じ問題を修正する場合は、修正する PR を選択します。
   変更する行が少なくなります。もう一方は勝者を示すメモで閉じます。
3. **コレクター ブランチ** — `pr-wave-N` を作成し、クリーンな PR をマージし、解決します
   ダーティなものと競合しています。`bun test && bun run build` で確認してください
4. **コンテキストを含めて閉じる** — 閉じられたすべての PR には、説明するコメントが表示されます。
   なぜ、そして（もしあれば）何がそれを置き換えるのか。貢献者たちは実際に仕事をしました。
   明確なコミュニケーションでそれを尊重してください。
5. **1 つの PR として出荷** — すべての属性を保持した状態でメインに単一の PR を送信します
   マージコミットで。何が統合され、何が閉鎖されたのかをまとめた表を含めます。

例として、最初のウェーブについては [PR #205](../../pull/205) (v0.8.3) を参照してください。

## アップグレードの移行

リリースによってディスク上の状態が変更されたとき (ディレクトリ構造、構成フォーマット、古い状態)
ファイル) `./setup` だけでは修正できない方法で、既存の移行スクリプトを追加します。
ユーザーはクリーンなアップグレードを取得できます。



- スキルディレクトリの作成方法を変更しました（シンボリックリンクと実際のディレクトリ）
- `~/.gstack/config.yaml` の設定キーの名前変更または移動
- 以前のバージョンから孤立したファイルを削除する必要がある
- `~/.gstack/` 状態ファイルの形式を変更しました

次の移行を追加しないでください: 新機能 (ユーザーが自動的に取得)、新しい機能
スキル (セットアップによって検出される)、またはコードのみの変更 (ディスク上の状態なし)。

### 追加方法

1. `{VERSION}` が一致する `gstack-upgrade/migrations/v{VERSION}.sh` を作成します
   修正が必要なリリースの VERSION ファイル。
2. 実行可能にします: `chmod +x gstack-upgrade/migrations/v{VERSION}.sh`
3. スクリプトは **冪等** (複数回実行しても安全) である必要があります。
   **致命的ではない** (失敗はログに記録されますが、アップグレードはブロックされません)。
4. 何が変更されたのか、なぜ変更されたのかを説明するコメント ブロックを上部に含めます。
   移行が必要かどうか、どのユーザーが影響を受けるかなどを確認します。

例：

```bash
#!/usr/bin/env bash
# Migration: v0.15.2.0 — Fix skill directory structure
# Affected: users who installed with --no-prefix before v0.15.2.0
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
"$SCRIPT_DIR/bin/gstack-relink" 2>/dev/null || true
```

### 実行方法

`/gstack-upgrade` の間、`./setup` が完了した後 (ステップ 4.75)、アップグレードは
スキルは `gstack-upgrade/migrations/` をスキャンし、すべての `v*.sh` スクリプトを実行します。
version is newer than the user's old version. Scripts run in version order.
Failures are logged but never block the upgrade.

### 移行のテスト

移行は、`bun test` (ティア 1、無料) の一部としてテストされます。テストスイート
`gstack-upgrade/migrations/` のすべての移行スクリプトが
実行可能ファイルを実行し、構文エラーなしで解析します。

## 変更を送信する

スキルの編集に満足したら:

```bash
/ship
```

これにより、テストが実行され、差分がレビューされ、Greptile コメントが優先順位付けされ (2 段階のエスカレーションが行われます)、TODOS.md が管理され、バージョンが上げられ、PR が開きます。完全なワークフローについては、`ship/SKILL.md` を参照してください。