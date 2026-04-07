# 着陸前レビューチェックリスト

＃＃ 説明書

以下にリストされている問題については、`git diff origin/main` 出力を確認してください。具体的にしてください — `file:line` を引用し、修正を提案してください。 Skip anything that's fine.実際の問題にのみフラグを立ててください。

**2 パス レビュー:**
- **パス 1 (クリティカル):** SQL とデータ セーフティ、競合状態、LLM 出力信頼境界、シェル インジェクション、列挙完全性を最初に実行します。 Highest severity.
- **パス 2 (情報):** 以下の残りのカテゴリを実行します。 Lower severity but still actioned.
- **専門カテゴリ (このチェックリストではなく、並行サブエージェントによって処理されます):** テスト ギャップ、デッド コード、マジック ナンバー、条件付き副作用、パフォーマンスとバンドルの影響、暗号とエントロピー。 See `review/specialists/` for these.

すべての発見事項は、Fix-First Review を通じてアクションを取得します。明らかな機械的な修正は自動的に適用されます。
本当にあいまいな問題は 1 つのユーザーの質問にまとめられます。

**出力形式:**

```
Pre-Landing Review: N issues (X critical, Y informational)

**AUTO-FIXED:**
- [file:line] Problem → fix applied

**NEEDS INPUT:**
- [file:line] Problem description
  Recommended fix: suggested fix
```



簡潔に。問題ごとに、1 行で問題を説明し、1 行で修正を説明します。前置きも要約も、「全体的には良く見える」もありません。

---

## レビュー カテゴリ

### パス 1 — クリティカル

#### SQL とデータの安全性
- SQL での文字列補間 (値が `.to_i`/`.to_f` であっても — パラメーター化されたクエリを使用します (Rails: sanitize_sql_array/Arel、Node: 準備されたステートメント、Python: パラメーター化されたクエリ))
- TOCTOU レース: アトミックである必要があるパターンをチェックしてから設定します `WHERE` + `update_all`
- DB への直接書き込みのモデル検証をバイパスします (Rails: update_column; Django: QuerySet.update(); Prisma: raw クエリ)
- N+1 クエリ: ループ/ビューで使用される関連付けの積極的な読み込み (Rails: .includes(); SQLAlchemy:joinload(); Prisma: include) が欠落しています

#### 競合状態と同時実行性
- 一意性制約なしの読み取り-チェック-書き込み、または重複キーエラーをキャッチして再試行 (例: 同時挿入を処理せずに `where(hash:).first` の次に `save!` )
- 一意の DB インデックスを使用しない検索または作成 - 同時呼び出しにより重複が作成される可能性があります
- アトミック `WHERE old_status = ? UPDATE SET new_status` を使用しないステータス遷移 — 同時更新により遷移をスキップまたは二重適用できる
- ユーザー制御データ (XSS) 上の安全でない HTML レンダリング (Rails: .html_safe/raw(); React: darklySetInnerHTML; Vue: v-html; Django: |safe/mark_safe)

#### LLM 出力の信頼境界
- LLM によって生成された値 (電子メール、URL、名前) が DB に書き込まれるか、形式検証なしでメーラーに渡されます。永続化する前に、軽量ガード (`EMAIL_REGEXP`、`URI.parse`、`.strip`) を追加します。
- 構造化ツール出力 (配列、ハッシュ) は、データベース書き込み前の型/形状チェックなしで受け入れられます。
- ホワイトリストなしで取得された LLM 生成の URL — URL が内部ネットワークを指している場合、SSRF リスクが発生します (Python: `urllib.parse.urlparse` → `requests.get`/`httpx.get` の前にホスト名をブロックリストと照合してください)
- LLM 出力はサニタイズなしでナレッジ ベースまたはベクター DB に保存されます - 保存されたプロンプト インジェクションのリスク

#### シェル インジェクション (Python 固有)
- コマンド文字列内の `subprocess.run()` / `subprocess.call()` / `subprocess.Popen()` と `shell=True` および f-string/`.format()` 補間 — 代わりに引数配列を使用します
- 変数補間を使用した `os.system()` — 引数配列を使用して `subprocess.run()` に置き換えます
- サンドボックスなしの LLM 生成コードの `eval()` / `exec()`

