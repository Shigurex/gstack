---
名前: gstack-upgrade
バージョン: 1.1.0
説明: |
  gstack を最新バージョンにアップグレードします。グローバルインストールとベンダーインストールを検出し、
  アップグレードを実行し、新機能を表示します。 「gstack をアップグレードする」ように求められた場合に使用します。
  「gstack を更新する」または「最新バージョンを取得する」。
  音声トリガー (音声テキスト変換エイリアス): 「ツールのアップグレード」、「ツールの更新」、「Gee stack upgrade」、「G stack upgrade」。
許可されたツール:
  - バッシュ
  - 読む
  - 書く
  - ユーザーに質問する
---
<!-- SKILL.md.tmpl から自動生成 — 直接編集しないでください -->
<!-- 再生成: bun run gen:skill-docs -->

# /gstack-upgrade

gstack を最新バージョンにアップグレードして、新機能を表示します。

## インライン アップグレード フロー

This section is referenced by all skill preambles when they detect `UPGRADE_AVAILABLE`.

### ステップ 1: ユーザーに質問する (または自動アップグレード)

まず、自動アップグレードが有効になっているかどうかを確認します。
```bash
_AUTO=""
[ "${GSTACK_AUTO_UPGRADE:-}" = "1" ] && _AUTO="true"
[ -z "$_AUTO" ] && _AUTO=$(~/.claude/skills/gstack/bin/gstack-config get auto_upgrade 2>/dev/null || true)
echo "AUTO_UPGRADE=$_AUTO"
```

**`AUTO_UPGRADE=true` または `AUTO_UPGRADE=1` の場合:** AskUserQuestion をスキップします。 「自動アップグレード gstack v{old} → v{new}...」をログに記録し、ステップ 2 に直接進みます。自動アップグレード中に `./setup` が失敗した場合は、バックアップ (`.bak` ディレクトリ) から復元し、ユーザーに「自動アップグレードに失敗しました — 前のバージョンが復元されました。`/gstack-upgrade` を手動で実行して再試行してください。」と警告します。

**それ以外の場合**、AskUserQuestion を使用します。
- 質問: 「gstack **v{new}** は利用可能です (v{old} を使用しています)。今すぐアップグレードしますか?」
- オプション: [「はい、今すぐアップグレードします」、「常に最新の状態に保ちます」、「今はしない」、「二度と質問しない」]

**「はい、今すぐアップグレードします」の場合:** ステップ 2 に進みます。

**「常に最新の情報を入手する」場合:**
```bash
~/.claude/skills/gstack/bin/gstack-config set auto_upgrade true
```
ユーザーに「自動アップグレードが有効になっています。今後のアップデートは自動的にインストールされます。」と伝えます。その後、ステップ 2 に進みます。

**「今は実行しない」場合:** エスカレートするバックオフでスヌーズ状態を書き込み (最初のスヌーズ = 24 時間、2 回目 = 48 時間、3 回目以降 = 1 週間)、現在のスキルを続行します。アップグレードについては再度言及しないでください。
```bash
_SNOOZE_FILE=~/.gstack/update-snoozed
_REMOTE_VER="{new}"
_CUR_LEVEL=0
if [ -f "$_SNOOZE_FILE" ]; then
  _SNOOZED_VER=$(awk '{print $1}' "$_SNOOZE_FILE")
  if [ "$_SNOOZED_VER" = "$_REMOTE_VER" ]; then
    _CUR_LEVEL=$(awk '{print $2}' "$_SNOOZE_FILE")
    case "$_CUR_LEVEL" in *[!0-9]*) _CUR_LEVEL=0 ;; esac
  fi
fi
_NEW_LEVEL=$((_CUR_LEVEL + 1))
[ "$_NEW_LEVEL" -gt 3 ] && _NEW_LEVEL=3
echo "$_REMOTE_VER $_NEW_LEVEL $(date +%s)" > "$_SNOOZE_FILE"
```
注: `{new}` は、`UPGRADE_AVAILABLE` 出力からのリモート バージョンです。更新チェック結果から置き換えてください。

ユーザーにスヌーズ期間を伝えます:「次のリマインダーは 24 時間以内」(レベルに応じて 48 時間または 1 週間)。ヒント: 「自動アップグレードするには、`~/.gstack/config.yaml` に `auto_upgrade: true` を設定します。」

**「二度と質問しない」場合:**
```bash
~/.claude/skills/gstack/bin/gstack-config set update_check false
```
ユーザーに「更新チェックが無効になっています。再度有効にするには、`~/.claude/skills/gstack/bin/gstack-config set update_check true` を実行してください。」と伝えます。
現在のスキルを継続します。

### ステップ 2: インストール タイプを検出する

