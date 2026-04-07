＃ 建築

このドキュメントでは、gstack がこのように構築されている **理由** について説明します。セットアップとコマンドについては、CLAUDE.md を参照してください。貢献については、CONTRIBUTING.md を参照してください。

## 核となるアイデア

gstack は、Claude Code に永続的なブラウザと一連の独自のワークフロー スキルを提供します。難しいのはブラウザです。その他はすべて Markdown です。

重要な洞察: ブラウザーと対話する AI エージェントには **1 秒未満の遅延** と **永続的な状態** が必要です。すべてのコマンドがブラウザをコールドスタートすると、ツール呼び出しごとに 3 ～ 5 秒待つことになります。コマンド間でブラウザが停止すると、Cookie、タブ、ログイン セッションが失われます。そのため、gstack は、CLI がローカルホスト HTTP 経由で通信する長寿命の Chromium デーモンを実行します。

```
Claude Code                     gstack
─────────                      ──────
                               ┌──────────────────────┐
  Tool call: $B snapshot -i    │  CLI (compiled binary)│
  ─────────────────────────→   │  • reads state file   │
                               │  • POST /command      │
                               │    to localhost:PORT   │
                               └──────────┬───────────┘
                                          │ HTTP
                               ┌──────────▼───────────┐
                               │  Server (Bun.serve)   │
                               │  • dispatches command  │
                               │  • talks to Chromium   │
                               │  • returns plain text  │
                               └──────────┬───────────┘
                                          │ CDP
                               ┌──────────▼───────────┐
                               │  Chromium (headless)   │
                               │  • persistent tabs     │
                               │  • cookies carry over  │
                               │  • 30min idle timeout  │
                               └───────────────────────┘
```

最初の呼び出しですべてが開始されます (約 3 秒)。以降のすべての呼び出し: ~100 ～ 200 ミリ秒。

## なぜパンなのか

Node.js は機能します。ここでは 3 つの理由から Bun の方が優れています。

1. **コンパイルされたバイナリ。** `bun build --compile` は、最大 58MB の単一の実行可能ファイルを生成します。実行時に `node_modules` はありません。 `npx` もありません。PATH 構成もありません。バイナリはそのまま実行されます。 gstack はユーザーが Node.js プロジェクトを管理することを期待していない `~/.claude/skills/` にインストールされるため、これは重要です。

2. **ネイティブ SQLite。** Cookie 復号化は、Chromium の SQLite Cookie データベースを直接読み取ります。 Bun には `new Database()` が組み込まれています — いいえ `better-sqlite3`、ネイティブ アドオン コンパイル、Gyp はありません。さまざまなマシンで壊れる問題が 1 つ減ります。

3. **ネイティブ TypeScript。** 開発中、サーバーは `bun run server.ts` として実行されます。コンパイル手順、`ts-node`、デバッグするソース マップはありません。コンパイルされたバイナリはデプロイメント用です。ソースファイルは開発用です。

4. **内蔵 HTTP サーバー** `Bun.serve()` は高速かつシンプルで、Express や Fastify は必要ありません。サーバーは合計約 10 個のルートを処理します。フレームワークはオーバーヘッドになります。

ボトルネックは常に Chromium であり、CLI やサーバーではありません。 Bun の起動速度 (コンパイルされたバイナリでは約 1 ミリ秒、ノードでは約 100 ミリ秒) は優れていますが、それを選択した理由ではありません。コンパイルされたバイナリとネイティブ SQLite は次のとおりです。

## デーモンモデル

### コマンドごとにブラウザを起動してみてはいかがでしょうか?

Playwright は約 2 ～ 3 秒で Chromium を起動できます。スクリーンショット 1 枚の場合は問題ありません。 20 以上のコマンドを含む QA セッションの場合、ブラウザーの起動に 40 秒以上のオーバーヘッドがかかります。さらに悪いことに、コマンド間のすべての状態が失われます。 Cookie、localStorage、ログインセッション、開いているタブ、すべてが消えてしまいます。

デーモン モデルとは次のことを意味します。

- **永続的な状態。** 一度ログインすると、ログインしたままになります。タブを開くと、開いたままになります。 localStorage persists across commands.
- **1 秒未満のコマンド。** 最初の呼び出しの後、すべてのコマンドは単なる HTTP POST です。 ~100-200ms round-trip including Chromium's work.
- **自動ライフサイクル。** サーバーは最初の使用時に自動起動し、30 分間アイドル状態が続くと自動的にシャットダウンします。 No process management needed.

