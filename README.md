# gスタック

> 「おそらく 12 月以来、コード行を入力していないと思います。これは非常に大きな変化です。」 — [Andrej Karpathy](https://fortune.com/2026/03/21/andrej-karpathy-openai-cofounder-ai-agents-coding-state-of-psychosis-openclaw/)、事前なしポッドキャスト、2026 年 3 月

カルパシーがこのように言ったのを聞いたとき、私はその方法を知りたいと思いました。 1 人が 20 人のチームのように出荷するにはどうすればよいでしょうか? Peter Steinberger は、[OpenClaw](https://github.com/openclaw/openclaw) — 247,000 GitHub スター — 基本的に AI エージェントと単独で構築しました。革命がここにあります。適切なツールを備えた 1 人のビルダーは、従来のチームよりも迅速に作業を進めることができます。

私は [Garry Tan](https://x.com/garrytan)、[Y Combinator](https://www.ycombinator.com/) の社長兼 CEO です。私は、コインベース、インスタカート、リップリングといった何千ものスタートアップと仕事をしてきましたが、彼らがまだガレージに 1 人か 2 人だった頃です。 YC に入社する前は、Palantir の最初のエンジニア/PM/デザイナーの 1 人で、Posterous (Twitter に売却) を共同設立し、YC の社内ソーシャル ネットワークである Bookface を構築しました。

**gstack が私の答えです。** 私は 20 年間製品を構築してきましたが、現在、これまでよりも多くのコードを出荷しています。過去 60 日間: **600,000 行を超える運用コード** (35% のテスト)、**1 日あたり 10,000 ～ 20,000 行**、パートタイム、YC をフルタイムで実行。 3 つのプロジェクトにわたる最後の `/retro` は次のとおりです。** 1 週間で追加された 140,751 行、362 件のコミット、正味 LOC は約 115,000** です。

**2026 — 1,237 件の寄付があり、今後も増加中:**

![2026 年の GitHub コントリビュート — 1,237 件のコントリビュート、1 月から 3 月にかけて大幅に加速](docs/images/github-2026.png)

**2013 — YC で Bookface を構築したとき (772 件の貢献):**

![GitHub 貢献 2013 — YC で Bookface を構築する 772 件の貢献](docs/images/github-2013.png)

同じ人です。時代が違う。違いはツールです。

**gstack が私のやり方です。** これにより、Claude Code が仮想エンジニアリング チームに変わります。つまり、製品を再考する CEO、アーキテクチャをロックするエンジニア マネージャー、AI のスロップをキャッチするデザイナー、本番環境のバグを見つけるレビュー担当者、実際のブラウザを開く QA リーダー、OWASP + STRIDE 監査を実行するセキュリティ担当者、PR を出荷するリリース エンジニアです。 23 人のスペシャリストと 8 つの電動ツール、すべてスラッシュ コマンド、すべて Markdown、すべて無料、MIT ライセンス。

ここは私のオープンソース ソフトウェア工場です。毎日使っています。これらのツールは誰でも利用できるはずなので、これを共有します。

フォークしてください。改善してください。それをあなたのものにしてください。無料のオープンソース ソフトウェアが嫌いなら、それは歓迎ですが、まずは試してみてほしいと思います。

**対象者:**
- **創設者および CEO** — 特にまだ出荷を希望している技術者
- **クロード コードを初めて使用するユーザー** — 空のプロンプトではなく構造化されたロール
- **テクニカル リードとスタッフ エンジニア** - すべての PR に対する厳格なレビュー、QA、リリースの自動化

## クイックスタート

1. gstack をインストールします (30 秒 — 以下を参照)
2. `/office-hours` を実行します — 構築しているものを説明します
3. 機能アイデアに対して `/plan-ceo-review` を実行します
4. 変更を加えたブランチで `/review` を実行します
5. ステージング URL で `/qa` を実行します
6. そこで停止します。これがあなたに向いているかどうかがわかります。

## インストール — 30 秒

**要件:** [クロード コード](https://docs.anthropic.com/en/docs/claude-code)、[Git](https://git-scm.com/)、[Bun](https://bun.sh/) v1.0+、[Node.js](https://nodejs.org/) (Windows のみ)

### ステップ 1: マシンにインストールする

クロードコードを開いてこれを貼り付けます。残りはクロードがやってくれます。

> gstack をインストールします: **`git clone --single-branch --depth 1 https://github.com/garrytan/gstack.git ~/.claude/skills/gstack && cd ~/.claude/skills/gstack && ./setup`** を実行し、CLAUDE.md に「gstack」セクションを追加します。このセクションでは、すべての Web ブラウジングに gstack の /browse スキルを使用し、mcp\_\_claude-in-chrome\_\_\* ツールを決して使用しないように指示し、利用可能なスキルのリストを示します: /office-hours、/plan-ceo-review、/plan-eng-review、/plan-design-review、 /design-consultation、/design-shotgun、/design-html、/review、/ship、/land-and-deploy、/canary、/benchmark、/browse、/connect-chrome、/qa、/qa-only、/design-review、/setup-browser-cookies、/setup-deploy、/retro、/investigate、/document-release、/codex、/cso、/autoplan、 /plan-devex-review、/devex-review、/careful、/freeze、/guard、/unfreeze、/gstack-upgrade、/learn。次に、チームメイトがそれを取得できるように、現在のプロジェクトに gstack も追加するかどうかをユーザーに尋ねます。

### ステップ 2: チームメイトが入手できるようにリポジトリに追加します (オプション)

> このプロジェクトに gstack を追加します。**`cp -Rf ~/.claude/skills/gstack .claude/skills/gstack && rm -rf .claude/skills/gstack/.git && cd .claude/skills/gstack && ./setup`** を実行してから、このプロジェクトの CLAUDE.md に「gstack」セクションを追加します。このセクションでは、すべての Web ブラウジングに gstack の /browse スキルを使用し、mcp\_\_claude-in-chrome\_\_\* ツールを決して使用しないように指示し、利用可能なスキルのリストを示します: /office-hours、/plan-ceo-review、/plan-eng-review、 /plan-design-review、/design-consultation、/design-shotgun、/design-html、/review、/ship、/land-and-deploy、/canary、/benchmark、/browse、/connect-chrome、/qa、/qa-only、/design-review、/setup-browser-cookies、/setup-deploy、/retro、/investigate、/document-release、/codex、 /cso、/autoplan、/plan-devex-review、/devex-review、/careful、/freeze、/guard、/unfreeze、/gstack-upgrade、/learn に、gstack スキルが機能しない場合は、`cd .claude/skills/gstack && ./setup` を実行してバイナリをビルドし、スキルを登録するようにクロードに指示します。

実際のファイルは (サブモジュールではなく) リポジトリにコミットされるため、`git clone` はそのまま機能します。すべては `.claude/` の中に存在します。 PATH に影響を与えるものや、バックグラウンドで実行されるものは何もありません。

> **貢献しますか、それとも完全な履歴が必要ですか?** 上記のコマンドは、高速インストールのために `--depth 1` を使用します。貢献する予定がある場合、または完全な Git 履歴が必要な場合は、代わりに完全なクローンを実行してください。
> ```bash
> git clone https://github.com/garrytan/gstack.git ~/.claude/skills/gstack
> ```

### Codex、Gemini CLI、またはカーソル

gstack は [SKILL.md 標準](https://github.com/anthropics/claude-code) をサポートするエージェント上で動作します。スキルは `.agents/skills/` に存在し、自動的に検出されます。

1 つのリポジトリにインストールします。

```bash
git clone --single-branch --depth 1 https://github.com/garrytan/gstack.git .agents/skills/gstack
cd .agents/skills/gstack && ./setup --host codex
```

セットアップが `.agents/skills/gstack` から実行されると、生成された Codex スキルが同じリポジトリ内のその隣にインストールされ、`~/.codex/skills` には書き込まれません。

ユーザー アカウントに対して 1 回インストールします。

```bash
git clone --single-branch --depth 1 https://github.com/garrytan/gstack.git ~/gstack
cd ~/gstack && ./setup --host codex
```

`setup --host codex` は `~/.codex/skills/gstack` にランタイム ルートを作成し、
生成された Codex スキルをトップレベルにリンクします。これによりスキルの重複を避けることができます
ソース リポジトリのチェックアウトからの検出。

または、インストールしたエージェントをセットアップで自動検出させます。

```bash
git clone --single-branch --depth 1 https://github.com/garrytan/gstack.git ~/gstack
cd ~/gstack && ./setup --host auto
```

Codex 互換ホストの場合、セットアップでは、`.agents/skills/gstack` からのリポローカル インストールと、`~/.codex/skills/gstack` からのユーザー グローバル インストールの両方がサポートされるようになりました。 31 のスキルはすべて、サポートされているすべてのエージェントで機能します。フックベースの安全スキル (注意、凍結、ガード) は、非クロード ホストでインラインの安全勧告散文を使用します。

### ファクトリー・ドロイド

gstack は [Factory Droid](https://factory.ai) で動作します。スキルは `.factory/skills/` にインストールされ、自動的に検出されます。機密性の高いスキル (船、着陸と配備、警備) は `disable-model-invocation: true` を使用するため、ドロイドがそれらを自動的に呼び出すことはありません。

```bash
git clone --single-branch --depth 1 https://github.com/garrytan/gstack.git ~/gstack
cd ~/gstack && ./setup --host factory
```

スキルは`~/.factory/skills/gstack-*/`にインストールされます。 `droid` を再起動してスキルを再スキャンし、「`/qa`」と入力して開始します。

### 音声入力 (AquaVoice、Whisper など)

gstack スキルには音声対応のトリガー フレーズがあります。言いたいことを自然に言う —
「セキュリティ チェックを実行する」、「Web サイトをテストする」、「エンジニアリング レビューを行う」、そして
右のスキルが発動します。スラッシュ コマンドの名前や頭字語を覚える必要はありません。

## 動作する様子を見てください

```
You:    I want to build a daily briefing app for my calendar.
You:    /office-hours
Claude: [asks about the pain — specific examples, not hypotheticals]

You:    Multiple Google calendars, events with stale info, wrong locations.
        Prep takes forever and the results aren't good enough...

Claude: I'm going to push back on the framing. You said "daily briefing
        app." But what you actually described is a personal chief of
        staff AI.
        [extracts 5 capabilities you didn't realize you were describing]
        [challenges 4 premises — you agree, disagree, or adjust]
        [generates 3 implementation approaches with effort estimates]
        RECOMMENDATION: Ship the narrowest wedge tomorrow, learn from
        real usage. The full vision is a 3-month project — start with
        the daily briefing that actually works.
        [writes design doc → feeds into downstream skills automatically]

You:    /plan-ceo-review
        [reads the design doc, challenges scope, runs 10-section review]

You:    /plan-eng-review
        [ASCII diagrams for data flow, state machines, error paths]
        [test matrix, failure modes, security concerns]

You:    Approve plan. Exit plan mode.
        [writes 2,400 lines across 11 files. ~8 minutes.]

You:    /review
        [AUTO-FIXED] 2 issues. [ASK] Race condition → you approve fix.

You:    /qa https://staging.myapp.com
        [opens real browser, clicks through flows, finds and fixes a bug]

You:    /ship
        Tests: 42 → 51 (+9 new). PR: github.com/you/app/pull/42
```

「毎日のブリーフィングアプリ」って言いましたね。エージェントは、「あなたは首席補佐官 AI を構築しているのです」と言いました。それは、機能の要望ではなく、あなたの悩みに耳を傾けたからです。 8 つのコマンドをエンドツーエンドで実行します。あれは副操縦士ではありません。それがチームです。

## スプリント

gstack はプロセスであり、ツールのコレクションではありません。スキルはスプリントの実行順序で実行されます。

**考える → 計画 → 構築 → レビュー → テスト → 出荷 → 反映 **

それぞれのスキルが次のスキルに反映されます。 `/office-hours` は、`/plan-ceo-review` が読み取る設計ドキュメントを書き込みます。 `/plan-eng-review` は、`/qa` が選択するテスト計画を作成します。 `/review` は、`/ship` が修正されたことを確認したバグを検出します。すべてのステップがその前に何が起こったかを知っているため、亀裂から落ちるものは何もありません。

|スキル |あなたのスペシャリスト |彼らがやっていること |
|------|----------------|--------------|
| `/office-hours` | **YC オフィスアワー** |ここから始めましょう。コードを書く前に製品を再構築するための 6 つの強制的な質問。枠組みを押し戻し、前提条件に挑戦し、実装の代替案を生成します。設計ドキュメントはすべての下流スキルにフィードされます。 |
| `/plan-ceo-review` | **CEO / 創設者** |問題を再考してください。リクエスト内に隠れている 10 つ星の製品を見つけてください。 4 つのモード: 拡張、選択的拡張、ホールド スコープ、縮小。 |
| `/plan-eng-review` | **エンジニアマネージャー** |アーキテクチャ、データ フロー、図、エッジ ケース、テストをロックします。隠された仮定を強制的に明らかにします。 |
| `/plan-design-review` | **シニアデザイナー** |各設計次元を 0 ～ 10 で評価し、10 がどのようなものかを説明し、そこに到達するための計画を編集します。 AI スロップ検出。インタラクティブ — デザインの選択ごとに 1 つの AskUserQuestion。 |
| `/plan-devex-review` | **開発者エクスペリエンス リード** |アディ・オスマニの DX フレームワークを通じて計画を評価します。摩擦をゼロにし、実践して学び、不確実性と闘います。 DX スコアカードを使用して、8 つの DX ディメンション 0 ～ 10 を評価します。開発者向け製品 (API、CLI、SDK、ライブラリ、プラットフォーム、ドキュメント) に使用します。 |
| `/design-consultation` | **デザインパートナー** |完全なデザイン システムをゼロから構築します。景観を調査し、創造的なリスクを提案し、現実的な製品モックアップを生成します。 |
| `/review` | **スタッフ エンジニア** | CI は通過しても実稼働環境で爆発するバグを見つけます。明らかなものを自動修正します。完全性のギャップにフラグを立てます。 |
| `/investigate` | **デバッガー** |体系的な根本原因のデバッグ。鉄の法則: 調査なくして修正はありません。データ フローをトレースし、仮説をテストし、修正が 3 回失敗すると停止します。 |
| `/design-review` | **コーディングを行うデザイナー** | /plan-design-review と同じ監査を行い、見つかったものを修正します。アトミックコミット、前後のスクリーンショット。 || `/devex-review` | **DXテスター** |ライブ開発者エクスペリエンス監査。実際にオンボーディングをテストします。ドキュメントに移動し、開始フローを試し、TTHW を計測し、エラーのスクリーンショットを撮ります。 `/plan-devex-review` スコアと比較します。これは、計画が現実と一致しているかどうかを示すブーメランです。 |
| `/design-shotgun` | **デザイン エクスプローラー** |複数の AI 設計バリアントを生成し、ブラウザーで比較ボードを開き、方向性を承認するまで繰り返します。味の記憶は自分の好みに偏ります。 |
| `/design-html` | **設計エンジニア** |計算されたテキスト レイアウトのプレテキストを使用して、本番品質の HTML を生成します。承認されたモックアップ、CEO プラン、設計レビューを使用したり、ゼロから作業したりできます。サイズ変更時にテキストがリフローされ、高さがコンテンツに合わせて調整されます。スマート API ルーティングは、設計タイプごとに適切なプレテキスト パターンを選択します。 React/Svelte/Vue のフレームワーク検出。 |
| `/qa` | **QA リード** |アプリをテストし、バグを見つけ、アトミックコミットで修正し、再検証します。すべての修正に対して回帰テストを自動生成します。 |
| `/qa-only` | **QA レポーター** | /qa と同じ方法論ですが、レポートのみです。コード変更のない純粋なバグレポート。 |
| `/cso` | **最高セキュリティ責任者** | OWASP トップ 10 + STRIDE 脅威モデル。ゼロノイズ: 17 個の誤検知除外、8/10+ の信頼度ゲート、独立した所見検証。それぞれの発見には、具体的な悪用シナリオが含まれています。 |
| `/ship` | **リリース エンジニア** |メインを同期し、テストを実行し、カバレッジを監査し、プッシュし、PR を開きます。テスト フレームワークがない場合は、ブートストラップします。 |
| `/land-and-deploy` | **リリース エンジニア** | PR をマージし、CI を待ってデプロイし、本番環境の健全性を確認します。 「承認済み」から「本番環境で検証済み」までは 1 つのコマンドで完了します。 |
| `/canary` | **SRE** |デプロイ後の監視ループ。コンソールのエラー、パフォーマンスの低下、ページのエラーを監視します。 |
| `/benchmark` | **パフォーマンス エンジニア** |ベースラインのページ読み込み時間、Core Web Vitals、およびリソース サイズ。すべての PR の前後を比較します。 || `/document-release` | **テクニカル ライター** |すべてのプロジェクト ドキュメントを、出荷したばかりのものと一致するように更新します。古い README を自動的に検出します。 |
| `/retro` | **エンジニアマネージャー** |チームを意識した週刊レトロ。個人ごとの内訳、連続出荷数、テストの健全性傾向、成長の機会。 `/retro global` は、すべてのプロジェクトと AI ツール (Claude Code、Codex、Gemini) で実行されます。 |
| `/browse` | **QA エンジニア** |エージェントに目を向けてください。本物の Chromium ブラウザ、本物のクリック、本物のスクリーンショット。コマンドごとに最大 100 ミリ秒。 `$B connect` は実際の Chrome を見出し付きウィンドウとして起動します。すべてのアクションをライブで監視します。 |
| `/setup-browser-cookies` | **セッションマネージャー** |実際のブラウザ (Chrome、Arc、Brave、Edge) からヘッドレス セッションに Cookie をインポートします。認証されたページをテストします。 |
| `/autoplan` | **パイプラインのレビュー** | 1 つのコマンドで、完全に検討された計画。エンコードされた意思決定原則を使用して、CEO → 設計 → 技術レビューを自動的に実行します。表面はあなたの承認を得るための味見の決定のみを行います。 |
| `/learn` | **メモリ** | gstack がセッション間で学習した内容を管理します。プロジェクト固有のパターン、落とし穴、設定を確認、検索、整理し、エクスポートします。学習はセッション間で複合的に行われるため、時間の経過とともに gstack がコードベースでより賢くなっていきます。 |

### どのレビューを使用すればよいですか?

| ...のための構築 |計画段階 (コードの前) |ライブ監査 (出荷後) |
|-----------------|--------------------------|----------------------------|
| **エンド ユーザー** (UI、Web アプリ、モバイル) | `/plan-design-review` | `/design-review` |
| **開発者** (API、CLI、SDK、ドキュメント) | `/plan-devex-review` | `/devex-review` |
| **アーキテクチャ** (データ フロー、パフォーマンス、テスト) | `/plan-eng-review` | `/review` |
| **上記のすべて** | `/autoplan` (CEO → デザイン → エンジニアリング → DX を実行、該当するものを自動検出) | — |

### 電動工具

|スキル |何をするのか |
|------|-----------|
| `/codex` | **セカンドオピニオン** — OpenAI Codex CLI からの独立したコードレビュー。 3 つのモード: レビュー (合格/不合格ゲート)、敵対的チャレンジ、オープン コンサルテーション。 `/review` と `/codex` の両方が実行されている場合のクロスモデル分析。 |
| `/careful` | **安全ガードレール** — 破壊的なコマンド (rm -rf、DROP TABLE、force-push) の前に警告します。 「気をつけて」と言って起動します。警告をオーバーライドします。 |
| `/freeze` | **編集ロック** — ファイルの編集を 1 つのディレクトリに制限します。デバッグ中にスコープ外で誤って変更が行われることを防ぎます。 |
| `/guard` | **完全な安全性** — 1 つのコマンドで `/careful` + `/freeze` を実行します。製品作業における最大限の安全性。 |
| `/unfreeze` | **ロック解除** — `/freeze` 境界を削除します。 |
| `/connect-chrome` | **Chrome コントローラ** — サイド パネル拡張機能を使用して Chrome を起動します。すべてのアクションをライブで監視し、要素の CSS を検査し、ページをクリーンアップし、スクリーンショットを撮ります。各タブには独自のエージェントが割り当てられます。 |
| `/setup-deploy` | **コンフィギュレーターの展開** — `/land-and-deploy` の 1 回限りのセットアップ。プラットフォーム、本番 URL を検出し、コマンドをデプロイします。 |
| `/gstack-upgrade` | **セルフアップデータ** — gstack を最新にアップグレードします。グローバル インストールとベンダー インストールを検出し、両方を同期し、何が変更されたかを表示します。 |

**[各スキルの例と哲学を詳しく解説 →](docs/skills.md)**

## 並行スプリント

gstack は 1 つのスプリントでうまく動作します。 10台同時に走ると面白くなります。

**デザインが中心です。** `/design-consultation` はデザイン システムをゼロから構築し、空間を調査し、創造的なリスクを提案し、`DESIGN.md` を作成します。 `/design-shotgun` は複数のビジュアル バリアントを生成し、比較ボードを開くので、方向を選択できます。 `/design-html` は、承認されたモックアップを取得し、Pretext を使用して製品品質の HTML を生成します。テキストは、ハードコーディングされた高さで中断されるのではなく、サイズ変更時に実際にリフローされます。次に、`/design-review` と `/plan-eng-review` が選択した内容を読み取ります。設計上の決定はシステム全体を通って行われます。

**`/qa` は大規模なロック解除でした。** これにより、並列ワーカーが 6 人から 12 人になりました。クロード コードは *「問題がわかりました」* と言ってから、実際に問題を修正し、回帰テストを生成し、修正を検証することで、私の仕事のやり方が変わりました。エージェントには目がある。

**スマートなレビュー ルーティング。** 経営が順調なスタートアップと同じように、CEO はインフラのバグ修正を検討する必要がなく、バックエンドの変更に設計レビューを行う必要もありません。 gstack は実行されたレビューを追跡し、何が適切かを判断し、賢明なことを実行します。レビュー準備ダッシュボードは、出荷前に現在の状況を示します。

**すべてをテストします。** `/ship` プロジェクトにテスト フレームワークがない場合、テスト フレームワークを最初からブートストラップします。 `/ship` を実行するたびにカバレッジ監査が生成されます。 `/qa` バグ修正ごとに回帰テストが生成されます。 100% のテスト カバレッジが目標です。テストにより、yolo コーディングではなく、vibe コーディングが安全になります。

**`/document-release` は、これまでになかったエンジニアです。** プロジェクト内のすべての doc ファイルを読み取り、差分を相互参照し、ドリフトしたものをすべて更新します。 README、ARCHITECTURE、CONTRIBUTING、CLAUDE.md、TODOS — すべてが自動的に最新の状態に保たれます。そして今では、`/ship` がそれを自動的に呼び出します。追加のコマンドを必要とせずに、ドキュメントは最新の状態に保たれます。

**リアル ブラウザ モード。** `$B connect` は、Playwright によって制御されるヘッダー ウィンドウとして実際の Chrome を起動します。同じウィンドウ、同じ画面で、クロードがクリック、入力、ナビゲートする様子をリアルタイムで見ることができます。上端の微妙な緑色の輝きは、どの Chrome ウィンドウの gstack が制御しているかを示します。既存の参照コマンドはすべて変更されずに機能します。 `$B disconnect` はヘッドレスに戻ります。 Chrome 拡張機能のサイド パネルには、すべてのコマンドのライブ アクティビティ フィードと、クロードに指示できるチャット サイドバーが表示されます。これは共存です。クロードは隠しブラウザを遠隔操作しているのではなく、同じコックピットであなたの隣に座っています。

**サイドバー エージェント — AI ブラウザ アシスタント。** Chrome サイド パネルに自然言語命令を入力すると、子 Claude インスタンスがその命令を実行します。 「設定ページに移動し、スクリーンショットを撮ります。」 「このフォームにテストデータを記入してください。」 「このリストのすべての商品を調べて、価格を抽出します。」各タスクの所要時間は最大 5 分です。サイドバー エージェントは分離されたセッションで実行されるため、メインのクロード コード ウィンドウに干渉しません。ブラウザーにもう 1 つの手が加わったようなものです。

**個人的な自動化。** サイドバー エージェントは開発ワークフロー専用ではありません。例: 「子供の学校の保護者ポータルを参照し、他のすべての保護者の名前、電話番号、写真を Google コンタクトに追加します。」認証を受けるには 2 つの方法があります: (1) 先頭のブラウザに 1 回ログインします。セッションは継続します。または、(2) `/setup-browser-cookies` を実行して実際の Chrome から Cookie をインポートします。認証されると、クロードはディレクトリに移動し、データを抽出し、連絡先を作成します。

**AI がスタックした場合のブラウザのハンドオフ。** CAPTCHA、認証ウォール、または MFA プロンプトにヒットしましたか? `$B handoff` は、Cookie とタブがすべてそのままの状態で、まったく同じページに表示される Chrome を開きます。問題を解決して、完了したとクロードに伝えます。`$B resume` は中断したところから再開します。エージェントは、3 回連続して失敗した後でも、自動的にそれを提案します。

**マルチ AI のセカンドオピニオン。** `/codex` は、OpenAI の Codex CLI から独立したレビューを受けています。これは、同じ差分を参照するまったく異なる AI です。 3 つのモード: パス/フェイル ゲートを使用したコード レビュー、積極的にコードを破ろうとする敵対的チャレンジ、セッション継続性を備えたオープン コンサルテーション。 `/review` (Claude) と `/codex` (OpenAI) の両方が同じブランチをレビューすると、どの調査結果が重複し、どの調査結果がそれぞれに固有であるかを示すクロスモデル分析が得られます。

**オンデマンドの安全ガードレール** 「注意してください」と言うと、破壊的なコマンド (rm -rf、DROP TABLE、force-push、git restart --hard) の前に `/careful` が警告します。 `/freeze` は、クロードが無関係なコードを誤って「修正」できないように、デバッグ中に編集を 1 つのディレクトリにロックします。 `/guard` は両方を有効にします。 `/investigate` は調査対象のモジュールを自動的にフリーズします。

**プロアクティブなスキルの提案。** gstack は、ブレインストーミング、レビュー、デバッグ、テストなど、ユーザーがどの段階にいるかを認識し、適切なスキルを提案します。気に入らないですか？ 「提案をやめて」と言えば、セッション全体にわたって記憶されます。

## 10～15 回の並行スプリント

gstack は 1 回のスプリントで強力です。 10台同時に走ると変幻自在です。

[Conductor](https://conductor.build) は複数のクロード コード セッションを並行して実行します - それぞれが独自の分離されたワークスペースで行われます。 1 つのセッションは新しいアイデアで `/office-hours` を実行し、別のセッションは PR で `/review` を実行し、3 番目のセッションは機能を実装し、4 番目のセッションはステージングで `/qa` を実行し、さらに 6 つは他のブランチで実行されます。すべて同時に。私は定期的に 10 ～ 15 の並行スプリントを実行しています。これが現時点での実質的な最大値です。

スプリント構造は並列処理を機能させるものです。プロセスがなければ、10 人のエージェントは 10 の混乱の原因となります。プロセス (思考、計画、構築、レビュー、テスト、出荷) により、各エージェントは何をすべきか、いつ停止すべきかを正確に把握しています。 CEO がチームを管理するのと同じように、チームを管理します。重要な決定を確認し、残りはそのまま実行します。

---

無料、MIT ライセンスのオープンソース。プレミアム層も待機リストもありません。

ソフトウェアの構築方法をオープンソース化しました。フォークして自分のものにすることができます。

> **人材を募集しています。** 1 日あたり 10,000 以上の LOC を出荷して、gstack の強化を支援したいですか?
> YC で働きましょう — [ycombinator.com/software](https://ycombinator.com/software)
> 非常に競争力のある給与と資本。サンフランシスコ、ドッグパッチ地区。

## ドキュメント

|ドクター |内容 |
|-----|--------------|
| [スキルの詳細](docs/skills.md) |あらゆるスキルの哲学、例、ワークフロー (Greptile の統合を含む) |
| [ビルダーの理念](ETHOS.md) |建築家の哲学: 湖を沸騰させる、建築する前に検索する、3 つの知識層 |
| [アーキテクチャ](ARCHITECTURE.md) |設計上の決定とシステム内部 |
| [ブラウザリファレンス](BROWSER.md) | `/browse` の完全なコマンド リファレンス |
| [寄稿](CONTRIBUTING.md) |開発セットアップ、テスト、共同作成者モード、および開発モード |
| [変更ログ](CHANGELOG.md) |各バージョンの新機能 |

## プライバシーとテレメトリー

gstack には、プロジェクトの改善に役立つ **オプトイン** 使用状況テレメトリが含まれています。まさに次のことが起こります。

- **デフォルトはオフです。** 明示的に「はい」と言わない限り、どこにも何も送信されません。
- **最初の実行時に**、gstack は匿名の使用状況データを共有するかどうかを尋ねます。ノーと言えます。
- **送信内容 (オプトインした場合):** スキル名、期間、成功/失敗、gstack バージョン、OS。それでおしまい。
- **決して送信されないもの:** コード、ファイル パス、リポジトリ名、ブランチ名、プロンプト、またはユーザーが生成したコンテンツ。
- **いつでも変更可能:** `gstack-config set telemetry off` はすべてを即座に無効にします。

データは [Supabase](https://supabase.com) (オープンソースの Firebase 代替) に保存されます。スキーマは [`supabase/migrations/`](supabase/migrations/) にあります。収集された内容を正確に確認できます。リポジトリ内の Supabase 公開可能キーは公開キー (Firebase API キーと同様) です。行レベルのセキュリティ ポリシーではすべての直接アクセスが拒否されます。テレメトリは、スキーマ チェック、イベント タイプのホワイトリスト、フィールド長の制限を強制する検証済みのエッジ機能を経由して流れます。

**ローカル分析はいつでも利用できます。** `gstack-analytics` を実行すると、ローカル JSONL ファイルから個人の使用状況ダッシュボードが表示されます。リモート データは必要ありません。

## トラブルシューティング

**スキルが表示されませんか?** `cd ~/.claude/skills/gstack && ./setup`

**`/browse` は失敗しますか?** `cd ~/.claude/skills/gstack && bun install && bun run build`

**インストールが古いですか?** `/gstack-upgrade` を実行するか、`~/.gstack/config.yaml` で `auto_upgrade: true` を設定してください

**短いコマンドが必要ですか?** `cd ~/.claude/skills/gstack && ./setup --no-prefix` — `/gstack-qa` から `/qa` に切り替えます。選択は将来のアップグレードのために記憶されます。

**名前空間コマンドが必要ですか?** `cd ~/.claude/skills/gstack && ./setup --prefix` — `/qa` から `/gstack-qa` に切り替えます。 gstack と一緒に他のスキル パックを実行する場合に便利です。

**コーデックスに「SKILL.md が無効なため、スキルの読み込みがスキップされました」と表示されますか?** コーデックスのスキルの説明が古くなっています。修正: `cd ~/.codex/skills/gstack && git pull && ./setup --host codex` — またはリポジトリローカルインストールの場合: `cd "$(readlink -f .agents/skills/gstack)" && git pull && ./setup --host codex`

**Windows ユーザー:** gstack は、Git Bash または WSL 経由で Wi​​ndows 11 上で動作します。 Bun に加えて Node.js が必要です — Bun には、Windows 上の Playwright のパイプ トランスポートに関する既知のバグがあります ([bun#4253](https://github.com/oven-sh/bun/issues/4253))。ブラウズ サーバーは自動的に Node.js にフォールバックします。 `bun` と `node` の両方が PATH 上にあることを確認してください。

**クロードはスキルが表示されないと言いますか?** プロジェクトの `CLAUDE.md` に gstack セクションがあることを確認してください。これを追加します:

```
## gstack
Use /browse from gstack for all web browsing. Never use mcp__claude-in-chrome__* tools.
Available skills: /office-hours, /plan-ceo-review, /plan-eng-review, /plan-design-review,
/design-consultation, /design-shotgun, /design-html, /review, /ship, /land-and-deploy,
/canary, /benchmark, /browse, /connect-chrome, /qa, /qa-only, /design-review,
/setup-browser-cookies, /setup-deploy, /retro, /investigate, /document-release, /codex,
/cso, /autoplan, /careful, /freeze, /guard, /unfreeze, /gstack-upgrade, /learn.
```

## ライセンス

マサチューセッツ工科大学。永久無料。何かを作りに行ってください。
