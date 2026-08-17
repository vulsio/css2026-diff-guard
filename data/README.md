# data/ — 発動事例の確定データセット(2026-04-23 〜 2026-08-17)

論文の全数調査の元データ。maintainer workspace の `docs/diff-guard-incidents.md` /
`docs/diff-guard-incidents-data/` から 2026-08-17 に確定・転記したスナップショット。
以後、論文が参照する数値の正本はこのディレクトリとする。

| ファイル | 内容 |
|---|---|
| `diff-guard-incidents.md` | 発動事例カタログ(P-1〜A-27)+ 集計と考察(§5)。全期間対応済み |
| `02a`〜`02e-runs-*.md` | ガード FAIL 全 420 run の表。`02e`(07-14〜08-17)は per-source 化後で target 名の後に `[source]` を併記 |
| `03-promote-history.md` | promote-digest.yml 全 101 run / 92 unique digest(全て FAIL 候補と一致) |
| `guard-failures.tsv` | 機械可読版(run_id, workflow, created_at, event, kind, failed_checks, fail_rows, digest)。guard-trip 418 + guard-infra 2 + 参考の build/other-fail 12 |
| `log-extracts/` | 各 run のログ抜粋(FAIL 行・集約 rc 行) |
| `stats.py` | 集計スクリプト。`python3 stats.py > stats-output.txt` で再生成 |
| `stats-output.txt` | 集計結果(sequence / episode / per-source / 時系列 / 明示ソース内訳) |

- 図 3・図 4([../figs/](../figs/))はこのディレクトリの `stats-output.txt` と `guard-failures.tsv` を読む
- 収集方法: run 一覧と失敗ステップは GitHub Actions API、FAIL 行は run ログ、候補 digest は
  "Push vuls.db to GHCR (tagless, digest-only)" ステップ完了時刻と GHCR package versions の
  created_at の突合(前半窓 293/295 一意一致 + 2 件は completed_at 一致、後半窓 125/125 が誤差 0〜1 秒で一意一致)
- 期間を延長する場合: CI を再収集して `guard-failures.tsv` と `02x` / `03` を追記 → `stats.py` 再実行 →
  `figs/` の図を再生成 → 論文本文の数値を更新
