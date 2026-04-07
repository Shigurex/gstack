# gstack開発

## コマンド

```bash
bun install          # install dependencies
bun test             # run free tests (browse + snapshot + skill validation)
bun run test:evals   # run paid evals: LLM judge + E2E (diff-based, ~$4/run max)
bun run test:evals:all  # run ALL paid evals regardless of diff
bun run test:gate    # run gate-tier tests only (CI default, blocks merge)
bun run test:periodic  # run periodic-tier tests only (weekly cron / manual)
bun run test:e2e     # run E2E tests only (diff-based, ~$3.85/run max)
bun run test:e2e:all # run ALL E2E tests regardless of diff
bun run eval:select  # show which tests would run based on current diff
bun run dev <cmd>    # run CLI in dev mode, e.g. bun run dev goto https://example.com
bun run build        # gen docs + compile binaries
bun run gen:skill-docs  # regenerate SKILL.md files from templates
bun run skill:check  # health dashboard for all skills
bun run dev:skill    # watch mode: auto-regen + validate on change
bun run eval:list    # list all eval runs from ~/.gstack-dev/evals/
bun run eval:compare # compare two eval runs (auto-picks most recent)
bun run eval:summary # aggregate stats across all eval runs
```

`test:evals` には `ANTHROPIC_API_KEY` が必要です。 Codex E2E テスト (`test/codex-e2e.test.ts`)
`~/.codex/` 設定から Codex 独自の認証を使用します。`OPENAI_API_KEY` 環境変数は必要ありません。
E2E は、ストリームの進行状況をリアルタイムでテストします (「--output-format stream-json 経由でツールごと)」
--verbose`). Results are persisted to `~/.gstack-dev/evals/` 自動比較あり
前走に対して。

**差分ベースのテスト選択:** `test:evals` および `test:e2e` 自動選択テストベース
`git diff` でベース ブランチに対して。各テストはファイルの依存関係を次のように宣言します。
`test/helpers/touchfiles.ts`。グローバル touchfile への変更 (session-runner、eval-store、
touchfiles.ts 自体）すべてのテストをトリガーします。 `EVALS_ALL=1` または `:all` スクリプトを使用します
すべてのテストを強制するバリアント。 `eval:select` を実行して、実行されるテストをプレビューします。

**2 層システム:** テストは、`E2E_TIERS` の `gate` または `periodic` として分類されます。
(`test/helpers/touchfiles.ts`内)。 CI はゲート テスト (`EVALS_TIER=gate`) のみを実行します。
定期テストは cron 経由または手動で毎週実行されます。 `EVALS_TIER=gate` を使用するか、
`EVALS_TIER=periodic` をフィルタリングします。新しい E2E テストを追加する場合は、次のように分類します。
1. 安全ガードレールまたは確定的な機能テスト? -> `gate`
2. 品質ベンチマーク、Opus モデル テスト、それとも非決定的? -> `periodic`
3. 外部サービス (Codex、Gemini) が必要ですか? -> `periodic`

## テスト

```bash
bun test             # run before every commit — free, <2s
bun run test:evals   # run before shipping — paid, diff-based (~$4/run max)
```

`bun test` はスキルの検証、gen-skill-docs の品質チェック、および参照を実行します。
統合テスト。 `bun run test:evals` は LLM 判定品質評価と E2E を実行します
`claude -p` 経由でテストします。 PR を作成する前に両方に合格する必要があります。

## プロジェクトの構造

```
gstack/
├── browse/          # Headless browser CLI (Playwright)
│   ├── src/         # CLI + server + commands
│   │   ├── commands.ts  # Command registry (single source of truth)
│   │   └── snapshot.ts  # SNAPSHOT_FLAGS metadata array
│   ├── test/        # Integration tests + fixtures
│   └── dist/        # Compiled binary
├── scripts/         # Build + DX tooling
│   ├── gen-skill-docs.ts  # Template → SKILL.md generator
│   ├── resolvers/   # Template resolver modules (preamble, design, review, etc.)
│   ├── skill-check.ts     # Health dashboard
│   └── dev-skill.ts       # Watch mode
├── test/            # Skill validation + eval tests
│   ├── helpers/     # skill-parser.ts, session-runner.ts, llm-judge.ts, eval-store.ts
│   ├── fixtures/    # Ground truth JSON, planted-bug fixtures, eval baselines
│   ├── skill-validation.test.ts  # Tier 1: static validation (free, <1s)
│   ├── gen-skill-docs.test.ts    # Tier 1: generator quality (free, <1s)
│   ├── skill-llm-eval.test.ts   # Tier 3: LLM-as-judge (~$0.15/run)
│   └── skill-e2e-*.test.ts       # Tier 2: E2E via claude -p (~$3.85/run, split by category)
├── qa-only/         # /qa-only skill (report-only QA, no fixes)
├── plan-design-review/  # /plan-design-review skill (report-only design audit)
├── design-review/    # /design-review skill (design audit + fix loop)
├── ship/            # Ship workflow skill
├── review/          # PR review skill
├── plan-ceo-review/ # /plan-ceo-review skill
├── plan-eng-review/ # /plan-eng-review skill
├── autoplan/        # /autoplan skill (auto-review pipeline: CEO → design → eng)
├── benchmark/       # /benchmark skill (performance regression detection)
├── canary/          # /canary skill (post-deploy monitoring loop)
├── codex/           # /codex skill (multi-AI second opinion via OpenAI Codex CLI)
├── land-and-deploy/ # /land-and-deploy skill (merge → deploy → canary verify)
├── office-hours/    # /office-hours skill (YC Office Hours — startup diagnostic + builder brainstorm)
├── investigate/     # /investigate skill (systematic root-cause debugging)
├── retro/           # Retrospective skill (includes /retro global cross-project mode)
├── bin/             # CLI utilities (gstack-repo-mode, gstack-slug, gstack-config, etc.)
├── document-release/ # /document-release skill (post-ship doc updates)
├── cso/             # /cso skill (OWASP Top 10 + STRIDE security audit)
├── design-consultation/ # /design-consultation skill (design system from scratch)
├── design-shotgun/  # /design-shotgun skill (visual design exploration)
├── connect-chrome/  # /connect-chrome skill (headed Chrome with side panel)
├── design/          # Design binary CLI (GPT Image API)
│   ├── src/         # CLI + commands (generate, variants, compare, serve, etc.)
│   ├── test/        # Integration tests
│   └── dist/        # Compiled binary
├── extension/       # Chrome extension (side panel + activity feed + CSS inspector)
├── lib/             # Shared libraries (worktree.ts)
├── docs/designs/    # Design documents
├── setup-deploy/    # /setup-deploy skill (one-time deploy config)
├── .github/         # CI workflows + Docker image
│   ├── workflows/   # evals.yml (E2E on Ubicloud), skill-docs.yml, actionlint.yml
│   └── docker/      # Dockerfile.ci (pre-baked toolchain + Playwright/Chromium)
├── setup            # One-time setup: build binary + symlink skills
├── SKILL.md         # Generated from SKILL.md.tmpl (don't edit directly)
├── SKILL.md.tmpl    # Template: edit this, run gen:skill-docs
├── ETHOS.md         # Builder philosophy (Boil the Lake, Search Before Building)
└── package.json     # Build scripts for browse
```

## SKILL.md ワークフロー

SKILL.md ファイルは、`.tmpl` テンプレートから**生成**されます。ドキュメントを更新するには:

1. `.tmpl` ファイルを編集します (例: `SKILL.md.tmpl` または `browse/SKILL.md.tmpl`)
2. `bun run gen:skill-docs` (または自動的に実行する `bun run build`) を実行します。
3. `.tmpl` ファイルと生成された `.md` ファイルの両方をコミットします

新しい参照コマンドを追加するには: `browse/src/commands.ts` に追加して再構築します。
スナップショットフラグを追加するには、`browse/src/snapshot.ts`の`SNAPSHOT_FLAGS`に追加してリビルドします。

**SKILL.md ファイルの競合をマージします:** 生成された SKILL.md の競合を決して解決しないでください。
どちらかの側を受け入れてファイルを作成します。代わりに: (1) `.tmpl` テンプレートの競合を解決します。
および `scripts/gen-skill-docs.ts` (真実の情報源)、(2) `bun run gen:skill-docs` を実行します
すべての SKILL.md ファイルを再生成するには、(3) 再生成されたファイルをステージングします。一方の側の意見を受け入れる
生成された出力は、相手側のテンプレートの変更をサイレントに削除します。

## プラットフォームに依存しない設計

スキルはフレームワーク固有のコマンド、ファイル パターン、またはディレクトリを決してハードコーディングしてはなりません
構造物。その代わり：

1. **CLAUDE.md** を読み、プロジェクト固有の設定 (テスト コマンド、評価コマンドなど) を確認します。
2. **見つからない場合は、AskUserQuestion** — ユーザーに教えてもらうか、gstack にリポジトリを検索させます
3. **CLAUDE.md への回答を永続化**して、再度質問する必要がないようにします

これは、test コマンド、eval コマンド、deploy コマンド、およびその他のコマンドに適用されます。
プロジェクト固有の動作。プロジェクトはその構成を所有します。 gstack がそれを読み取ります。

## SKILL テンプレートの作成

SKILL.md.tmpl ファイルは **クロードによって読み取られるプロンプト テンプレート**であり、bash スクリプトではありません。
各 bash コード ブロックは個別のシェルで実行されます。変数はブロック間で保持されません。

ルール:
- **ロジックと状態には自然言語を使用します。** 渡すためにシェル変数を使用しないでください。
  コードブロック間の状態。代わりに、クロードに覚えておくべきことと参考にするべきことを教えてください
  散文で表現します (例: 「ステップ 0 で検出されたベース ブランチ」)。
- **ブランチ名をハードコーディングしないでください。** `main`/`master`/etc を動的に検出します。
  `gh pr view` または `gh repo view`。 PR ターゲティングには `{{BASE_BRANCH_DETECT}}` を使用します
  スキル。散文では「ベース ブランチ」を使用し、コード ブロックのプレースホルダーでは `<base>` を使用します。
- **bash ブロックを自己完結型に保ちます。** 各コード ブロックは独立して動作する必要があります。
  ブロックに前のステップのコンテキストが必要な場合は、それを上記の散文で再説明します。
- **条件文を英語として表現します。** bash でネストされた `if/elif/else` の代わりに、
  番号付きの決定ステップを書きます: 「1. X の場合は Y を実行します。2. それ以外の場合は Z を実行します。」

## ブラウザーの操作

ブラウザと対話する必要がある場合 (QA、ドッグフーディング、Cookie のセットアップ)、
`/browse` スキルを使用するか、`$B <command>` 経由で参照バイナリを直接実行します。絶対に使用しないでください
`mcp__claude-in-chrome__*` ツール — 速度が遅く、信頼性が低く、このようなものではありません
プロジェクトが使用します。

## ベンダーのシンボリックリンク認識

gstack を開発する場合、`.claude/skills/gstack` はこれへのシンボリックリンクである可能性があります
作業ディレクトリ (gitignored)。これは、スキルの変更が**すぐに反映される**ことを意味します —
迅速な反復には最適ですが、スキルが中途半端に書かれている大規模なリファクタリング中は危険です
gstack を同時に使用している他のクロード コード セッションが中断される可能性があります。

**セッションごとに 1 回確認します:** `ls -la .claude/skills/gstack` を実行して、
シンボリックリンクまたは実際のコピー。作業ディレクトリへのシンボリックリンクの場合は、次の点に注意してください。
- テンプレートの変更 + `bun run gen:skill-docs` は、すべての gstack 呼び出しに直ちに影響します
- SKILL.md.tmpl ファイルへの重大な変更により、同時実行の gstack セッションが中断される可能性があります
- 大規模なリファクタリング中は、シンボリックリンク (`rm .claude/skills/gstack`) を削除します。
  代わりに、`~/.claude/skills/gstack/` のグローバル インストールが使用されます

**プレフィックス設定:** セットアップは最上位に実際のディレクトリ (シンボリックリンクではない) を作成します
内部に SKILL.md シンボリックリンクが含まれています (例: `qa/SKILL.md -> gstack/qa/SKILL.md`)。これ
これにより、クロードはそれらを `gstack/` の下にネストされず、トップレベルのスキルとして検出できるようになります。
名前は短い (`qa`) か名前空間付き (`gstack-qa`) のいずれかで、次によって制御されます。
`~/.gstack/config.yaml` の `skill_prefix`。プロジェクトにベンダーとして参加する場合は、次を実行します。
シンボリックリンクを作成してスキルごとのディレクトリを作成した後、`./setup`。 `--no-prefix` を通過
または `--prefix` を使用して対話型プロンプトをスキップします。

**プランのレビューについて:** スキル テンプレートまたは
gen-skill-docs パイプライン、変更を個別にテストする必要があるかどうかを検討する
ライブになる前に (特にユーザーが他のウィンドウで gstack を積極的に使用している場合)。

**アップグレード移行:** 変更によりディスク上の状態 (ディレクトリ構造、
構成フォーマット、古いファイルなど）既存のユーザーのインストールを破壊する可能性がある方法で、
移行スクリプトを `gstack-upgrade/migrations/` に追加します。 COTRIBUTING.md の「アップグレード」を読んでください。
形式とテスト要件については、「移行」セクションを参照してください。アップグレードスキルが発動する
これらは、`./setup` 以降、`/gstack-upgrade` の間に自動的に行われます。

## コンパイルされたバイナリ — 決してbrowse/dist/またはdesign/dist/をコミットしないでください

`browse/dist/` および `design/dist/` ディレクトリには、コンパイルされた Bun バイナリが含まれています
(`browse`、`find-browse`、`design`、それぞれ最大 58MB)。これらは Mach-O arm64 のみです -
Linux、Windows、または Intel Mac では動作しません。 `./setup` スクリプトはすでにビルドされています
すべてのプラットフォームのソースから取得されるため、チェックインされたバイナリは冗長です。彼らは
歴史的な間違いにより git によって追跡されており、最終的には次のコマンドで削除する必要があります。
`git rm --cached`。

**これらのファイルは決してステージングまたはコミットしないでください。** これらは `git status` で変更されたものとして表示されます
`.gitignore` にもかかわらず追跡されているため、無視してください。ファイルをステージングするとき、
常に特定のファイル名 (`git add file1 file2`) を使用します。`git add .` や
`git add -A`、これには誤ってバイナリが含まれます。

## コミットスタイル

**コミットは常に 2 等分します。** すべてのコミットは単一の論理変更である必要があります。いつ
複数の変更を行った場合 (例: 名前変更 + 書き換え + 新しいテスト)、それらを分割します。
プッシュする前に個別のコミットに分割します。各コミットは独立している必要があります
理解可能で元に戻せる。

適切な二等分例:
- 動作の変更とは別に名前を変更/移動する
- テスト実装から分離されたテスト インフラストラクチャ (タッチファイル、ヘルパー)
- 生成されたファイルの再生成とは別にテンプレートを変更します
- 新しい機能から分離された機械的なリファクタリング

ユーザーが「コミットを二分する」または「二分してプッシュする」と言った場合、ステージング済み/ステージングされていないものを分割します。
論理コミットとプッシュに変更されます。

## コミュニティ PR ガードレール

コミュニティ PR を確認または統合する場合は、受け入れる前に **必ず AskUserQuestion** を行ってください。
次のようなコミット:

1. **ETHOS.md に触れる** — このファイルは、Garry の個人的なビルダーの哲学です。編集なし
   外部の貢献者や AI エージェントからのものです。
2. **宣伝資料を削除または和らげます** — YC への言及、創設者の視点、
   と製品の音声は意図的です。 PRs that frame these as "unnecessary" or
   「あまりにも宣伝的なもの」は拒否されなければなりません。
3. **ギャリーの声を変える** — スキルにおける口調、ユーモア、率直さ、視点
   templates, CHANGELOG, and docs are not generic.声を書き換えるPR
   より「中立的」または「プロフェッショナル」なものは拒否されなければなりません。

たとえエージェントが変更によってプロジェクトが改善されると強く信じていたとしても、これら 3 つは
カテゴリには、AskUserQuestion による明示的なユーザーの承認が必要です。例外はありません。
自動マージはありません。いいえ、「これをきれいにします。」

## 変更履歴 + バージョンのスタイル

**VERSION と CHANGELOG はブランチ スコープです。** 出荷されるすべての機能ブランチは、
独自のバージョン バンプと CHANGELOG エントリ。このエントリでは、このブランチが追加する内容について説明します。
すでにメインにあったものではありません。

**CHANGELOG エントリを書き込むタイミング:**
- 開発中またはブランチ途中ではなく、`/ship` 時 (ステップ 5)。
- このエントリは、このブランチとベース ブランチ上のすべてのコミットをカバーします。
- 新しい作業を、以前のバージョンの既存の CHANGELOG エントリに組み込まないでください。
  すでにメインに着陸しました。メインに v0.10.0.0 があり、ブランチに機能が追加されている場合、
  新しいエントリで v0.10.1.0 に移行します。v0.10.0.0 エントリは編集しないでください。

**書く前の重要な質問:**
1. 私はどのブランチにいるのですか?このブランチは何を変更しましたか?
2. 基本ブランチのバージョンはすでにリリースされていますか? (はいの場合は、バンプして新しいエントリを作成します。)
3. このブランチの既存のエントリは、以前の作業をすでにカバーしていますか? (「はい」の場合は交換します
   最終バージョンでは 1 つの統合エントリが含まれます)。

**メインをマージすることは、メインのバージョンを採用することを意味するものではありません。** オリジン/メインをマージする場合
機能ブランチ、main は新しい CHANGELOG エントリとより高いバージョンをもたらす可能性があります。あなたの支店
独自のバージョンのバンプがまだ必要です。メインが v0.13.8.0 で、ブランチが追加した場合
機能を追加すると、新しいエントリで v0.13.9.0 に移行します。変更をエントリに詰め込まないでください。
すでにメインに着陸しました。次にブランチが配置されるため、エントリが一番上に表示されます。

**メインをマージした後は、必ず次の点を確認してください。**
- CHANGELOG には、メインのエントリとは別にブランチ独自のエントリがありますか?
- VERSION はメインの VERSION よりも上位ですか?
- あなたのエントリは CHANGELOG の最上位のエントリ (メインの最新のものより上) ですか?
答えが「いいえ」の場合は、続行する前に修正してください。

**エントリを移動、追加、または削除する CHANGELOG 編集後、** すぐに実行します。
`grep "^## \[" CHANGELOG.md` を実行し、完全なバージョンのシーケンスが連続していることを確認します。
コミットする前にギャップや重複がないようにしてください。バージョンが欠落している場合は、編集
何かを壊した。次に進む前に修正してください。

CHANGELOG.md は **ユーザー向け** であり、寄稿者向けではありません。製品のリリースノートのように書きます。

- ユーザーが以前はできなかったことが**できる**ようになりました。機能を販売します。
- 実装の詳細ではなく、平易な言葉を使用します。 「…をリファクタリングしました」ではなく「…できるようになりました」
- **TODOS.md、内部追跡、評価インフラストラクチャ、または寄稿者対応については決して言及しないでください
  詳細。** これらはユーザーには表示されず、意味がありません。
- 貢献者/内部の変更を下部の別の「貢献者向け」セクションに配置します。
- どの作品も「いいな、やってみたい」と思ってもらえるものでなければなりません。
- 専門用語は使用しません。「すべての質問で、自分がどのプロジェクトとブランチに属しているかがわかります」とは言いません。
  「AskUserQuestion 形式は、プリアンブル リゾルバーを介してスキル テンプレート全体で標準化されました。」

## AI の労力の圧縮

労力を見積もったり議論したりするときは、常に人間チームと CC+Gstack 時間の両方を表示してください。

|タスクの種類 |人間チーム | CC+Gスタック |圧縮 |
|----------|-----------|---------------|-------------|
|ボイラープレート/足場 | 2日間 | 15分 | ～100倍 |
|テストライティング | 1日 | 15分 | ～50倍 |
|機能の実装 | 1週間 | 30分 | ～30倍 |
|バグ修正 + 回帰テスト | 4時間 | 15分 | ～20倍 |
|建築・デザイン | 2日間 | 4時間 | ～5倍 |
|研究・探査 | 1日 | 3時間 | ～3倍 |

完成度は安いです。完全な実装時にはショートカットを推奨しない
は「湖」（到達可能）であり、「海」（複数四半期にわたる移住）ではありません。を参照してください。
完全な哲学のスキルの前文にある完全性の原則。

## 構築する前に検索する

Before designing any solution that involves concurrency, unfamiliar patterns,
インフラストラクチャ、またはランタイム/フレームワークに以下が組み込まれている可能性のあるものすべて:

1.「{ランタイム} {シング} ビルトイン」を検索します
2.「{thing} のベスト プラクティス {今年}」を検索します
3. 公式ランタイム/フレームワークのドキュメントを確認する

知識の 3 つの層: 実績のある知識 (層 1)、新しく人気のある知識 (層 2)、
first-principles (Layer 3).何よりもレイヤー3を賞品にします。 See ETHOS.md for the full
ビルダーの哲学。

## ローカルプラン

寄稿者は、長距離ビジョン ドキュメントと設計ドキュメントを `~/.gstack-dev/plans/` に保存できます。
これらはローカルのみです (チェックインされていません)。 TODOS.md を確認するときは、`plans/` で候補を確認してください
TODO に昇格するか、実装する準備ができている可能性があります。

## E2E 評価失敗責任プロトコル

`/ship` またはその他のワークフロー中に E2E 評価が失敗した場合、**決して「そうではない」と主張しないでください。
** これらのシステムには目に見えない結合があります —
プリアンブル テキストの変更はエージェントの動作に影響し、新しいヘルパーはタイミングを変更します。
再生成された SKILL.md はプロンプトのコンテキストを変更します。

**障害の原因を「既存」とする前に必須:**
1. メイン (またはベース ブランチ) で同じ評価を実行し、そこでも失敗することを示します。
2. メインでは成功してもブランチでは失敗した場合、それはあなたの変更です。責任を追跡します。
3. メインで実行できない場合は、「未検証 — 関連しているかもしれないし、関連していないかもしれない」と言ってフラグを立てます。
   PR 機関のリスクとして

レシートのない「既存」というのは怠惰な主張です。証明するか、言わないか。

## 長時間実行されるタスク: 諦めないでください

eval、E2E テスト、または長時間実行されるバックグラウンド タスクを実行する場合、**次の時点までポーリングします。
完了**。 `sleep 180 && echo "ready"` + `TaskOutput` を 3 回ごとのループで使用します
分。ブロッキング モードに切り替えたり、ポーリングがタイムアウトになったときに諦めたりしないでください。決してしない
「完了したら通知されます」と言ってチェックをやめ、ループを続けます
タスクが終了するか、ユーザーが停止するよう指示するまで。

完全な E2E スイートには 30 ～ 45 分かかる場合があります。これは 10 ～ 15 ポーリング サイクルに相当します。すべてを実行してください
彼ら。各チェックで進行状況をレポートします (どのテストが合格したか、どのテストが実行中か、
これまでの失敗）。ユーザーは、実行が完了することを約束するのではなく、実行が完了することを望んでいます。
後で確認します。

## E2E テスト フィクスチャ: コピーせずに抽出します

**SKILL.md ファイル全体を E2E テスト フィクスチャにコピーしないでください。** SKILL.md ファイルは
1500～2000行。 `claude -p` が大きなファイルを読み取ると、コンテキストの肥大化が発生します。
タイムアウト、不安定なターン制限、必要以上に 5 ～ 10 倍の時間がかかるテスト。

代わりに、テストに実際に必要なセクションのみを抽出します。

```typescript
// BAD — agent reads 1900 lines, burns tokens on irrelevant sections
fs.copyFileSync(path.join(ROOT, 'ship', 'SKILL.md'), path.join(dir, 'ship-SKILL.md'));

