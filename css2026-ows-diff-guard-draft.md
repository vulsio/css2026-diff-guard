# 脆弱性情報アップストリームの不安定性の実測 — 履歴管理基盤上の公開前差分ゲート 82 日間の全数運用調査

<!--
CSS 2026 OWS トラック投稿用たたき台(第 2 稿 / A4 4ページ目安、本番 TeX 4〜5ページ想定)。

フレーミング(第 2 稿での変更):
- 主命題を「上流不安定性の測定研究」に昇格。diff guard は主役ではなく「測定器」。
- 昨年 CSS2025 論文(中岡・篠原「広範な脆弱性情報の統合管理と履歴追跡」)を
  「原因帰属の方法論を成立させた基盤」として §1 / §4 / §8 に明示的に配線。
  昨年の future work(§5.2 論理的差分・§5.3 パイプライン堅牢化)への回答である旨も明記。

タイトル代案:
- 「脆弱性情報の上流はどれほど動くか — 公開前差分ゲートによる 82 日間の定量観測」
- 「公開前差分ゲートで観測した脆弱性フィードの不安定性と公開品質管理の実践」

元資料(maintainer ローカル workspace のパス。この repo には含まれない): docs/diff-guard-incidents.md(発動事例集)、diff-guard.md(設計・検証)、
vulsio/css2025-vuls2/docs/css.pdf(昨年論文)。数値・識別子はすべて元資料からの転記。
TeX 化の際は run ID / digest は脚注または付録リポジトリ参照に落とす。
-->

## 執筆 TODO(この md はたたき台 — 最終稿は TeX)

**締切(CSS 2026)**
- [ ] **アブストラクト登録: 2026-08-03(月)24:00** — 冒頭の概要を投稿システム向けに切り出して登録
- [ ] 最終原稿: 2026-08-21(金)17:00。本文最大 8 ページ(参考文献含む)+ 付録最大 5 ページ
- [ ] OWS 専用ページの投稿要領を確認(和文/英文、テンプレート、採録形態)

**内容**
- [ ] 用語統一: 「差分ゲート」「閾値ゲート」「ゲート」呼びをやめる方向(概要は「公開前検査」に統一済み、フィードバック反映)。本文は §1 で「公開前検査(diff guard)」と一度定義し、以後「検査」または「diff guard」で通す案。タイトルの「公開前差分ゲート」も要修正
- [ ] 欧文語のカタカナ化を本文でも統一(概要は advisory→アドバイザリ対応済み)。本文に advisory 表記が多数残存。fixture, baseline, target, promote, grooming 等をどこまで開くかも方針を決める(固有名詞・コマンド名は英字のまま)
- [ ] 「抽出器」「ビルダ」の初出定義を本文で明示(概要からは排除済み、フィードバック反映)。§2.1 の fetch / extract / db build 工程と語の対応(抽出器 = extract 工程のコード、ビルダ = db build のコード)を §2.1 か §4 の初出で一言定義する
- [ ] タイトル確定 — 和文・英文セットで(冒頭コメントに和文代案 2 つ、概要直下に英文案。用語統一を反映して再検討)
- [ ] 和文概要を修正したら英文 Abstract も追従させる(概要直下に併記済み)
- [ ] 観測期間を投稿時点まで延長するか決める — 現本文は 82 日 / 671 run / 50 episode(〜07-14)固定。A-18〜A-21(07-15〜07-26)を含めるなら `stats.py` を `guard-failures.tsv` に再実行して全数値を更新
- [ ] 図 4 枚の作成(方針決定済み: 人間の手描きはしない。図 1 = TikZ、図 2〜4 = matplotlib でベクタ PDF 生成):
  - 図 1: パイプライン全体図 + ガード挿入位置 + 各工程の履歴 — **TikZ**(standalone クラスで単体プレビュー可、本文 TeX 化を待たず着手できる)
  - 図 2: 導入前 44 日ベンチマークの drift 時系列 — matplotlib(データ: diff-guard.md の 35 ペア表)
  - 図 3: 発動ガントチャート — matplotlib(データ: guard-failures.tsv / stats-output.txt の 50 episode)
  - 図 4: 変動率ヒストグラム対数軸・二峰性 — matplotlib(データ: guard-failures.tsv 1,040 行)
  - いずれもスクリプト/ソース管理し、観測期間延長時に再実行で追従させる
- [ ] triage の AI 委任を本文に明記するか検討 — 現状は「AI エージェントには調査支援まで許し promote は実行させない」という制限側の記述のみ(§3.3, §6.6)。実運用では帰属手順を skill 化した AI エージェントが triage を実施し人間がレビューしている。書くなら §4 の手順書共有のくだり(「手順は AI エージェント用スキルとしても整備され、triage の一次調査は AI が実施する」等)+ §6.6 の役割分担と接続。概要には入れない(決定済み)
- [ ] 関連研究: 国内先行(CSS/SCIS 予稿)の手動確認(web 索引に乗らないため未調査)
- [ ] 発動事例の全数データの公開方法を決める(付録 5 ページ枠 or 公開リポジトリ参照)
- [ ] 著者・所属の確認(昨年論文と同体制か)

