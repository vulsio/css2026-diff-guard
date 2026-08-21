# 脆弱性情報の上流は安定していない: 公開前検査による116日間の全数観測 @ コンピュータセキュリティシンポジウム2026

<div style="text-align:center">
  <img src="https://vuls.io/img/docs/vuls_logo.png">
</div>

## 資料

- 論文PDF(CSS 提出版): https://raw.githubusercontent.com/vulsio/css2026-diff-guard/main/css2026-diff-guard.pdf

cf.
- CSS 2026: https://www.iwsec.org/css/2026/
- OSSセキュリティ技術ワークショップ(OWS) 2026: https://www.iwsec.org/ows/2026/

## 概要

OSS 脆弱性スキャナ [Vuls](https://github.com/future-architect/vuls) の脆弱性データベース公開 CI に、公開候補と直前公開版を自動比較する**公開前検査(diff guard)**を実装し、116 日間・943 run の全数調査から上流フィードの不安定性を測定した研究の、原稿とデータのリポジトリ。昨年の[「広範な脆弱性情報の統合管理と履歴追跡」(CSS 2025)](https://github.com/vulsio/css2025-vuls2)の続編にあたる。

## リポジトリ構成

| パス | 内容 |
|---|---|
| [doc/](doc/) | 原稿(TeX 単一ファイル + refs.bib)とビルド済み PDF。`cd doc && make build` で再ビルド(Docker の paperist/alpine-texlive-ja + latexmk) |
| [data/](data/) | 観測 116 日間(2026-04-23〜08-16)の確定データセット: 発動事例カタログ、run 表、promote 履歴、機械可読 TSV、ログ抜粋、69 episode 別判定表、集計スクリプト。詳細は [data/README.md](data/README.md) |
| [figs/](figs/) | 図 2〜4 を data/ から生成する matplotlib スクリプト |

## 参考 URL

実装関係

- vuls-data-update
  - https://github.com/MaineK00n/vuls-data-update
  - raw, extracted の収集・変換ロジック
- vuls2
  - https://github.com/MaineK00n/vuls2
  - データベース構築・検知ロジックと、公開前検査(diff guard)の差分計算本体
- vuls-data-db
  - https://github.com/vulsio/vuls-data-db
  - 公開 CI の workflow と、検査の閾値・override 設定

GitHub Container Registry 関係

- vuls-data-db
  - https://github.com/vulsio/vuls-data-db/pkgs/container/vuls-data-db
  - raw, extracted の履歴管理されたデータ置き場
- vuls-nightly-db
  - https://github.com/vulsio/vuls-nightly-db/pkgs/container/vuls-nightly-db
  - データベース置き場。検査 FAIL 時のタグなし候補 digest も https://github.com/vulsio/vuls-nightly-db/pkgs/container/vuls-nightly-db/versions で参照できる

その他

- VulsDB
  - https://cve.vuls.biz/
  - extracted データを元にした脆弱性情報を参照できるサイト

## 付録

```bibtex
@InProceedings{css2026-diff-guard,
  title = {脆弱性情報の上流は安定していない: 公開前検査による116日間の全数観測},
  etitle = {Vulnerability Feeds Are Not Stable: A 116-Day Exhaustive Observation via Pre-Publication Inspection},
  author = {篠原 俊一, 中岡 典弘, 神戸 康多},
  yomi = {Shunichi Shinohara, Norihiro Nakaoka, Kota Kanbe},
  booktitle = {コンピュータセキュリティシンポジウム2026論文集},
  pages = {xxx--xxx},
  year = {2026},
  month = {10},
  annote = {https://www.iwsec.org/css/2026/}
}
```

## License / Copyright

論文本体([doc/](doc/) および [css2026-diff-guard.pdf](css2026-diff-guard.pdf))を**除き**、本リポジトリの内容(data/、figs/ ほか)は [CC BY 4.0](LICENSE) で提供する。

論文本体にはライセンスを付与しない。その著作権は著者および(採録後は)情報処理学会の著作権規程に従う。

Copyright by Shunichi Shinohara, Norihiro Nakaoka, Kota Kanbe and Future Corporation.
