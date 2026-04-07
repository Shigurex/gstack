---
名前：慎重
バージョン: 0.1.0
説明: |
  破壊的なコマンドのための安全ガードレール。 rm -rf、DROP TABLE、の前に警告します。
  force-push、git replace --hard、kubectl delete、および同様の破壊的な操作。
  ユーザーは各警告を上書きできます。製品に触れたり、ライブ システムをデバッグしたりするときに使用します。
  または共有環境で作業します。 「注意してください」「セーフティモード」などを求められた場合に使用します。
  「本番モード」または「慎重モード」。 (Gスタック)
許可されたツール:
  - バッシュ
  - 読む
フック:
  プレツールの使用:
    - マッチャー: 「バッシュ」
      フック:
        - タイプ: コマンド
          コマンド: 「bash ${CLAUDE_SKILL_DIR}/bin/check-careful.sh」
          statusMessage: "破壊的なコマンドをチェックしています..."
---
<!-- SKILL.md.tmpl から自動生成 — 直接編集しないでください -->
<!-- 再生成: bun run gen:skill-docs -->

# /careful — 破壊的なコマンドのガードレール

セーフティモードは**アクティブ**になりました。すべての bash コマンドは破壊的かどうかチェックされます。
走る前の模様。破壊的なコマンドが検出された場合は警告が表示されます
そして続行するかキャンセルするかを選択できます。

```bash
mkdir -p ~/.gstack/analytics
echo '{"skill":"careful","ts":"'$(date -u +%Y-%m-%dT%H:%M:%SZ)'","repo":"'$(basename "$(git rev-parse --show-toplevel 2>/dev/null)" 2>/dev/null || echo "unknown")'"}'  >> ~/.gstack/analytics/skill-usage.jsonl 2>/dev/null || true
```

## 保護されるもの

|パターン |例 |リスク |
|-------|-------|------|
| `rm -rf` / `rm -r` / `rm --recursive` | `rm -rf /var/data` |再帰的な削除 |
| `DROP TABLE` / `DROP DATABASE` | `DROP TABLE users;` |データ損失 |
| `TRUNCATE` | `TRUNCATE orders;` |データ損失 |
| `git push --force` / `-f` | `git push -f origin main` |歴史の書き換え |
| `git reset --hard` | `git reset --hard HEAD~3` |コミットされていない仕事の損失 |
| `git checkout .` / `git restore .` | `git checkout .` |コミットされていない仕事の損失 |
| `kubectl delete` | `kubectl delete pod` |生産への影響 |
| `docker rm -f` / `docker system prune` | `docker system prune -a` |コンテナ/イメージの損失 |

## 安全な例外

これらのパターンは警告なしで許可されます。
- `rm -rf node_modules` / `.next` / `dist` / `__pycache__` / `.cache` / `build` / `.turbo` / `coverage`

## 仕組み

フックはツール入力 JSON からコマンドを読み取り、それを
上記のパターンを使用すると、警告メッセージとともに `permissionDecision: "ask"` が返されます。
一致するものが見つかった場合。 You can always override the warning and proceed.

非アクティブにするには、会話を終了するか、新しい会話を開始します。フックはセッションスコープです。