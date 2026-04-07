# デザイン: gstack ビジュアルデザイン生成 (`design` バイナリ)

2026 年 3 月 26 日に /office-hours によって生成されました
ブランチ: garrytan/agent-design-tools
リポジトリ: gstack
ステータス: ドラフト
モード: 社内起業家精神

＃＃ コンテクスト

gstack の設計スキル (/office-hours、/design-consultation、/plan-design-review、/design-review) はすべて、設計の **テキスト説明**、つまり 16 進コードを含む DESIGN.md ファイル、散文でピクセル仕様を含む計画ドキュメント、ASCII アート ワイヤーフレームを生成します。作成者は OmniGraffle で HelloSign を手作業でデザインしたデザイナーですが、これを恥ずかしいと感じています。

値の単位が間違っています。 Users don't need richer design language — they need an executable visual artifact that changes the conversation from "do you like this spec?" to "is this the screen?"

## 問題ステートメント

デザインスキルは、デザインを示すのではなく、テキストでデザインを説明します。 Argus UX オーバーホール プランはその例です。487 行の詳細な感情アーク仕様、タイポグラフィーの選択、アニメーションのタイミング — 視覚的なアーティファクトはゼロです。 「設計」する AI コーディング エージェントは、見て直感的に反応できるものを生成する必要があります。

## 証拠の要求

作成者/主要ユーザーは、現在の出力を恥ずかしいと感じます。すべてのデザイン スキル セッションは、モックアップがあるべき散文で終わります。 GPT Image API は、正確なテキスト レンダリングを備えたピクセル完璧な UI モックアップを生成するようになりました。テキストのみの出力を正当化する機能のギャップはもう存在しません。

## 最も狭いウェッジ

OpenAI 画像/応答 API をラップするコンパイル済み TypeScript バイナリ (`design/dist/design`)。`$D` (既存の`$B` ブラウズ バイナリ パターンをミラーリング) 経由でスキル テンプレートから呼び出すことができます。統合の優先順位: /office-hours → /plan-design-review → /design-consultation → /design-review。

## 合意された敷地

1. GPT Image API (OpenAI Responses API 経由) は適切なエンジンです。 Google Stitch SDK はバックアップです。
2. **ビジュアル モックアップは、オプトインではなく、簡単なスキップ パスを備えた設計スキル向けにデフォルトでオンになっています**。 (Codex チャレンジごとに改訂されました。)
3. 統合は共有ユーティリティ (スキルごとの再実装ではありません) であり、どのスキルでも呼び出すことができる `design` バイナリです。
4. 優先順位: /office-hours が最初で、次に /plan-design-review、/design-consultation、/design-review の順です。

## クロスモデルの視点 (コーデックス)

Codex は、「問題はマークダウン内の出力品質ではなく、現在の値の単位が間違っていることです。」という核心理論を独自に検証しました。主な貢献:
- 前提条件 #2 (オプトイン → デフォルトオン) への異議申し立て — 受け入れ
- 提案されたビジョンベースの品質ゲート: GPT-4o ビジョンを使用して、生成されたモックアップで読めないテキスト、欠落しているセクション、破損したレイアウト、1 回の自動再試行を検証します。
- 48 時間限定のプロトタイプ: 共有 `visual_mockup.ts` ユーティリティ、/office-hours + /plan-design-review のみ、ヒーロー モックアップ + 2 つのバリアント

## 推奨されるアプローチ: `design` バイナリ (アプローチ B)

＃＃＃ 建築

**ブラウズ バイナリのコンパイルと配布パターンを共有します** (bun build --compile、セットアップ スクリプト、スキル テンプレートの $VARIABLE 解決) が、アーキテクチャ的にはより単純です。永続的なデーモン サーバー、Chromium、ヘルス チェック、トークン認証はありません。デザイン バイナリは、OpenAI API 呼び出しを行って PNG をディスクに書き込むステートレス CLI です。セッション状態 (複数ターンの反復の場合) は JSON ファイルです。

**新しい依存関係:** `openai` npm パッケージ (ランタイム deps ではなく、`devDependencies` に追加)。 openai がブラウズ バイナリを肥大化させないように、ブラウズとは別にコンパイルされたデザイン バイナリ。

```
design/
├── src/
│   ├── cli.ts            # Entry point, command dispatch
│   ├── commands.ts        # Command registry (source of truth for docs + validation)
│   ├── generate.ts        # Generate mockups from structured brief
│   ├── iterate.ts         # Multi-turn iteration on existing mockups
│   ├── variants.ts        # Generate N design variants from brief
│   ├── check.ts           # Vision-based quality gate (GPT-4o)
│   ├── brief.ts           # Structured brief type + assembly helpers
│   └── session.ts         # Session state (response IDs for multi-turn)
├── dist/
│   ├── design             # Compiled binary
│   └── .version           # Git hash
└── test/
    └── design.test.ts     # Integration tests
```

### コマンド