#### 列挙型と値の完全性
diff に新しい列挙値、ステータス文字列、層名、または型定数が導入される場合:
- **すべてのコンシューマを通じてトレースします。** スイッチをオンにする、フィルタリングする、または値を表示する各ファイルを読み取ります (単に grep するだけではなく、読み取ります)。新しい値を処理しないコンシューマがある場合は、フラグを立てます。よくあるミス: フロントエンドのドロップダウンに値を追加しても、バックエンドのモデル/計算メソッドがその値を保持しない。
- **許可リスト/フィルター配列を確認します。** 兄弟値を含む配列または `%w[]` リストを検索します (たとえば、階層に「revise」を追加する場合、すべての `%w[quick lfg mega]` を見つけて、必要に応じて「revise」が含まれていることを確認します)。
- **`case`/`if-elsif` チェーンを確認してください。** 既存のコードが列挙型で分岐する場合、新しい値は間違ったデフォルトに落ちますか?
これを行うには、Grep を使用して、兄弟値へのすべての参照を検索します (たとえば、すべての階層コンシューマーを検索するには、「lfg」または「mega」を grep します)。各試合を読んでください。この手順では、diff の外側にあるコードを読み取る必要があります。



#### 非同期/同期ミキシング (Python 固有)
- `async def` エンドポイント内の同期 `subprocess.run()`、`open()`、`requests.get()` — イベント ループをブロックします。代わりに、`asyncio.to_thread()`、`aiofiles`、または `httpx.AsyncClient` を使用してください。
- 非同期関数内で `time.sleep()` — `asyncio.sleep()` を使用します
- `run_in_executor()` ラップなしの非同期コンテキストでの同期 DB 呼び出し

#### 列/フィールド名の安全性
- ORM クエリの列名 (`.select()`、`.eq()`、`.gte()`、`.order()`) を実際の DB スキーマと照合して検証します。間違った列名は、黙って空の結果を返すか、飲み込まれたエラーをスローします。
- クエリ結果に対する `.get()` 呼び出しが実際に選択された列名を使用していることを確認します
- 利用可能な場合はスキーマ ドキュメントとの相互参照

#### デッドコードと一貫性 (バージョン/変更ログのみ - その他の項目は保守性スペシャリストが処理します)
- PR タイトルと VERSION/CHANGELOG ファイル間のバージョンの不一致
- 変更を不正確に説明する CHANGELOG エントリ (例: X が存在しなかったのに「X から Y に変更された」)

#### LLM プロンプトの問題
- プロンプト内の 0 から始まるインデックスのリスト (LLM は確実に 1 から始まるインデックスを返します)
- `tool_classes`/`tools` 配列に実際に接続されているものと一致しない利用可能なツール/機能をリストするプロンプト テキスト
- 単語/トークンの制限が複数の場所で記載されているため、変動する可能性があります

#### 完全性のギャップ
- 完全バージョンの CC 時間が 30 分未満となるショートカット実装 (例: 部分的な列挙処理、不完全なエラー パス、簡単に追加できる欠落しているエッジ ケース)
- 人間チームの作業量の見積もりのみで提示されるオプション — 人間時間と CC+Gstack 時間の両方を表示する必要があります
- 不足しているテストを追加すると「海」ではなく「湖」となるテスト カバレッジ ギャップ (例: ネガティブ パス テストの不足、ハッピー パス構造を反映するエッジ ケース テストの不足)
- 控えめな追加コードで 100% が達成可能な場合でも、80 ～ 90% で機能が実装されます

#### タイムウィンドウの安全性
- 「今日」が 24 時間をカバーすると仮定した日付キーの検索 - 太平洋時間午前 8 時のレポートでは、今日のキーでは午前 0 時→午前 8 時のみが表示されます
- 関連する機能間の時間枠の不一致 — 1 つは時間ごとのバケットを使用し、もう 1 つは同じデータに対して日次のキーを使用します

#### Type Coercion at Boundaries
- 型が変更される可能性がある Ruby→JSON→JS の境界を越える値 (数値と文字列) — ハッシュ/ダイジェスト入力は型を正規化する必要があります
- シリアル化前に `.to_s` または同等のものを呼び出さないハッシュ/ダイジェスト入力 — `{ cores: 8 }` と `{ cores: "8" }` では異なるハッシュが生成されます

#### ビュー/フロントエンド
- パーシャル内のインライン `<style>` ブロック (レンダリングごとに再解析)
- ビュー内の O(n*m) ルックアップ (`index_by` ハッシュではなくループ内の `Array#find`)
- Ruby 側の `.select{}` `WHERE` 句となる DB 結果のフィルタリング (先頭のワイルドカード `LIKE` を意図的に回避しない限り)

