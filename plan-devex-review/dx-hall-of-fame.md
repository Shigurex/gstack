# DX殿堂リファレンス

現在のレビュー パスのセクションのみをお読みください。ファイル全体をロードしないでください。

## パス 1: はじめに

**ゴールドスタンダード:**
- **ストライプ**: カードにチャージするための 7 行のコード。ドキュメントには、ログイン時にテスト API キーが事前に入力されます。Stripe Shell はドキュメント ページ内で CLI を実行します。ローカルにインストールする必要はありません。
- **Vercel**: `git push` = HTTPS を使用したグローバル CDN 上のライブ サイト。すべての PR はプレビュー URL を取得します。 1 つの CLI コマンド: `vercel`。
- **事務員**: `<SignIn />`、`<SignUp />`、`<UserButton />`。 3 つの JSX コンポーネント。電子メール、ソーシャル、MFA で認証をすぐに使用できます。
- **Supabase**: Postgres テーブルを作成し、REST API + リアルタイム + 自己文書化ドキュメントを即座に自動生成します。
- **Firebase**: `onSnapshot()`。オフライン永続性が組み込まれているすべてのクライアント間のリアルタイム同期のための 3 行。
- **Twilio**: コンソール内の仮想電話。番号やクレジット カードを購入せずに SMS を送受信できます。結果: 活性化が 62% 向上しました。

**アンチパターン:**
- 値の前に電子メールで検証します (フローを中断します)
- サンドボックスの前にクレジット カードが必要です
- 複数のパスを備えた「自分の冒険を選択」 (決断疲れ、1 つの黄金のパスが勝利)
- API キーは設定に隠されています (Stripe はコード例に API キーを事前に入力します)
- 言語切り替えを行わない静的コード例
- ドキュメント サイトをダッシュボードから分離する (コンテキストの切り替え)

## パス 2: API/CLI/SDK 設計

**ゴールドスタンダード:**
- **ストライプ接頭辞付き ID**: 請求の場合は `ch_`、顧客の場合は `cus_`。自己文書化。間違った ID タイプを渡すことはできません。
- **ストライプ展開可能オブジェクト**: デフォルトでは ID 文字列が返されます。 `expand[]` は完全なオブジェクトをインラインで取得します。最大 4 レベルまでのネストされた拡張。
- **ストライプ冪等キー**: 突然変異時に `Idempotency-Key` ヘッダーを渡します。安全な再試行。いいえ、「二重請求しましたか？」不安。
- **ストライプ API のバージョン管理**: 最初に呼び出すと、アカウントがその日のバージョンに固定されます。 `Stripe-Version` ヘッダーを介してリクエストごとに新しいバージョンをテストします。
- **GitHub CLI**: ターミナルとパイプを自動検出します。ターミナルでは人間が判読可能で、パイプ接続時にはタブ区切りになります。 `gh pr <tab>` はすべての PR アクションを示します。
- **SwiftUI の段階的な開示**: `Button("Save") { save() }` から完全なカスタマイズ、すべてのレベルで同じ API。
- **htmx**: HTML 属性が JS を置き換えます。合計14KB。 `hx-get="/search" hx-trigger="keyup changed delay:300ms"`。ビルドステップはゼロ。
- **shadcn/ui**: ソース コードをプロジェクトにコピーします。すべてのラインを所有しているのはあなたです。依存関係やバージョンの競合はありません。

**Anti-patterns:**
- Chatty API: requiring 5 calls for one user-visible action
- Inconsistent naming: `/users` (plural) vs `/user/123` (singular) vs `/create-order` (verb in URL)
- Implicit failure: 200 OK with error nested in response body
- God endpoint: 47 parameter combinations with different behavior per subset
- Documentation-required API: 3 pages of docs before first call = too much ceremony



**Three tiers of error quality:**

**Tier 1、Elm (会話型コンパイラー):**
```
-- TYPE MISMATCH ---- src/Main.elm
I cannot do addition with String values like this one:
42|   "hello" + 1
     ^^^^^^^
Hint: To put strings together, use the (++) operator instead.
```
一人称、完全な文、正確な場所、修正案、詳細情報。

**Tier 2、Rust (注釈付きソース):**
```
error[E0308]: mismatched types
 --> src/main.rs:4:20
help: consider borrowing here
  |
4 |     let name: &str = &get_name();
  |                       +
```
エラーコードはチュートリアルへのリンクです。プライマリ + セカンダリ ラベル。ヘルプセクションに正確な編集内容が表示されます。