```bash
# Generate a hero mockup from a structured brief
$D generate --brief "Dashboard for a coding assessment tool. Dark theme, cream accents. Shows: builder name, score badge, narrative letter, score cards. Target: technical users." --output /tmp/mockup-hero.png

# Generate 3 design variants
$D variants --brief "..." --count 3 --output-dir /tmp/mockups/

# Iterate on an existing mockup with feedback
$D iterate --session /tmp/design-session.json --feedback "Make the score cards larger, move the narrative above the scores" --output /tmp/mockup-v2.png

# Vision-based quality check (returns PASS/FAIL + issues)
$D check --image /tmp/mockup-hero.png --brief "Dashboard with builder name, score badge, narrative"

# One-shot with quality gate + auto-retry
$D generate --brief "..." --output /tmp/mockup.png --check --retry 1

# Pass a structured brief via JSON file
$D generate --brief-file /tmp/brief.json --output /tmp/mockup.png

# Generate comparison board HTML for user review
$D compare --images /tmp/mockups/variant-*.png --output /tmp/design-board.html

# Guided API key setup + smoke test
$D setup
```

**簡単な入力モード:**
- `--brief "plain text"` — 自由形式のテキスト プロンプト (シンプル モード)
- `--brief-file path.json` — `DesignBrief` インターフェイスに一致する構造化 JSON (リッチ モード)
- スキルは JSON 概要ファイルを作成し、/tmp に書き込み、`--brief-file` を渡します

**すべてのコマンドは、`--check`と`--retry`を含む`commands.ts`**に`generate`のフラグとして登録されます。

### 設計検討ワークフロー (英語レビューより)

ワークフローは並列ではなく逐次的です。 PNG は視覚的な探索 (人間側) 用で、HTML ワイヤーフレームは実装用 (エージェント側) です。

```
1. $D variants --brief "..." --count 3 --output-dir /tmp/mockups/
   → Generates 2-5 PNG mockup variations

2. $D compare --images /tmp/mockups/*.png --output /tmp/design-board.html
   → Generates HTML comparison board (spec below)

3. $B goto file:///tmp/design-board.html
   → User reviews all variants in headed Chrome

4. User picks favorite, rates, comments, clicks [Submit]
   Agent polls: $B eval document.getElementById('status').textContent
   Agent reads: $B eval document.getElementById('feedback-result').textContent
   → No clipboard, no pasting. Agent reads feedback directly from the page.

5. Claude generates HTML wireframe via DESIGN_SKETCH matching approved direction
   → Agent implements from the inspectable HTML, not the opaque PNG
```

### 比較ボードの設計仕様 (/plan-design-review より)

**分類子: APP UI** (タスク中心のユーティリティ ページ)。製品のブランディングはありません。

**レイアウト: 1 列、全幅のモックアップ。** 各バリアントは完全なビューポートを取得します。
画像の忠実性を最大限に高めるための幅。ユーザーはバリアントを垂直方向にスクロールします。

```
┌─────────────────────────────────────────────────────────────┐
│  HEADER BAR                                                 │
│  "Design Exploration" . project name . "3 variants"         │
│  Mode indicator: [Wide exploration] | [Matching DESIGN.md]  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              VARIANT A (full width)                    │  │
│  │         [ mockup PNG, max-width: 1200px ]              │  │
│  ├───────────────────────────────────────────────────────┤  │
│  │ (●) Pick   ★★★★☆   [What do you like/dislike?____]   │  │
│  │            [More like this]                            │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              VARIANT B (full width)                    │  │
│  │         [ mockup PNG, max-width: 1200px ]              │  │
│  ├───────────────────────────────────────────────────────┤  │
│  │ ( ) Pick   ★★★☆☆   [What do you like/dislike?____]   │  │
│  │            [More like this]                            │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                             │
│  ... (scroll for more variants)                             │
│                                                             │
│  ─── separator ─────────────────────────────────────────    │
│  Overall direction (optional, collapsed by default)         │
│  [textarea, 3 lines, expand on focus]                       │
│                                                             │
│  ─── REGENERATE BAR (#f7f7f7 bg) ───────────────────────    │
│  "Want to explore more?"                                    │
│  [Totally different]  [Match my design]  [Custom: ______]   │
│                                          [Regenerate ->]    │
│  ─────────────────────────────────────────────────────────  │
│                                        [ ✓ Submit ]         │
└─────────────────────────────────────────────────────────────┘
```

**ビジュアル仕様:**
- 背景: #fff。影もカードの境界線もありません。バリアント区切り: 1px #e5e5e5 行。
- タイポグラフィ: システム フォント スタック。ヘッダー: 16 ピクセルの半太字。ラベル: 14 ピクセルの半太字。フィードバック プレースホルダー: 13px 通常 #999。
- 星評価: クリック可能な 5 つ星、塗りつぶし = #000、塗りつぶしなし = #ddd。着色されておらず、アニメーションもありません。
- ラジオ ボタン「選択」: 明示的なお気に入りの選択。バリアントごとに 1 つ、相互に排他的です。
- 「More like this」ボタン: バリアントごとに、そのバリアントのスタイルをシードとして再生成をトリガーします。
- 送信ボタン: #000 背景、白いテキスト、右揃え。単一の CTA。
- バーを再生成: #f7f7f7 背景。フィードバック領域とは視覚的に異なります。
- 最大幅: モックアップ画像の場合は中央に 1200 ピクセル。マージン: 辺 24 ピクセル。

