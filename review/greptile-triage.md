# グレプタイルのコメントトリアージ

GitHub PR 上の Greptile レビュー コメントを取得、フィルタリング、分類するための共有リファレンス。 `/review` (ステップ 2.5) と `/ship` (ステップ 3.75) の両方がこのドキュメントを参照しています。

---

## フェッチ

これらのコマンドを実行して PR を検出し、コメントを取得します。両方の API 呼び出しは並行して実行されます。

```bash
REPO=$(gh repo view --json nameWithOwner --jq '.nameWithOwner' 2>/dev/null)
PR_NUMBER=$(gh pr view --json number --jq '.number' 2>/dev/null)
```

**失敗するか空の場合:** Greptile トリアージをサイレントにスキップします。この統合は追加的なものであり、ワークフローはそれなしでも機能します。

```bash
# Fetch line-level review comments AND top-level PR comments in parallel
gh api repos/$REPO/pulls/$PR_NUMBER/comments \
  --jq '.[] | select(.user.login == "greptile-apps[bot]") | select(.position != null) | {id: .id, path: .path, line: .line, body: .body, html_url: .html_url, source: "line-level"}' > /tmp/greptile_line.json &
gh api repos/$REPO/issues/$PR_NUMBER/comments \
  --jq '.[] | select(.user.login == "greptile-apps[bot]") | {id: .id, body: .body, html_url: .html_url, source: "top-level"}' > /tmp/greptile_top.json &
wait
```

**両方のエンドポイントで API エラーまたは Greptile コメントがゼロの場合:** サイレントにスキップします。

行レベルのコメントに対する `position != null` フィルターは、強制プッシュされたコードから古いコメントを自動的にスキップします。

---

## 抑制チェック

プロジェクト固有の履歴パスを導出します。
```bash
REMOTE_SLUG=$(browse/bin/remote-slug 2>/dev/null || ~/.claude/skills/gstack/browse/bin/remote-slug 2>/dev/null || basename "$(git rev-parse --show-toplevel 2>/dev/null || pwd)")
PROJECT_HISTORY="$HOME/.gstack/projects/$REMOTE_SLUG/greptile-history.md"
```

`$PROJECT_HISTORY` が存在する場合はそれを読み取ります (プロジェクトごとの抑制)。各行には、以前の優先順位付けの結果が記録されます。

```
<date> | <repo> | <type:fp|fix|already-fixed> | <file-pattern> | <category>
```

**カテゴリ** (固定セット): `race-condition`、`null-check`、`error-handling`、`style`、`type-safety`、`security`、`performance`、 `correctness`、`other`

取得した各コメントを次のエントリと照合します。
- `type == fp` (既知の誤検知のみを抑制し、実際の問題は以前に修正されていません)
- `repo` は現在のリポジトリと一致します
- `file-pattern` はコメントのファイルパスと一致します
- `category` はコメント内の課題タイプと一致します

一致したコメントを **SUPPRESSED** としてスキップします。

履歴ファイルが存在しないか、解析できない行がある場合は、それらの行をスキップして続行します。不正な形式の履歴ファイルで失敗することはありません。

---

## 分類する



1. **行レベルのコメント:** 指定された `path:line` および周囲のコンテキスト (±10 行) のファイルを読み取ります。
2. **トップレベルのコメント:** コメント本文全体を読む
3. コメントを完全な差分 (`git diff origin/main`) およびレビュー チェックリストと相互参照します。
4. 分類:
   - **有効かつ対処可能** - 現在のコードに存在する実際のバグ、競合状態、セキュリティ上の問題、または正確性の問題
   - **有効だがすでに修正済み** — この問題はブランチでの後続のコミットで解決されました。 Identify the fixing commit SHA.
   - **FALSE POSITIVE** — コメントがコードを誤解している、別の場所で処理されたものにフラグを立てている、または文体のノイズである
   - **SUPPRESSED** — 上記の抑制チェックですでにフィルターされています

---

## 応答 API

Greptile コメントに返信するときは、コメント ソースに基づいて正しいエンドポイントを使用します。

**行レベルのコメント** (`pulls/$PR/comments` より):
```bash
gh api repos/$REPO/pulls/$PR_NUMBER/comments/$COMMENT_ID/replies \
  -f body="<reply text>"
```

**トップレベルのコメント** (`issues/$PR/comments` より):
```bash
gh api repos/$REPO/issues/$PR_NUMBER/comments \
  -f body="<reply text>"
```

**応答 POST が失敗した場合** (例: PR が閉じられ、書き込み権限がない): 警告して続行します。 Do not stop the workflow for a failed reply.

---

## 返信テンプレート

すべての Greptile 返信にこれらのテンプレートを使用してください。常に具体的な証拠を含めてください。曖昧な返信は決して投稿しないでください。

### Tier 1 (最初の対応) — フレンドリーで証拠を含む

