# TODOS.md フォーマットのリファレンス

正規の TODOS.md 形式の共有リファレンス。一貫した TODO 項目構造を確保するために、`/ship` (ステップ 5.5) および `/plan-ceo-review` (TODOS.md 更新セクション) によって参照されます。

---

## ファイル構造

```markdown
# TODOS

## <Skill/Component>     ← e.g., ## Browse, ## Ship, ## Review, ## Infrastructure
<items sorted P0 first, then P1, P2, P3, P4>

## Completed
<finished items with completion annotation>
```

**セクション:** スキルまたはコンポーネントごとに整理します (`## Browse`、`## Ship`、`## Review`、`## QA`、`## Retro`、`## Infrastructure`)。各セクション内で、項目を優先順位 (P0 が先頭) に基づいて並べ替えます。

---

## TODO項目のフォーマット

各項目はそのセクションの H3 です。

```markdown
### <Title>

**What:** One-line description of the work.

**Why:** The concrete problem it solves or value it unlocks.

**Context:** Enough detail that someone picking this up in 3 months understands the motivation, the current state, and where to start.

**Effort:** S / M / L / XL
**Priority:** P0 / P1 / P2 / P3 / P4
**Depends on:** <prerequisites, or "None">
```

**必須フィールド:** 内容、理由、コンテキスト、労力、優先度
**オプションのフィールド:** 依存、ブロック

---

## 優先順位の定義

- **P0** — ブロッキング: 次のリリース前に実行する必要があります
- **P1** — クリティカル: このサイクルで実行する必要があります
- **P2** — 重要: P0/P1 がクリアされているときに実行してください。
- **P3** — あれば便利: 導入/使用データの後に再確認
- **P4** — いつか: 良いアイデアですが、緊急性はありません

---

## 完成した項目フォーマット

項目が完了したら、元のコンテンツを保存して以下を追加して、項目を `## Completed` セクションに移動します。

```markdown
**Completed:** vX.Y.Z (YYYY-MM-DD)
```