**インタラクション状態:**
- 読み込み中 (画像が準備できる前にページが開きます): カードごとに「バリアント A を生成中...」のスケルトン パルス。スター/テキストエリア/選択が無効になりました。
- 部分的な失敗 (3 つ中 2 つが成功): 正常なものを表示し、バリアントごとの [再試行] で失敗した場合のエラー カードを表示します。
- 送信後: 「フィードバックを送信しました。コーディング エージェントに返信してください。」ページは開いたままになります。
- 再生: スムーズな移行、古いバリアントのフェードアウト、スケルトン パルス、新しいバリアントのフェードイン。スクロールが先頭にリセットされます。以前のフィードバックはクリアされました。

**フィードバック JSON 構造** (非表示の #フィードバック結果要素に書き込まれます):
```json
{
  "preferred": "A",
  "ratings": { "A": 4, "B": 3, "C": 2 },
  "comments": {
    "A": "Love the spacing, header feels right",
    "B": "Too busy, but good color palette",
    "C": "Wrong mood entirely"
  },
  "overall": "Go with A, make the CTA bigger",
  "regenerated": false
}
```

**アクセシビリティ:** 星評価によるキーボード操作が可能 (矢印キー)。 (「バリアント A のフィードバック」) というラベルの付いたテキスト領域。可視フォーカスリングでアクセス可能な送信/再生成キーボード。すべてのテキストは白地に #333+ です。

**レスポンシブ:** >1200px: 快適なマージン。 768-1200px: マージンが狭くなります。 <768px: 全幅、水平スクロールなし。

**スクリーンショットの同意 ($DEVO の初回のみ):** 「これにより、デザインの進化のためにライブ サイトのスクリーンショットが OpenAI に送信されます。[続行] [再度質問しないでください]」 ~/.gstack/config.yaml に design_screenshot_consent として保存されます。

シーケンシャルである理由: Codex の敵対的レビューにより、ラスター PNG はエージェントに対して不透明である (DOM、状態、拡散可能な構造がない) ことが判明しました。 HTML ワイヤーフレームは、コードへの橋渡しを保持します。 PNG は人間が「はい、その通りです」と言うためのものです。 HTML は、エージェントが「これを構築する方法を知っています」と伝えるためのものです。

### 主要な設計上の決定事項

**1.デーモンではなくステートレス CLI**
ブラウズには永続的な Chromium インスタンスが必要です。設計は単なる API 呼び出しであり、サーバーを必要とする必要はありません。マルチターン反復のセッション状態は、`previous_response_id` を含む `/tmp/design-session-{id}.json` に書き込まれる JSON ファイルです。
- **セッション ID:** `${PID}-${timestamp}` から生成され、`--session` フラグを介して渡されます
- **検出:** `generate` コマンドはセッション ファイルを作成し、そのパスを出力します。 `iterate` は `--session` 経由で読み取ります
- **クリーンアップ:** /tmp 内のセッション ファイルは一時的なものです (OS がクリーンアップします)。明示的なクリーンアップは必要ありません

**2.構造化された簡単な入力**
ブリーフは、スキルの文章と画像生成の間のインターフェイスです。スキルはデザインコンテキストからそれを構築します。
```typescript
interface DesignBrief {
  goal: string;           // "Dashboard for coding assessment tool"
  audience: string;       // "Technical users, YC partners"
  style: string;          // "Dark theme, cream accents, minimal"
  elements: string[];     // ["builder name", "score badge", "narrative letter"]
  constraints?: string;   // "Max width 1024px, mobile-first"
  reference?: string;     // Path to existing screenshot or DESIGN.md excerpt
  screenType: string;     // "desktop-dashboard" | "mobile-app" | "landing-page" | etc.
}
```

**3.デフォルトでオンになっているデザインスキル**
スキルはデフォルトでモックアップを生成します。テンプレートにはスキップ言語が含まれています。
```
Generating visual mockup of the proposed design... (say "skip" if you don't need visuals)
```

**4.ビジョンクオリティゲート**
生成後、オプションで画像を GPT-4o ビジョンに渡して以下を確認します。
- テキストの読みやすさ (ラベル/見出しは読みやすいか?)
- レイアウトの完全性 (要求された要素はすべて存在しますか?)
- 視覚的な一貫性 (コラージュではなく、実際の UI のように見えますか?)
失敗時に 1 回自動再試行します。それでも失敗する場合は、とにかく警告を表示します。

**5.出力場所: /tmp の探索、`docs/designs/`** の承認された最終結果
- 探索バリアントは `/tmp/gstack-mockups-{session}/` に移動します (一時的、コミットされていません)
- **ユーザーが承認した最終**モックアップのみが `docs/designs/` に保存されます (チェックインされています)
- CLAUDE.md `design_output_dir` 設定でデフォルトの出力ディレクトリを設定可能
- ファイル名パターン: `{skill}-{description}-{timestamp}.png`
- `docs/designs/` が存在しない場合は作成します (mkdir -p)
- 設計ドキュメントはコミットされたイメージのパスを参照します
- 常に読み取りツール (クロード コードで画像をインラインでレンダリングします) を介してユーザーに表示されます。
- これにより、リポジトリの肥大化が回避されます。すべての探索バリアントではなく、承認されたデザインのみがコミットされます。
- フォールバック: git リポジトリにない場合は、`/tmp/gstack-mockup-{timestamp}.png` に保存します

**6.信頼境界確認**
デフォルトで生成すると、設計概要テキストが OpenAI に送信されます。これは、完全にローカルな既存の HTML ワイヤーフレーム パスに対する、新しい外部データ フローです。概要には抽象的なデザインの説明 (目標、スタイル、要素) のみが含まれており、ソース コードやユーザー データは含まれません。 $B からのスクリーンショットは OpenAI には送信されません (DesignBrief の参照フィールドはエージェントによって使用されるローカル ファイル パスであり、API にはアップロードされません)。これを CLAUDE.md に文書化します。

**7.レート制限の緩和**
バリアント生成では時間差並列を使用します。各 API 呼び出しは `Promise.allSettled()` を介して 1 秒間隔で遅延を伴い開始します。これにより、イメージ生成における 5 ～ 7 RPM のレート制限が回避されますが、それでも完全なシリアルよりも高速になります。 429 を呼び出す場合は、指数バックオフ (2 秒、4 秒、8 秒) で再試行します。

### テンプレートの統合

**既存のリゾルバーに追加:** `scripts/resolvers/design.ts` (新しいファイルではありません)
- `{{DESIGN_SETUP}}` プレースホルダーに `generateDesignSetup()` を追加します (ミラー `generateBrowseSetup()`)
- `{{DESIGN_MOCKUP}}` プレースホルダーに `generateDesignMockup()` を追加します (完全な探索ワークフロー)
- すべてのデザイン リゾルバーを 1 つのファイルに保持します (既存のコードベース規則と一致します)。

**新しい HostPaths エントリ:** `types.ts`
```typescript
// claude host:
designDir: '~/.claude/skills/gstack/design/dist'
// codex host:
designDir: '$GSTACK_DESIGN'
```
注: Codex ランタイム セットアップ (`setup` スクリプト) は、`GSTACK_BROWSE` の設定方法と同様に、`GSTACK_DESIGN` 環境変数もエクスポートする必要があります。

**`$D` 解像度 bash ブロック** (`{{DESIGN_SETUP}}` によって生成):
```bash
_ROOT=$(git rev-parse --show-toplevel 2>/dev/null)
D=""
[ -n "$_ROOT" ] && [ -x "$_ROOT/.claude/skills/gstack/design/dist/design" ] && D="$_ROOT/.claude/skills/gstack/design/dist/design"
[ -z "$D" ] && D=~/.claude/skills/gstack/design/dist/design
if [ -x "$D" ]; then
  echo "DESIGN_READY: $D"
else
  echo "DESIGN_NOT_AVAILABLE"
fi
```
`DESIGN_NOT_AVAILABLE` の場合: スキルは HTML ワイヤーフレーム生成 (既存の `DESIGN_SKETCH` パターン) にフォールバックします。デザインのモックアップは段階的な機能強化であり、厳しい要件ではありません。

**既存のリゾルバーの新機能:** `scripts/resolvers/design.ts`
- `{{DESIGN_SETUP}}` に `generateDesignSetup()` を追加 — `generateBrowseSetup()` パターンをミラーリングします
- `{{DESIGN_MOCKUP}}` に `generateDesignMockup()` を追加 — 完全な生成+チェック+提示ワークフロー
- すべてのデザイン リゾルバーを 1 つのファイルに保持します (既存のコードベース規則と一致します)。

### スキル統合（優先順位）

**1. /office-hours** — Visual Sketch セクションを置き換えます
- アプローチの選択後 (フェーズ 4)、ヒーローのモックアップ + 2 つのバリエーションを生成します
- 読み取りツールを介して 3 つすべてを提示し、ユーザーに選択を依頼します
- リクエストに応じて反復します
- 選択したモックアップをデザインドキュメントと一緒に保存します

**2. /plan-design-review** — 「見た目はどうなるか」
- 設計寸法を 7/10 未満と評価する場合、10/10 がどのようになるかを示すモックアップを生成します。
- 並べて表示: 現在 ($B 経由のスクリーンショット) と提案済み ($D 経由のモックアップ)

**3. /design-consultation** — デザイン システムのプレビュー
- 提案されたデザイン システム (タイポグラフィ、色、コンポーネント) の視覚的なプレビューを生成します。
- /tmp HTML プレビュー ページを適切なモックアップに置き換えます。

**4. /design-review** — 設計意図の比較
- plan/DESIGN.md 仕様から「設計意図」モックアップを生成
- ライブサイトのスクリーンショットと比較して視覚的なデルタを確認

### 作成するファイル

|ファイル |目的 |
|-----|----------|
| `design/src/cli.ts` |エントリポイント、コマンドディスパッチ |
| `design/src/commands.ts` |コマンドレジストリ |
| `design/src/generate.ts` | Responses API による GPT イメージの生成 |
| `design/src/iterate.ts` |セッション状態を使用したマルチターン反復 |
| `design/src/variants.ts` | N 個の設計バリアントを生成 |
| `design/src/check.ts` |ビジョンベースのクオリティゲート |
| `design/src/brief.ts` |構造化されたブリーフタイプ + ヘルパー |
| `design/src/session.ts` |セッション状態管理 |
| `design/src/compare.ts` | HTML比較ボードジェネレーター |
| `design/test/design.test.ts` |統合テスト (OpenAI API のモック) |
| (なし — 既存の `scripts/resolvers/design.ts` に追加) | `{{DESIGN_SETUP}}` + `{{DESIGN_MOCKUP}}` リゾルバー |

### 変更するファイル

|ファイル |変更 |
|------|----------|
| `scripts/resolvers/types.ts` | `designDir` を `HostPaths` に追加 |
| `scripts/resolvers/index.ts` | DESIGN_SETUP + DESIGN_MOCKUP リゾルバーを登録する |
| `package.json` | `design` ビルド コマンドを追加 |
| `setup` |参照 | と一緒に設計バイナリをビルドします。
| `scripts/resolvers/preamble.ts` | Codex ホスト用の `GSTACK_DESIGN` 環境変数エクスポートを追加 |
| `test/gen-skill-docs.test.ts` |新しいリゾルバー用に DESIGN_SKETCH テスト スイートを更新 |
| `setup` |デザインバイナリビルド + Codex/Kiro アセットリンクを追加 |
| `office-hours/SKILL.md.tmpl` | Visual Sketch セクションを `{{DESIGN_MOCKUP}}` に置き換えます |
| `plan-design-review/SKILL.md.tmpl` | `{{DESIGN_SETUP}}` を追加 + スコアの低いディメンションのモックアップ生成 |

### 再利用する既存のコード

|コード |場所 |用途 |
|------|----------|----------|
| CLI パターンを参照 | `browse/src/cli.ts` |コマンドディスパッチアーキテクチャ |
| `commands.ts` レジストリ | `browse/src/commands.ts` |単一ソースの真実のパターン |
| `generateBrowseSetup()` | `scripts/resolvers/browse.ts` | `generateDesignSetup()` のテンプレート |
| `DESIGN_SKETCH` リゾルバー | `scripts/resolvers/design.ts` | `DESIGN_MOCKUP` リゾルバーのテンプレート |
|ホストパスシステム | `scripts/resolvers/types.ts` |マルチホストパス解決 |
|パイプラインの構築 | `package.json` ビルド スクリプト | `bun build --compile` パターン |

### APIの詳細

**生成:** `image_generation` ツールを使用した OpenAI Response API
```typescript
const response = await openai.responses.create({
  model: "gpt-4o",
  input: briefToPrompt(brief),
  tools: [{ type: "image_generation", size: "1536x1024", quality: "high" }],
});
// Extract image from response output items
const imageItem = response.output.find(item => item.type === "image_generation_call");
const base64Data = imageItem.result; // base64-encoded PNG
fs.writeFileSync(outputPath, Buffer.from(base64Data, "base64"));
```

**反復:** `previous_response_id` と同じ API
```typescript
const response = await openai.responses.create({
  model: "gpt-4o",
  input: feedback,
  previous_response_id: session.lastResponseId,
  tools: [{ type: "image_generation" }],
});
```
**注意:** `previous_response_id` によるマルチターン画像反復は、プロトタイプの検証が必要な仮定です。 Responses API は会話スレッドをサポートしていますが、編集スタイルの反復で生成された画像の視覚的なコンテキストを保持するかどうかはドキュメントで確認されていません。 **フォールバック:** マルチターンが機能しない場合、`iterate` は単一のプロンプトで元の概要と蓄積されたフィードバックを使用して再生成にフォールバックします。

**チェック:** GPT-4o ビジョン
```typescript
const check = await openai.chat.completions.create({
  model: "gpt-4o",
  messages: [{
    role: "user",
    content: [
      { type: "image_url", image_url: { url: `data:image/png;base64,${imageData}` } },
      { type: "text", text: `Check this UI mockup. Brief: ${brief}. Is text readable? Are all elements present? Does it look like a real UI? Return PASS or FAIL with issues.` }
    ]
  }]
});
```

**コスト:** デザイン セッションあたり ~$0.10 ～ $0.40 (1 ヒーロー + 2 バリアント + 1 品質チェック + 1 イテレーション)。各スキル呼び出しですでに LLM コストに次いで無視できます。

### 認証 (スモークテストで検証)

**Codex OAuth トークンは画像生成には機能しません。** 2026 年 3 月 26 日テスト済み: 画像 API と応答 API の両方が、「スコープが欠落しています: api.model.images.request」で `~/.codex/auth.json` access_token を拒否します。 Codex CLI にはネイティブの imagegen 機能もありません。

**認証解決順序:**
1. `~/.gstack/openai.json` → `{ "api_key": "sk-..." }` を読み取ります (ファイル権限 0600)
2. `OPENAI_API_KEY` 環境変数にフォールバックします
3. どちらも存在しない場合 → ガイド付きセットアップ フロー:
   - ユーザーに次のように伝えます: 「デザイン モックアップには、画像生成権限を持つ OpenAI API キーが必要です。platform.openai.com/api-keys で取得してください。」
   - ユーザーにキーを貼り付けるように求めます
   - 0600 権限で `~/.gstack/openai.json` に書き込みます
   - スモーク テストを実行して (1024x1024 のテスト イメージを生成)、キーが機能することを確認します。
   - 煙テストに合格した場合は、続行します。失敗した場合は、エラーを表示し、DESIGN_SKETCH に戻ります。
4. 認証は存在するが API 呼び出しが失敗した場合 → DESIGN_SKETCH (既存の HTML ワイヤーフレーム アプローチ) にフォールバックします。デザインのモックアップは段階的な機能強化であり、決して難しい要件ではありません。

**新しいコマンド:** `$D setup` — ガイド付き API キー設定 + スモーク テスト。いつでも実行してキーを更新できます。

## プロトタイプで検証する前提

1. **画質:** 「ピクセル完璧な UI モックアップ」は意欲的です。 GPT イメージの生成では、正確な UI 忠実度で正確なテキストのレンダリング、配置、間隔が確実に生成されない可能性があります。ビジョン品質ゲートは役に立ちますが、「実装するのに十分なレベル」という達成基準には、スキルを完全に統合する前にプロトタイプの検証が必要です。
2. **マルチターン反復:** `previous_response_id` が視覚的なコンテキストを保持するかどうかは証明されていません (API の詳細セクションを参照)。
3. **コスト モデル:** 推定 $0.10 ～ $0.40/セッションには実際の検証が必要です。

**プロトタイプ検証計画:** コミット 1 をビルド (コア生成 + チェック)、さまざまな画面タイプで 10 個の設計ブリーフを実行し、スキル統合に進む前に出力品質を評価します。

## CEO 拡張範囲 (/plan-ceo-review 範囲拡張経由で受け入れられます)

### 1. 設計メモリ + 探索幅制御
- 承認されたモックアップからビジュアル言語を DESIGN.md に自動抽出します。
- DESIGN.md が存在する場合、将来のモックアップを確立された設計言語に制限します。
- DESIGN.md (ブートストラップ) がない場合は、さまざまな方向に幅広く探索してください
- 漸進的制約: より確立された設計 = より狭い探査帯域
- 比較ボードには探索コントロールを備えた REGENERATE セクションが追加されます。
  - 「まったく違うもの」（幅広い探索）
  - 「オプション ___ のようなもの」 (お気に入りを絞り込む)
  - 「既存のデザインに一致」 (DESIGN.md に制限)
  - 特定の方向変更のための自由テキスト入力
  - 再生成によりページが更新され、エージェントが新しい送信をポーリングします。

### 2. モックアップの差分分析
- `$D diff --before old.png --after new.png` は視覚的な差分を生成します
- 変更された領域を強調表示して並べて表示
- GPT-4o ビジョンを使用して違いを識別します
- 使用場所: /design-review、反復フィードバック、PR レビュー

### 3. スクリーンショットからモックアップへの進化
- `$D evolve --screenshot current.png --brief "make it calmer"`
- ライブサイトのスクリーンショットを撮り、どのように見えるべきかを示すモックアップを生成します
- 空白のキャンバスではなく、現実から始まります
- /design-review の批評と視覚的な修正提案の間の橋渡し

### 4. 設計意図の検証
- /design-review 中に、承認されたモックアップ (docs/designs/) をライブ スクリーンショットにオーバーレイします。
- 相違点を強調: 「X を設計し、Y を構築しました。ここにギャップがあります」
- 完全なループを閉じる: 設計 -> 実装 -> 視覚的に検証
- $B スクリーンショット + $D 差分 + ビジョン分析を組み合わせます

### 5. レスポンシブなバリアント
- `$D variants --brief "..." --viewports desktop,tablet,mobile`
- 複数のビューポート サイズでモックアップを自動生成します
- 比較ボードには、同時承認のための応答性の高いグリッドが表示されます
- レスポンシブ デザインをモックアップの段階から最優先事項にします

### 6. デザインからコードへのプロンプト
- 比較委員会の承認後、構造化された実装プロンプトが自動生成されます
- ビジョン分析により、承認された PNG から色、タイポグラフィ、レイアウトを抽出します
- 構造化された仕様として DESIGN.md および HTML ワイヤーフレームと結合します
- 解釈ギャップゼロで「承認された設計」から「エージェントがコーディングを開始」までブリッジします。

### 将来のエンジン (この計画の範囲外)
- Magic Patterns の統合 (既存のデザインからパターンを抽出)
- バリアント API (出荷時、マルチバリエーション React コード + プレビュー)
- Figma MCP (双方向デザイン ファイル アクセス)
- Google Stitch SDK (無料の TypeScript 代替)

## 未解決の質問

1. Variant が API を出荷する場合、統合パスは何ですか? (デザイン バイナリ内の別個のエンジン、それともスタンドアロンのバリアント バイナリ?)
2. マジック パターンはどのように統合する必要がありますか? ($D の別のエンジン、それとも別のツール?)
3. 複数世代のバックエンドをサポートするために、デザイン バイナリにプラグイン/エンジン アーキテクチャが必要になるのはどの時点ですか?

## 成功基準

- UI アイデアで `/office-hours` を実行すると、デザイン ドキュメントと一緒に実際の PNG モックアップが生成されます
- `/plan-design-review` を実行すると、「より良く見えるもの」が散文ではなくモックアップとして表示されます
- モックアップは、開発者がモックアップから実装できるほど優れています。
- 品質ゲートは明らかに壊れたモックアップを検出し、再試行します
- 設計セッションあたりのコストは 0.50 ドル未満にとどまります

## 配布計画

デザイン バイナリはコンパイルされ、ブラウズ バイナリと一緒に配布されます。
- `bun build --compile design/src/cli.ts --outfile design/dist/design`
- `./setup` と `bun run build` の間に構築されました
- 既存の `~/.claude/skills/gstack/` インストール パスを介してシンボリックリンクされています

## 次のステップ (実装順序)

### コミット 0: プロトタイプの検証 (インフラストラクチャを構築する前に合格する必要があります)
- 3 つの異なる設計ブリーフを GPT Image API に送信する単一ファイルのプロトタイプ スクリプト (約 50 行)
- 検証: テキストのレンダリング品質、レイアウトの精度、視覚的な一貫性
- 出力が UI モックアップの「恥ずかしいほどひどい AI アート」である場合は、停止してください。アプローチを再評価します。
- これは、インフラストラクチャの 8 ファイルを構築する前に、中核となる前提条件を検証する最も安価な方法です。

### コミット 1: バイナリ コアの設計 (生成 + チェック + 比較)
- `design/src/` と cli.ts、commands.ts、generate.ts、check.ts、brief.ts、session.ts、compare.ts
- 認証モジュール (~/.gstack/openai.json の読み取り、環境変数へのフォールバック、ガイド付きセットアップ フロー)
- `compare` コマンドは、バリアントごとのフィードバック テキストエリアを備えた HTML 比較ボードを生成します
- `package.json` ビルドコマンド (`bun build --compile` をブラウズから分離)
- `setup` スクリプトの統合 (Codex + Kiro アセットのリンクを含む)
- モック OpenAI API サーバーを使用した単体テスト

### コミット 2: バリアント + 反復
- `design/src/variants.ts`、`design/src/iterate.ts`
- 時間差並列生成 (開始間の遅延 1 秒、429 の指数バックオフ)
- マルチターンのセッション状態管理
- 反復フロー + レート制限処理のテスト

### コミット 3: テンプレートの統合
- 既存の`scripts/resolvers/design.ts`に`generateDesignSetup()` + `generateDesignMockup()`を追加します
- `scripts/resolvers/types.ts`の`HostPaths`に`designDir`を追加
- DESIGN_SETUP + DESIGN_MOCKUPを`scripts/resolvers/index.ts`に登録します
- GSTACK_DESIGN 環境変数エクスポートを `scripts/resolvers/preamble.ts` (Codex ホスト) に追加
- `test/gen-skill-docs.test.ts` (DESIGN_SKETCH テスト スイート) を更新します
- SKILL.mdファイルを再生成します

### コミット 4: /office-hours の統合
- Visual Sketch セクションを `{{DESIGN_MOCKUP}}` に置き換えます
- 連続ワークフロー: バリアントの生成 → $D 比較 → ユーザー フィードバック → DESIGN_SKETCH HTML ワイヤーフレーム
- 承認されたモックアップを docs/designs/ に保存します (承認されたモックアップのみ、探索は含まれません)

### コミット 5: /plan-design-review 統合
- `{{DESIGN_SETUP}}` を追加し、スコアの低いディメンションのモックアップ生成を追加
- 「10/10 はどのように見えるか」モックアップの比較

### コミット 6: デザイン メモリ + 探索幅制御 (CEO 拡張)
- モックアップの承認後、GPT-4o ビジョンを介して視覚言語を抽出します
- 抽出した色、タイポグラフィ、間隔、レイアウト パターンを使用して DESIGN.md を作成/更新します
- DESIGN.md が存在する場合、それを制約コンテキストとして今後のすべてのモックアップ プロンプトにフィードします。
- 比較ボード HTML に REGENERATE セクションを追加 (チクレット + フリー テキスト + リフレッシュ ループ)
- 簡単な構造の漸進的制約ロジック

### コミット 7: モックアップの差分 + 設計意図の検証 (CEO 拡張)
- `$D diff` コマンド: 2 つの PNG を取得し、GPT-4o ビジョンを使用して相違点を識別し、オーバーレイを生成します
- `$D verify` コマンド: $B 経由でライブ サイトのスクリーンショットを取得し、docs/designs/ から承認されたモックアップとの差分を取得します。
- /design-review テンプレートへの統合: 承認されたモックアップが存在する場合に自動検証

### コミット 8: スクリーンショットからモックアップへの進化 (CEO の拡張)
- `$D evolve` コマンド: スクリーンショットと概要を取得し、「どのように見えるか」モックアップを生成します
- スクリーンショットを参照画像として GPT Image API に送信します
- /design-review への統合: 「修正は次のようになります」というビジュアル提案

### コミット 9: レスポンシブバリアント + デザインからコードへのプロンプト (CEO 拡張)
- マルチサイズ生成用の `$D variants` の `--viewports` フラグ
- 比較ボードの応答性の高いグリッド レイアウト
- 承認後に構造化された実装プロンプトを自動生成
- 承認された PNG の視覚分析により、プロンプトの色、タイポグラフィ、レイアウトを抽出します

## 課題

Variant に API を構築するように指示します。投資家として: 「AI エージェントがプログラムでビジュアル デザインを生成するワークフローを構築しています。GPT Image API は現在機能しますが、デザインの探索にはマルチバリエーション アプローチの方が適しているため、むしろ Variant を使用したいと考えています。API エンドポイントを出荷します。プロンプトを入力し、React コード + プレビュー画像を出力します。私はあなたの最初の統合パートナーになります。」

＃＃ 検証

1. `bun run build` は `design/dist/design` バイナリをコンパイルします
2. `$D generate --brief "Landing page for a developer tool" --output /tmp/test.png` は実際の PNG を生成します
3. `$D check --image /tmp/test.png --brief "Landing page"` は PASS/FAIL を返します
4. `$D variants --brief "..." --count 3 --output-dir /tmp/variants/` は 3 つの PNG を生成します
5. UI アイデアで `/office-hours` を実行すると、インラインでモックアップが生成されます
6. `bun test` 合格 (スキル検証、gen-skill-docs)
7. `bun run test:evals` に合格 (E2E テスト)

## あなたの考え方について気づいたこと

――文字の説明やアスキーアートについて「それはデザインではない」とおっしゃっていました。それはデザイナーの本能です。あなたは、物事を説明することと、物を見せることの違いを知っています。 AI ツールを構築している人のほとんどは、デザイナーではなかったため、このギャップに気づきません。
- 上流の活用ポイントである /office-hours を最初に優先しました。ブレインストーミングによって実際のモックアップが生成される場合、すべての下流スキル (/plan-design-review、/design-review) には、散文を再解釈する代わりに参照する視覚的なアーティファクトが含まれます。
- あなたは Variant に資金を提供し、すぐに「API が必要だ」と思いました。それはユーザーとしての投資家の考え方です。あなたは単に会社を評価しているのではなく、その製品が自分のワークフローにどのように適合するかを設計しているのです。
- Codex がオプトインの前提に異議を唱えたとき、あなたはすぐにそれを受け入れました。エゴの防御はありません。それが正しい答えへの一番の近道です。

## 仕様レビューの結果

ドクは1ラウンドの敵対的レビューを生き延びた。 11 件の問題が見つかり、修正されました。
品質スコア: 7/10 → 修正後の推定値は 8.5/10。

修正された問題:
1. OpenAI SDK 依存関係の宣言
2. 画像データ抽出パス指定(response.出力項目形状)
3. --check および --retry フラグがコマンド レジストリに正式に登録されました
4. 指定された簡単な入力モード (プレーンテキストと JSON ファイル)
5. リゾルバーファイルの矛盾を修正 (既存の design.ts に追加)
6. HostPaths Codex 環境変数の設定をメモしました
7. 「ミラーブラウズ」を「共有編集/配布パターン」にリフレーム
8. セッション状態の指定 (ID 生成、検出、クリーンアップ)
9. プロトタイプの検証が必要な仮定として「ピクセルパーフェクト」のフラグが立てられる
10. フォールバック計画で証明されていないとフラグが立てられたマルチターン反復
11. DESIGN_SKETCH へのフォールバックを備えた完全に指定された $D 検出 bash ブロック

## エンジニアリングレビュー完了の概要

- ステップ 0: スコープ チャレンジ — スコープはそのまま受け入れられます (完全なバイナリ、ユーザーによるオーバーライド削減の推奨)
- アーキテクチャレビュー: 5 つの問題が見つかりました (openai dep 分離、グレースフル デグレード、出力ディレクトリ設定、認証モデル、信頼境界)
- コード品質レビュー: 1 件の問題が見つかりました (8 ファイル対 5、8 件のまま)
- テストレビュー: 図の作成、42 のギャップの特定、テスト計画の作成
- パフォーマンスレビュー: 1 件の問題が見つかりました (時間差スタートの並列バリアント)
- 対象外: Google Stitch SDK 統合、Figma MCP、Variant API (延期)
- 既存のもの: CLI パターンの参照、DESIGN_SKETCH リゾルバー、HostPaths システム、gen-skill-docs パイプライン
- 外部の声: 4 パス (クロード構造化 12 問題、コーデックス構造化 8 問題、クロード敵対的 1 つの致命的欠陥、コーデックス敵対的 1 つの致命的欠陥)。重要な洞察: PNG→HTML の連続ワークフローにより、「不透明なラスター」という致命的な欠陥が解決されました。
- 障害モード: 重大なギャップは 0 (特定されたすべての障害モードにはエラー処理があり、テストは計画されています)
- Lake Score: 7/7 の推奨事項が完全なオプションを選択しました

## GSTACK レビュー レポート

|レビュー |トリガー |なぜ |走る |ステータス |調査結果 |
|--------|-----------|-----|------|--------|----------|
|営業時間 | `/office-hours` |デザインブレインストーミング | 1 |完了 | 4 つの前提、1 つは改訂されました (コーデックス: オプトイン -> デフォルトオン) |
| CEO レビュー | `/plan-ceo-review` |範囲と戦略 | 1 |クリア |拡張: 6 件が提案、6 件が承認、0 件が延期 |
|エンジニアリングレビュー | `/plan-eng-review` |アーキテクチャとテスト (必須) | 1 |クリア | 7 つの問題、0 つの重大なギャップ、4 つの外部の声 |
|デザインレビュー | `/plan-design-review` | UI/UX のギャップ | 1 |クリア |スコア: 2/10 -> 8/10、5 つの決定が下されました |
|外部の声 |構造化 + 敵対的 |自主的な挑戦 | 4 |完了 |シーケンシャル PNG->HTML ワークフロー、信頼境界が示される |

**CEO の拡張:** デザイン メモリ + 探索幅、モックアップの比較、スクリーンショットの進化、設計意図の検証、レスポンシブ バリアント、デザインからコードまでのプロンプト。
**設計上の決定事項:** 単一列の全幅レイアウト、カードごとの「More like this」、明示的なラジオピック、スムーズなフェード再生成、スケルトンロード状態。
**未解決:** 0
**評決:** CEO + ENG + デザインはクリアされました。実装する準備ができました。コミット 0 (プロトタイプの検証) から始めます。