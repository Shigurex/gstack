# セッションインテリジェンスレイヤー

＃＃ 問題

Claude Code のコンテキスト ウィンドウは一時的なものです。すべてのセッションは新鮮に始まります。いつ
自動圧縮は ~167K トークンで起動され、一般的な概要は保持されますが、
ファイルの読み取り、推論チェーン、中間の決定を破壊します。

gstack はすでにディスク上に残る貴重な成果物を生成しています: CEO の計画、
工学レビュー、設計レビュー、QA レポート、学習。これらのファイルには以下が含まれます
現在の作品を形作った決定、制約、コンテキスト。でもクロード
彼らの存在を知りません。圧縮後の計画とレビューは、
すべての決定が通知され、文脈から静かに消えます。

エコシステムはこれに取り組んでいます。 claude-mem (9,000 つ星以上) がツールの使用状況をキャプチャします
そして、将来のセッションにコンテキストを挿入します。クロード HUD はリアルタイム エージェントを表示します
ステータス。 Anthropic 独自の `claude-progress.txt` パターンは進行状況ファイルを使用します
エージェントが各セッションの開始時に読みます。

**スキルで生成されたアーティファクト**を作成するという具体的な問題を解決している人は誰もいません
圧縮に耐えます。なぜなら、他に gstack のアーティファクト アーキテクチャを持っている人がいないからです。

## 洞察力

gstack はすでに構造化アーティファクトを `~/.gstack/projects/$SLUG/` に書き込んでいます。
- CEO の計画: `ceo-plans/`
- デザインレビュー: `design-reviews/`
- 英語レビュー: `eng-reviews/`
- 学習: `learnings.jsonl`
- スキル使用量: `../analytics/skill-usage.jsonl`

The missing piece is not storage.それは認識です。 The preamble needs to tell
エージェント: 「これらのファイルは存在します。これらのファイルには、あなたがすでに行った決定が含まれています。
After compaction, re-read them."

## アーキテクチャ

```
                   ┌─────────────────────────────────────┐
                   │        Claude Context Window         │
                   │   (ephemeral, ~167K token limit)     │
                   │                                      │
                   │   Compaction fires ──► summary only   │
                   └──────────────┬──────────────────────┘
                                  │
                          reads on start / after compaction
                                  │
                   ┌──────────────▼──────────────────────┐
                   │    ~/.gstack/projects/$SLUG/         │
                   │    (persistent, survives everything) │
                   │                                      │
                   │  ceo-plans/         ← /plan-ceo-review
                   │  eng-reviews/       ← /plan-eng-review
                   │  design-reviews/    ← /plan-design-review
                   │  checkpoints/       ← /checkpoint (new)
                   │  timeline.jsonl     ← every skill (new)
                   │  learnings.jsonl    ← /learn
                   └─────────────────────────────────────┘
                                  │
                          rolled up weekly
                                  │
                   ┌──────────────▼──────────────────────┐
                   │           /retro                      │
                   │  Timeline: 3 /review, 2 /ship, ...   │
                   │  Health trends: compile 8/10 (↑2)     │
                   │  Learnings applied: 4 this week       │
                   └─────────────────────────────────────┘
```

## 特徴

### レイヤ 1: コンテキストの回復 (前文、すべてのスキル)
前文に約 10 行の散文。圧縮またはコンテキストの劣化後、
エージェントは `~/.gstack/projects/$SLUG/` で最近の計画、レビュー、
チェックポイント。ディレクトリを一覧表示し、最新のファイルを読み取ります。

コスト: ほぼゼロ。利点: すべてのスキルの計画/レビューは圧縮後も存続します。

### レイヤ 2: セッション タイムライン (前文、すべてのスキル)
すべてのスキルは 1 行の JSONL エントリを `timeline.jsonl`: タイムスタンプに追加します。
スキル名、ブランチ、主要な結果。 `/retro` がレンダリングします。

プロジェクトの AI 支援による作業履歴を可視化します。 「今週: 3 /レビュー、
2 /出荷、1 /ブランチ全体の機能認証と修正請求を調査します。」

### レイヤ 3: クロスセッション インジェクション (前文、すべてのスキル)
最近のアーティファクトを含むブランチで新しいセッションが開始されると、プリアンブル
「最後のセッション: JWT 認証が実装され、3/5 のタスクが完了しました。
計画: ~/.gstack/projects/$SLUG/checkpoints/latest.md"

エージェントは、ファイルを読み取る前にどこから中断したかを認識します。

### Layer 4: /checkpoint (opt-in skill)
作業状態の手動スナップショット: 何が行われているか、編集中のファイル、
decisions made, what's remaining. Useful before stepping away, before
複雑な操作、ワークスペースの引き継ぎ、または数日後の復帰など。

### レイヤ 5: /health (オプトイン スキル)
コード品質ダッシュボード: 型チェック、lint、テスト スイート、デッド コード スキャン。
総合0-10スコア。時間の経過を追跡します。 `/retro` はトレンドを示します。 `/ship`
設定可能なしきい値でのゲート。

## 複合効果

各機能は独立して役立ちます。一緒に何かを創り出す
それは次のことを複合させます：

セッション 1: /plan-ceo-review は計画を作成します。ディスクに保存されました。
セッション 2: エージェントはプリアンブルの後に計画を読みます。決定を再度尋ねません。
セッション 3: /checkpoint は進行状況を保存します。タイムラインには 2 /review、1 /ship が表示されます。
セッション 4: リファクタリング中に圧縮が開始されます。エージェントはチェックポイントを再読み取りします。
           重要な決定、タイプ、残りの作業を回復します。続けます。
セッション 5: /retro は週をロールアップします。健康傾向: 6/10 → 8/10。
           タイムラインには、3 つのブランチにわたる 12 のスキル呼び出しが表示されます。

このプロジェクトの AI の歴史はもはや一時的なものではありません。それは持続し、複合化し、
今後のすべてのセッションがよりスマートになります。それがセッションインテリジェンスです
層。

## これは何ではありませんか

- Claude の組み込み圧縮 (セッションを処理する) の代替ではありません。
  状態。 gstack アーティファクトを処理します)
- claude-mem のような完全なメモリ システムではありません (クロスセッションを処理します)
  SQLite経由のメモリ。私たちは構造化されたスキルアーティファクトを扱います）
- データベースやサービスではありません (ディスク上の単なるマークダウン ファイル)

## 研究ソース

- [Anthropic: 長期稼働エージェント向けの効果的なハーネス](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)
- [人間性: 効果的なコンテキスト エンジニアリング](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
- [クロード・メム](https://github.com/thedotmack/claude-mem)
- [クロードHUD](https://github.com/jarrodwatts/claude-hud)
- [CodeScene: エージェントティック AI コーディングのベスト プラクティス](https://codescene.com/blog/agentic-ai-coding-best-practice-patterns-for-speed-with-quality)
- [git-persisted state (Beads) による圧縮後のリカバリ](https://dev.to/jeremy_longshore/building-post-compaction-recovery-for-ai-agent-workflows-with-beads-207l)