### 状態ファイル

サーバーは `.gstack/browse.json` を書き込みます (tmp + rename によるアトミック書き込み、モード 0o600):

```json
{ "pid": 12345, "port": 34567, "token": "uuid-v4", "startedAt": "...", "binaryVersion": "abc123" }
```

CLI はこのファイルを読み取り、サーバーを見つけます。ファイルが見つからない場合、またはサーバーが HTTP ヘルスチェックに失敗した場合、CLI は新しいサーバーを生成します。 Windows では、Bun バイナリでは PID ベースのプロセス検出の信頼性が低いため、ヘルス チェック (GET /health) がすべてのプラットフォームで主要な活性信号となります。

### ポートの選択

10000 ～ 60000 の間のランダムなポート (衝突時に最大 5 回再試行)。これは、10 個の Conductor ワークスペースがそれぞれ独自の参照デーモンを設定なし、ポート競合なしで実行できることを意味します。古いアプローチ (9400 ～ 9409 をスキャン) は、マルチワークスペース設定で常に機能しませんでした。

### バージョンの自動再起動

ビルドは `git rev-parse HEAD` を `browse/dist/.version` に書き込みます。 CLI を呼び出すたびに、バイナリのバージョンが実行中のサーバーの `binaryVersion` と一致しない場合、CLI は古いサーバーを強制終了し、新しいサーバーを起動します。これにより、「古いバイナリ」クラスのバグが完全に防止されます。バイナリが再構築され、次のコマンドがそれを自動的に取得します。

## セキュリティモデル

### ローカルホストのみ

HTTP サーバーは、`0.0.0.0` ではなく、`localhost` にバインドされます。ネットワークからはアクセスできません。

### ベアラートークン認証

すべてのサーバー セッションはランダムな UUID トークンを生成し、モード 0o600 (所有者専用読み取り) で状態ファイルに書き込まれます。すべての HTTP リクエストには `Authorization: Bearer <token>` を含める必要があります。トークンが一致しない場合、サーバーは 401 を返します。

これにより、同じマシン上の他のプロセスがブラウズ サーバーと通信できなくなります。 Cookie ピッカー UI (`/cookie-picker`) とヘルス チェック (`/health`) は除外されます。これらはローカルホストのみであり、コマンドは実行されません。

### Cookie のセキュリティ

Cookie は、gstack が処理する最も機密性の高いデータです。デザイン:

1. **キーチェーン アクセスにはユーザーの承認が必要です。** ブラウザごとに最初に Cookie をインポートすると、macOS キーチェーン ダイアログがトリガーされます。ユーザーは「許可」または「常に許可」をクリックする必要があります。 gstack がサイレントに認証情報にアクセスすることはありません。

2. **復号化はプロセス内で行われます。** Cookie 値はメモリ (PBKDF2 + AES-128-CBC) で復号化され、Playwright コンテキストにロードされ、平文でディスクに書き込まれることはありません。 Cookie ピッカー UI には Cookie 値は表示されず、ドメイン名とカウントのみが表示されます。

3. **データベースは読み取り専用です。** gstack は Chromium cookie DB を一時ファイルにコピーし (実行中のブラウザとの SQLite ロックの競合を避けるため)、それを読み取り専用で開きます。実際のブラウザの Cookie データベースが変更されることはありません。

4. **キーのキャッシュはセッションごとです。** キーチェーンのパスワードと派生 AES キーは、サーバーの存続期間中メモリにキャッシュされます。サーバーがシャットダウンすると (アイドル タイムアウトまたは明示的な停止)、キャッシュは失われます。

5. **ログに Cookie 値は含まれません。** コンソール、ネットワーク、ダイアログ ログには Cookie 値が含まれることはありません。 `cookies` コマンドは Cookie メタデータ (ドメイン、名前、有効期限) を出力しますが、値は切り捨てられます。

### シェルインジェクションの防止

ブラウザー レジストリ (Comet、Chrome、Arc、Brave、Edge) はハードコーディングされています。データベース パスは、ユーザー入力からではなく、既知の定数から構築されます。キーチェーン アクセスでは、シェル文字列補間ではなく、明示的な引数配列で `Bun.spawn()` を使用します。

## 参照システム

参照 (`@e1`、`@e2`、`@c1`) は、CSS セレクターや XPath を記述せずにエージェントがページ要素をアドレス指定する方法です。

