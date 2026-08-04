# css2026-diff-guard

CSS 2026 OWS トラック投稿論文「脆弱性情報アップストリームの不安定性の実測: 履歴管理基盤上の公開前検査による 82 日間の全数運用調査」(仮題)の原稿リポジトリ。

- **原稿の正本**: [docs/css2026-diff-guard.tex](docs/css2026-diff-guard.tex)(本文は単一ファイル)+ [docs/refs.bib](docs/refs.bib)
- **ビルド**: `cd docs && make build`(Docker の paperist/alpine-texlive-ja + latexmk。css2026-data の構成を移植)。ビルド済み [docs/css2026-diff-guard.pdf](docs/css2026-diff-guard.pdf) は共有用にコミットする(ソース変更時は再ビルドして一緒にコミット)
- **図**: 図 1 は TeX 内 TikZ。図 2〜4 は [figs/](figs/) の matplotlib スクリプトで `docs/figures/*.pdf` を生成(データスナップショット同梱)。`cd figs && python3 fig{2,3,4}_*.py`
- 2026-07-29 時点で 8 ページ(参考文献が 8 ページ目前半で終了 = 本文+文献の上限 8 ページ内。研究倫理は制限外)
- 元資料(maintainer ローカル workspace。この repo には含まれない): diff-guard 発動事例集 `docs/diff-guard-incidents.md`、設計・検証 `diff-guard.md`、昨年論文 vulsio/css2025-vuls2

## 締切(CSS 2026)

- [x] アブストラクト登録(締切 2026-08-03)— 登録済み
- [ ] **最終原稿: 2026-08-21(金)17:00**。本文最大 8 ページ(参考文献含む)+ 付録最大 5 ページ
- [ ] OWS 専用ページの投稿要領を確認(和文/英文、テンプレート、採録形態)

## TODO

- [ ] タイトル確定 — 和文・英文セットで(現状は仮。代案は下記「執筆メモ」)
- [ ] 観測期間を投稿時点まで延長するか決める — 現本文は 82 日 / 671 run / 50 episode(〜07-14)固定。延長するなら maintainer workspace で `stats.py` を `guard-failures.tsv` に再実行して全数値を更新し、figs/data/ のスナップショットも差し替えて図を再生成
- [ ] triage の AI 委任を本文に明記するか検討 — 実運用では帰属手順を skill 化した AI エージェントが一次調査を実施し人間がレビュー。書くなら §4 の手順書共有のくだり + §6.6 の役割分担と接続(概要には入れない = 決定済み)
- [ ] 発動事例の全数データの公開方法を決める(付録 5 ページ枠 or 公開リポジトリ参照)
- [ ] 細部の書誌修正: wunder24 の巻号表記(number 欠落で「Vol. 5 , .」と出る)。分量超過時の削減候補: nguyen13, wunder24

## 執筆メモ(決定事項・規約)

- 句読点は「，．」(css.cls / 情報処理学会様式)
- em-dash(「〜 — 〜」挿入構文)は使わない。句読点・接続詞・コロンで書く
- 「・」は 2 項並列に使わない(「と」「か」で接続)。3 項以上は読点+「および」か「〜や〜といった」。複合名詞を含む列挙には使わない。「収集・変換・構築」のような 1 語同士の同種並列と外来語・人名の区切りのみ可
- 用語: 「公開前検査(diff guard)」を §1 で定義し、以後「検査」または「diff guard」。「ゲート」は使わない。「抽出器」(extract 工程のコード)「ビルダ」(db build 工程のコード)は §2.1 で定義
- 表記: advisory → アドバイザリ。fixture / baseline / target / promote / grooming / override はコマンド・運用用語として英字のまま
- 概要は自己完結: 先行研究への言及は「既報の」(「昨年報告した」等の時間参照は使わない)。和文概要を修正したら英文 abstract も追従させる
- タイトル代案(未採用): 「脆弱性情報の上流はどれほど動くか: 公開前検査による 82 日間の定量観測」/「公開前検査で観測した脆弱性フィードの不安定性と公開品質管理の実践」
- 国内先行調査(2026-07-29)の結論: フィード不安定性を定量計測した国内学術研究は見当たらない(§7 に明記)。CSS2024/2025 予稿の書誌は OWS 公式プログラムページで確認(PDF は非公開)。kanai24 は著者陣に本論文著者を含む自己先行

## 参考文献の出典 URL(検証用メモ)

全エントリ 2026-07-29 に出典ページで実在確認済み。refs.bib に URL の無い学術文献の検証先:

- dong19: https://www.usenix.org/conference/usenixsecurity19/presentation/dong
- lin26: https://doi.org/10.1145/3779208.3806085
- anwar22: https://doi.org/10.1109/TDSC.2021.3125270
- nguyen13: https://doi.org/10.1145/2484313.2484377
- ruohonen19: https://doi.org/10.1016/j.aci.2017.12.002
- wunder24: https://doi.org/10.1145/3688806
- imtiaz21: https://doi.org/10.1145/3475716.3475769
- churakova25: https://arxiv.org/abs/2503.14388
- li19: https://www.usenix.org/conference/usenixsecurity19/presentation/li
- bouwman20: https://www.usenix.org/conference/usenixsecurity20/presentation/bouwman
- griffioen20: https://doi.org/10.1007/978-3-030-57878-7_14
- torres19: https://www.usenix.org/conference/usenixsecurity19/presentation/torres-arias
- lamb22: https://doi.org/10.1109/MS.2021.3073045
- newman22: https://doi.org/10.1145/3548606.3560596
- samuel10: https://doi.org/10.1145/1866307.1866315
- schelter18: https://doi.org/10.14778/3229863.3229867
- breck19: https://proceedings.mlsys.org/paper_files/paper/2019/hash/928f1160e52192e3e0017fb63ab65391-Abstract.html
- tu23: https://doi.org/10.1145/3580305.3599776
- redyuk21: https://dblp.org/rec/conf/edbt/RedyukKMS21.html
- shankar23: https://arxiv.org/abs/2303.06094
- yoo12: https://doi.org/10.1002/stvr.430
- terada05: https://cir.nii.ac.jp/crid/1050282812859379072
- kuzuno24 / kanai24: https://www.iwsec.org/ows/2024/main.html
