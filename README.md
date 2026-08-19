# css2026-diff-guard

CSS 2026 OWS トラック投稿論文「脆弱性情報の上流は安定していない: 公開前検査による 116 日間の全数観測」の原稿リポジトリ。

- **原稿の正本**: [docs/css2026-diff-guard.tex](docs/css2026-diff-guard.tex)(本文は単一ファイル)+ [docs/refs.bib](docs/refs.bib)
- **ビルド**: `cd docs && make build`(Docker の paperist/alpine-texlive-ja + latexmk。css2026-data の構成を移植)。ビルド済み [docs/css2026-diff-guard.pdf](docs/css2026-diff-guard.pdf) は共有用にコミットする(ソース変更時は再ビルドして一緒にコミット)
- **図**: 図 1 は TeX 内 TikZ。図 2〜4 は [figs/](figs/) の matplotlib スクリプトで `docs/figures/*.pdf` を生成(データは [data/](data/) を参照)。`cd figs && python3 fig{2,3,4}_*.py`
- 2026-08-17 時点で本文+参考文献 8 ページ(上限内)。研究倫理節は昨年同様不要と判断し削除済み
- **データ**: 発動事例の確定データセット(事例カタログ・run 表・TSV・ログ抜粋・集計スクリプト)は [data/](data/) に収録(2026-08-17 確定)。設計・検証ドキュメント `diff-guard.md` は maintainer ローカル参照、昨年論文は [vulsio/css2025-vuls2](https://github.com/vulsio/css2025-vuls2)

## 締切(CSS 2026)

- [x] アブストラクト登録(締切 2026-08-03)— 登録済み
- [ ] **最終原稿: 2026-08-21(金)17:00**。本文最大 8 ページ(参考文献含む)+ 付録最大 5 ページ
- [x] OWS 専用ページの投稿要領を確認 — OWS ページは CSS2026 募集要項を参照するのみで、追加の規定なし(本文 8 ページ + 付録 5 ページ、研究倫理は制限外)

## TODO

- [x] タイトル確定(主張先行型): 和「脆弱性情報の上流は安定していない: 公開前検査による 116 日間の全数観測」/ 英「Vulnerability Feeds Are Not Stable: A 116-Day Exhaustive Observation via Pre-Publication Inspection」。投稿システム側のタイトル・アブストラクトも最新版へ更新済み(2026-08-17)
- [x] 観測期間を 116 日(2026-04-23〜08-17)へ延長済み。945 run / 69 episode / 1,465 FAIL 行 / promote 92 digest。データは data/ に確定(再延長手順は data/README.md)
- [x] triage の AI 委任を本文に明記(§4 の手順書共有 + §6.6 の役割分担。概要には入れない)
- [x] 発動事例の全数データ: 本文では公開に言及しない(private repo のため、締切までに確実にできない約束はしない)
- [x] wunder24 の書誌: 号・頁が一次情報で確認できなかったため誌名と年のみに整理(volume を削除)
- [x] 分量超過時の削減候補: nguyen13, wunder24 — 2026-08-17 の関連研究圧縮で ruohonen19 と共に引用を削除(bib エントリは残置)

## 執筆メモ(決定事項・規約)

- 句読点は「，．」(css.cls / 情報処理学会様式)
- em-dash(「〜 — 〜」挿入構文)は使わない。句読点・接続詞・コロンで書く
- 「・」は 2 項並列に使わない(「と」「か」で接続)。3 項以上は読点+「および」か「〜や〜といった」。複合名詞を含む列挙には使わない。「収集・変換・構築」のような 1 語同士の同種並列と外来語・人名の区切りのみ可
- 用語: 「公開前検査(diff guard)」を §1 で定義し、以後「検査」または「diff guard」。「ゲート」は使わない。「抽出器」(extract 工程のコード)「ビルダ」(db build 工程のコード)は §2.1 で定義
- チェックの略記は Dn(検知差分・新スキャナ)/ Do(同・旧)/ DB(DB 構造差分)。旧称 M / O / D(CI の det_master / det_old / db 由来)は論文では使わない
- 表記: advisory → アドバイザリ。fixture / baseline / target / promote / grooming / override はコマンド・運用用語として英字のまま
- 概要は自己完結: 先行研究への言及は「既報の」(「昨年報告した」等の時間参照は使わない)。和文概要を修正したら英文 abstract も追従させる
- タイトル代案(未採用): 「脆弱性情報の上流はどれほど動くか: 公開前検査による 116 日間の定量観測」/「公開前検査で観測した脆弱性フィードの不安定性と公開品質管理の実践」
- 後半窓(07-14〜08-17)の原因帰属は、非上流と判定したイベントは原因 PR の差分で直接立証、上流由来はビルダ・抽出器・取得設定の 3 者をコミット履歴で除外する消去法(§4 に証拠水準として明記済み)
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