**TeX 化時**
- [ ] 情報処理学会様式へ転記。この md は構成・文章のソースであり最終稿ではない
- [ ] 本文中の em-dash(「〜 — 〜」挿入構文)を句読点や接続詞に書き換える(概要は対応済み。§1, §4, §5, §6 に残存)
- [ ] 本文の「・」を整理(概要は対応済み)。方針: 2 項並列は「と」「か」、3 項以上は読点+「および」か「〜や〜といった」、複合名詞を含む列挙には使わない。残すのは外来語や人名の区切りと 1 語同士の同種並列のみ(例: 「収集・変換・構築」は 1 語同士なので可、「検知結果・検知条件構造」型は不可)
- [ ] run ID / digest / URL を脚注または付録参照へ落とす
- [ ] 参考文献 27 件を様式整形。分量超過時の削減候補: nguyen13, wunder24, croft23
- [ ] 本文中の [css2025] 等の仮キーを正式な引用番号へ
- [ ] 図参照(図 1〜4)とプレースホルダの差し替え

---

**概要**: 脆弱性データベースは多数の上流データソースを集約して構築されるが、上流は必ずしも安定せず、データの消失や公開済みアドバイザリの遡及的な書き換えが現実に起きている。本研究では、この不安定性を定量観測するため、OSS 脆弱性スキャナ Vuls の DB 公開 CI に公開前検査を実装した。検査は公開候補と直前の公開版を、検知結果と検知条件構造の 2 観点で比較し、変動率が閾値を超えた場合は公開を保留して人間の確認に委ねる。82 日間の本番運用の全数調査では 50 件の独立イベントで検査が発動し、全工程を履歴管理する既報の基盤を用いて、その全てについて原因が上流データの変化か、変換や DB 構築といった自前の処理かを切り分けて特定できた。日常変動と構造的イベントは変動率で桁が分離しており、閾値による単純な判定が実用になること、また欠損 DB の公開を 3 回阻止したことを示す。

<!-- 用語メモ(2026-07-29 フィードバック反映): 概要では「差分ゲート」の造語をやめ
「公開前検査」に統一。「閾値ゲート」という第二の呼び名も排除(→「閾値による単純な判定」)。
本文はまだ「ゲート/diff guard」呼びのまま — 統一方針は TODO 参照。 -->

**英文タイトル(案)**: Measuring Upstream Instability of Vulnerability Information: An 82-Day Exhaustive Study of Pre-Publication Inspection on a History-Managed Database Pipeline

**Abstract**: Vulnerability databases are built by aggregating many upstream data sources, but these upstreams are not always stable: data disappears, and published advisories are retroactively rewritten. To quantify this instability, we implemented a pre-publication inspection in the CI pipeline that builds and publishes the database of Vuls, an open-source vulnerability scanner. The inspection compares each publication candidate with the previously published version in terms of detection results and detection-criteria structure, and when the change rate exceeds a threshold, it withholds publication pending human review. In an exhaustive study covering 82 days of production operation, the inspection fired on 50 independent events, and our previously reported infrastructure, which keeps every pipeline stage under version control, allowed us to attribute every event to either upstream data changes or our own processing such as data transformation and database construction. We show that everyday fluctuation and structural events are separated by an order of magnitude in change rate, making this simple threshold-based inspection practical, and that the inspection blocked the publication of defective databases three times.

<!-- 英文は和文概要(現行版)の忠実訳。和文を直したら英文も追従させること。
タイトル和英とも未確定(用語統一 TODO と連動)。 -->

<!-- 概要の文体メモ: em-dash(—)は和文では使わない方針(ユーザー指摘)。本文にも
「〜 — 〜」構文が複数残っているので、TeX 化時に一掃する(TODO 参照)。
triage 手順の SKILL 化は概要では触れない(本文 §4 / §6.6 で受ける)。 -->

---

## 1. はじめに

脆弱性対応の実務は、ディストリビュータやベンダーが公開する advisory・脆弱性フィードを「正」として組み立てられている。脆弱性スキャナはこれらを集約した脆弱性データベース(以下、脆弱性 DB)に依存し、検知結果はフィードの内容をほぼそのまま反映する。ここで暗黙に置かれている仮定 — 上流フィードは概ね安定しており、変化は新規脆弱性の追加という単調な形をとる — は、どの程度正しいのだろうか。

我々は OSS 脆弱性スキャナ Vuls [vuls] のエコシステムにおいて、40 超のデータソースから脆弱性 DB(vuls.db)を CI で自動ビルドし、6 時間おきに公開している。昨年の本シンポジウムでは、この収集(fetch)・変換(extract)・構築(db build)の全工程をバージョン管理システムと連携させ、脆弱性情報の変更履歴を客観的事実として追跡・再現可能にする履歴管理基盤を報告した [css2025]。本稿はその続編にあたる。昨年の基盤が「脆弱性情報の変化を*記録できる*」ことを示したのに対し、本稿はその記録能力を使って「上流は実際に*どう変化しているか*」を系統的に測定し、さらにその測定を DB の公開品質管理(公開前ゲート)として実用化した結果を報告する。

測定の装置は単純である。公開直前の候補 DB を、現に公開されている直前版(baseline)と自動比較し、変動率が閾値を超えたら公開をブロックして人間に見せる — 我々はこれを diff guard と呼ぶ。導入の直接の動機は、上流の破損データとパイプライン変更の複合、および DB とスキャナのバージョン非互換によって「壊れた DB」を公開してしまった 2 件のインシデント(§2.2)であり、ゲートは第一義には安全ネットである。しかし 82 日間の本番運用で得られた発動記録の全数調査は、副産物として、脆弱性情報の上流がいかに大きく・頻繁に・時に黙って動くかの縦断観測データとなった。

本稿の貢献は次の 3 点である。