### 仕組み

```
1. Agent runs: $B snapshot -i
2. Server calls Playwright's page.accessibility.snapshot()
3. Parser walks the ARIA tree, assigns sequential refs: @e1, @e2, @e3...
4. For each ref, builds a Playwright Locator: getByRole(role, { name }).nth(index)
5. Stores Map<string, RefEntry> on the BrowserManager instance (role + name + Locator)
6. Returns the annotated tree as plain text

Later:
7. Agent runs: $B click @e3
8. Server resolves @e3 → Locator → locator.click()
```

### DOM ミューテーションではなくロケーターを使用する理由

明らかなアプローチは、`data-ref="@e1"` 属性を DOM に挿入することです。これは次のように続きます。

- **CSP (コンテンツ セキュリティ ポリシー)** 多くの運用サイトでは、スクリプトによる DOM の変更がブロックされています。
- **React/Vue/Svelte のハイドレーション。** フレームワークの調整により、挿入された属性が削除される可能性があります。
- **Shadow DOM.** 外部から内部のシャドウ ルートにアクセスできません。

Playwright Locator は DOM の外部にあります。これらは、アクセシビリティ ツリー (Chromium が内部で維持している) と `getByRole()` クエリを使用します。 DOM の変更、CSP の問題、フレームワークの競合はありません。

### 参照ライフサイクル

Ref はナビゲーションでクリアされます (メイン フレームの `framenavigated` イベント)。これは正しいです。ナビゲーション後は、すべてのロケーターが古くなります。新しい参照を取得するには、エージェントは再度 `snapshot` を実行する必要があります。これは仕様によるものです。古い参照は間違った要素をクリックするのではなく、大声で失敗する必要があります。

### Ref の古さの検出

SPA は、`framenavigated` をトリガーせずに DOM を変更できます (例: React ルーターの遷移、タブの切り替え、モーダルの開き)。これにより、ページ URL が変更されていない場合でも、refs が古くなります。これをキャッチするために、 `resolveRef()` は、参照を使用する前に非同期 `count()` チェックを実行します。

```
resolveRef(@e3) → entry = refMap.get("e3")
                → count = await entry.locator.count()
                → if count === 0: throw "Ref @e3 is stale — element no longer exists. Run 'snapshot' to get fresh refs."
                → if count > 0: return { locator }
```

これは、要素が欠落している場合に Playwright の 30 秒のアクション タイムアウトが期限切れになるのではなく、高速に失敗します (最大 5 ミリ秒のオーバーヘッド)。 `RefEntry` は、ロケーターと一緒に `role` および `name` メタデータを保存するため、エラー メッセージでエージェントがその要素が何であるかを伝えることができます。

### カーソルインタラクティブ参照 (@c)

`-C` フラグは、クリック可能だが ARIA ツリー内にない要素、つまり `cursor: pointer` でスタイル設定された要素、`onclick` 属性を持つ要素、またはカスタム `tabindex` を検索します。これらは、別の名前空間で `@c1`、`@c2` 参照を取得します。これは、フレームワークが `<div>` としてレンダリングするが、実際にはボタンであるカスタム コンポーネントをキャッチします。

## ロギングアーキテクチャ

3 つのリング バッファ (それぞれ 50,000 エントリ、O(1) プッシュ):

```
Browser events → CircularBuffer (in-memory) → Async flush to .gstack/*.log
```

コンソール メッセージ、ネットワーク リクエスト、ダイアログ イベントにはそれぞれ独自のバッファがあります。フラッシュは 1 秒ごとに行われます。サーバーは、最後のフラッシュ以降の新しいエントリのみを追加します。これはつまり：

- HTTP リクエストの処理がディスク I/O によってブロックされることはありません
- サーバーがクラッシュしてもログは残ります (最大 1 秒のデータ損失)
- メモリは制限されています (50K エントリ × 3 バッファ)
- ディスク ファイルは追加専用で、外部ツールで読み取り可能です

`console`、`network`、および `dialog` コマンドは、ディスクではなくメモリ内のバッファから読み取ります。ディスク ファイルは事後デバッグ用です。

## SKILL.md テンプレート システム

＃＃＃ 問題

SKILL.md ファイルは、クロードに参照コマンドの使用方法を指示します。ドキュメントに存在しないフラグがリストされている場合、または追加されたコマンドが欠落している場合、エージェントはエラーを発生します。手動で管理されたドキュメントは常にコードから逸脱します。