**階層 3、Stripe API (doc_url で構造化):**
```json
{"error":{"type":"invalid_request_error","code":"resource_missing","message":"No such customer: 'cus_nonexistent'","param":"customer","doc_url":"https://stripe.com/docs/error-codes/resource-missing"}}
```
5 つのフィールド、曖昧さゼロ。

**The formula:** What happened + Why + How to fix + Where to learn more + Actual values that caused it.

**Anti-pattern:** TypeScript buries "Did you mean?" at the BOTTOM of long error chains. Most actionable info should appear FIRST.

## Pass 4: Documentation & Learning

**Gold standards:**
- **Stripe docs**: Three-column layout (nav / content / live code). API keys injected when logged in. Language switcher persists across ALL pages. Hover-to-highlight. Stripe Shell for in-browser API calls. Built and open-sourced Markdoc. Features don't ship until docs are finalized. Docs contributions affect performance reviews.
- 52% of developers blocked by lack of documentation (Postman 2023)
- Companies with world-class docs see 2.5x increase in adoption
- "Docs as product": ships with the feature or the feature doesn't ship

## Pass 5: Upgrade & Migration Path

**ゴールドスタンダード:**
- **Next.js**: `npx @next/codemod upgrade major`。 1 つのコマンドで Next.js、React、React DOM をアップグレードし、関連するすべての codemod を実行します。
- **AG Grid**: v31 以降のすべてのリリースには codemod が含まれています。
- **ストライプ API のバージョン管理**: 内部的には 1 つのコードベース。アカウントごとのバージョンの固定。重大な変更に驚かれることはありません。
- **Martin Fowler のパイプライン パターン**: 1 つのモノリシック codemod ではなく、小さくてテスト可能な変換を作成します。
- Maven Central の破壊的変更の 21.9% は文書化されていませんでした (Ochoa et al., 2021)

## Pass 6: Developer Environment & Tooling

**ゴールドスタンダード:**
- **Bun**: npm install より 100 倍、Node.js ランタイムより 4 倍高速です。スピードはDX。
- 87 interruptions per day average; 25 minutes to recover from each. Devs code only 2-4 hours/day.
- DXI の 1 ポイントの改善ごとに、開発者あたり 1 週間あたり 13 分が節約されます。
- **GitHub Copilot**: タスクの完了が 55.8% 高速化されました。 PR time from 9.6 days to 2.4 days.

## Pass 7: Community & Ecosystem

- Dev tools require ~14 exposures before purchase (Matt Biilmann, Netlify). Incompatible with quarterly OKR cycles.
- 4-5x performance multiplier for teams with strong developer experience (DevEx framework).

## Pass 8: DX Measurement

**3 つの学術フレームワーク:**
1. **スペース** (Microsoft Research、2021): 満足度、パフォーマンス、アクティビティ、コミュニケーション、効率。少なくとも 3 つの寸法を測定します。
2. **DevEx** (ACM キュー、2023): フィードバック ループ、認知負荷、フロー状態。知覚データとワークフロー データを組み合わせます。
3. **ファーガーホルムとムンク** (IEEE、2012): 認知、感情、認知。心理学の「心の三部作」。



クロード コード スキル、MCP サーバー、または AI エージェント ツールの計画を検討するときに使用します。

- [ ] **AskUserQuestion デザイン**: 通話ごとに 1 つの問題。コンテキスト (プロジェクト、ブランチ、タスク) を再接地します。視覚的なフィードバックのためのブラウザーハンドオフ。
- [ ] **状態ストレージ**: グローバル (~/.tool/)、プロジェクトごと ($SLUG/)、セッションごと。監査証跡用の追加専用 JSONL。
- [ ] **プログレッシブ同意**: マーカー ファイルを使用した 1 回限りのプロンプト。決して再質問しないでください。可逆。
- [ ] **自動アップグレード**: キャッシュ + スヌーズ バックオフによるバージョン チェック。移行スクリプト。インラインオファー。
- [ ] **スキル構成**: チェーンによる恩恵。連鎖を確認します。セクションをスキップしたインライン呼び出し。
- [ ] **エラー回復**: 失敗から再開します。部分的な結果が保存されます。チェックポイントセーフ。
- [ ] **セッションの継続性**: タイムライン イベント。圧縮回復。セッションをまたいだ学習。
- [ ] **制限された自律性**: 操作上の制限をクリアします。破壊的な行為には必須のエスカレーション。監査証跡。

参照実装: gstack の設計ショットガン ループ、自動アップグレード フロー、プログレッシブ コンセント、階層ストレージ。