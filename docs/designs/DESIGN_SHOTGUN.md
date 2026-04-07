# 設計: Shotgun の設計 — ブラウザからエージェントへのフィードバック ループ

2026-03-27 に生成
ブランチ: garrytan/agent-design-tools
ステータス: LIVING DOCUMENT — バグが見つかって修正され次第更新します

## この機能の内容

Design Shotgun は複数の AI デザイン モックアップを生成し、それらを並べて開きます。
ユーザーの実際のブラウザを比較ボードとして使用し、構造化されたフィードバックを収集します (選択
お気に入り、代替案の評価、メモを残す、再生成のリクエストなど）。フィードバックの流れ
コーディング エージェントに戻り、コーディング エージェントがそれに基づいて動作します。
バリアントを作成するか、新しいバリアントを生成してボードをリロードします。

ユーザーはブラウザのタブから離れることはありません。エージェントは冗長な質問をすることはありません。
ボードはフィードバック機構です。

## 核心問題: 話し合わなければならない 2 つの世界

```
  ┌─────────────────────┐          ┌──────────────────────┐
  │   USER'S BROWSER    │          │   CODING AGENT       │
  │   (real Chrome)     │          │   (Claude Code /     │
  │                     │          │    Conductor)         │
  │  Comparison board   │          │                      │
  │  with buttons:      │   ???    │  Needs to know:      │
  │  - Submit           │ ──────── │  - What was picked   │
  │  - Regenerate       │          │  - Star ratings      │
  │  - More like this   │          │  - Comments          │
  │  - Remix            │          │  - Regen requested?  │
  └─────────────────────┘          └──────────────────────┘
```

「？？」難しい部分です。ユーザーが Chrome でボタンをクリックします。実行中のエージェント
端末はそれについて知る必要があります。これらは 2 つの完全に別個のプロセスです。
共有メモリ、共有イベント バス、WebSocket 接続はありません。

## アーキテクチャ: リンケージの仕組み

```
  USER'S BROWSER                    $D serve (Bun HTTP)              AGENT
  ═══════════════                   ═══════════════════              ═════
       │                                   │                           │
       │  GET /                            │                           │
       │ ◄─────── serves board HTML ──────►│                           │
       │    (with __GSTACK_SERVER_URL      │                           │
       │     injected into <head>)         │                           │
       │                                   │                           │
       │  [user rates, picks, comments]    │                           │
       │                                   │                           │
       │  POST /api/feedback               │                           │
       │ ─────── {preferred:"A",...} ─────►│                           │
       │                                   │                           │
       │  ◄── {received:true} ────────────│                           │
       │                                   │── writes feedback.json ──►│
       │  [inputs disabled,                │   (or feedback-pending    │
       │   "Return to agent" shown]        │    .json for regen)       │
       │                                   │                           │
       │                                   │                  [agent polls
       │                                   │                   every 5s,
       │                                   │                   reads file]
```

### 3 つのファイル

|ファイル |いつ書かれた |手段 |エージェントのアクション |
|------|---------------|------|---------------|
| `feedback.json` |ユーザーが「送信」をクリックします |最終選択、完了 |読んで続行してください |
| `feedback-pending.json` |ユーザーが「再生成」/「もっと見る」をクリックします。新しいオプションが欲しい |読み取り、削除、新しいバリアントの生成、ボードのリロード |
| `feedback.json` (ラウンド 2+) |ユーザーは再生成後に「送信」をクリックします。反復後の最終選択 |読んで続行してください |

### ステートマシン

```
  $D serve starts
       │
       ▼
  ┌──────────┐
  │ SERVING  │◄──────────────────────────────────────┐
  │          │                                        │
  │ Board is │  POST /api/feedback                    │
  │ live,    │  {regenerated: true}                   │
  │ waiting  │──────────────────►┌──────────────┐     │
  │          │                   │ REGENERATING │     │
  │          │                   │              │     │
  └────┬─────┘                   │ Agent has    │     │
       │                         │ 10 min to    │     │
       │  POST /api/feedback     │ POST new     │     │
       │  {regenerated: false}   │ board HTML   │     │
       │                         └──────┬───────┘     │
       ▼                                │             │
  ┌──────────┐                POST /api/reload        │
  │  DONE    │                {html: "/new/board"}    │
  │          │                          │             │
  │ exit 0   │                          ▼             │
  └──────────┘                   ┌──────────────┐     │
                                 │  RELOADING   │─────┘
                                 │              │
                                 │ Board auto-  │
                                 │ refreshes    │
                                 │ (same tab)   │
                                 └──────────────┘
```

### ポートディスカバリ

エージェントは `$D serve` をバックグラウンドにして、ポートの stderr を読み取ります。

```
SERVE_STARTED: port=54321 html=/path/to/board.html
SERVE_BROWSER_OPENED: url=http://127.0.0.1:54321
```

エージェントは stderr から `port=XXXXX` を解析します。このポートは後で POST するために必要になります
`/api/reload` ユーザーが再生成を要求したとき。エージェントがポートを失った場合
いいえ、ボードをリロードできません。

### なぜローカルホストではなく 127.0.0.1 なのか

Bun.serve() がリッスンしている間、一部のシステムでは `localhost` が IPv6 `::1` に解決されることがあります
IPv4 のみ。さらに重要なのは、`localhost` がすべてのドメインのすべての開発 Cookie を送信することです。
開発者が取り組んできました。アクティブなセッションが多数あるマシンでは、これは
Bun のデフォルトのヘッダー サイズ制限を超えています (HTTP 431 エラー)。 `127.0.0.1` は回避します
どちらの問題も。

## あらゆるエッジケースと落とし穴

### 1. ゾンビフォームの問題

**内容:** ユーザーがフィードバックを送信すると、POST が成功し、サーバーが終了します。しかし、HTML
ページは Chrome でまだ開いています。インタラクティブに見えます。ユーザーは自分のファイルを編集する可能性があります。
フィードバックを入力し、もう一度「送信」をクリックします。サーバーがなくなっているので何も起こりません。

**修正:** POST が成功した後、ボード JS:
- すべての入力 (ボタン、ラジオ、テキストエリア、星評価) を無効にします。
- 再生バーを完全に非表示にします
- 送信ボタンを「フィードバックを受け取りました! コーディング エージェントに返信してください。」に置き換えます。
- 表示: 「さらに変更を加えますか? `/design-shotgun` をもう一度実行してください。」
- ページは送信された内容の読み取り専用の記録になります。

**実装場所:** `compare.ts:showPostSubmitState()` (484 行目)

### 2. デッドサーバーの問題

**内容:** ユーザーがまだアクセスしている間に、サーバーがタイムアウトするか (デフォルトは 10 分)、クラッシュします。
ボードが開きます。ユーザーが「送信」をクリックします。 fetch() はサイレントに失敗します。

**修正:** `postFeedback()` 関数には `.catch()` ハンドラーがあります。ネットワーク障害の場合:
- 赤いエラー バナーが表示されます:「接続が失われました」
- 収集されたフィードバック JSON をコピー可能な `<pre>` ブロックに表示します
- ユーザーはそれをコピーしてコーディング エージェントに直接貼り付けることができます

**実装場所:** `compare.ts:showPostFailure()` (行 546)

### 3. 古くなった再生スピナー

**内容:** ユーザーが「再生成」をクリックします。ボードにはスピナーと投票が表示されます `/api/progress`
2秒ごとに。エージェントがクラッシュするか、新しいバリアントの生成に時間がかかりすぎます。の
スピナーは永遠に回転します。

**修正:** 進行状況ポーリングには 5 分間のハード タイムアウトがあります (150 ポーリング x 2 秒間隔)。
5分後:
- スピナーは「何か問題が発生しました。」と置き換えられました。
- 表示: 「コーディング エージェントで `/design-shotgun` を再度実行します。」
- ポーリングが停止します。ページは情報提供になります。

**実装場所:** `compare.ts:startProgressPolling()` (行 511)

### 4. file:// URL の問題 (元のバグ)

**内容:** スキル テンプレートは元々 `$B goto file:///path/to/board.html` を使用していました。
ただし、`browse/src/url-validation.ts:71` はセキュリティのため `file://` URL をブロックします。の
フォールバック `open file://...` はユーザーの macOS ブラウザを開きますが、 `$B eval` はポーリングを行います
Playwright のヘッドレス ブラウザ (別のプロセス、ページは決して読み込まれません)。
エージェントは空の DOM を永久にポーリングします。

**修正:** `$D serve` は HTTP 経由で提供されます。ボードには `file://` を決して使用しないでください。の
`$D compare` の `--serve` フラグは、ボード生成と HTTP サービスを組み合わせます。
一つのコマンド。

**証拠:** `.context/attachments/image-v2.png` を参照 — 実際のユーザーはこれを正確にヒットしました
バグ。エージェントは正しく診断しました: (1) `$B goto` が `file://` URL を拒否します。
(2) ブラウズ デーモンを使用してもポーリング ループは発生しません。

### 5. ダブルクリックレース

**内容:** ユーザーが [送信] を素早く 2 回クリックします。 2 つの POST リクエストがサーバーに到着します。
最初の方法では、状態を「done」に設定し、100 ミリ秒以内に exit(0) をスケジュールします。 2本目到着
その 100ms ウィンドウの間に。

**現在の状態:** 完全に保護されていません。 `handleFeedback()` 関数はチェックしません
処理前に状態がすでに「完了」している場合。 2 回目の POST は成功し、
2 番目の `feedback.json` (無害、同じデータ) を書き込みます。その後も出口が起動します
100ミリ秒。

**リスク:** 低い。ボードは、最初に成功した POST 応答ですべての入力を無効にします。
したがって、2 回目のクリックは 1 ミリ秒以内に到達する必要があります。そして両方の書き込みには次のものが含まれます
同じフィードバックデータ。

**修正の可能性:** `handleFeedback()` の先頭に `if (state === 'done') return Response.json({error: 'already submitted'}, {status: 409})` を追加します。

### 6. ポート調整の問題

**内容:** エージェントは `$D serve` をバックグラウンド化し、stderr から `port=54321` を解析します。エージェント
後で再生成中に `/api/reload` を POST するためにこのポートが必要になります。エージェントの場合
コンテキストが失われます (会話が圧縮され、コンテキスト ウィンドウがいっぱいになります)。
港を思い出してください。

**現在の状態:** ポートは stderr に 1 回出力されます。エージェントはそれを覚えておく必要があります。
ディスクに書き込まれたポート ファイルがありません。

**修正の可能性:** ボード HTML の隣に `serve.pid` または `serve.port` ファイルを書き込みます
起動時。エージェントはいつでもそれを読むことができます:
```bash
cat "$_DESIGN_DIR/serve.port"  # → 54321
```

### 7. フィードバック ファイルのクリーンアップの問題

**内容:** 再生成ラウンドからの `feedback-pending.json` がディスク上に残ります。もし
エージェントが読み取り前にクラッシュすると、次の `$D serve` セッションで古いファイルが見つかります。

**現在の状態:** リゾルバー テンプレートのポーリング ループは削除するように指示しています。
`feedback-pending.json` を読んだ後。ただし、これはフォローするエージェント次第です
指示を完璧に。ファイルが古いと、新しいセッションが混乱する可能性があります。

**修正の可能性:** `$D serve` は、古いフィードバック ファイルをチェックして削除する可能性がありました。
スタートアップ。または: タイムスタンプ (`feedback-pending-1711555200.json`) を使用してファイルに名前を付けます。

### 8. 順次生成ルール

**内容:** 基盤となる OpenAI GPT Image API は、同時イメージ生成のレート制限を行います。
リクエスト。 3 つの `$D generate` 呼び出しが並行して実行されると、1 つは成功し、2 つは中止されます。

**修正:** スキル テンプレートでは、「一度に 1 つずつモックアップを生成します。
`$D generate` 呼び出しを並列化しないでください。」これはプロンプトレベルの指示ではなく、
コードレベルのロック。デザイン バイナリはシーケンシャル実行を強制しません。

**リスク:** エージェントは、独立した作業を並列化するようにトレーニングされています。明示的に言わずに
命令を実行すると、3 つの生成を同時に実行しようとします。これにより API 呼び出しが無駄になります
そしてお金。

### 9. AskUserQuestion の冗長性

**内容:** ユーザーがボード経由でフィードバックを送信した後 (優先バリアントを使用して、
評価、コメントはすべて JSON 内にある)、エージェントは再度質問します。「どのバリアントが
あなたのほうが好きですか？」これは迷惑です。理事会の重要な点は、これを回避することです。

**修正:** スキル テンプレートには、「ユーザーの質問に AskUserQuestion を使用しないでください」と記載する必要があります。
好み。 `feedback.json` を読んでください。そこには彼らの選択が含まれています。ユーザーにのみ質問する
正しく理解したことを確認するためであり、再質問するためではありません。」

### 10. CORS 問題

**内容:** ボードの HTML が外部リソース (CDN からのフォント、画像) を参照している場合、
ブラウザは `Origin: http://127.0.0.1:PORT` を使用してリクエストを送信します。ほとんどの CDN では許可されています
これですが、ブロックする人もいるかもしれません。

**現在の状態:** サーバーは CORS ヘッダーを設定しません。ボードのHTMLは
自己完結型 (画像は Base64 でエンコードされ、スタイルはインライン) なので、これは
実際の問題。

**リスク:** 現在の設計では低いです。ボードが外部にロードされているかどうかは重要です
リソース。

### 11. ペイロードが大きい問題

**内容:** `/api/feedback` への POST 本文にサイズ制限はありません。何らかの形でボードがあれば
複数 MB のペイロードを送信すると、`req.json()` がそれをすべてメモリに解析します。

**現在の状態:** 実際には、フィードバック JSON は約 500 バイトから約 2KB です。リスクは
理論的であり、実践的ではありません。ボード JS は、固定形状の JSON オブジェクトを構築します。

### 12. fs.writeFileSync エラー

**内容:** `feedback.json` `serve.ts:138` は、`fs.writeFileSync()` を使用せずに書き込みます
試す/捕まえる。ディスクがいっぱいであるか、ディレクトリが読み取り専用の場合、これはスローされ、
サーバーがクラッシュします。ユーザーにはスピナーが永遠に表示されます (サーバーは停止していますが、ボードは停止しています)
わかりません）。

**リスク:** 実際には低い (ボードの HTML は同じディレクトリに書き込まれただけですが、
書き込み可能であることを証明します)。ただし、応答が 500 の try/catch の方がきれいです。

## 完全なフロー (ステップバイステップ)

### ハッピー パス: 最初の試行でユーザーが選択

```
1. Agent runs: $D compare --images "A.png,B.png,C.png" --output board.html --serve &
2. $D serve starts Bun.serve() on random port (e.g. 54321)
3. $D serve opens http://127.0.0.1:54321 in user's browser
4. $D serve prints to stderr: SERVE_STARTED: port=54321 html=/path/board.html
5. $D serve writes board HTML with injected __GSTACK_SERVER_URL
6. User sees comparison board with 3 variants side by side
7. User picks Option B, rates A: 3/5, B: 5/5, C: 2/5
8. User writes "B has better spacing, go with that" in overall feedback
9. User clicks Submit
10. Board JS POSTs to http://127.0.0.1:54321/api/feedback
    Body: {"preferred":"B","ratings":{"A":3,"B":5,"C":2},"overall":"B has better spacing","regenerated":false}
11. Server writes feedback.json to disk (next to board.html)
12. Server prints feedback JSON to stdout
13. Server responds {received:true, action:"submitted"}
14. Board disables all inputs, shows "Return to your coding agent"
15. Server exits with code 0 after 100ms
16. Agent's polling loop finds feedback.json
17. Agent reads it, summarizes to user, proceeds
```

### 再生成パス: ユーザーはさまざまなオプションを望んでいます

```
1-6.  Same as above
7.  User clicks "Totally different" chiclet
8.  User clicks Regenerate
9.  Board JS POSTs to /api/feedback
    Body: {"regenerated":true,"regenerateAction":"different","preferred":"","ratings":{},...}
10. Server writes feedback-pending.json to disk
11. Server state → "regenerating"
12. Server responds {received:true, action:"regenerate"}
13. Board shows spinner: "Generating new designs..."
14. Board starts polling GET /api/progress every 2s

    Meanwhile, in the agent:
15. Agent's polling loop finds feedback-pending.json
16. Agent reads it, deletes it
17. Agent runs: $D variants --brief "totally different direction" --count 3
    (ONE AT A TIME, not parallel)
18. Agent runs: $D compare --images "new-A.png,new-B.png,new-C.png" --output board-v2.html
19. Agent POSTs: curl -X POST http://127.0.0.1:54321/api/reload -d '{"html":"/path/board-v2.html"}'
20. Server swaps htmlContent to new board
21. Server state → "serving" (from reloading)
22. Board's next /api/progress poll returns {"status":"serving"}
23. Board auto-refreshes: window.location.reload()
24. User sees new board with 3 fresh variants
25. User picks one, clicks Submit → happy path from step 10
```

### 「もっと似たもの」パス

```
Same as regeneration, except:
- regenerateAction is "more_like_B" (references the variant)
- Agent uses $D iterate --image B.png --brief "more like this, keep the spacing"
  instead of $D variants
```

### フォールバック パス: $D サーブが失敗する

```
1. Agent tries $D compare --serve, it fails (binary missing, port error, etc.)
2. Agent falls back to: open file:///path/board.html
3. Agent uses AskUserQuestion: "I've opened the design board. Which variant
   do you prefer? Any feedback?"
4. User responds in text
5. Agent proceeds with text feedback (no structured JSON)
```

## これを実装するファイル

|ファイル |役割 |
|------|------|
| `design/src/serve.ts` | HTTP サーバー、ステート マシン、ファイル書き込み、ブラウザ起動 |
| `design/src/compare.ts` |ボード HTML 生成、評価/選択/再生成用の JS、POST ロジック、送信後のライフサイクル |
| `design/src/cli.ts` | CLI エントリ ポイント、`serve` および `compare --serve` コマンドの配線 |
| `design/src/commands.ts` |コマンド レジストリ。 `serve` と `compare` を引数とともに定義します。
| `scripts/resolvers/design.ts` | `generateDesignShotgunLoop()` — ポーリング ループとリロード命令を出力するテンプレート リゾルバー |
| `design-shotgun/SKILL.md.tmpl` |完全なフローを調整するスキル テンプレート: コンテキスト収集、バリアント生成、`{{DESIGN_SHOTGUN_LOOP}}`、フィードバック確認 |
| `design/test/serve.test.ts` | HTTP エンドポイントと状態遷移の単体テスト |
| `design/test/feedback-roundtrip.test.ts` | E2E テスト: ブラウザーのクリック → JS フェッチ → HTTP POST → ディスク上のファイル |
| `browse/test/compare-board.test.ts` |比較ボード UI の DOM レベルのテスト |

## まだ問題が発生する可能性があるもの

### 既知のリスク (可能性の高い順)

1. **エージェントは順次生成ルールに従っていません** - ほとんどの LLM は並列化を望んでいます。バイナリで強制を行わない場合、これは無視できるプロンプトレベルの指示です。

2. **エージェントがポート番号を失う** — コンテキスト圧縮により stderr 出力がドロップされます。エージェントはボードをリロードできません。軽減策: ポートをファイルに書き込みます。

3. **古いフィードバック ファイル** — クラッシュしたセッションから残った `feedback-pending.json` は、次回の実行を混乱させます。軽減策: 起動時にクリーン。

4. **fs.writeFileSync クラッシュ** — フィードバック ファイルの書き込みで try/catch が発生しません。ディスクがいっぱいの場合はサイレントサーバーが停止します。ユーザーには無限スピナーが表示されます。

5. **進行状況ポーリング ドリフト** — 5 分間にわたる `setInterval(fn, 2000)`。実際には、JavaScript タイマーは十分に正確です。ただし、ブラウザ タブがバックグラウンドになっている場合、Chrome は間隔を 1 分に 1 回に調整することがあります。

### うまくいくこと

1. **デュアルチャネル フィードバック** — フォアグラウンド モードの場合は標準出力、バックグラウンド モードの場合はファイル。どちらも常にアクティブです。エージェントは機能するものを使用できます。

2. **自己完結型 HTML** — ボードには、すべての CSS、JS、および Base64 でエンコードされた画像がインラインで含まれています。外部依存関係はありません。オフラインでも動作します。

3. **同じタブの再生成** — ユーザーは 1 つのタブに留まります。ボードは、`/api/progress` ポーリング + `window.location.reload()` を介して自動更新されます。タブの爆発はありません。

4. **正常な機能低下** — POST エラーにより、コピー可能な JSON が表示されます。進行状況のタイムアウトにより、明確なエラー メッセージが表示されます。サイレントな失敗はありません。

5. **送信後のライフサイクル** — ボードは送信後に読み取り専用になります。ゾンビの形態はありません。 「次に何をすべきか」というメッセージをクリアします。

## テストカバレッジ

### テスト内容

|フロー |テスト |ファイル |
|------|------|------|
|送信 → ディスク上のフィードバック.json |ブラウザをクリック → ファイル | `feedback-roundtrip.test.ts` |
|送信後の UI ロックダウン |入力は無効になり、成功が表示されます | `feedback-roundtrip.test.ts` |
|再生成→フィードバック保留.json |チクレット + リジェネクリック → ファイル | `feedback-roundtrip.test.ts` |
| 「もっとこう」 → 具体的なアクション | JSON の more_like_B | `feedback-roundtrip.test.ts` |
|再生後のスピナー | DOM はテキストの読み込みを示しています | `feedback-roundtrip.test.ts` |
|完全に再生成→リロード→送信 | 2往復 | `feedback-roundtrip.test.ts` |
|サーバーはランダムなポートで起動します |ポート 0 バインディング | `serve.test.ts` |
|サーバー URL の HTML インジェクション | __GSTACK_SERVER_URL チェック | `serve.test.ts` |
|無効な JSON 拒否 | 400 応答 | `serve.test.ts` |
| HTML ファイルの検証 |見つからない場合は 1 を終了します | `serve.test.ts` |
|タイムアウトの動作 |タイムアウト後に終了 1 | `serve.test.ts` |
|ボード DOM 構造 |ラジオ、スター、チクレット | `compare-board.test.ts` |

### テストされていないもの

|ギャップ |リスク |優先順位 |
|-----|------|----------|
|ダブルクリックしてレースを送信 |低 - 最初の応答で入力が無効になります。 P3 |
|進行状況ポーリングのタイムアウト (150 回の反復) |中 — テストで 5 分は待つのに長い | P2 |
|再生成中にサーバーがクラッシュする |中 — ユーザーには無限のスピナーが表示されます。 P2 |
| POST 中のネットワーク タイムアウト |低い - ローカルホストは速い | P3 |
|バックグラウンドの Chrome タブのスロットリング間隔 |中 - 5 分のタイムアウトを 30 分以上に延長できる | P2 |
|大きなフィードバック ペイロード |低 — ボードは固定形状の JSON を構築します。 P3 |
|同時セッション (2 つのボード、1 つのサーバー) |低 — 各 $D サーブは独自のポートを取得します。 P3 |
|前のセッションからの古いフィードバック ファイル |中 - 新しいポーリング ループを混乱させる可能性があります。 P2 |

## 改善の可能性

### 短期 (当支店)

1. **ポートをファイルに書き込む** — `serve.ts` は起動時に `serve.port` をディスクに書き込みます。エージェントはいつでもそれを読みます。 5行。
2. **起動時に古いファイルを削除** — `serve.ts` は起動前に `feedback*.json` を削除します。 3行。
3. **ダブルクリックをガード** — `handleFeedback()` の上部にある `state === 'done'` をチェックします。 2行。
4. **try/catch ファイルの書き込み** — try/catch で `fs.writeFileSync` をラップし、失敗した場合は 500 を返します。 5行。

### 中期（フォローアップ）

5. **ポーリングの代わりに WebSocket** — `setInterval` + `GET /api/progress` を WebSocket 接続に置き換えます。新しい HTML が準備できると、ボードは即座に通知を受け取ります。ポーリング ドリフトとバックグラウンド タブのスロットルを排除します。 serve.ts に最大 50 行 + Compare.ts に最大 20 行。

6. **エージェントのポート ファイル** — `{"port": 54321, "pid": 12345, "html": "/path/board.html"}` から `$_DESIGN_DIR/serve.json` を書き込みます。エージェントは標準エラー出力を解析する代わりにこれを読み取ります。システムをコンテキスト損失に対してより堅牢にします。

7. **フィードバック スキーマの検証** — 書き込む前に、JSON スキーマに対して POST 本文を検証します。下流のエージェントを混乱させるのではなく、不正なフィードバックを早期にキャッチします。

### 長期 (設計方向性)

8. **永続デザイン サーバー** — セッションごとに `$D serve` を起動する代わりに、存続期間の長いデザイン デーモン (ブラウズ デーモンなど) を実行します。複数のボードが 1 つのサーバーを共有します。コールドスタートを解消します。ただし、デーモンのライフサイクル管理が複雑になります。

9. **リアルタイム コラボレーション** — 2 人のエージェント (または 1 人のエージェント + 1 人の人間) が同じボード上で同時に作業します。サーバーは WebSocket 経由で状態の変更をブロードキャストします。フィードバック時に競合を解決する必要があります。