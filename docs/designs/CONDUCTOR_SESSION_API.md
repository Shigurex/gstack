# Conductor セッションストリーミング API の提案

＃＃ 問題

クロードが CDP (gstack `$B connect`) 経由で実際のブラウザを制御すると、2 つのブラウザが表示されます。
ウィンドウ: **Conductor** (クロードの思考を確認するため) および **Chrome** (クロードの行動を確認するため)。

gstack の Chrome 拡張機能のサイド パネルには、すべてのコマンド、結果、ブラウズ アクティビティが表示されます。
そしてエラー。ただし、*完全な* セッション ミラーリング (クロードの思考、ツール呼び出し、コード編集) の場合、
サイドパネルには会話ストリームを公開するための Conductor が必要です。

## これにより何が可能になるか

gstack Chrome 拡張機能のサイド パネルの「セッション」タブには次のものが表示されます。
- クロードの思考/内容 (パフォーマンスのために省略されています)
- ツール呼び出し名 + アイコン (Edit、Bash、Read など)
- コスト見積もりを使用して方向転換境界を設定する
- 会話の進行に応じてリアルタイムで更新

ユーザーはすべてを 1 か所で確認できます (ブラウザーでのクロードのアクション + クロードのアクション)。
ウィンドウを切り替えることなく、サイド パネルで考えます。

## 提案された API

### `GET http://127.0.0.1:{PORT}/workspace/{ID}/session/stream`

クロード コードの会話を NDJSON イベントとして再発行する Server-Sent Events エンドポイント。

**イベント タイプ** (Claude Code の `--output-format stream-json` 形式を再利用):

```
event: assistant
data: {"type":"assistant","content":"Let me check that page...","truncated":true}

event: tool_use
data: {"type":"tool_use","name":"Bash","input":"$B snapshot","truncated_input":true}

event: tool_result
data: {"type":"tool_result","name":"Bash","output":"[snapshot output...]","truncated_output":true}

event: turn_complete
data: {"type":"turn_complete","input_tokens":1234,"output_tokens":567,"cost_usd":0.02}
```

**コンテンツの切り詰め:** ツールの入力/出力はストリーム内で 500 文字に制限されます。フル
データは Conductor の UI に残ります。サイド パネルは概要ビューであり、置き換えられるものではありません。

### `GET http://127.0.0.1:{PORT}/api/workspaces`

アクティブなワークスペースをリストする検出エンドポイント。

```json
{
  "workspaces": [
    {
      "id": "abc123",
      "name": "gstack",
      "branch": "garrytan/chrome-extension-ctrl",
      "directory": "/Users/garry/gstack",
      "pid": 12345,
      "active": true
    }
  ]
}
```

Chrome 拡張機能は、ブラウズ サーバーの git リポジトリと一致することでワークスペースを自動選択します
(`/health` 応答から) ワークスペースのディレクトリまたは名前に変換します。

＃＃ 安全

- **Localhost のみ。** Claude Code 自身のデバッグ出力と同じ信頼モデル。
- **認証は必要ありません。** Conductor が認証を必要とする場合は、ベアラー トークンを
  拡張機能が SSE リクエストで渡すワークスペースのリスト。
- **コンテンツの切り詰め**は、長いコード出力、ファイルの内容、および
  機密ツールの結果が Conductor の完全な UI から離れることはありません。

## gstack が構築するもの (拡張側)

サイドパネルの「セッション」タブですでにスキャフォールディングされています（現在はプレースホルダーが表示されています）。

Conductor の API が利用可能な場合:
1. サイドパネルはポートプローブまたは手動入力を介して導体を検出します
2. `/api/workspaces` を取得し、ブラウズサーバーのリポジトリと一致します
3. `EventSource` から `/workspace/{id}/session/stream` を開きます
4. レンダリング: アシスタント メッセージ、ツール名 + アイコン、ターン境界、コスト
5. 正常にフォールバックします: 「フルセッションビューのために Conductor を接続」

推定労力: `sidepanel.js` で ~200 LOC。

## Conductor が構築するもの (サーバー側)

1. ワークスペースごとにクロード コードの stream-json を再発行する SSE エンドポイント
2. アクティブなワークスペース リストを含む`/api/workspaces` 検出エンドポイント
3. コンテンツの切り捨て (ツールの入力/出力の 500 文字の上限)

推定労力: Conductor がすでにクロード コード ストリームをキャプチャしている場合は ~100 ～ 200 LOC
内部的に (これは独自の UI レンダリングのために行われます)。

## 設計上の決定

|決定 |選択 |理論的根拠 |
|----------|--------|-----------|
|輸送 | SSE (WebSocket ではない) | Unidirectional, auto-reconnect, simpler |
|フォーマット |クロードのストリーム-json | Conductor already parses this;新しいスキーマはありません |
|発見 | HTTP endpoint (not file) | Chrome extensions can't read filesystem |
|認証 |なし (ローカルホスト) | Same as browse server, CDP port, Claude Code |
|切り捨て | 500文字 | Side Panel is ~300px wide;長いコンテンツは役に立たない |