1. **上流不安定性の実測**(§5, §6): 82 日間・671 run の全数調査により、上流フィードの不安定性を 50 件の独立イベントとして分類・定量化した。観測されたイベントは、可用性の不安定(月次データの消失とフラッピング)、完全性の危うさ(遡及的な再キュレーション、アナウンスなきサーバ側再編)、スケールの分布(日常変動と構造的イベントの桁分離)の 3 群に整理できる。これらの上流は他の脆弱性ツール(Trivy、Grype、OSV 系等)も共有しており、知見はエコシステム横断で再利用可能である。
2. **原因帰属の方法論**(§4): 発動の原因をビルダ → 抽出器 → 上流の順に容疑を除外して確定する切り分け手順を定義し、全イベントに適用した。各ステップは履歴管理基盤 [css2025] の対応する工程の履歴(DB メタデータ、抽出器のコミット履歴、raw データの Git 差分)に依拠しており、全工程の履歴管理が帰属の成立条件であることを示す。
3. **公開前差分ゲートの設計と運用機構**(§3): 検知結果差分と DB 構造差分の 2 観点によるゲート本体に加え、監査証跡付き手動 override(promote)、対象別閾値の統計的導出と定期的な再導出(grooming)という、ゲートを運用し続けるための機構を設計・実装した。ゲートは欠損 DB の公開を 3 回阻止した。

> **[図 1 予定]** 全体アーキテクチャ。上流 40+ ソース → fetch / extract / db build(各工程 Git 履歴管理 [css2025])→ **diff guard** → GHCR 公開 → スキャナ。diff guard の挿入位置、FAIL 時に候補が tagless で残るフロー、および切り分け手順(§4)が参照する各工程の履歴を 1 枚に示す。

## 2. 背景

### 2.1 履歴管理基盤(昨年報告)の要点

vuls.db の生成は 3 工程からなる [css2025]。fetch 工程は一次情報源から取得したデータを原形をほぼ保った vuls-data-raw 形式で、extract 工程はそれを共通スキーマの vuls-data-extracted 形式で、それぞれ Git 管理下に置く。db build 工程は extracted データから BoltDB 形式の vuls.db を構築し、コンテナレジストリ(GHCR)にタグおよび digest で公開する。この構成により、(1) 任意時点の上流データの状態をコミット単位で遡れる、(2) DB を digest で固定して検知結果を再現できる、という 2 つの性質が得られている。本稿の測定はこの 2 性質の直接の応用である。

### 2.2 動機となった 2 つのインシデント

2026 年 3 月、生成物としての DB が壊れているのに公開が成功してしまう事象を 2 件経験した。

**インシデント 1(RHEL VEX、false negative)**: パイプラインにデータ形式変更を投入したのと同じ日に、Red Hat が壊れた VEX データを配信した。抽出処理はエラー終了してデータが旧形式のまま残り、新形式を前提とする後段フィルタが空データを生成した。結果、redhat:9 で本来検知されるべき CVE の 51.9%(3,387 件)が「影響なし」となる DB が公開された。

**インシデント 2(Ubuntu `vulnerable: false`、false positive)**: DB 側に導入されたマーカを、それを解釈するフィルタを持たない旧バージョンのスキャナが読んだ結果、ubuntu_2204 の検知件数が 5,968 → 12,296 件(+106.0%)に倍増した。DB 単体でもスキャナ単体でも正常であり、組み合わせの非互換が原因である。

従来の CI が検査するのはビルドの成否であって、生成物のデータとしての妥当性ではない。また 2 件は対照的で、前者は DB 単体を見れば検出できるが、後者は DB とスキャナ(の特定バージョン)の組で実行しなければ検出できない。この 2 面性が次章の設計に直結する。

## 3. diff guard の設計

### 3.1 導入前ベンチマーク — 閾値ゲートの成立可能性

脆弱性 DB は日々更新されるため差分ゼロはあり得ず、閾値ゲートが成立するには正常な変動と異常なイベントが変動率で分離する必要がある。導入前に、GHCR 上に履歴として残っている過去 37 日分の nightly DB(2026-02-15〜03-29)を用い、連続 1 日ペア 35 組で DB 構造差分を実測した。通常運用の変動率は中央値 0.3%・最大 6.2% に収まり、期間中に 10% を超えた 2 組はいずれも実在の上流データ品質イベント(Red Hat VEX 構造変更で redhat:6 65.1%、SUSE OVAL 大規模更新で 12〜16%)であった。正常帯と異常イベントが桁で分離するというこの観測が、閾値ゲート成立の根拠である。なお、過去任意時点の DB ペアでこの種のベンチマークが実行できること自体、公開物が digest 付きで履歴化されている [css2025] ことの恩恵である。

> **[図 2 予定]** 導入前ベンチマークの日次変動率時系列(35 ペア)。中央値 0.3% / 最大 6.2% の正常帯と、2 件の上流イベント(65.1% / 12〜16%)が桁で分離することを示す。

### 3.2 3 つのチェック

公開 CI の圧縮後・公開前に、次の 3 チェックを実行する(以下 M / O / D と略記)。