```bash
if [ -d "$HOME/.claude/skills/gstack/.git" ]; then
  INSTALL_TYPE="global-git"
  INSTALL_DIR="$HOME/.claude/skills/gstack"
elif [ -d "$HOME/.gstack/repos/gstack/.git" ]; then
  INSTALL_TYPE="global-git"
  INSTALL_DIR="$HOME/.gstack/repos/gstack"
elif [ -d ".claude/skills/gstack/.git" ]; then
  INSTALL_TYPE="local-git"
  INSTALL_DIR=".claude/skills/gstack"
elif [ -d ".agents/skills/gstack/.git" ]; then
  INSTALL_TYPE="local-git"
  INSTALL_DIR=".agents/skills/gstack"
elif [ -d ".claude/skills/gstack" ]; then
  INSTALL_TYPE="vendored"
  INSTALL_DIR=".claude/skills/gstack"
elif [ -d "$HOME/.claude/skills/gstack" ]; then
  INSTALL_TYPE="vendored-global"
  INSTALL_DIR="$HOME/.claude/skills/gstack"
else
  echo "ERROR: gstack not found"
  exit 1
fi
echo "Install type: $INSTALL_TYPE at $INSTALL_DIR"
```

上で出力されたインストール タイプとディレクトリ パスは、後続のすべての手順で使用されます。

### ステップ 3: 古いバージョンを保存する

以下のステップ 2 の出力からのインストール ディレクトリを使用します。

```bash
OLD_VERSION=$(cat "$INSTALL_DIR/VERSION" 2>/dev/null || echo "unknown")
```

### ステップ 4: アップグレード

ステップ 2 で検出されたインストール タイプとディレクトリを使用します。

**git インストールの場合** (グローバル git、ローカル git):
```bash
cd "$INSTALL_DIR"
STASH_OUTPUT=$(git stash 2>&1)
git fetch origin
git reset --hard origin/main
./setup
```
`$STASH_OUTPUT` に「保存された作業ディレクトリ」が含まれている場合は、ユーザーに次のように警告します。「注: ローカルの変更は隠されています。それらを復元するには、スキル ディレクトリで `git stash pop` を実行してください。」

**ベンダー インストールの場合** (ベンダー、ベンダー グローバル):
```bash
PARENT=$(dirname "$INSTALL_DIR")
TMP_DIR=$(mktemp -d)
git clone --depth 1 https://github.com/garrytan/gstack.git "$TMP_DIR/gstack"
mv "$INSTALL_DIR" "$INSTALL_DIR.bak"
mv "$TMP_DIR/gstack" "$INSTALL_DIR"
cd "$INSTALL_DIR" && ./setup
rm -rf "$INSTALL_DIR.bak" "$TMP_DIR"
```

### ステップ 4.5: ローカルのベンダーのコピーを同期する

ステップ 2 のインストール ディレクトリを使用します。更新が必要なローカル ベンダーのコピーも存在するかどうかを確認します。

```bash
_ROOT=$(git rev-parse --show-toplevel 2>/dev/null)
LOCAL_GSTACK=""
if [ -n "$_ROOT" ] && [ -d "$_ROOT/.claude/skills/gstack" ]; then
  _RESOLVED_LOCAL=$(cd "$_ROOT/.claude/skills/gstack" && pwd -P)
  _RESOLVED_PRIMARY=$(cd "$INSTALL_DIR" && pwd -P)
  if [ "$_RESOLVED_LOCAL" != "$_RESOLVED_PRIMARY" ]; then
    LOCAL_GSTACK="$_ROOT/.claude/skills/gstack"
  fi
fi
echo "LOCAL_GSTACK=$LOCAL_GSTACK"
```

`LOCAL_GSTACK` が空でない場合は、新しくアップグレードしたプライマリ インストールからコピーして更新します (README ベンダー インストールと同じアプローチ)。
```bash
mv "$LOCAL_GSTACK" "$LOCAL_GSTACK.bak"
cp -Rf "$INSTALL_DIR" "$LOCAL_GSTACK"
rm -rf "$LOCAL_GSTACK/.git"
cd "$LOCAL_GSTACK" && ./setup
rm -rf "$LOCAL_GSTACK.bak"
```
ユーザーに「ベンダーのコピーも `$LOCAL_GSTACK` で更新されました。準備ができたら `.claude/skills/gstack/` をコミットしてください。」と伝えます。

`./setup` が失敗した場合は、バックアップから復元し、ユーザーに次の警告を出します。
```bash
rm -rf "$LOCAL_GSTACK"
mv "$LOCAL_GSTACK.bak" "$LOCAL_GSTACK"
```
ユーザーに次のように伝えます: 「同期に失敗しました — `$LOCAL_GSTACK` で以前のバージョンが復元されました。`/gstack-upgrade` を手動で実行して再試行してください。」

### ステップ 4.75: バージョン移行の実行