### 解決策

```
SKILL.md.tmpl          (human-written prose + placeholders)
       ↓
gen-skill-docs.ts      (reads source code metadata)
       ↓
SKILL.md               (committed, auto-generated sections)
```

テンプレートには、人間の判断が必要なワークフロー、ヒント、例が含まれています。プレースホルダーはビルド時にソース コードから埋められます。

|プレースホルダー |出典 |生成されるもの |
|-------------|--------|--------|
| `{{COMMAND_REFERENCE}}` | `commands.ts` |カテゴリー別コマンド表 |
| `{{SNAPSHOT_FLAGS}}` | `snapshot.ts` |例を含むフラグのリファレンス |
| `{{PREAMBLE}}` | `gen-skill-docs.ts` |スタートアップ ブロック: 更新チェック、セッション トラッキング、投稿者モード、AskUserQuestion 形式 |
| `{{BROWSE_SETUP}}` | `gen-skill-docs.ts` |バイナリ検出 + セットアップ手順 |
| `{{BASE_BRANCH_DETECT}}` | `gen-skill-docs.ts` | PR ターゲティング スキルのための動的なベース ブランチ検出 (出荷、レビュー、QA、計画-CEO-レビュー) |
| `{{QA_METHODOLOGY}}` | `gen-skill-docs.ts` | /qa および /qa のみの共有 QA 方法論ブロック |
| `{{DESIGN_METHODOLOGY}}` | `gen-skill-docs.ts` | /plan-design-review および /design-review の共有設計監査方法論 |
| `{{REVIEW_DASHBOARD}}` | `gen-skill-docs.ts` | /ship の飛行前準備ダッシュボードを確認する |
| `{{TEST_BOOTSTRAP}}` | `gen-skill-docs.ts` | /qa、/ship、/design-review のテスト フレームワークの検出、ブートストラップ、CI/CD セットアップ |
| `{{CODEX_PLAN_REVIEW}}` | `gen-skill-docs.ts` | /plan-ceo-review および /plan-eng-review のオプションのクロスモデル プラン レビュー (Codex または Claude サブエージェント フォールバック) |
| `{{DESIGN_SETUP}}` | `resolvers/design.ts` | `$D` デザイン バイナリ、ミラー `{{BROWSE_SETUP}}` の検出パターン |
| `{{DESIGN_SHOTGUN_LOOP}}` | `resolvers/design.ts` | /design-shotgun、/plan-design-review、/design-consultation の共有比較ボード フィードバック ループ |

これは構造的には適切です。コマンドがコード内に存在する場合、それはドキュメントに表示されます。存在しない場合は表示できません。

### 前文

すべてのスキルは、スキル自体のロジックの前に実行される `{{PREAMBLE}}` ブロックから始まります。単一の bash コマンドで 5 つのことを処理します。

1. **更新チェック** — `gstack-update-check` を呼び出し、アップグレードが利用可能かどうかを報告します。
2. **セッション追跡** — `~/.gstack/sessions/$PPID` をタッチすると、アクティブなセッション (過去 2 時間以内に変更されたファイル) がカウントされます。 3 つ以上のセッションが実行されている場合、すべてのスキルは「ELI16 モード」に入ります。ユーザーはウィンドウを操作しているため、すべての質問でコンテキストを再認識することになります。
3. **運用上の自己改善** — すべてのスキル セッションの終了時に、エージェントは失敗 (CLI エラー、間違ったアプローチ、プロジェクトの癖) を振り返り、今後のセッションのために運用上の学習をプロジェクトの JSONL ファイルに記録します。
4. **AskUserQuestion 形式** — 汎用形式: コンテキスト、質問、`RECOMMENDATION: Choose X because ___`、文字付きオプション。 Consistent across all skills.
5. **構築前に検索** — インフラストラクチャや不慣れなパターンを構築する前に、まず検索します。知識の 3 つの層: 実証済み (層 1)、新しく普及したもの (層 2)、第一原理 (層 3)。第一原理推論によって従来の通念が間違っていることが明らかになった場合、エージェントは「エウレカモーメント」と名付けて記録します。完全なビルダーの哲学については、`ETHOS.md` を参照してください。

### なぜ実行時に生成されずにコミットされるのでしょうか?

3 つの理由:

1. **クロードはスキルのロード時に SKILL.md を読み取ります。** ユーザーが `/browse` を呼び出すとき、ビルドステップはありません。ファイルはすでに存在しており、正しいものである必要があります。
2. **CI は鮮度を検証できます。** `gen:skill-docs --dry-run` + `git diff --exit-code` はマージ前に古いドキュメントを検出します。
3. **Gitblame は機能します。** コマンドがいつ、どのコミットに追加されたかを確認できます。

### テンプレートのテスト層

|階層 |何を |コスト |スピード |
|------|------|------|------|
| 1 — 静的検証 | SKILL.md 内のすべての `$B` コマンドを解析し、レジストリに対して検証します。無料 | <2秒 |
| 2 — `claude -p` 経由の E2E |実際のクロード セッションを生成し、各スキルを実行し、エラーをチェックします。 ~$3.85 | ～20分 |
| 3 — 裁判官としての LLM | Sonnet は、明快さ、完全性、実行可能性についてドキュメントを採点します。 ~0.15ドル | ～30代 |

Tier 1 runs on every `bun test`. Tiers 2+3 are gated behind `EVALS=1`.アイデアは、問題の 95% を無料で捕捉し、LLM は判断の際にのみ使用するというものです。

## コマンドディスパッチ

コマンドは副作用ごとに分類されています。

- **読み取り** (テキスト、HTML、リンク、コンソール、Cookie など): 変更はありません。安全に再試行できます。ページの状態を返します。
- **WRITE** (g​​oto、click、fill、press、...): ページの状態を変更します。べき等ではありません。
- **メタ** (スナップショット、スクリーンショット、タブ、チェーンなど): 読み取り/書き込みに適切に適合しないサーバーレベルの操作。

これは組織的なものだけではありません。サーバーはそれをディスパッチに使用します。

```typescript
if (READ_COMMANDS.has(cmd))  → handleReadCommand(cmd, args, bm)
if (WRITE_COMMANDS.has(cmd)) → handleWriteCommand(cmd, args, bm)
if (META_COMMANDS.has(cmd))  → handleMetaCommand(cmd, args, bm, shutdown)
```

`help` コマンドは 3 つのセットすべてを返すため、エージェントは利用可能なコマンドを自己検出できます。

## エラーの哲学

エラーは人間ではなく AI エージェントに発生します。すべてのエラー メッセージは対処可能である必要があります。

- 「要素が見つかりません」 → 「要素が見つからないか、対話可能ではありません。利用可能な要素を確認するには、`snapshot -i` を実行してください。」
- 「セレクターは複数の要素に一致しました」 → 「セレクターは複数の要素に一致しました。代わりに `snapshot` の @refs を使用してください。」
・タイムアウト→「30秒後にナビゲーションがタイムアウトしました。ページが遅いか、URLが間違っている可能性があります。」

Playwright のネイティブ エラーは、内部スタック トレースを削除し、ガイダンスを追加するために、`wrapError()` を通じて書き換えられます。エージェントは、人間の介入なしにエラーを読み取り、次に何をすべきかを知ることができる必要があります。

### クラッシュリカバリ

The server doesn't try to self-heal. Chromium がクラッシュすると (`browser.on('disconnected')`)、サーバーはただちに終了します。 CLI は次のコマンドで停止したサーバーを検出し、自動再起動します。これは、半分停止したブラウザ プロセスに再接続しようとするよりも簡単で信頼性が高くなります。

## E2E テスト インフラストラクチャ



E2E テストは、エージェント SDK を介さずに完全に独立したサブプロセスとして `claude -p` を生成します。エージェント SDK はクロード コード セッション内にネストできません。ランナー:

1. プロンプトを一時ファイルに書き込みます (シェルエスケープの問題を回避します)。
2. Spawns `sh -c 'cat prompt | claude -p --output-format stream-json --verbose'`
3. リアルタイムの進行状況のために標準出力から NDJSON をストリーミングします
4. Races against a configurable timeout
5. 完全な NDJSON トランスクリプトを解析して構造化された結果を生成します

`parseNDJSON()` 関数は純粋であり、I/O や副作用がなく、独立してテストできます。