- **M — 検知結果差分(スキャナ最新版)**: baseline / target 両 DB に対して同一のスキャン結果 fixture 群(実機スキャン由来、数十ファイル)でスキャナを実際に実行し、ファイル単位で検知 CVE 集合を比較する。変動率は (added + removed) / baseline で定義する。
- **O — 検知結果差分(固定した旧バージョンのスキャナ)**: 過去バージョンとの組でのみ現れる非互換退行(インシデント 2 型)を捕捉する。
- **D — DB 構造差分**: BoltDB を直接開き、ecosystem(後に source 単位へ細分化)ごとに検知条件木を leaf Criterion レベルまで平坦化して構造比較する。スキャン結果もスキャナも不要で DB のみで完結する。比較粒度を bytes ではなく Criterion にしたのは、JSON キー順などの無害な変更での偽陽性を避けつつ、分母(全体で約 330 万 Criterion)を大きく取り正常変動を小さな drift として吸収するためである。

チェック結果は変動率・増減の内訳・変動した CVE/advisory ID を含む構造化された Markdown レポートとして常に CI の Job Summary に出力される。これは昨年課題として挙げた「行ベース差分ではなく論理的な構造としての差分提示」[css2025, §5.2] の、公開品質管理という文脈での実装形でもある。導入当初は最初の FAIL でゲートが停止する実装だったが、先に FAIL したチェックが後段のシグナルを隠す問題が判明し(§6.4)、現在は 3 チェックすべてを実行してから集約判定する。

### 3.3 FAIL 時の運用 — 監査証跡付き手動 promote

候補 DB はゲート実行前に digest のみ(tagless)で GHCR に push しておき、PASS 時にのみタグを付けて「公開」する。FAIL した場合、候補は untagged のまま digest で取得可能な状態で残るため、事後検証が可能である。オペレータがレポートを確認し正当な変更と判断した場合は、専用 workflow で該当 digest に手動でタグ付けする(promote)。実行者・digest・タグが run 履歴に残り、「誰が何を根拠に override したか」が追跡できる。運用ルールとして、promote の判断・実行は人間に限定している(調査を支援する AI エージェントには実行させない)。

### 3.4 閾値の per-target / per-source 化と grooming

閾値はデフォルト detection 5% / db 10% とし、運用実績に基づき対象別に緩和する override 機構を持つ。導入 1 ヶ月の運用で、新ディストリビューション立ち上がり期の一括 triage、rolling release、ベンダー月次サイクルといった反復的な正当変動が毎回ゲートに引っかかることが判明したためである。override 値は失敗履歴の統計から「観測ピーク + ヘッドルーム」で導出し、単発スパイクは override せず fail させて人間に見せる(例: EOL ディストリビューションが 39% 動くのは異常として意図的に残置)。リストの陳腐化を防ぐため約 2 ヶ月周期で全再導出する(grooming)。さらに運用後期、ecosystem 一括の変動率では大きなソースがノイズフロアになって小さなソースの異常を希釈する問題が顕在化し(§5.3)、閾値・レポートともソース単位(`<ecosystem>/<source>`)に細分化した。

## 4. 測定方法論 — 全数調査と原因帰属

**全数調査**: 本番導入(2026-04-23)から 07-14 までの 82 日間、2 系統(安定版 / nightly)の全 671 run を対象に、run ログ・PR・promote 履歴を GitHub API で全数収集した。FAIL 中は promote があるまで baseline が動かず、同じ差分で 6 時間おきの cron が再 FAIL し続けるため、run 数は重複を含む。そこで連続 FAIL を 1 つに潰した fail sequence(66 件)、さらに 2 系統を束ねソース単位の出現時系列で分解した source-episode(**50 件**)を独立イベントの単位として定義した。

**原因帰属**: 各イベントについて、次の順で容疑を除外して原因を確定する。

1. **ビルダ除外**: baseline / target 両 DB のメタデータに記録されたビルダのバージョン(`created_by`)を比較する。一致すれば DB 構築コードは無罪。
2. **抽出器除外**: 対象期間の抽出器リポジトリのコミット履歴を走査する。当該ソースの fetch / extract コードに変更がなければ変換コードは無罪。
3. **上流確定**: raw データの Git 履歴から対象期間のコミットを特定し、差分の中に変動と件数・ID が一致する変更実体(smoking gun — 例: 新規 advisory ファイル群、ディレクトリの消失)を突き止める。

この手順の各ステップは、履歴管理基盤 [css2025] の対応する工程の履歴にそれぞれ依拠している。ビルダ除外は DB メタデータ、抽出器除外はコードのコミット履歴、上流確定は raw / extracted データの Git 履歴である。全工程が履歴化されていなければ、例えば「上流の一時障害なので候補を破棄すべき」と「正当な変更なので promote してよい」の区別(§5.2)は当て推量になる。逆に言えば、履歴管理は本測定の成立条件であり、昨年基盤の実証でもある。実際、全 50 イベントで帰属は完了し、「原因不明」は残らなかった。また帰属手順は再現可能な triage 手順書として整備し、チームで共有している。

## 5. 運用結果

### 5.1 規模と原因分布

671 run 中、失敗は 339 run。うち 295 run がゲートのステップで失敗した(閾値超過 293 + ゲート内インフラ障害 2)。独立イベントは 50 source-episode、事例カタログとしては約 21 イベント(複数ソースの同時多発を 1 事例に束ねた粒度)である。原因の分布を表 1 に示す。

**表 1: 原因帰属の分布(事例単位)**

