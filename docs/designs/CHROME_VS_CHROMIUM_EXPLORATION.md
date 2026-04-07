# Chrome と Chromium: Playwright のバンドルされた Chromium を使用する理由

## 当初のビジョン

`$B connect` を構築したときの計画は、ユーザーの **実際の Chrome ブラウザ**、つまり Cookie、セッション、拡張機能、開いているタブを備えたブラウザに接続することでした。 Cookie のインポートはもう必要ありません。設計では次のことが求められました。

1. `chromium.connectOverCDP(wsUrl)` CDP 経由で実行中の Chrome に接続する
2. Chrome を正常に終了し、`--remote-debugging-port=9222` で再起動します
3. ユーザーの実際の閲覧コンテキストにアクセスする

これが、`chrome-launcher.ts` が存在する理由 (ブラウザーのバイナリ検出、CDP ポートのプローブ、およびランタイム検出の 361 LOC) であり、このメソッドが `connectCDP()` と呼ばれた理由です。

## 実際に何が起こったのか

本物の Chrome は、Playwright の `channel: 'chrome'` 経由で起動されると、`--load-extension` を静かにブロックします。拡張機能が読み込まれません。サイド パネル (アクティビティ フィード、参照、チャット) の拡張機能が必要でした。

実装は、Playwright にバンドルされている Chromium を使用して `chromium.launchPersistentContext()` に戻りました。これにより、`--load-extension` および `--disable-extensions-except` を介して拡張機能が確実に読み込まれます。ただし、名前は `connectCDP()`、`connectionMode: 'cdp'`、`BROWSE_CDP_URL`、`chrome-launcher.ts` のままです。

当初のビジョン (ユーザーの実際のブラウザ状態にアクセスする) は実装されませんでした。私たちは毎回新しいブラウザを起動しました。機能的には Playwright の Chromium と同じですが、361 行のデッド コードと誤解を招く名前が含まれていました。



`/office-hours` 設計セッション中に、アーキテクチャを追跡し、次のことを発見しました。

1. `connectCDP()` は CDP を使用せず、`launchPersistentContext()` を呼び出します
2. `connectionMode: 'cdp'` は誤解を招きます – それは単なる「頭付きモード」です
3. `chrome-launcher.ts` はデッドコードです — その唯一のインポートは、到達不能な `attemptReconnect()` メソッド内にありました
4. `preExistingTabIds` は、決して接続しない実際の Chrome タブを保護するために設計されました
5. `$B handoff` (ヘッドレス → ヘッドあり) は、拡張機能を読み込むことができない別の API (`launch()` + `newContext()`) を使用し、2 つの異なる「ヘッド付き」エクスペリエンスを作成しました

## 修正

### 名前が変更されました
- `connectCDP()` → `launchHeaded()`
- `connectionMode: 'cdp'` → `connectionMode: 'headed'`
- `BROWSE_CDP_URL` → `BROWSE_HEADED`

### 削除されました
- `chrome-launcher.ts` (361 LOC)
- `attemptReconnect()` (デッドメソッド)
- `preExistingTabIds` (死んだ概念)
- `reconnecting` フィールド (デッドステート)
- `cdp-connect.test.ts` (削除されたコードのテスト)

### 統合
- `$B handoff` は `launchPersistentContext()` + 拡張ロードを使用するようになりました (`$B connect` と同じ)
- 2 頭モードではなく 1 頭モード
- Handoff では拡張機能とサイドパネルを無料で提供します

### ゲート付き
- `--chat` フラグの背後にあるサイドバー チャット
- `$B connect` (デフォルト): アクティビティ フィード + 参照のみ
- `$B connect --chat`: + 試験的なスタンドアロン チャット エージェント

## アーキテクチャ (後)

```
Browser States:
  HEADLESS (default) ←→ HEADED ($B connect or $B handoff)
     Playwright            Playwright (same engine)
     launch()              launchPersistentContext()
     invisible             visible + extension + side panel

Sidebar (orthogonal add-on, headed only):
  Activity tab    — always on, shows live browse commands
  Refs tab        — always on, shows @ref overlays
  Chat tab        — opt-in via --chat, experimental standalone agent

Data Bridge (sidebar → workspace):
  Sidebar writes to .context/sidebar-inbox/*.json
  Workspace reads via $B inbox
```

## なぜ本物の Chrome ではないのでしょうか?

実際の Chrome は、Playwright によって起動されると `--load-extension` をブロックします。これは Chrome のセキュリティ機能です。悪意のある拡張機能の挿入を防ぐために、コマンドライン引数を介して読み込まれる拡張機能は Chromium ベースのブラウザーで制限されます。

Playwright にバンドルされている Chromium はテストと自動化のために設計されているため、この制限はありません。 `ignoreDefaultArgs` オプションを使用すると、Playwright 独自の拡張機能ブロック フラグをバイパスできます。

ユーザーの実際の Cookie/セッションにアクセスしたい場合、パスは次のとおりです。
1. Cookie インポート (`$B cookie-import` 経由ですでに機能しています)
2. Conductor セッション インジェクション (将来 - サイドバーがワークスペース エージェントにメッセージを送信)