```
  skill-e2e-*.test.ts
        │
        │ generates runId, passes testName + runId to each call
        │
  ┌─────┼──────────────────────────────┐
  │     │                              │
  │  runSkillTest()              evalCollector
  │  (session-runner.ts)         (eval-store.ts)
  │     │                              │
  │  per tool call:              per addTest():
  │  ┌──┼──────────┐              savePartial()
  │  │  │          │                   │
  │  ▼  ▼          ▼                   ▼
  │ [HB] [PL]    [NJ]          _partial-e2e.json
  │  │    │        │             (atomic overwrite)
  │  │    │        │
  │  ▼    ▼        ▼
  │ e2e-  prog-  {name}
  │ live  ress   .ndjson
  │ .json .log
  │
  │  on failure:
  │  {name}-failure.json
  │
  │  ALL files in ~/.gstack-dev/
  │  Run dir: e2e-runs/{runId}/
  │
  │         eval-watch.ts
  │              │
  │        ┌─────┴─────┐
  │     read HB     read partial
  │        └─────┬─────┘
  │              ▼
  │        render dashboard
  │        (stale >10min? warn)
```

**所有権の分割:** session-runner はハートビート (現在のテスト状態) を所有し、eval-store は部分的な結果 (完了したテスト状態) を所有します。ウォッチャーは両方を読み取ります。どちらのコンポーネントも相手のことを知りません。ファイルシステムを通じてのみデータを共有します。

**致命的ではないすべて:** すべての可観測性 I/O は try/catch でラップされます。書き込み失敗によってテストが失敗することはありません。テスト自体が真実の源です。可観測性はベストエフォートです。

**機械可読診断:** 各テスト結果には、`exit_reason` (success、timeout、error_max_turns、error_api、exit_code_N)、`timeout_at_turn`、および `last_tool_call` が含まれます。これにより、次のような `jq` クエリが有効になります。
```bash
jq '.tests[] | select(.exit_reason == "timeout") | .last_tool_call' ~/.gstack-dev/evals/_partial-e2e.json
```

### 評価永続化 (`test/helpers/eval-store.ts`)

`EvalCollector` はテスト結果を蓄積し、次の 2 つの方法で書き込みます。

1. **インクリメンタル:** `savePartial()` は、各テスト後に `_partial-e2e.json` を書き込みます (アトミック: `.tmp`、`fs.renameSync` を書き込みます)。殺しても生き残る。
2. **最終:** `finalize()` は、タイムスタンプ付きの eval ファイル (例: `e2e-20260314-143022.json`) を書き込みます。部分ファイルはクリーンアップされることはなく、可観測性を確保するために最終ファイルと一緒に保持されます。

`eval:compare` diffs two eval runs. `eval:summary` は、`~/.gstack-dev/evals/` のすべての実行にわたる統計を集計します。

### テスト層

|階層 |何を |コスト |スピード |
|------|------|------|-------|
| 1 — Static validation | `$B` コマンドの解析、レジストリに対する検証、可観測性単体テスト |無料 | <5秒 |
| 2 — E2E via `claude -p` |実際のクロード セッションを生成し、各スキルを実行し、エラーをスキャンします。 ~$3.85 | ～20分 |
| 3 — 裁判官としての LLM | Sonnet は、明快さ、完全性、実行可能性についてドキュメントを採点します。 ~0.15ドル | ～30代 |

Tier 1 はすべての `bun test` で実行されます。 Tier 2+3 は `EVALS=1` の後ろでゲートされています。アイデア: 問題の 95% を無料で捕捉し、LLM は判断の呼び出しと統合テストにのみ使用します。

## 意図的にここにないもの

- **WebSocket ストリーミングはありません。** HTTP リクエスト/レスポンスはよりシンプルで、curl でデバッグ可能で、十分に高速です。ストリーミングにより複雑さが増すだけで、利益はわずかになります。
- **MCP プロトコルなし。** MCP はリクエストごとに JSON スキーマのオーバーヘッドを追加し、永続的な接続を必要とします。プレーン HTTP + プレーン テキスト出力はトークンが軽く、デバッグが簡単です。
- **マルチユーザー サポートなし。** ワークスペースごとに 1 つのサーバー、1 人のユーザー。トークン認証は多層防御であり、マルチテナンシーではありません。
- **Windows/Linux Cookie の復号化はありません。** サポートされている認証情報ストアは macOS キーチェーンのみです。 Linux (GNOME キーリング/kwallet) と Windows (DPAPI) はアーキテクチャ的には可能ですが、実装されていません。
- **iframe 自動検出はありません。** `$B frame` はクロスフレーム インタラクション (CSS セレクター、@ref、`--name`、`--url` マッチング) をサポートしますが、ref システムは `snapshot` 中に iframe を自動クロールしません。最初にフレーム コンテキストを明示的に入力する必要があります。