| 判定 | 件数 | 代表例 |
|---|---|---|
| 上流由来 (a) 正当な変更 | 約 15/21 | 月次パッチ、新ディストリ立ち上がり、マス更新 |
| 上流由来 (b) 一時的データ障害(**公開阻止**) | 2 | Microsoft CVRF 月次データ消失 ×2 |
| 上流由来 (c) 恒久的データ品質イベント | 2 | AlmaLinux errata 再キュレーション |
| 抽出器由来・コードバグ(**公開阻止**) | 1 | 出力順の非決定化バグ |
| 抽出器由来・意図的変更 | 1 | CPE マッチ品質分類の導入(実験系統先行) |
| ビルダ由来 | 0 | (2 件で精査したがいずれも無罪) |

> **[図 3 予定]** 82 日間の発動タイムライン。横軸日付、縦軸ソース(ubuntu / microsoft / suse / rocky / alma / oracle / amazon / fedora / cpe / redhat / debian)、各 episode を持続時間の横棒で示すガントチャート。promote 時刻と override 導入時点を縦線で重ねる。

### 5.2 実害を防いだ 3 事例

1. **Microsoft CVRF 月次データ全消失(2 回)**: 上流 API が当月分のセキュリティ更新ドキュメント(700〜1,300 ファイル)を丸ごと返さなくなり、Windows 系 13 ターゲットで最大 53.6% の削除のみの差分が発生した。公開されていればインシデント 1 と同型の大量 false negative である。ゲートは候補を破棄させ、上流回復後の再実行のみで復旧した。raw 履歴上、当月ファイル数は 1273 → 0 → 1273 → 0 → 1278 とフラッピングしており、単発の取得失敗ではなく上流配信自体の不安定であった(フラップの各時点がコミットとして残っているため、この認定自体が履歴管理の産物である)。
2. **抽出器の非決定性バグ**: raw の変更は 266 ファイルなのに extracted は 23,163 ファイル動くという異常を D チェックが 274.5% の drift として検出した。原因は抽出器が型の取り違えでソート処理をスキップし出力順序が非決定になっていたことで、修正 PR に帰結した。期間中唯一の「上流のせいではないコード起因の異常」の捕捉である。
3. **(限定的)VulnCheck 一斉ロールアウト**: 単一コミットで 145,672 ファイル・+957 万行という生成 CPE 設定の一斉付与を D チェックが検出した。ただし当時の ecosystem 一括の変動率では「cpe 28.9%」としか言えず、候補は promote された。事後のソース単位の再分析で、当該ソース単独では 189.6% の変動であり、かつ実検知が 60〜75% 消失する退行を含んでいたことが判明した。この教訓がソース単位への細分化(§3.4)の直接の動機である。「発動したが分解能不足で判定を誤りかけた」事例として記録する。

### 5.3 false positive 論と運用ループ

発動の大半は正当な上流変更であり、これを「誤報」と見るかは設計思想による。本ゲートは安全ネットであり、822 CVE を単一 advisory に同梱するカーネル更新や、約 600 パッケージを束ねた単一 advisory(5,312 検知条件)のマス更新は、正当であっても公開前に人間が一目見るに値する。一方、反復性が確立した既知の変動は override で恒久緩和する。82 日間の手動 promote は 59 unique digest あり、その **100% がゲート FAIL run の候補 digest と一致**した — 「ゲート → 人間のレポート確認 → 監査証跡付き override」というループが例外なく回っていたことを示す。

## 6. 考察 — 観測された上流の危うさ

### 6.1 消える・戻る・また消える(可用性)

月次データの丸ごと消失(§5.2)は 2 ヶ月連続で発生し、2 回目は 2 日間に消失と復活を 4 回繰り返した。フィードの取得は「ある時点のスナップショット」であり、欠損の瞬間を取り込めばビルドは成功したまま欠損 DB ができあがる。公開前の差分検査なしにこれを防ぐ手段は事実上ない。

### 6.2 遡及的に書き換わる(完全性・一貫性)

- **errata の再キュレーション**: AlmaLinux の errata feed が 1 週間に複数回再編成され、advisory 数が 279 → 一時 60 まで減少、削除された advisory が参照する CVE の 87%(376 件)がフィードから完全消失した。生き残った advisory も、kernel 更新の検知条件が 73 → 2 パッケージへ縮退する「骨抜き」を伴った。過去にも同様のパージ実績がある反復性の高い上流運用である。対応として、劣化ソースの取り込みを commit 単位でピン留めし、代替ソース(OVAL)の抽出器を整備してから計画的にアンピンした — ピン留めという対応自体、取り込みが履歴管理されているから可能な操作である。
- **サイレントなサーバ側再編**: Cisco openVuln API では、advisory の更新日時もバージョンも一切変わらないまま、advisory と影響バージョンのマッピングだけが日次で書き換わり、93 advisory から製品バージョン 2,022 件が削除された(例: 2014 年の advisory の製品リストが 149 → 36)。changelog にも issue にもアナウンスはない。過剰マッピングの整理というデータ品質改善の側面が強い一方、該当バージョンを監視している利用者には黙った検知消失となる。
- **一斉再生成の両義性**: VulnCheck の全年代 CVE への生成 CPE 一括付与(§5.2)は情報の拡充である一方、CPE 語彙の現代化により既存のマッチングから外れる検知退行を同時に含んでいた。2 週間後、上流側の修正により退行の一部は「回復イベント」としてもう一度ゲートを発動させた。拡充・退行・回復のいずれもが大変動として観測される。

### 6.3 正当でも桁違いに動く(スケール)