#### ディストリビューションおよび CI/CD パイプライン
- CI/CD ワークフローの変更 (`.github/workflows/`): ビルド ツールのバージョンがプロジェクト要件と一致していること、アーティファクト名/パスが正しいこと、シークレットがハードコードされた値ではなく `${{ secrets.X }}` を使用していることを確認します。
- 新しいアーティファクト タイプ (CLI バイナリ、ライブラリ、パッケージ): パブリッシュ/リリース ワークフローが存在し、正しいプラットフォームをターゲットにしていることを確認します。
- クロスプラットフォーム ビルド: CI マトリックスがすべてのターゲット OS/アーキテクチャの組み合わせ、またはテストされていないドキュメントをカバーしていることを確認します。
- バージョンタグ形式の一貫性: `v1.2.3` 対 `1.2.3` — VERSION ファイル、git タグ、および公開スクリプト間で一致する必要があります
- パブリッシュステップの冪等性: パブリッシュワークフローの再実行は失敗しません (例: `gh release create` の前に `gh release delete`)

**フラグを立てないでください:**
- 既存の自動デプロイ パイプラインを使用した Web サービス (Docker ビルド + K8s デプロイ)
- 社内ツールはチーム外に配布されない
- テストのみの CI の変更 (公開ステップではなくテストステップを追加)

---

## 重大度分類

```
CRITICAL (highest severity):      INFORMATIONAL (main agent):      SPECIALIST (parallel subagents):
├─ SQL & Data Safety              ├─ Async/Sync Mixing             ├─ Testing specialist
├─ Race Conditions & Concurrency  ├─ Column/Field Name Safety      ├─ Maintainability specialist
├─ LLM Output Trust Boundary      ├─ Dead Code (version only)      ├─ Security specialist
├─ Shell Injection                ├─ LLM Prompt Issues             ├─ Performance specialist
└─ Enum & Value Completeness      ├─ Completeness Gaps             ├─ Data Migration specialist
                                   ├─ Time Window Safety            ├─ API Contract specialist
                                   ├─ Type Coercion at Boundaries   └─ Red Team (conditional)
                                   ├─ View/Frontend
                                   └─ Distribution & CI/CD Pipeline

All findings are actioned via Fix-First Review. Severity determines
presentation order and classification of AUTO-FIX vs ASK — critical
findings lean toward ASK (they're riskier), informational findings
lean toward AUTO-FIX (they're more mechanical).
```

---

## 修正優先ヒューリスティック

このヒューリスティックは、`/review` と `/ship` の両方によって参照されます。かどうかを決定します。
エージェントは検出結果を自動修正するか、ユーザーに質問します。

```
AUTO-FIX (agent fixes without asking):     ASK (needs human judgment):
├─ Dead code / unused variables            ├─ Security (auth, XSS, injection)
├─ N+1 queries (missing eager loading)      ├─ Race conditions
├─ Stale comments contradicting code       ├─ Design decisions
├─ Magic numbers → named constants         ├─ Large fixes (>20 lines)
├─ Missing LLM output validation           ├─ Enum completeness
├─ Version/path mismatches                 ├─ Removing functionality
├─ Variables assigned but never read       └─ Anything changing user-visible
└─ Inline styles, O(n*m) view lookups        behavior
```

**経験則:** 修正が機械的なものであり、上級エンジニアが適用する場合
議論するまでもなく、それは AUTO-FIX です。理性的なエンジニアが同意できない可能性がある場合は、
解決策は ASK です。

**重要な結果はデフォルトで ASK に向けられます** (本質的にリスクが高くなります)。
**情報的な結果はデフォルトで AUTO-FIX** になります (より機械的です)。

---

## 抑制 — これらにフラグを立てないでください

- 冗長性が無害で読みやすさに役立つ場合、「X は Y と冗長です」 (例: `present?` `length > 20` と冗長)
- 「このしきい値/定数が選択された理由を説明するコメントを追加します」 - しきい値はチューニング中に変更され、コメントは腐ります
- アサーションがすでに動作をカバーしている場合、「このアサーションはさらに厳密になる可能性があります」
- 一貫性のみを考慮した変更の提案 (別の定数の保護方法に一致するように条件で値をラップする)
- 入力が制約されており、実際には X が発生しない場合、「正規表現はエッジ ケース X を処理しません」
- 「テストでは複数のガードを同時に実行します」 - それは問題ありません。テストではすべてのガードを隔離する必要はありません
- 評価しきい値の変更 (max_actionable、min スコア) - これらは経験的に調整され、常に変化します
- 無害な no-ops (例: 配列内に存在しない要素に対する `.reject`)
- レビューしている差分ですでに対処されているもの - コメントする前に完全な差分を読んでください