// GOOD — agent reads ~60 lines, finishes in 38s instead of timing out
const full = fs.readFileSync(path.join(ROOT, 'ship', 'SKILL.md'), 'utf-8');
const start = full.indexOf('## Review Readiness Dashboard');
const end = full.indexOf('\n---\n', start);
fs.writeFileSync(path.join(dir, 'ship-SKILL.md'), full.slice(start, end > start ? end : undefined));
```

また、障害をデバッグするために対象を絞った E2E テストを実行する場合:
- `&` および `tee` ではバックグラウンドではなく、**フォアグラウンド** (`bun test ...`) で実行します
- 決して `pkill` 評価プロセスを実行して再起動しないでください。結果が失われ、お金が無駄になります。
- 1 回のクリーンな実行は、3 回の強制終了して再起動した実行よりも優れています

## アクティブなスキルへのデプロイ

The active skill lives at `~/.claude/skills/gstack/`.変更を加えた後:

1. ブランチをプッシュします
2. スキルディレクトリでフェッチしてリセットします: `cd ~/.claude/skills/gstack && git fetch origin && git reset --hard origin/main`
3. リビルド: `cd ~/.claude/skills/gstack && bun run build`

または、バイナリを直接コピーします。
- `cp browse/dist/browse ~/.claude/skills/gstack/browse/dist/browse`
- `cp design/dist/design ~/.claude/skills/gstack/design/dist/design`