観測された最大変動率は 428.3%(AlmaLinux 再キュレーション)、305.9%(CPE 系)、274.5%(抽出器バグ)に達する一方、日常変動は 5〜20% 帯に収まり、両者は概ね桁で分離する — 導入前ベンチマーク(§3.1)の観測が本番でも維持されたことになり、これが単純な閾値ゲートが実用になる理由である。ただし分離が崩れる構造要因が 2 つある。(1) baseline が小さい対象は 1 バッチの正当な追加で容易に 100% を超える。(2) FAIL で baseline が停滞すると比較窓が伸び、日常変動が蓄積して閾値を超える。前者は per-target 閾値、後者は迅速な promote 運用で吸収している。

> **[図 4 予定]** 全 FAIL 行(1,040 行)の変動率ヒストグラム(対数軸)。日常変動帯(5〜20%)と構造イベント帯(100% 超)の二峰性、および閾値(5% / 10%)と override 値の位置を示す。

### 6.4 ゲート自身の盲点と改良

運用はゲート自身の弱点も露呈させた。(1) Windows 更新プログラム(KB)の比較はキー集合しか見ておらず、CVE エントリの大量消失時に 0% を返した(「0% ≠ 変化なし」)。(2) 導入初期は最初の FAIL で停止する実装で、先に FAIL したチェックが別の異常を隠した(→ 全チェック実行+集約へ)。(3) ecosystem 一括の変動率は大ソースが小ソースの異常を希釈した(→ ソース単位へ細分化)。(4) override の系統間非対称が片系統だけの慢性 FAIL を生んだ(→ grooming で両系統を同時に見る)。ゲートは一度作って終わりではなく、発動事例からのフィードバックで分解能と運用を継続的に改良する対象である。

### 6.5 運用コストの実態

run 単位の FAIL の 52% は土日に発生しているが、これは上流ではなく人間側の信号である — promote が平日日中にしか行われないため、金曜夕方以降のイベントが週末じゅう再 FAIL し続ける(週末滞留)。fail sequence の持続時間(中央値 11h / p90 48h)はゲートの検出性能ではなくオペレータの応答時間の分布を測っており、通知・承認フローの自動化余地を見積もる直接の根拠となる。

### 6.6 開発プロセスに対する最終ガードレールとしての価値

本ゲートの副次的だが実感の大きい価値として、パイプライン開発の最終防衛線としての機能がある。ユニットテストやコードレビューが工程ごとのコードの正しさを検査するのに対し、データパイプラインの意味的な正しさは集約後の出力でしか観測できない。実際、型の取り違えによるソート処理の欠落(§5.2)はコンパイルもテストも通過する類のバグであり、出力の構造差分としてのみ顕在化した。また運用上は、実験系統(nightly)に破壊的変更を先行投入しゲートで影響規模を定量観測してから安定版へ降ろす、変更前から FAIL を予期しその発現範囲が想定に閉じていることを混入なしの証拠として使う(§6.2 のピン解除)、といった能動的な使い方も定着した。この「作られ方に依存せず生成物を検証する」性質は、AI エージェントによるコード生成が開発の速度と量を押し上げる今後、コードレビューのスケール限界を補う出力レベルのガードレールとして重要性を増すと考える。なお本運用では、ゲート越えの判断(promote)は人間に限定し、AI エージェントには調査支援までを許している(§3.3)— 生成は速く、検証は出力で、承認は人間で、という役割分担である。

## 7. 関連研究

<!-- 全文献は 2026-07-29 に web 調査で実在確認済み(書誌・URL は参考文献欄)。
国内先行(CSS/SCIS 予稿)は web 索引が弱く網羅できていない — 手動確認の余地あり。
分量調整で落とす候補: nguyen13, wunder24, croft23(ICSE 2023, 研究用データセットの品質)-->

**脆弱性データベースの品質**: NVD をはじめとする脆弱性 DB の品質は繰り返し測定されてきた。CVE/NVD と外部レポート間の影響バージョン不整合の大規模検出 [dong19]、NVD・JVNDB・CNVD の登録プロセスとカバレッジの比較 [lin26]、NVD コーパスの品質監査と自動修正 [anwar22]、影響バージョン情報の実地検証 [nguyen13]、CVSS 付与遅延の回帰分析 [ruohonen19]、NVD 利用者の定性調査 [wunder24] などがある。また、同一対象に対するスキャナ・SCA ツール間の検知結果の大きな不一致が、参照する脆弱性 DB の差に相当程度帰着することも示されている [imtiaz21, churakova25]。2024 年の NVD enrichment 停滞は産業側の分析でも定量化された [vulncheck24, anchore25]。これらはいずれもフィードを外部から静的に — スナップショット間比較、コーパス監査、回顧的分析として — 測定するものである。本稿はこれに対し、測定器を本番の取り込み・公開パイプラインに常設し、フィード内容の経時変化そのものを下流消費者の視点で縦断観測した点で異なる。

**セキュリティデータフィードの品質測定**: 脅威インテリジェンスフィードについては、量・カバレッジ・遅延・正確性等の指標による比較測定が行われ、フィード間の重複の少なさや、消費者にとって品質が不可視であることが示されている [li19, bouwman20, griffioen20]。フィードの内容品質を測るという点で方法論的に本稿へ最も近い系譜だが、いずれも外部の研究として実施された横断測定である。本稿は、単一フィードを自身の公開履歴と比較する縦断測定を、公開をブロックする運用機構として常設した点が新しい。