**修正の場合 (ユーザーが問題の修正を選択した場合):**

```
**Fixed** in `<commit-sha>`.

\`\`\`diff
- <old problematic line(s)>
+ <new fixed line(s)>
\`\`\`

**Why:** <1-sentence explanation of what was wrong and how the fix addresses it>
```

**すでに修正されている場合 (ブランチでの以前のコミットで解決された問題):**

```
**Already fixed** in `<commit-sha>`.

**What was done:** <1-2 sentences describing how the existing commit addresses this issue>
```

**誤検知の場合 (コメントが間違っています):**

```
**Not a bug.** <1 sentence directly stating why this is incorrect>

**Evidence:**
- <specific code reference showing the pattern is safe/correct>
- <e.g., "The nil check is handled by `ActiveRecord::FinderMethods#find` which raises RecordNotFound, not nil">

**Suggested re-rank:** This appears to be a `<style|noise|misread>` issue, not a `<what Greptile called it>`. Consider lowering severity.
```

### Tier 2 (Greptile が事前の返信後に再報告) — 確固たる圧倒的な証拠

エスカレーション検出 (下記) によって同じスレッド上の以前の GStack 応答が特定された場合は、Tier 2 を使用します。議論を終わらせるために最大限の証拠を含めてください。

```
**This has been reviewed and confirmed as [intentional/already-fixed/not-a-bug].**

\`\`\`diff
<full relevant diff showing the change or safe pattern>
\`\`\`

**Evidence chain:**
1. <file:line permalink showing the safe pattern or fix>
2. <commit SHA where it was addressed, if applicable>
3. <architecture rationale or design decision, if applicable>

**Suggested re-rank:** Please recalibrate — this is a `<actual category>` issue, not `<claimed category>`. [Link to specific file change permalink if helpful]
```

---

## エスカレーションの検出

返信を作成する前に、以前の GStack 返信がこのコメント スレッドにすでに存在するかどうかを確認してください。

1. **行レベルのコメントの場合:** `gh api repos/$REPO/pulls/$PR_NUMBER/comments/$COMMENT_ID/replies` 経由で返信を取得します。返信本文に GStack マーカー (`**Fixed**`、`**Not a bug.**`、`**Already fixed**`) が含まれているかどうかを確認します。

2. **For top-level comments:** Scan the fetched issue comments for replies posted after the Greptile comment that contain GStack markers.

3. **以前の GStack 返信が存在し、かつ Greptile が同じファイル + カテゴリに再度投稿された場​​合:** Tier 2 (しっかりとした) テンプレートを使用します。

4. **以前の GStack 応答が存在しない場合:** Tier 1 (フレンドリー) テンプレートを使用します。

If escalation detection fails (API error, ambiguous thread): default to Tier 1. Never escalate on ambiguity.

---

## Severity Assessment & Re-ranking

When classifying comments, also assess whether Greptile's implied severity matches reality:

- If Greptile flags something as a **security/correctness/race-condition** issue but it's actually a **style/performance** nit: include `**Suggested re-rank:**` in the reply requesting the category be corrected.
- If Greptile flags a low-severity style issue as if it were critical: push back in the reply.
- Always be specific about why the re-ranking is warranted — cite code and line numbers, not opinions.

---

## History File Writes

Before writing, ensure both directories exist:
```bash
REMOTE_SLUG=$(browse/bin/remote-slug 2>/dev/null || ~/.claude/skills/gstack/browse/bin/remote-slug 2>/dev/null || basename "$(git rev-parse --show-toplevel 2>/dev/null || pwd)")
mkdir -p "$HOME/.gstack/projects/$REMOTE_SLUG"
mkdir -p ~/.gstack
```

トリアージ結果ごとに 1 行を **両方** ファイルに追加します (抑制の場合はプロジェクトごと、レトロの場合はグローバル)。
- `~/.gstack/projects/$REMOTE_SLUG/greptile-history.md` (per-project)
- `~/.gstack/greptile-history.md` (global aggregate)

形式:
```
<YYYY-MM-DD> | <owner/repo> | <type> | <file-pattern> | <category>
```

エントリの例:
```
2026-03-13 | garrytan/myapp | fp | app/services/auth_service.rb | race-condition
2026-03-13 | garrytan/myapp | fix | app/models/user.rb | null-check
2026-03-13 | garrytan/myapp | already-fixed | lib/payments.rb | error-handling
```

---

## 出力フォーマット

出力ヘッダーに Greptile の概要を含めます。
```
+ N Greptile comments (X valid, Y fixed, Z FP)
```

For each classified comment, show:
- 分類タグ: `[VALID]`、`[FIXED]`、`[FALSE POSITIVE]`、`[SUPPRESSED]`
- ファイル: ライン参照 (ラインレベルの場合) または `[top-level]` (トップレベルの場合)
- 本文の一行要約
- Permalink URL (the `html_url` field)