# 謝辞

/cso v2 was informed by research across the security audit landscape. Credits to:

- **[Sentry Security Review](https://github.com/getsentry/skills)** — 信頼度ベースのレポート システム (信頼度が高い結果のみがレポートされる) と「レポート前の調査」方法論 (データ フローのトレース、上流の検証のチェック) により、毎日 8/10 の信頼度ゲートが検証されました。 TimOnWeb は、テストされた 5 つのセキュリティ スキルのうち、インストールする価値がある唯一のセキュリティ スキルであると評価しました。
- **[ビット スキルの軌跡](https://github.com/trailofbits/skills)** — 監査コンテキスト構築方法論 (バグを探す前にメンタル モデルを構築する) は、フェーズ 0 に直接影響を与えました。 彼らの亜種分析の概念 (脆弱性が 1 つ見つかった場合? コードベース全体で同じパターンを検索する) は、フェーズ 12 の亜種分析ステップに影響を与えました。
- **[Shannon by Keygraph](https://github.com/KeygraphHQ/shannon)** — XBOW ベンチマークで 96.15% を達成した自律型 AI ペンテスター (100/104 エクスプロイト)。 AI がチェックリストのスキャンだけでなく、実際のセキュリティ テストを実行できることが検証されました。私たちのフェーズ 12 アクティブ検証は、シャノンが実際に行っていることの静的解析バージョンです。
- **[afiqmal/claude-security-audit](https://github.com/afiqiqmal/claude-security-audit)** — AI/LLM 固有のセキュリティ チェック (プロンプト インジェクション、RAG ポイズニング、ツール呼び出し権限) はフェーズ 7 に影響を与えました。フレームワーク レベルの自動検出 (「Node/TypeScript」だけでなく「Next.js」を検出する) は、フェーズ 0 のフレームワーク検出ステップに影響を与えました。
- **[Snyk ToxicSkills Research](https://snyk.io/blog/toxicskills-malicious-ai-agent-skills-clawhub/)** — AI エージェント スキルの 36% にセキュリティ上の欠陥があり、13.4% が悪意に触発されたものであるという調査結果 フェーズ 8 (スキル サプライ チェーン スキャン)。
- **[Daniel Miessler のパーソナル AI インフラストラクチャ](https://github.com/danielmiessler/Personal_AI_Infrastructure)** — インシデント対応のプレイブックと保護ファイルの概念は、修復フェーズと LLM セキュリティ フェーズに影響を与えました。
- **[McGo/claude-code-security-audit](https://github.com/McGo/claude-code-security-audit)** — 共有可能なレポートと実用的なエピックを生成するというアイデアは、レポート形式の進化に影響を与えました。
- **[Claude Code Security Pack](https://dev.to/myougatheaxo/automate-owasp-security-audits-with-claude-code-security-pack-4mah)** — モジュール型アプローチ (個別の /security-audit、/secret-scanner、/deps-check スキル) は、これらが別個の懸念事項であることを検証しました。私たちの統一されたアプローチでは、クロスフェーズ推論のためのモジュール性が犠牲になります。- **[Anthropic Claude Code Security](https://www.anthropic.com/news/claude-code-security)** — 多段階検証と信頼度スコアリングにより、当社の並行発見検証アプローチが検証されました。 Found 500+ zero-days in open source.
- **[@gus_argon](https://x.com/gus_aragon/status/2035841289602904360)** — 特定された重大な v1 盲点: スタック検出なし (すべての言語パターンを実行)、Claude Code の Grep ツールの代わりに bash grep を使用、`| head -20` 結果がサイレントに切り捨てられ、プリアンブルが肥大化しています。これらは、v2 のスタックファーストアプローチと Grep ツールの義務を直接形作りました。