**ソフトウェアサプライチェーン保全**: SLSA [slsa]、in-toto [torres19]、reproducible builds [lamb22]、Sigstore [newman22]、TUF [samuel10] は、artifact の来歴・ビルド完全性・署名・配布を保護する枠組みである。これらは「正規の上流から正規の手順で作られ、改竄されていないこと」を保証するが、正規に取得され正しく署名された DB の内容が、上流の劣化により意味的に欠損していても全チェックを通過する。本稿のゲートは、これらの枠組みが守る来歴・完全性レイヤの上に、データ内容の意味レイヤの検証を積む補完関係にある。

**データパイプラインの検証**: 宣言的制約によるデータ品質検証 [schelter18, breck19] に加え、パイプライン自身の実行履歴から検証基準を自動導出する研究 [tu23, redyuk21]、新しいデータバッチが履歴から逸脱した際に下流の ML 再学習をブロックするゲート [shankar23] があり、特に後者は「履歴との比較で公開・利用を止める」という意味論まで本稿と同型である。テスト理論の観点では、本稿のゲートは前公開版を比較対象(オラクル)とする differential testing [mckeeman98] の時間軸変種、あるいはデータ artifact に対する回帰テスト [yoo12] の適用とみなせる。これらとの差分は、(1) 列統計ではなく検知結果・検知条件構造という意味レベルの差分を取ること、(2) セキュリティクリティカルな公開物を対象に、監査証跡付きの human-in-the-loop override を備えること、(3) ゲートの発動記録そのものを上流不安定性の測定データとして全数分析したこと、の 3 点である。

## 8. おわりに

脆弱性 DB の公開 CI に公開前差分ゲートを実装し、82 日間・671 run の全数調査を通じて、脆弱性情報の上流ソースの不安定性を 50 件の独立イベントとして定量観測した。上流は消え、戻り、遡及的に書き換わり、アナウンスなく再編される — そしてその大半は「正当」である。得られた知見は次の通りである。(1) 正常変動と異常イベントは変動率で概ね桁分離し、単純な閾値ゲートが実用になる。ただし分解能(ソース単位)と閾値(対象単位の override + 定期 grooming)は運用実績から継続的に導出する必要がある。(2) 発動原因の帰属は、収集・変換・構築の全工程が履歴管理されていることを成立条件とする。昨年報告した履歴管理基盤 [css2025] は、本測定と公開品質管理の土台として実証された。本稿は同論文が課題として挙げた「差分の論理的な提示」「パイプラインの堅牢化」への、運用を伴う一つの回答でもある。(3) FAIL 時の復旧は「人間によるレポート確認 + 監査証跡付き override」として設計すべきで、本運用では全 override がこのループに乗った。(4) 上流の恒久的劣化には、取り込みのピン留めと代替ソース整備という出口が要る。(5) 生成物を出力レベルで検証するゲートは、上流だけでなく自らの開発プロセスに対する最終防衛線としても機能し、テストとレビューをすり抜ける意味的バグの捕捉や、破壊的変更の影響範囲の定量確認に実際に寄与した — コード生成に AI が入り込む開発形態において、この価値は今後増すと考える。

今後の課題として、fetch 段階での欠損検出(月次ドキュメント丸ごと消失時に commit しない等)、通知・承認フローの改善による週末滞留の解消、観測の長期蓄積による時系列特性(月次サイクル等)の統計的確立、および同一上流を消費する他エコシステムとの観測の突合が挙げられる。

## 参考文献

<!-- 全エントリ 2026-07-29 に出典ページで実在確認済み。TeX 化時に情報処理学会様式へ整形。 -->

**自著・システム**
- [css2025] 中岡典弘, 篠原俊一: 広範な脆弱性情報の統合管理と履歴追跡, コンピュータセキュリティシンポジウム 2025 (CSS 2025).
- [vuls] Vuls: VULnerability Scanner. https://github.com/future-architect/vuls
- vuls-data-update / vuls2 / vuls-data-db(vulsio, MaineK00n)各リポジトリ
- 発動事例の全数データ(run 表・promote 履歴・機械可読 TSV): 公開方法は要検討(付録 or リポジトリ参照)

**脆弱性 DB の品質**
- [dong19] Y. Dong, W. Guo, Y. Chen, X. Xing, Y. Zhang, G. Wang: Towards the Detection of Inconsistencies in Public Security Vulnerability Reports, USENIX Security 2019, pp. 869–885. https://www.usenix.org/conference/usenixsecurity19/presentation/dong
- [lin26] J. Lin, X. W. Wang, G. Stringhini, M. Egele: A Comparative Analysis of NVD, JVNDB and CNVD: Insights into Global and Regional Vulnerability Reporting, ACM ASIA CCS 2026. https://doi.org/10.1145/3779208.3806085
- [anwar22] A. Anwar, A. Abusnaina, S. Chen, F. Li, D. Mohaisen: Cleaning the NVD: Comprehensive Quality Assessment, Improvements, and Analyses, IEEE TDSC, vol. 19, no. 6, 2022. https://doi.org/10.1109/TDSC.2021.3125270
- [nguyen13] V. H. Nguyen, F. Massacci: The (Un)Reliability of NVD Vulnerable Versions Data: An Empirical Experiment on Google Chrome Vulnerabilities, ACM ASIA CCS 2013, pp. 493–498. https://doi.org/10.1145/2484313.2484377
- [ruohonen19] J. Ruohonen: A Look at the Time Delays in CVSS Vulnerability Scoring, Applied Computing and Informatics, vol. 15, no. 2, 2019. https://doi.org/10.1016/j.aci.2017.12.002
- [wunder24] J. Wunder, A. Corona, A. Hammer, Z. Benenson: On NVD Users' Attitudes, Experiences, Hopes, and Hurdles, ACM DTRAP, vol. 5, 2024. https://doi.org/10.1145/3688806
- [imtiaz21] N. Imtiaz, S. Thorn, L. Williams: A Comparative Study of Vulnerability Reporting by Software Composition Analysis Tools, ESEM 2021. https://doi.org/10.1145/3475716.3475769
- [churakova25] Y. Churakova, M. Ekstedt, L. Schmid: Vexed by VEX Tools: Consistency Evaluation of Container Vulnerability Scanners, arXiv:2503.14388, 2025. https://arxiv.org/abs/2503.14388
- [croft23] R. Croft, M. A. Babar, M. M. Kholoosi: Data Quality for Software Vulnerability Datasets, ICSE 2023, pp. 121–133. https://doi.org/10.1109/ICSE48619.2023.00022(分量次第で省略可)
- [vulncheck24] VulnCheck: The Real Danger Lurking in the NVD Backlog, 2024. https://www.vulncheck.com/blog/nvd-backlog-exploitation
- [anchore25] Anchore: The NVD Enrichment Crisis: One Year Later, 2025. https://anchore.com/blog/nvd-crisis-one-year-later/