`./setup` が完了したら、古いバージョン間の移行スクリプトを実行します。
そして新しいバージョン。移行は、`./setup` だけではカバーできない状態の修正を処理します
(古い構成、孤立したファイル、ディレクトリ構造の変更)。

```bash
MIGRATIONS_DIR="$INSTALL_DIR/gstack-upgrade/migrations"
if [ -d "$MIGRATIONS_DIR" ]; then
  for migration in $(find "$MIGRATIONS_DIR" -maxdepth 1 -name 'v*.sh' -type f 2>/dev/null | sort -V); do
    # Extract version from filename: v0.15.2.0.sh → 0.15.2.0
    m_ver="$(basename "$migration" .sh | sed 's/^v//')"
    # Run if this migration version is newer than old version
    # (simple string compare works for dotted versions with same segment count)
    if [ "$OLD_VERSION" != "unknown" ] && [ "$(printf '%s\n%s' "$OLD_VERSION" "$m_ver" | sort -V | head -1)" = "$OLD_VERSION" ] && [ "$OLD_VERSION" != "$m_ver" ]; then
      echo "Running migration $m_ver..."
      bash "$migration" || echo "  Warning: migration $m_ver had errors (non-fatal)"
    fi
  done
fi
```

移行は、`gstack-upgrade/migrations/` のべき等な bash スクリプトです。それぞれに名前が付けられています
`v{VERSION}.sh` は、古いバージョンからアップグレードする場合にのみ実行されます。 CONTRIBUTING.md を参照してください。
新しい移行を追加する方法については、こちらを参照してください。

### ステップ 5: マーカーの書き込み + キャッシュのクリア

```bash
mkdir -p ~/.gstack
echo "$OLD_VERSION" > ~/.gstack/just-upgraded-from
rm -f ~/.gstack/last-update-check
rm -f ~/.gstack/update-snoozed
```

### ステップ 6: 新機能を表示する

`$INSTALL_DIR/CHANGELOG.md` をお読みください。古いバージョンと新しいバージョンの間のすべてのバージョン エントリを検索します。テーマごとに 5 ～ 7 つの箇条書きでまとめます。圧倒されすぎず、ユーザー向けの変更に焦点を当ててください。重要でない限り、内部リファクタリングをスキップします。

形式:
```
gstack v{new} — upgraded from v{old}!

What's new:
- [bullet 1]
- [bullet 2]
- ...

Happy shipping!
```

### ステップ 7: 続行

What's New を表示した後、ユーザーが最初に呼び出したスキルを続行します。アップグレードは完了しました。これ以上のアクションは必要ありません。

---

## スタンドアロンでの使用

(プリアンブルからではなく) `/gstack-upgrade` として直接呼び出された場合:

1. 新しい更新チェックを強制します (キャッシュをバイパス):
```bash
~/.claude/skills/gstack/bin/gstack-update-check --force 2>/dev/null || \
.claude/skills/gstack/bin/gstack-update-check --force 2>/dev/null || true
```
出力を使用して、アップグレードが利用可能かどうかを判断します。

2. `UPGRADE_AVAILABLE <old> <new>` の場合: 上記の手順 2 ～ 6 に従います。

3. 出力がない場合 (プライマリが最新の場合): ローカル ベンダーの古いコピーがないか確認します。

上記のステップ 2 の bash ブロックを実行して、プライマリ インストール タイプとディレクトリ (`INSTALL_TYPE` および `INSTALL_DIR`) を検出します。次に、上記のステップ 4.5 検出 bash ブロックを実行して、ローカル ベンダーのコピー (`LOCAL_GSTACK`) を確認します。

**`LOCAL_GSTACK` が空の場合** (ローカル ベンダーのコピーがない): ユーザーに「すでに最新バージョン (v{version}) を使用しています。」と伝えます。

**`LOCAL_GSTACK` が空でない場合**、バージョンを比較します。
```bash
PRIMARY_VER=$(cat "$INSTALL_DIR/VERSION" 2>/dev/null || echo "unknown")
LOCAL_VER=$(cat "$LOCAL_GSTACK/VERSION" 2>/dev/null || echo "unknown")
echo "PRIMARY=$PRIMARY_VER LOCAL=$LOCAL_VER"
```

**バージョンが異なる場合:** 上記のステップ 4.5 同期 bash ブロックに従って、プライマリからローカル コピーを更新します。ユーザーに次のように伝えます: 「グローバル v{PRIMARY_VER} は最新です。ローカル ベンダーのコピーを v{LOCAL_VER} → v{PRIMARY_VER} に更新しました。準備ができたら `.claude/skills/gstack/` をコミットしてください。」

**バージョンが一致する場合:** ユーザーに「最新バージョン (v{PRIMARY_VER}) を使用しています。グローバル コピーとローカル ベンダー コピーは両方とも最新です。」と伝えます。