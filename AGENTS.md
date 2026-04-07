# gstack — AI エンジニアリング ワークフロー

gstack は、AI エージェントに構造化された役割を与える SKILL.md ファイルのコレクションです。
ソフトウェア開発。 CEO レビュー担当者、エンジニア マネージャー、
デザイナー、QA リード、リリース エンジニア、デバッガーなど。

## 利用可能なスキル

スキルは `.agents/skills/` にあります。名前で呼び出します (例: `/office-hours`)。

|スキル |何をするのか |
|------|-----------|
| `/office-hours` |ここから始めましょう。コードを書く前に製品アイデアを再構成します。 |
| `/plan-ceo-review` | CEO レベルのレビュー: リクエスト内で 10 つ星の製品を見つけます。 |
| `/plan-eng-review` |ロック アーキテクチャ、データ フロー、エッジ ケース、テスト。 |
| `/plan-design-review` |各デザインの寸法を 0 ～ 10 で評価し、10 がどのようなものかを説明します。 |
| `/design-consultation` |完全なデザイン システムをゼロから構築します。 |
| `/review` |着陸前のPRレビュー。 CI は通過するが本番環境に侵入するバグを見つけます。 |
| `/debug` |体系的な根本原因のデバッグ。調査なくして修正はありません。 |
| `/design-review` |アトミックコミットによる監査と修正のループを設計します。 |
| `/qa` |実際のブラウザを開き、バグを見つけて修正し、再確認します。 |
| `/qa-only` | /qa と同じですが、レポートのみです。コードの変更はありません。 |
| `/ship` |テストを実行し、レビューし、プッシュし、PR を開きます。コマンドは 1 つです。 |
| `/document-release` |出荷したものと一致するようにすべてのドキュメントを更新します。 |
| `/retro` |個人ごとの内訳と連続出荷数を含む毎週のレトロ。 |
| `/browse` |ヘッドレス ブラウザ — 本物の Chromium、実際のクリック数、コマンドあたり最大 100 ミリ秒。 |
| `/setup-browser-cookies` |認証テストのために実際のブラウザから Cookie をインポートします。 |
| `/careful` |破壊的なコマンド (rm -rf、DROP TABLE、force-push) の前に警告します。 |
| `/freeze` |編集を 1 つのディレクトリにロックします。単なる警告ではなくハードブロック。 |
| `/guard` |慎重＋凍結を同時に発動。 |
| `/unfreeze` |ディレクトリ編集制限を削除します。 |
| `/gstack-upgrade` | gstack を最新バージョンに更新します。 |

## ビルドコマンド

```bash
bun install              # install dependencies
bun test                 # run tests (free, <5s)
bun run build            # generate docs + compile binaries
bun run gen:skill-docs   # regenerate SKILL.md files from templates
bun run skill:check      # health dashboard for all skills
```

## 主要な規則

- SKILL.md ファイルは、`.tmpl` テンプレートから**生成**されます。出力ではなくテンプレートを編集します。
- `bun run gen:skill-docs --host codex` を実行して、Codex 固有の出力を再生成します。
- ブラウズ バイナリは、ヘッドレス ブラウザ アクセスを提供します。 `$B <command>` をスキルで使用します。
- 安全スキル (注意、凍結、ガード) は、インラインの勧告散文を使用します。破壊的な操作の前に必ず確認してください。