**セキュリティデータフィードの品質測定**
- [li19] V. G. Li, M. Dunn, P. Pearce, D. McCoy, G. M. Voelker, S. Savage, K. Levchenko: Reading the Tea Leaves: A Comparative Analysis of Threat Intelligence, USENIX Security 2019, pp. 851–867. https://www.usenix.org/conference/usenixsecurity19/presentation/li
- [bouwman20] X. Bouwman, H. Griffioen, J. Egbers, C. Doerr, B. Klievink, M. van Eeten: A different cup of TI? The added value of commercial threat intelligence, USENIX Security 2020. https://www.usenix.org/conference/usenixsecurity20/presentation/bouwman
- [griffioen20] H. Griffioen, T. Booij, C. Doerr: Quality Evaluation of Cyber Threat Intelligence Feeds, ACNS 2020, LNCS 12147, pp. 277–296. https://doi.org/10.1007/978-3-030-57878-7_14

**ソフトウェアサプライチェーン保全**
- [slsa] OpenSSF: SLSA — Supply-chain Levels for Software Artifacts. https://slsa.dev(仕様、アクセス日付を付す)
- [torres19] S. Torres-Arias, H. Afzali, T. K. Kuppusamy, R. Curtmola, J. Cappos: in-toto: Providing farm-to-table guarantees for bits and bytes, USENIX Security 2019, pp. 1393–1410. https://www.usenix.org/conference/usenixsecurity19/presentation/torres-arias
- [lamb22] C. Lamb, S. Zacchiroli: Reproducible Builds: Increasing the Integrity of Software Supply Chains, IEEE Software, vol. 39, no. 2, 2022, pp. 62–70. https://doi.org/10.1109/MS.2021.3073045
- [newman22] Z. Newman, J. S. Meyers, S. Torres-Arias: Sigstore: Software Signing for Everybody, ACM CCS 2022. https://doi.org/10.1145/3548606.3560596
- [samuel10] J. Samuel, N. Mathewson, J. Cappos, R. Dingledine: Survivable Key Compromise in Software Update Systems, ACM CCS 2010, pp. 61–72. https://doi.org/10.1145/1866307.1866315

**データパイプラインの検証**
- [schelter18] S. Schelter, D. Lange, P. Schmidt, M. Celikel, F. Biessmann, A. Grafberger: Automating Large-Scale Data Quality Verification, PVLDB, vol. 11, no. 12, 2018, pp. 1781–1794. https://doi.org/10.14778/3229863.3229867
- [breck19] E. Breck, M. Zinkevich, N. Polyzotis, S. E. Whang, S. Roy: Data Validation for Machine Learning, MLSys (SysML) 2019. https://proceedings.mlsys.org/paper_files/paper/2019/hash/928f1160e52192e3e0017fb63ab65391-Abstract.html
- [tu23] D. Tu, Y. He, W. Cui, S. Ge, H. Zhang, S. Han, D. Zhang, S. Chaudhuri: Auto-Validate by-History: Auto-Program Data Quality Constraints to Validate Recurring Data Pipelines, KDD 2023. https://doi.org/10.1145/3580305.3599776
- [redyuk21] S. Redyuk, Z. Kaoudi, V. Markl, S. Schelter: Automating Data Quality Validation for Dynamic Data Ingestion, EDBT 2021, pp. 61–72.
- [shankar23] S. Shankar, L. Fawaz, K. Gyllstrom, A. G. Parameswaran: Moving Fast With Broken Data, arXiv:2303.06094, 2023. https://arxiv.org/abs/2303.06094
- [mckeeman98] W. M. McKeeman: Differential Testing for Software, Digital Technical Journal, vol. 10, no. 1, 1998, pp. 100–107.
- [yoo12] S. Yoo, M. Harman: Regression testing minimization, selection and prioritization: a survey, STVR, vol. 22, no. 2, 2012, pp. 67–120. https://doi.org/10.1002/stvr.430

**フィード・データソース**(本文で言及するもののみ URL を付す)
- NVD, VulnCheck, Microsoft MSRC CVRF, Red Hat VEX/CSAF, AlmaLinux errata, Cisco openVuln API, 各ディストリビュータのフィード
