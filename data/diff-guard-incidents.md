# diff-guard 発動事例集 — 本番運用インシデント記録

**目的**: vulsio/vuls-data-db の DB 公開 CI に組み込んだ diff-guard(`vuls diff detection` / `vuls diff db`)が本番運用で実際に発動(FAIL)した事例を、日時・digest・データ変更内容・原因切り分け・対応策まで含めて網羅的に記録する。論文・報告書の素材として正確さを優先し、識別子(run ID / digest / CVE ID / commit hash)は全て原文のまま記載する。

**記録期間**: ガード本番導入 (2026-04-23) 〜 2026-07-14(本ドキュメント作成日)

**全数調査の範囲**: 期間内の DB(db-main.yml)343 run + DB(Nightly)(db-nightly.yml)331 run = 674 run をすべて分類した(うち 6 run はガード導入コミット(nightly 04-23 10:05Z / main 04-24 03:45Z)より前で検査ステップ自体が無い)。failed 339 run のうち **295 run が "Run diff guard" ステップで失敗**(threshold trip 293 + ガード内インフラ障害 2)。全 295 run の failing target・変動率・候補 digest は付録([`diff-guard-incidents-data/`](diff-guard-incidents-data/))に完全収録。

なお FAIL は promote 介入があるまで 6 時間おきの cron で**コケ続ける**ため、run 数は発動の重複カウントを含む。連続 FAIL を 1 つに潰した **fail sequence 数は 104**(DB 52 + DB(Nightly) 52。同一 workflow 内で隣接 FAIL の間隔 ≤9h を同一 sequence と判定 — 間に PASS が挟まると間隔は 12h 以上になるため分離される)。sequence 長は中央値 2〜3 run、最長 19 run(DB(Nightly) 05-02〜05-06 の debian_13 ストリーク)。ただし sequence は main / nightly を束ねられず、1 つの sequence に別イベントが相乗りもするため、**イベントの正準単位は source-episode = 69 件**(24h 集約規則であり、上流イベントの独立性の保証ではない)(source ごとに main/nightly を束ねた FAIL 出現時系列を作り、24h 以上途切れたら別エピソードと数える。§5.6)。

**情報源**:
- vulsio/vuls-data-db の全 run ログ・PR 本文・コミット履歴・promote-digest 履歴(GitHub API による全数収集、2026-07-14 実施)
- 各発動時の triage セッション記録(diff-guard-triage skill による調査。2026-06-08 以降はセッション記録が完全に残存)
- ローカル再現記録 `vuls-data-db/local-diff-guard.lo/`(2026-04-27 の初期ストリーク triage)
- 設計・検証記録 `diff-guard.md`, `verification-playbook.md`(maintainer ローカル workspace。この repo には含まれない)

---

## 1. 背景 — diff-guard とは

### 1.1 動機となった2つのインシデント(ガード導入前)

diff-guard は、以下の 2 件の「壊れた vuls.db を公開してしまった」インシデントを受けて設計された。

| | インシデント 1: RHEL VEX バグ | インシデント 2: Ubuntu `vulnerable: false` バグ |
|---|---|---|
| 発生 | 2026-03-06 | (同年3月頃、運用環境で顕在化) |
| 機序 | vuls-data-update / filter-vuls-data-extracted-redhat に `Criteria.Repositories` 変更を投入した日に、Red Hat が壊れた VEX データを配信。extract がエラー終了し dotgit が旧形式のまま残り、新形式前提の filter が空データを生成 | vuls0 master HEAD には `vulnerable: false` フィルタが存在したが、運用環境の vuls0 ラッパーは古く、フィルタなしで DB を読んだ |
| 影響 | **false negative**: 検知されるべき脆弱性が大量に「影響なし」判定(redhat:7 で −858 件 13.5%、redhat:8 で −2604 件 44.7%、redhat:9 で −3387 件 51.9%) | **false positive**: 影響のない脆弱性が大量検知(ubuntu_2204: 5,968 → 12,296 件、+6,328 件 106.0%) |
| 分類 | extract パイプラインのバグ × 上流の壊れたデータの複合 | DB とコンシューマ(vuls0)のバージョン非互換 |

### 1.2 ガードの構成

DB 公開前(compact 後・push 前)に 3 つのチェックを composite action(`.github/actions/diff-guard/action.yml`)として実行する。以下、本文は論文と同じ **Dn / Do / DB** 表記を用いる(付録の run 表 02a〜02e と log-extracts は収集時の略記 **M / O / D** のまま。M=Dn、O=Do、D=DB):

1. **Dn — `vuls diff detection`(vuls0 master HEAD)** — baseline DB と候補 DB で同一スキャン結果(vulsio/integration の fixture 群)に対する検知 CVE 集合をファイル単位で比較。大きな検知差 ≒ 出荷不可のシグナル。
2. **Do — `vuls diff detection`(pinned 旧 vuls0 バイナリ)** — 過去バージョンの vuls0 に対してのみ現れる退行(インシデント 2 型)を捕捉。
3. **DB — `vuls diff db`** — BoltDB を直接開き、ecosystem ごとに detection データを leaf Criterion レベルで構造比較(Detection Change Rate)+ Windows KB データの比較(KB Change Rate)。スキャン結果・バイナリ不要の構造ガード。

導入当初は最初に FAIL したチェックでガードが停止していたが、2026-05-08 のリファクタ(PR #144)以降は **3 チェックとも必ず走り切り、最後の集約ステップで fail** する(1 つの失敗が他のシグナルを隠さない設計。`diff guard failed: detection(master)=X detection(old)=Y db=Z` の形で記録される)。レポートは `$GITHUB_STEP_SUMMARY` に常時出力され、監査証跡になる。

### 1.3 デプロイ構造と fail 時の挙動

- 対象 workflow は 2 系統: **`db-main.yml`(workflow 名 "DB")** — baseline は `:0`(schema_version)/`:latest`、**`db-nightly.yml`("DB(Nightly)")** — baseline は `:nightly`。いずれも 6 時間おきの cron。
- 候補 DB は**ガード実行前に tagless(digest のみ)で GHCR に push** される。ガード FAIL 時は promote がスキップされ、候補は untagged のまま digest で pull 可能な状態で残る(事後検証可能)。
- FAIL 後にオペレータが「正当な変更」と判断した場合は **`promote-digest.yml`**(workflow_dispatch)で該当 digest に手動でタグを付けて公開する。この復旧パスは初発動ストリークの最中(4/27)に整備された(PR #139)。actor / digest / tag が run 履歴に残る。

### 1.4 閾値と per-target override

- デフォルト閾値: **detection 5% / db 10%**。
- 導入後 1 ヶ月の運用で「新しいディストリ世代・rolling release・ベンダー月次サイクルによる正当な churn が繰り返しガードに引っかかる」ことが判明し、**per-target 閾値 override 機構**(PR #146、vuls2 側は MaineK00n/vuls2#371 の `--change-rate-threshold-override`)を導入。2026-05-21/22 に実失敗履歴の統計から初期値をシード(PR #152 / #153)。
- 2026-07-14 には **per-source 化**(MaineK00n/vuls2#400、`<ecosystem>/<source>=<rate>` 形式のキー)+ CPE 擬似サーバ fixture(vulsio/integration#43)を導入(PR #196)。§4 A-16 の cpe インシデントが直接の動機。
- override リストの陳腐化を防ぐため、**約 2 ヶ月周期の grooming 運用**(自動起票 issue + `.github/diff-guard-override-grooming-runbook.md`)を整備。リストは追記でなく全再導出する。

2026-07-14 時点の override 設定(db-main / db-nightly 共通。**例外: `opensuse_tumbleweed=15` は db-nightly のみ** — この非対称のため db-main は 7/11 以降 tumbleweed で FAIL し続けている。→ A-17):

```
DB (default 10%):        ubuntu:26.04=30, ubuntu:snap=30, microsoft=35, fedora:45=50
Detection (default 5%):  debian_13=20, ubuntu_2604=50, rocky_10=20,
                         windows_* 全27ファイル (高churn世代=20, その他=10)
```

---

## 2. 運用タイムライン(ガード関連の整備履歴)

| 日付 (UTC) | 出来事 | 参照 |
|---|---|---|
| 2026-04-23 | db-nightly.yml にガード追加(本番初投入)。閾値 db=10% / detection=5%、override なし | PR #134, `f1c06ba` |
| 2026-04-24 | db-main.yml にガード追加 | PR #137, `eb26010` |
| 2026-04-24 13:21 | **初の本番発動**(DB(Nightly)、microsoft KB 134.3%。→ §4 P-1) | run 24891731249 |
| 2026-04-27 | 初の手動 promote(2 digest)。同日、復旧用 promote-digest.yml 新設 | PR #139, `4698030` |
| 2026-04-28 | Ubuntu 24.04 / 26.04 の scan fixture 追加(integration_ref bump) | PR #142 |
| 2026-05-08 | ガード集約リファクタ: 3 チェックを常に全部実行し最後に集約(それまでは最初の FAIL で停止) | PR #144, `66b9c1a` |
| 2026-05-21 | per-target 閾値 override 機構の配線(リストはまだ空) | PR #146, vuls2#371 |
| 2026-05-21/22 | 失敗履歴の統計 triage から override 初期値シード | PR #152(nightly), #153(main) |
| 2026-05-25 | `ubuntu:snap=30` 追加(→ §4 P-3) | PR #156 |
| 2026-05-28 | `microsoft=35` を db-main にも追加、windows fixture を detection セットに投入 | PR #158 |
| 2026-06-08 | vuls0_old_ref bump(Do チェックの対象ファミリ拡大)。run summary に promote コマンドのコピペ出力 | PR #166, #165 |
| 2026-06-11 | `windows_*` detection override 27 件追加(→ §4 A-1) | PR #167 |
| 2026-06-15 | `rocky_10=20` 追加(→ §4 A-2) | PR #169 |
| 2026-06-18 | 「vuls-data-db への `gh workflow run` を AI からは実行しない」絶対ルール成文化(§4 A-5 の直後) | CLAUDE.md |
| 2026-06-01 / 07-08 | override grooming 運用(自動起票 issue #162 ほか、runbook 整備) | issue #154, #162 |
| 2026-07-08 | diff-guard-triage skill を vuls-data-db repo に配置しチーム共有 | `.claude/skills/diff-guard-triage/` |
| 2026-07-14 06:57 | per-source 閾値 + CPE fixtures 導入(→ §4 A-16 が動機)。同日 07:40 の run から per-source レポートが稼働 | PR #196, vuls2#400, integration#43 |

---

## 3. 事例の分類基準

diff-guard-triage skill(`vuls-data-db/.claude/skills/diff-guard-triage/SKILL.md`)の手順で、FAIL ごとに以下の順で切り分ける(builder → extractor → upstream の順に容疑を除外):

- **upstream-driven** — raw dotgit が動き、vuls-data-update の extractor/fetch コードに変更なし、builder(DB metadata の `created_by`)同一。上流データ配信の実態が原因。
- **extractor-driven** — raw は不変なのに extracted が動いた。vuls-data-update のコード変更(バグまたは意図的変更)が原因。
- **vuls2-builder-driven** — anchors 不変で `created_by` のみ相違。vuls2(DB ビルダ)の変更が原因。
- **threshold-only** — 小さい baseline のターゲットが日常ノイズで一律閾値を超えただけ。per-target override で恒久対応する。

「upstream-driven」はさらに次の 3 種に分けて記録する:

- **(a) 正当な上流変更** — 新 CVE/advisory の一括公開、リリース直後のシーディング等。候補 DB は正しいので promote して復旧。
- **(b) 上流の一時的データ障害** — 配信断・ファイル消失等。候補 DB は欠損しているので **promote してはならない**。上流回復後の再実行で復旧。
- **(c) 上流の恒久的データ品質イベント** — 再キュレーション・骨抜き等。個別判断(ピン留め・別ソース採用等)。

---

## 4. 発動事例カタログ

各事例に記載: 発生日時(UTC)/ workflow と run / baseline・target digest / 失敗チェック(Dn/Do/DB)と対象・変動率 / データ変更の実体(smoking gun)/ 切り分け判定 / 対応。digest は `ghcr.io/vulsio/vuls-nightly-db@sha256:...` の sha256 部分。個々の run の完全な FAIL 行と候補 digest は付録の run 表を参照。

---

### Phase 1: 導入直後(2026-04-24 〜 05-31)— 「正当な churn が常時引っかかる」問題の発見

#### P-1. 2026-04-24 〜 04-27 — 初発動ストリーク: microsoft KB / ubuntu:26.04 / debian_13

ガード投入の**翌日から**発動が始まり、初の手動 promote(4/27)まで 20 run が連続 FAIL した。3 つの独立した上流イベントが重なっている:

1. **microsoft KB 134.3%**(DB、nightly のみ): 初発動 run は DBB(Nightly) [24891731249](https://github.com/vulsio/vuls-data-db/actions/runs/24891731249)(04-24 13:21)。`microsoft` ecosystem の KB Change Rate 134.3%(Detection 0.0%)。旧い `:nightly` baseline に対する Windows KB データの大規模更新
2. **ubuntu:26.04 19.8%**(DB、main は 04-25 01:09 の [24918908102](https://github.com/vulsio/vuls-data-db/actions/runs/24918908102) から): Ubuntu 26.04 リリース直後の ubuntu-cve-tracker 大量 triage による構造 churn(Changed Root **18,871 件**)
3. **debian_13 6.0%**(Dn、04-25 18:31 以降): Debian trixie への新規 CVE 一括流入(2119 → 2246、Added 127 / Removed 0、CVE-2026-31536〜31580 等の連番)。当時のガードは最初の FAIL で停止する実装だったため、Dn(debian_13)が FAIL すると DB(ubuntu:26.04)は記録に現れなくなる — 04-27 のローカル全チェック再現(`vuls-data-db/local-diff-guard.lo/20260427-vuls-nightly-db-2796a350-vs-0/`、候補 `2796a350…`)で両方が FAIL することを確認している
- **判定**: いずれも **upstream-driven (a)**(新ディストリ立ち上がり期の bulk churn + ベンダー月次データ)
- **対応**:
  - 04-27 05:27〜06:00 に初の手動 promote: `e8fa973dc5f78c177382fae10c5ef5476deca7ced97f5a6c9d75696c4c58a935` → :nightly、`2796a3508aa0e0d433f27ee475cdfb7e993cac80ecea1e3a9411f30738939bb8` → :latest / :0(初回試行 run 24978122420 は失敗し 17 分後に再試行成功 — promote パス自体の初運用)
  - 当初は手元の `vuls-data-update dotgit registry tag` 実行で監査証跡が残らない問題が認識され、**同日 promote-digest.yml workflow を新設**(PR #139)
  - この事例が per-target override 機構(PR #146)の直接の動機(PR 本文に「ubuntu:26.04 19.8% / debian_13 6.0% とも build に問題はないのに手動 promote を要した」と明記)

#### P-2. 2026-04-30 〜 05-20 — 失敗ストリーク期(override シードの根拠データ)

FAIL 中は promote が止まり baseline が動かないため、**同じ差分で 6 時間おきの cron が再 FAIL し続ける**構造でストリーク化した(付録 02a に全 run)。主要ストリーク:

| 期間 | ターゲット(チェック) | 観測値 | 性質 |
|---|---|---|---|
| 04-30〜05-01 | ubuntu_2604(Dn) | 38.8% | 未来リリースの小 baseline churn |
| 05-02〜05-09 | debian_13(Dn) | 5.1–5.9%(断続) | trixie への定常的新 CVE 流入 |
| 05-05〜05-06 | opensuse_tumbleweed(Dn) | 7.1% | rolling release は設計上 churn する |
| 05-06 | debian_13 14.1% + debian_12 8.8%(Dn) | — | 単発スパイク |
| 05-08 | ubuntu_2604 14.5% + ubuntu_2404 5.5%(Dn+Do) | — | — |
| 05-10〜05-11 | amazon_2023(Dn) | 7.0% | ガード停止中に溜まったバッチ |
| 05-10〜05-11 | opensuse_leap_16 / 〜_kernel-default-base(Dn) | 100.0%(baseline 空: 0→1601 / 0→1553) | 新規 ecosystem 追加 |
| 05-13〜05-14 | oracle_8(Dn+Do)+ microsoft KB 15.6–18.3%(DB, nightly) | 6.7–7.0% | 単発の vendor advisory バッチ + Patch Tuesday |
| 05-16〜05-18 | amazon_2_extra_kernel(Dn) | 12.4% | 単発バッチ |
| 05-18 | fedora:45(DB) | 39.3% | 直近リリースの churn |
| 05-20 | ubuntu:16.04(DB) 39.0–39.5% + ubuntu:26.04 17.0%(DB) | — | **EOL ディストリが 39% 動くのは異常**として意図的に override せず残置 |

- **集計**(PR #152 / #153 の triage): db-nightly は 2026-04-30〜05-20 で **47 failed run / 7 イベント**、全て diff-guard trip。db-main は 05-01〜05-20 の 34 失敗中 33 が diff-guard trip、1 件のみ CI インフラ flake(run 25377929034)
- **判定**: 大半が **upstream-driven (a)** または **threshold-only**(小 baseline)。ここで「**繰り返し発生する上流由来 churn のみ override で緩和し、成熟ディストリの単発スパイクは fail させて人間に見せる**」という運用基準が確立された
- **対応**: PR #152(05-21, db-nightly)/ #153(05-22, db-main)で override をシード(観測ピーク + ヘッドルーム)。期間中の復旧は手動 promote(05-01, 05-03, 05-07, 05-08, 05-11, 05-14, 05-17, 05-18, 05-19, 05-21 — 付録 03 参照。actor: shino, MaineK00n)

#### P-3. 2026-05-23 〜 05-25 — ubuntu:snap: Go crypto 一括開示で小 baseline が跳ねる

- **Run**: 05-23 07:59 の DB [26327547220](https://github.com/vulsio/vuls-data-db/actions/runs/26327547220) から 05-25 03:41 まで、DB / DB(Nightly) 両系統の全 scheduled run(計 16 run)が連続 FAIL
- **FAIL 行**: DB `ubuntu:snap` Detection Change Rate **21.7%**(閾値 10%)、KB 0.0%
- **Anchors**(代表 run 26369890091 の triage): baseline `:0` = `sha256:d99cb46514d604e6ebd10e19863677743830e72bfc189ff6985811d922e9868b` / target = `sha256:8871c3e0c78c119fa01d6b9d1448174cd2afc10b4a20099bb0b41dc2ce7026c7`。`created_by` 同一(`vuls v0.0.1-alpha.0.20260520015748-4012c541274e`)→ builder 除外。ubuntu-cve-tracker raw `14909141`(05-22 14:28Z)→ `282e9683`(05-24 02:16Z)、窓内に `pkg/{extract,fetch}/ubuntu/tracker/` のコミットなし → extractor 除外
- **Smoking gun**: 追加 root ID 13 件すべてが raw の新規ファイル(`active/2026/CVE-2026-39827.json` 〜 `CVE-2026-46598.json`)で、いずれも `"packages": { "snapd": { "releases": { "snap": { "status": "needs-triage" } } } }`。description が `go.dev/cl/781320` / `GO-2026-5016` を参照 → **Go crypto 系一括開示**に対する Ubuntu tracker の snapd(同梱 `golang-go.crypto`)triage バッチ
- **判定**: **upstream-driven (a)**。ubuntu:snap は baseline 57 → 70 root と極小のため単一バッチで 10% を超える(threshold-only 的性質の複合)
- **対応**: PR #156(05-25)で両 workflow に `ubuntu:snap=30`(観測 21.7% + 約 8pt ヘッドルーム、`ubuntu:26.04=30` と同設計)

#### P-4. 2026-05-27 〜 05-28 — AlmaLinux 10 errata feed 再キュレーション(上流の恒久的データ品質イベント)

- **Run**: 05-27 08:53 DB [26501231316](https://github.com/vulsio/vuls-data-db/actions/runs/26501231316) から両系統で連続 FAIL。**alma_10 99.2%(Dn+Do)/ alma:10 99.7%(DB)** — さらに 05-28 04:00 の run 26553857530 / 26553887891 では **alma_10 428.3% / alma:10 264.0%** まで拡大
- **データ変更の実体**(07-02 の再調査で確定): AlmaLinux が 2026-05-19〜26 に errata feed を複数回**再キュレーション** — advisory 数 279 → 一時 60、ALSA-2025 → ALSA-2026 再採番を伴う。削除 143 advisory が参照する 434 CVE のうち **376 件(87%)が feed から完全消失**。2025-11-26 にも −102 件のパージ実績(反復性のある上流運用)
- **判定**: **upstream-driven (c) 恒久的データ品質イベント**。上流データが「正」だが検知能力の実質的毀損を伴う
- **対応**:
  - 閾値 override 案(PR #159)は**却下** — 閾値で吸収すべき性質ではない
  - 05-28 に promote で復旧(01:10〜05:34 に 4 digest: `34c24f3b…`→:0, `ba970318…`→:nightly, `d2c2a106…`→:0, `aee9b836…`→:nightly)
  - **alma-errata の extracted dotgit commit を Makefile でピン留め**(db-main.mk: `564e8bdd1c936e2f09452a6370a0cd63c6b0be3d`(05-21 時点)、db-nightly.mk: `e6b3fde`(05-27))して以後の劣化取り込みを停止 → 後日の計画的アンピンが A-14
- **小規模な後続**: 05-28 19:59〜 rocky_9 5.4%(Dn+Do、単発、05-29 promote)、05-29 opensuse_leap_16 系 12.9〜13.6%(新 ecosystem シーディング継続、05-29 promote)

#### P-5. 2026-05-30 〜 06-08 — rocky_10 初期シーディング + 6月初旬の windows 大変動

- **rocky_10**: 05-30 08:11([26678908271](https://github.com/vulsio/vuls-data-db/actions/runs/26678908271))〜06-01 に **rocky_10 34.4%(Dn+Do)+ rocky:10 14.1%(DB)** で両系統連続 FAIL。06-04〜05 に 11.6%、06-06〜08 に 8.7% と減衰しつつ再発。Rocky Linux 10 リリース直後のベンダー errata 初期シーディング(baseline 122 → 205 と成長中の小 baseline)
- **windows**: 06-02 に windows_* ×12 max 44.8%(Dn)、06-06〜08 に windows_* ×13 **max 76.3%**(Dn+Do)が rocky_10 と重なって FAIL(個別 triage 記録なし。当時 detection 側 windows override は未導入)
- **判定**: いずれも **upstream-driven (a)**(初期シーディング / Microsoft データ更新)
- **対応**: 都度 promote(06-01, 06-02, 06-05, 06-08 — 付録 03)。rocky_10 は 6/14 再発時に override 化(→ A-2)

---

### Phase 2: 定常運用期(2026-06-10 〜 07-09)— triage 記録が完全に残る事例群

以下は各発動時の triage セッション記録に基づく。判定の除外手順(builder `created_by` 比較 → extractor コミット走査 → raw/extracted dotgit diff)は全事例で共通に実施されている。

#### A-1. 2026-06-10 — Windows 6月 Patch Tuesday(detection 側の閾値非対称の露呈)

- **Run**: DB(Nightly) [27304209180](https://github.com/vulsio/vuls-data-db/actions/runs/27304209180)(06-09 Patch Tuesday の翌日、06-10 20:27)
- **FAIL**: Dn で **windows 系 13 ファイル、5.3〜14.2%、全て Added のみ**。最大 windows_11_25h2 / 24h2 = 14.2%(1081→1235、+154)、windows_server_2025 9.6%、windows_10_22h2 5.4% など
- **データ変更**: 2026-06-09 Patch Tuesday の新規 advisory/KB 一括公開(純増)
- **判定**: **upstream-driven (a) / threshold-only の複合**。db 側には `microsoft=35` override が既にあったのに、detection 側の windows は default 5% のままという**非対称**が根本原因(PR #158 で windows fixture を detection セットに入れた時点の据え置きが伏線)
- **対応**: PR #167(06-11)で `windows_*` 全 27 ファイルに detection override を 2 段階で追加(高 churn 世代 =20、その他 =10)。vuls2 の override は完全一致キーのみ(glob 非対応)のため全列挙。「月ごとにどのファイルが 5% を超えるかはローテーションする」ことも列挙の理由。直後の 06-12 に早速 windows_server_2008_r2 26.8% / 2012_r2 10.1% が新閾値 10% を超えて FAIL(付録 02b)

#### A-2. 2026-06-13 〜 06-14 — rocky_10 新規 errata バッチ

- **Run**: 06-13 08:41 から連続、代表 DB [27508894556](https://github.com/vulsio/vuls-data-db/actions/runs/27508894556)(06-14 19:01)
- **FAIL**: Dn+Do。**rocky_10 205→227、+22、10.7% > 5%**(nightly 側は並行して cpe 40.1% も FAIL — 後述 A-8 前段の nightly cpe 変動系列)
- **Anchors**: baseline `:0` = `sha256:450a9bd4…1001`(06-13 02:43 の**自動 promote** — 06-08 の手動 promote `bfbdad3d` ではない。baseline 特定の落とし穴として記録)/ target = `sha256:903923f681fb3e716409b84d72fed07fdd98eb65349e59268b2c24a4aad9637e`。builder 同一、extractor コミットなし
- **Smoking gun**: Rocky 10 向け新規 errata 8 件 — RLSA-2026:24985(poppler, Important, published 06-13, CVE-2026-23186), 25111, 25112, 25115, 25191, 25216, 25225, 25237
- **判定**: **upstream-driven (a)**
- **対応**: promote(903923f6 → :0、06-15)+ PR #169 で `rocky_10=20` を両 workflow に追加。PR には「06-01 の 34.4% スパイク(P-5)は初期シーディングであり 20% では救わない(定常レジームだけを対象にする)」と閾値設計の根拠を明記

#### A-3. 2026-06-15 〜 06-16 — fedora:45 マスアップデート(単一 advisory が 5,312 criterions)

- **Run**: 06-15 11:36 から連続、代表 DB [27589528643](https://github.com/vulsio/vuls-data-db/actions/runs/27589528643) + Nightly [27593150221](https://github.com/vulsio/vuls-data-db/actions/runs/27593150221)
- **FAIL**: **DB のみ**。fedora:45 Detection Change Rate 264.5 → **268.8% > override 50%**(criterions 1987 → 7329、+5342)。detection は PASS(fixture に F45 の広範なパッケージがないため)
- **Smoking gun**: **FEDORA-2026-54c7ad647e** — 約 600 src package を束ねた Bodhi マスアップデート(単一 advisory で 3.5MB / 5,312 criterions、extracted commit `404324ae` 06-15 21:10 で新規追加)。他 3 advisory(+21/+8/+1)と合計 5,342 で増分と完全一致
- **判定**: **upstream-driven (a)**
- **対応**: promote — main `sha256:95a6038a388ea769a635098524615a645963c32443fe446e383165667fc4f6ee`(:0)、nightly `sha256:0133aa170bb2e21af28de1bed657047df96e0e35b322f89879873ef0cd8a5291`(:nightly)。06-16 07:28–29 実施

#### A-4. 2026-06-16 — Microsoft CVRF 2026-Jun 全消失(ガードが出荷を止めた成功事例 ①)

- **Run**: 06-16 10:46 から連続、代表 DB [27646259547](https://github.com/vulsio/vuls-data-db/actions/runs/27646259547) + Nightly [27647167088](https://github.com/vulsio/vuls-data-db/actions/runs/27647167088)(両 run の diff レポートはバイト一致)
- **FAIL**: Dn のみ。**windows 13 ターゲットで削除のみの大変動** — windows_11_21h2 879→472(46.3%)、windows_11_25h2 1235→722(41.5%)、windows_server_2025 1802→1285(28.7%)等
- **Anchors**: main baseline `:0` = `sha256:95a6038a…`(06-16 07:29 promote、A-3 の復旧 digest)/ main target = `sha256:ff6889e11c00ca49b6fe40d98dcd6cfb10655e89a7343f93f5aee05e73222b58`。nightly baseline = `sha256:0133aa17…` / target = `sha256:b8c1fee3b0f80ba5b7619d293b389efa0f5b7ea52427bb36175056cf1407fc45`
- **Smoking gun**: raw microsoft-cvrf `4b5baa9→44181ca` で **`2026-Jun/` ディレクトリが丸ごと消失(723 → 0 ファイル)**。extracted `5e47f25→b21d21d` で CVE ファイル 777 本削除(うち 754 が CVE-2026、206,903 行削除)。例: CVE-2026-48574("Windows Media RCE", published 2026-06-09)がファイルごと消失。June 件数は 723→0→811 とフラップし、06-16 16:33 の raw `34a4bd5` で復旧
- **検証補強**: fetcher(`pkg/fetch/microsoft/cvrf/cvrf.go`)は fail-hard 設計でスキップ機構なし・期間中コード変更ゼロ → **MSRC API 側が一時的に June ドキュメントを返さなくなった**と判断
- **判定**: **upstream-driven (b) 一時的データ障害**。候補 DB は June の Windows 脆弱性情報を欠く欠陥品
- **対応**: **候補 ff6889e1 / b8c1fee3 は promote しない**。上流回復後の再実行のみで復旧。ガードが「大量 false negative の DB 公開」を水際で止めた、設計意図どおりの発動
- **副次的発見(ガードの盲点 2 件)**:
  - Do が PASS したのは red herring — 旧 vuls0 用 fixture セットからは windows_*.json が除外されている(action.yml)ため microsoft データを評価していない
  - **DB も PASS** — KB Change Rate は KB キー集合(10667→10667)しか見ておらず、CVE エントリの大量消失を見逃した(triage skill の警告事項に成文化: 「KB Change Rate = 0% は『変化なし』を意味しない」)

#### A-5. 2026-06-17 — fedora:45 マスアップデート撤回(A-3 の鏡像)

- **Run**: 06-17 10:19 から連続、代表 DB [27715637419](https://github.com/vulsio/vuls-data-db/actions/runs/27715637419) + Nightly [27716617109](https://github.com/vulsio/vuls-data-db/actions/runs/27716617109)
- **FAIL**: DB、fedora:45 **72.5% > 50%**(criterions 7329 → 2017)。Removed Root ID は **FEDORA-2026-54c7ad647e ただ 1 件**(5312/7329 = 72.5% で数値一致)
- **Smoking gun**: extracted `7fbd62c4`(06-17 05:52、日次 refresh 23,260 files 中、削除は 2 件のみ)= 上流(Bodhi)でのピンポイント撤回
- **判定**: **upstream-driven (a)**(正当な撤回。A-3 で入ったものが抜けただけ)
- **対応**: promote — main `sha256:1c66a9df131e16709cf758c2c3cca8ddc4a982a13354d560b6913a05ccacb24a`、nightly `sha256:585a4d1da2edc955b1b613ac2d55474eebe48a926ea3af96dfa6f58b6a4bd4f7`(06-17〜18)
- **備考**: この triage の直後(06-18)に「vuls-data-db への `gh workflow run` を AI が実行しない」絶対ルールが成文化された(promote 判断・実行は人間に限定)

#### A-6. 2026-06-19 — fedora-api extractor の非決定性バグ(**唯一の extractor-driven コードバグ**、ガードが出荷を止めた成功事例 ②)

- **Run**: DB [27801929985](https://github.com/vulsio/vuls-data-db/actions/runs/27801929985)(06-19 02:36。nightly 側 27804864132 も同様)
- **FAIL**: DB、fedora:45 **274.5% > 50%**(criterions 2066 → 7738、keys 89 → 92)。KB 0.0%
- **Anchors**: baseline `:0` = `sha256:1c66a9df…`(A-5 の復旧 digest)/ target = `sha256:808d7b35d51bea5b915a9ef12f43390b40079a4ace194b081a4b0cfd2c4b1860`
- **Smoking gun**: raw の変更は 266 files なのに extracted は 23,163 files(87 倍)。fedora:45 サンプル 60 件中 **59 件が raw blob バイト同一なのに extracted だけ変化**。具体例: `FEDORA-2026-54c7ad647e` の package `bind` の architectures 配列が baseline `["aarch64","i686","ppc64le","s390x","src","x86_64"]` → target `["src","x86_64","aarch64","i686","ppc64le","s390x"]` — **ソート済みだった集合が未ソートの回転列に**。レポートの "Added Root IDs" のうち 2 件はファイルとして実在しない(順序依存グルーピングのアーティファクト)
- **根本原因**: vuls-data-update の fedora-api extractor が `*dataTypes.Data`(ポインタ)を `util.Write` に渡していたため、type switch の `case dataTypes.Data:` にマッチせず `Sort()` が実行されない(api.go:115)。出力順序が非決定になり、構造比較が大規模ドリフトとして検出
- **判定**: **extractor-driven(真のコードバグ)**。本記録期間で唯一の、パイプライン側バグをガードが捕捉した事例
- **対応**: **promote しない**。修正 PR [MaineK00n/vuls-data-update#854](https://github.com/MaineK00n/vuls-data-update/pull/854)(06-19、base: nightly)

#### A-7. 2026-06-23 — Amazon Linux 10日分バッチ

- **Run**: DB [28014227227](https://github.com/vulsio/vuls-data-db/actions/runs/28014227227)(06-23 08:51)
- **FAIL**: Dn+Do — **amazon_2023 2080→2233(+153, 7.4%)**、**amazon_2_extra_kernel 1299→1367(+68, 5.2%)**、閾値 5%
- **Anchors**: baseline `:0` = `sha256:e43a2e5b…`(06-23 02:28、先行成功 run 27996707991 の自動 promote)/ target = `sha256:d2155fc061105ad241adeb67d86f22bfcbc081097c0ae5818feca38058194892`。builder 両者 `vuls …20260622074355-fab747f7e5ef`
- **Smoking gun**: amazon raw 単一コミット `cd2dc392`(06-23 02:04、185 files / +25,037 行)。新規 **ALAS2023-2026-1882**(kernel, Important, Issued 2026-06-22)の CVE 群(CVE-2023-53989, CVE-2025-39961, CVE-2026-23255, CVE-2026-23272, CVE-2026-23399, CVE-2026-23442, CVE-2026-31407 ほか)が Added IDs と一致。extra_kernel 分は `ALAS2KERNEL-5.15-2026-107`(CVE-2026-43079 等)
- **判定**: **upstream-driven (a)**(Amazon の advisory 公開が約 10 日ぶりでバッチが大きくなった)
- **対応**: promote(d2155fc0 → :0、06-23 12:26)。単発バッチのため override 不要と判断

#### A-8. 2026-06-11 〜 06-24 — nightly cpe 変動系列と CPE match quality 分類(意図的な extractor 変更)

nightly 系では 6 月中旬から cpe ecosystem の DB-FAIL が断続的に発生した(いずれも nightly のみ): 06-11 25.3%、06-14 40.1%、06-17 **122.7%**、06-19〜21 18.6%、06-24 18.0%(付録 02b/02c)。個別 triage 記録が残るのは 06-24 分:

- **Run**: DB(Nightly) [28125012733](https://github.com/vulsio/vuls-data-db/actions/runs/28125012733)(06-24 19:43)。amazon(A-7 とバイト一致)+ **cpe 18.0% > 10%**(KB 0%)— cpe に 16,228 root ID 追加(CVE-1999-0661 など歴史的 CVE を含む全年代)
- **Anchors**: baseline `:nightly` = `sha256:ce51b61fe37dfe2a70e57b1261fa3e778d2d0550c3806e7857bc80bfc36641f3`(06-22 05:17 で停止していた)/ target = `sha256:f3aff0464ef146737070da1d477aa51a809e961ab0e2ce659070090489202257`。builder 差分(`98ac8e52`→`fab747f7`)は精査の上、無関係と確認
- **原因**: vuls-data-update **`bfedbc24` feat!(extract/types/criterion): classify CPE match quality ([#850](https://github.com/MaineK00n/vuls-data-update/pull/850))** — CPE マッチ品質の Exact / VersionUnconfirmed 分類導入という**意図的な breaking change**(nightly ブランチ先行)
- **判定**: **extractor-driven(意図的変更)**。バグではなく、nightly が実験ブランチとして先行する設計どおりの挙動
- **対応**: promote(f3aff046 → :nightly、06-25)。それ以前の 6 月 nightly cpe 変動(06-11/14/17/19–21)は個別 triage 記録なし(nightly 先行の CPE 関連変更ないし CPE データソース churn。都度 promote で復旧: 74ddb522(06-12)、d6aa51e4(06-15)、96bf8d9c(06-17)、262696047a(06-22))

#### A-9. 2026-06-27 〜 06-29 — Ubuntu 26.04 triage 進行 + Red Hat VEX 全再生成(同時多発、main 側)

- **Run**: ubuntu_2604 単独では 06-27 01:50 から、redhat が加わるのは 06-28 02:00 から。代表 DB [28332593350](https://github.com/vulsio/vuls-data-db/actions/runs/28332593350)(06-28 18:56)
- **FAIL**(2 系統同時):
  1. Dn+Do: **ubuntu_2604 681→1044(+363, 53.3%)> override 50%** — ubuntu-cve-tracker raw に `resolute`(26.04)ブロックが **+25,009 行**。例: CVE-2026-52912 が needs-triage → needed/pending 7.0.0-28.28、新規 CVE-2025-60466
  2. DB: **redhat:5 21.9% / redhat:4 17.8% / redhat:6 13.5% / redhat:7 13.4% > 10%**(KB 0.0%)— Red Hat が 2026-06-27 に CSAF VEX を **SDEngine 4.6.12 → 5.2.6 で全再生成**。1 日スライスで 10,809 ファイルの version フリップ。例: CVE-2007-0044 の generator 変化、CVE-2007-3410 の RHEL4 product_id `4Desktop:/4ES:/4WS:HelixPlayer-…` 再構成
- **Anchors**: baseline `:0` = `sha256:55f19f110777772a0c4d21d829be6277d291b8ba502b64c1f1fe2c81e47c1cad`(06-26 15:00 自動 promote)/ target = `sha256:a2e7a0cc1436f0babbda4776febee800590e401d4ea2df7e831f7132db1b88d6`
- **判定**: いずれも **upstream-driven (a)**(VEX 再生成はツールチェーン更新に伴う無害な構造変化、検知内容は等価)
- **対応**: promote(a2e7a0cc → :0、06-29 02:15)

#### A-10. 2026-06-29 — 同上 + rhel_10 新規 CVE 流入(3 系統同時、nightly 側)

- **Run**: DB(Nightly) [28398716428](https://github.com/vulsio/vuls-data-db/actions/runs/28398716428)(06-29 19:55)
- **FAIL**(3 系統): ubuntu_2604 53.3%、**rhel_10 2997→3227(+233 / −3, 7.9% > 5%)**、redhat:4–7 14–22%。rhel_10 の Added 233 中 232 が CVE-2026 新規(例: CVE-2026-23071 が redhat-vex raw 06-27→28 スライスで新規、`red_hat_enterprise_linux_10:kernel…`。ほか CVE-2026-23300 / 23304 / 43027 / 46116 等)
- **builder 差分の精査**: vuls2 `4f87e838..a01483fb` の 1 コミットは pan-os 用 deps bump(go.mod/go.sum のみ)→ 無罪
- **Anchors**: baseline `:nightly` = `sha256:ab06363038be3b947f17b556366e0d50938e66f5aa419037c19b30a88ac4f89a`(06-26 05:38)/ target = `sha256:56244684c5f7b4f145f6e21796bb9b3a20d36c5e33db3115c65d0e04de541c2a`
- **判定**: **upstream-driven (a)** ×3
- **対応**: promote(56244684 → :nightly、06-30 02:02)+ 恒久 override 案 `rhel_10=10` を提案(RHEL10 の定常新 CVE 流入は今後も続くため)
- **備考**: 初回 triage レポートで rhel_10 行を見落とし、ユーザー指摘で訂正した記録あり(triage 品質の教訓)

#### A-11. 2026-07-01 — SUSE OVAL 大規模再発行

- **Run**: DB [28488390213](https://github.com/vulsio/vuls-data-db/actions/runs/28488390213)(07-01 02:01。nightly 側 28491908555 は sles12 + micro:6 のみ)
- **FAIL**: Dn+Do **opensuse_tumbleweed 10.9% / sles12 5.6% > 5%** + DB **suse.linux.micro:6 15.6% > 10%**(KB 0.0%)。追加のみ・削除ほぼなし
- **Anchors**: baseline `:0` = `sha256:438644f027c1a844cf6a08340a21f7bf6307b9ff8808988ee1d6243239bb20c9`(06-30 20:35 自動 promote)/ target = `sha256:24f409251bf671871b5e6371f7ed1b334c59a7a90fb5ddd3abde06badde5734f`
- **Smoking gun**: extracted suse-oval `8858b26e0 → fd1230336` で 12,488 files(Modified 12,240 / Added 247 / Deleted 1)。新 advisory **SUSE-SU-2026:22251-1** が raw OVAL に実在(`def:202634180` = CVE-2026-34180)し、既存 CVE への ecosystem 一括付与(sle12 +7,500、micro:6 +6,400、tumbleweed +6,400)
- **判定**: **upstream-driven (a)**(SUSE の OVAL 再発行サイクル。ガード検証期の 44 日ベンチマークでも 2026-03-06→07 に同種イベントを観測済み)
- **対応**: promote(24f40925 → :0、07-01 04:27)。override 案(`opensuse_tumbleweed=15` / `sles12=10` / `suse.linux.micro:6=20`)は必須でないと判断 — ただし tumbleweed は 7/11 以降 db-main で再発しており(→ A-17)、db-nightly のみ override 済みという非対称が残っている

#### A-12. 2026-07-02 〜 07-03 — MSRC CVRF June 再消失(A-4 の再発。ガードが出荷を止めた成功事例 ③)

- **Run**: 07-02 13:22 〜 07-03 19:19 の 8 run(windows_* ×13 max 53.6%)。代表 DB [28614789028](https://github.com/vulsio/vuls-data-db/actions/runs/28614789028)、[28593382639](https://github.com/vulsio/vuls-data-db/actions/runs/28593382639)
- **FAIL**: Dn で windows 系 13 ターゲット **16〜53% の removed-only**
- **Smoking gun**: raw microsoft-cvrf の `2026-Jun/` が **1273 → 0 → 1273 → 0 → 1278 とフラッピング**(07-01 14:17 `5a0dbb67` = 1273 → 07-02 02:01 `55abc741` = 0 → 07-02 13:26 復活 → 07-03 01:42 再消失 → 07-03 13:33 復活)。extracted `061ececb`(07-02 10:35)で 1,332 files / 227,724 行削除(CVE 1269+4 件)。代表削除例: CVE-2026-10881(June 2026 Security Updates / Chromium・Edge 系)
- **Anchors**: baseline = `sha256:00668b7bed51f2f34b5daae6f2995855e271c78206099df23bbd5b81323a73fc` / target = `sha256:e2a24401f80537b1f6e155a8b6b7ec1fa72da8f5d29fb2a4bdd2713d04980039`
- **判定**: **upstream-driven (b) 一時的データ障害の再発**
- **対応**: promote せず(データ欠損 DB のため不適切)。`:0` は 07-06〜08 の成功 run と手動 promote で自然回復(07-08 に事後 triage)。恒久策として「fetch 側で月ドキュメントが丸ごと消えたら commit しないガード」の検討余地をメモ(未実装)

#### A-13. 2026-07-04 〜 07-05 — MSRC "July 2026 Early Security Updates"(Edge 一括公開)

- **Run**: 07-04 08:15 から両系統の全 run が連続 FAIL(12 run)。代表 DB [28751305350](https://github.com/vulsio/vuls-data-db/actions/runs/28751305350) + Nightly [28751886446](https://github.com/vulsio/vuls-data-db/actions/runs/28751886446)
- **FAIL**: Dn のみ — **windows_11_21h2 25.6% / windows_11_22h2 24.9% / windows_10_20h2 20.6% > 閾値 10%**。全ターゲット一律 **+260 / Removed 0**。閾値 20% の 23h2/24h2/25h2 は 18.8–19.0% で僅差 PASS
- **Smoking gun**: raw microsoft-cvrf `4ccde37a07`(2026-07-04T01:33Z)で `2026-Jul/` に 354 files / +56,252 行(新規 329 件、うち **260 件が Edge Chromium detection**)。代表: CVE-2026-13774 "Chromium: Use after free in Extensions"(published 07-02、`Microsoft Edge (Chromium-based) < 150.0.4078.48`、document_title "July 2026 Early Security Updates")
- **Anchors**: main baseline `sha256:d59c1aea…` / target `sha256:be569c612fe128b59e30d44a0e5b4cf13b4d2a9553bf8228be1741a8db97eda6`。nightly baseline `sha256:311640f8…` / target `sha256:35147345437f010c0b9458066dace01629b00ddeb21d3a222b707368a8fd770c`
- **判定**: **upstream-driven (a)**(Patch Tuesday 本体より早い月次 Edge 一括公開)
- **対応**: promote(be569c61 → :0、35147345 → :nightly、07-06 01:27)。恒久策として windows の 10% 組 override を 20–25% に揃える案を提示(Edge 一括公開は毎月発生するため。7/12〜 の再発 → A-17 参照)

#### A-14. 2026-07-07 — alma ピン解除による計画的 baseline リセット(P-4 の後日談)

- **Run**: 07-07 06:53 Nightly [28847492830](https://github.com/vulsio/vuls-data-db/actions/runs/28847492830)、08:40 DB [28853199310](https://github.com/vulsio/vuls-data-db/actions/runs/28853199310)。PR #192(db-main.mk / db-nightly.mk の alma-errata ピン解除)マージ後の初回 run で、**計画された FAIL**
- **FAIL**(5 行): Dn+Do **alma_10 107.3%(259→343、+181/−97)**、**alma_9 13.7%(+151/−0)**、**alma_8 8.8%(+77/−0)** + DB **alma:10 146.5%**、**alma:9 11.7%**。他 ecosystem は全 PASS(影響が alma に閉じている = ピン解除以外の混入なしの証拠)
- **Anchors**: target(main 候補)= `sha256:71f6d50efb792417393a8cde91e93fe79569cf320577090e095060d9077636ec` / baseline `:0` = `sha256:c6c3fed1…`(07-07 02:50)。alma-errata extracted anchor: `564e8bd`(05-21 ピン)→ `a6a277e6a0`(07-07 current)。nightly 候補 = `sha256:8ddd89aeb8be8bab91c40ba2367abf5fd0a845771502828066c3354ef12a6667`
- **重要発見**: alma_10 の removed 97 件は baseline リセットの副産物ではなく、**上流 advisory の「骨抜き」の顕在化**。例: **ALSA-2026:2721**(kernel security update)がピン時点 73 criteria(`< 0:6.12.0-124.38.1.el10_1`)→ 現行 feed では kernel-doc / kernel-abi-stablelists の 2 criteria のみに縮退。生存 136 advisory 中 79 件(58%)がパッケージ数半減以下。feed / OSV / HTML の三者一致でこれが「上流の姿」と確認。CVE 例: CVE-2023-53034 の検知が消失。AlmaLinux Mantis #644 への追加証拠として記録
- **判定**: **upstream-driven (c) 恒久的データ品質イベント**(の、計画的な取り込み)
- **対応**:
  - promote(8ddd89ae → :nightly 07-07 08:39、71f6d50e → :0 07-07 10:46)。one-time ジャンプのため override 恒久追加は不要
  - 上流劣化への恒久対策を並行整備: raw 復元機構 PR #191(fetch-alma-errata.yml に RESTORE_SNAPSHOT / RESTORE_PATHS 245 件、HTML index をオラクルに使用)、**alma-oval データソースの復活**(vuls-data-update PR #882 — extractor が空スタブだったことが判明し約 480 行を新規実装。ALSA-2026:2721 が 75 criteria で復元することを実測)+ vuls-data-db PR #198(draft)
  - 引き継ぎ資料: `~/g/alma-data/docs/`

#### A-15. 2026-07-07 — Oracle UEK メガ advisory(単一 advisory に CVE 822 件)

- **Run**: 07-07 13:58 から 4 run。代表 DB [28892820817](https://github.com/vulsio/vuls-data-db/actions/runs/28892820817) + Nightly [28894311083](https://github.com/vulsio/vuls-data-db/actions/runs/28894311083)
- **FAIL**: Dn+Do — **oracle_10 511→1190(+679, 132.9%)**、**oracle_9 4675→5317(+642, 13.7%)> 5%**。oracle_7 +6 / oracle_8 +1 は PASS
- **Smoking gun**: raw `3944dd9e`(07-05)→ `ae6253d7`(07-07)、406 files / +17,281 行の純追加。本体は **ELSA-2026-50372 Unbreakable Enterprise Kernel security update**(IMPORTANT、issued 2026-07-02、OL9/OL10、**CVE 822 件**を単一 advisory に同梱。例: CVE-2024-14027, CVE-2025-21709, CVE-2025-22116, CVE-2024-58096/58097)。ほか ELSA-2026-50373 / 50374 / 33481
- **Anchors**: main baseline `:0` = `sha256:71f6d50efb…636ec`(07-07 10:46 手動 promote、A-14 の復旧 digest)/ target = `sha256:efd1f42996bbeeab2ca67ecc5b7bee399c377079341ec7cbc1cf8b76d3fbce74`。nightly baseline = `sha256:d5fc59a4d548162edc802ed4b0cd8081413fd5e0179f9d4c125447e7bcd7b665` / target = `sha256:f769596653f1fd3a848ba36a9673c5d57c2b3679daa68633ae7d8613d6f68f59`。builder 4 DB 全て同一(`…20260630120316-69ab575c2ebe`)
- **判定**: **upstream-driven (a)**(UEK の定期大型カーネル advisory)
- **対応**: promote(efd1f429 → :0、f7695966 → :nightly、07-08 01:16)。override は「822 CVE 級のイベントはどんな閾値でも人間が見るべき」として当面追加せず(参考値として `oracle_10=50` / `oracle_9=20` に言及)

#### A-16. 2026-07-08 〜 07-09 — VulnCheck NVD2 vcConfigurations 一斉ロールアウト(per-source ガード拡張の直接動機)

- **Run**: 07-08 の DB [28968111472](https://github.com/vulsio/vuls-data-db/actions/runs/28968111472)(Dn+Do: amazon_2_extra_kernel 6.3% / amazon_2023 5.4%。候補 `sha256:fac46aa3f42eb436d2aeb5c5b6895c6785529266e0e907511a521378a46f61ce` は 07-09 01:17 に :0 / :latest へ手動 promote)→ 07-09 01:24 の DB [28987458616](https://github.com/vulsio/vuls-data-db/actions/runs/28987458616) で cpe が FAIL。nightly 側は [28990615158](https://github.com/vulsio/vuls-data-db/actions/runs/28990615158)(amazon + cpe 29.0%)
- **FAIL**(run 28987458616): DB **cpe 28.9% > 10%**(KB 0.0%)。Added 587 / Removed 64 / **Changed 135,457** root IDs
- **Anchors**: baseline = `fac46aa3…` / target = `sha256:5343fc0beef13ffa26e7fe025d792f39bd2ec4d6c2eae04b19748bc8e733dd37`
- **Smoking gun**: raw `vuls-data-raw-vulncheck-nist-nvd2` の単一コミット `0bab5f5`(07-08 13:24 UTC)で **145,672 files / +9,575,634 / −872,147 行**。VulnCheck が legacy CVE を含む全年代に生成 CPE 設定 `vcConfigurations` を一斉付与(例: CVE-1999-0001 に `matchCriteriaId: ""` の vcConfigurations 新規付与、CVE-2015-0198 はワイルドカード → 明示バージョン列挙 + `vcVulnerableCPEs`)。60,095 ファイルが detections ブロックを新規獲得。Removed 64 は jvn-feed-rss の JVNDB ID 振り直し(JVNDB-2026-0221xx)で別件
- **判定**: **upstream-driven**(VulnCheck のデータ拡充ロールアウト)として promote(5343fc0b → :0、1c1ef17c → :nightly、07-09)
- **重要な後日談 — 検知退行の発見とガードの限界**: 07-09〜10 に同じ digest ペアで per-source 拡張版ガードを実測した結果:
  - 旧ガードの「cpe 28.9%」の実体は **`cpe / vulncheck-nist-nvd2` 単独で 189.6%**(他 6 source は ≤5.4% で PASS)— ecosystem 一括の変動率は、大きな source(NVD)がノイズフロアになって小さな source の異常を希釈する
  - 新設の `cpe_*` 検知 fixture では **vulncheck 経由の CPE 検知が 60〜75% 消失**していた(cpe_jvn: 69→17 CVE = 75.4% 消失、cpe_cisco: 67→24 = 64.2%、cpe_nvd: 24→19)。根本原因は VulnCheck が legacy CVE を現代 CPE 語彙で再生成したことで `part:vendor:product` インデックスからマッチが外れたこと — つまり **promote した DB には実検知の退行が含まれていた可能性**
  - この分析が **per-source 閾値 + CPE fixtures(PR #196、vuls2#400、integration#43、07-14 導入)** の実戦的根拠となった。per-source 版は同ペアで `cpe/vulncheck-nist-nvd2 189.6%` をピンポイントに示せることを検証済み(実行時間: diff db 1m07s / detection 8m40s @4 workers)

---

#### A-17. 2026-07-11 〜 07-14 — ubuntu:25.10 / cpe / windows / tumbleweed の複合クラスタ

07-11 01:15 の DB [29134285305](https://github.com/vulsio/vuls-data-db/actions/runs/29134285305) 以降、両系統の全 run が FAIL し続けた(promote は 07-09 を最後に停止)。FAIL 行は run 間で同一(= flaky ではなくデータ起因):

- **DB `ubuntu:25.10` 47.8%**(07-11 から一定)— ubuntu-cve-tracker 由来
- **DB `cpe` 12.0〜12.1%** — vulncheck 系の継続 churn
- **Dn `windows_11_21h2` / `windows_11_22h2`** — 07-12 に 20.4% / 20.0%(+ windows_10_20h2 17.1%)で発生し、baseline 前進により 07-13 には 11.0% / 10.8% に減衰(それでも閾値 10% 超)。A-13 と同型の月次 Edge/MSRC churn
- **Dn+Do `opensuse_tumbleweed` 5.7〜6.0%**(**db-main のみ**)— `opensuse_tumbleweed=15` override が db-nightly にしかない非対称の顕在化
- 07-14 01:07 の run 29297780197 では **DB `ubuntu:14.04` 13.5%** も追加
- **07-14 07:40 の DB [29315353553](https://github.com/vulsio/vuls-data-db/actions/runs/29315353553) は PR #196(per-source 化)マージ後の初 run**: 新しい per-source レポートが新設 CPE fixture の初期通過を default 5% で判定し、`cpe_jvn/vulncheck-nist-nvd2` **305.9%**、`cpe_cisco/vulncheck-nist-nvd2` 66.7%、`cpe_nvd/vulncheck-nist-nvd2` 26.3%、`cpe_fortinet/vulncheck-nist-nvd2` 20.0% が一斉 FAIL(PR #196 が意図的に override をシードせず「実測してから設定する」方針を採った初期観測に相当)。候補 digest `sha256:32316e7f3c789544ef2061d842e216e93bbda763f9f7874f3a49b6298ee08ba1`
- クラスタ内の非ガード失敗: run 29277164780(07-13 19:06)は runner の shutdown(exit 143)、run 29300917807(07-14 02:22)は Build DB の `failed to dotgit pull`(同日の Fetch All / Backup Daily 失敗と相関する上流/GHCR pull 側の部分障害)
- **判定(暫定)**: ubuntu:25.10 / windows / tumbleweed / ubuntu:14.04 は upstream-driven の定常 churn + override 未整備(per-source 化直後の移行期)。cpe_* per-source 群は fixture 新設に伴う初期 churn の実測フェーズ
- **対応(進行中)**: per-source override のシード値を実測から決定する段階。tumbleweed の main/nightly 非対称解消、windows 10% 組の 20〜25% 化(A-13 で提案済み)が候補
- **解消**: 07-14 09:51 に手動 promote(`:0 <- sha256:32316e7f…` = run 29315353553 の候補、続けて 09:52 に `:nightly <- sha256:88ae3917…`)。以後 07-14 12:57 / 18:55、07-15 01:05(DB)・02:21(Nightly)は成功し、系列終息

#### A-18. 2026-07-15(進行中)— July Patch Tuesday(microsoft-msuc)+ NVD の PAN-OS CVE 一括 Analyzed 化

- **Run**: DB [29398326912](https://github.com/vulsio/vuls-data-db/actions/runs/29398326912)(07-15 07:43、schedule)。det_master + db が FAIL、det_old は PASS(vuls0-old は cpe 系 scan-result を持たない)。後続 Nightly [29399593434](https://github.com/vulsio/vuls-data-db/actions/runs/29399593434)(08:06)も予想どおり同型 FAIL(det_master: cpe_paloalto 9.7% + db: microsoft-msuc KB 55.9%、候補 `14a1c1ed…`)。07-15 09:50〜10:00 に両候補を手動 promote(`3c9a3e3b…` → :0、`14a1c1ed…` → :nightly)して収束、以降の scheduled run は PASS に復帰した
- **FAIL**: DB **cpe_paloalto / nvd-feed-cve-v2 9.7% > 5.0%**(185 → 203、Added 18 / Removed 0)+ Dn **microsoft / microsoft-msuc KB 55.9% > 35.0%**(Added KB 11 / Changed KB 518)。`microsoft-wsusscn2` は 33.6% で僅差 PASS
- **Smoking gun(msuc)**: extracted `e4d179d..d7b60ad` で 530 files / +11,961 行。新 KB 11 件は 5099414/5099415/5099444/5099445/5099535/5099536/5099538/5099539/5099540/5101650/5102202 = "2026-07 Security Monthly Quality Rollup" / "Cumulative Security Update" 群(7/14 Patch Tuesday)。既存 KB `3148198.json` に新ロールアップ 5099415/5099444 への supersedes 追記 — この月次リップルで 518 KB が Changed。raw も `9173d56..bfcac98` で新規 29 update GUID(例: `051ffa01-…` = KB5099415 IE11 CSU for WS2012R2)
- **Smoking gun(paloalto)**: raw nvd-feed-cve-v2 `7b56401..cde8d3e` で CVE-2026-0256 等 26 件の PAN CVE が `"vulnStatus": "Awaiting Analysis"`(configurations 0 件)→ `"Analyzed"`(lastModified 2026-07-14T16:39Z、`cpe:2.3:o:paloaltonetworks:pan-os:*` criteria 付与)。2026-05-13 公開の PAN 5月バッチを NVD が 7/14 に一括エンリッチしたもので、うち 18 件が cpe_paloalto scan-result にヒット
- **Rule-out**: created_by 両 DB 一致(`vuls v0.0.1-alpha.0.20260714011358-2af27b6858b4`)。`pkg/{extract,fetch}/microsoft` は窓内 commit ゼロ。`pkg/extract/nvd` の 24eb1b6(vuls-data-update#874)は nvd 窓内だが、diff 確認の結果 `len(ds)==0` 時に Segments を省略するだけで Detections には触れず、+18 detections の原因たり得ない
- **Anchors**: baseline `sha256:27edceaea0bf6407c120b2940c38f421264d137b6bd1afd14fa934106aefb8cd`(07-15 02:54 に run 29380764321 が promote)/ target `sha256:3c9a3e3b1f74a3a74f9d4ba0a3233042c5bbbc4acf2a8a8a319da622412aa18b`
- **判定**: **upstream-driven (a)** ×2(月例 Patch Tuesday リップル + NVD バッチ解析)
- **対応**: promote 推奨(コマンド提示、実行は人間)。cpe_paloalto は**初トリップ**(guard-failures.tsv に前例 0)のため原則どおり override 見送り。microsoft=35 は月例イベントで 55.9% を記録 — 次回 grooming で 60 前後への引き上げ、または per-source key 化(msuc のみ緩和し wsusscn2 は 35 維持)を検討

#### A-19. 2026-07-16 — July Patch Tuesday 第2波: microsoft-cvrf の月例 CVE 一括流入(A-18 の続報)

- **Run**: DB(Nightly) [29466660712](https://github.com/vulsio/vuls-data-db/actions/runs/29466660712)(07-16 02:28、schedule)。det_master のみ FAIL(det_old は windows scan-result を持たない 42 ファイル構成のため PASS、db も PASS = msuc/wsusscn2 の KB 変動は A-18 の promote で baseline 側に取り込み済み)
- **FAIL**: Dn `windows_server_2019` **23.2% > 10.0%**(1360 → 1676、Added 316 / Removed 0)、`windows_11_25h2` 21.6% / `windows_11_24h2` 21.5%(> 20.0%)、`windows_server_2016` 16.8% / `windows_server_2012` 15.3% / `windows_server_2012_r2` 15.2%(> 10.0%)。`windows_server_2022` 18.6%、`windows_server_2025` 16.7%、`windows_10_22h2` 9.8% など他 windows target は僅差 PASS(いずれも Removed 0 の純増)
- **Anchors**: baseline `sha256:b68fcdc31082ae0122ca65b15841c77686d9c6613c97b6d121c074552ad945c5`(07-15 20:40 に run 29443320259 が promote した :nightly)/ target `sha256:fd0657e1b5a37e141a05c67dca937b5997380aaf0a4f7405a32a6bff0119d0a3`。`created_by` 両 DB 一致(`vuls v0.0.1-alpha.0.20260714011358-2af27b6858b4`)→ builder 除外
- **Smoking gun**: microsoft-cvrf raw `fbd6515..4b3d286` のうち `9683fd13`(07-15 01:13Z)が `2026-Jul/` 配下に **572 ファイル新規追加(+442,195 行)** = July 2026 Security Updates(revision 245、2026-07-15T01:41)。extracted は `efc33ad`(07-14 03:21)→ `2b63690`(07-15 21:16)の単一 commit で**新規 CVE 589 / 変更 3,324 ファイル**。代表: `data/CVE/2026/CVE-2026-49164.json`(Windows Active Directory Domain Services RCE、Windows Server 2019 対象)が raw(`2026-Jul/2026/CVE-2026-49164.json`)・extracted とも新規ファイル
- **Rule-out / 特記**: 窓内に extractor commit `e3709d2`(vuls-data-update#885「handle 2026-Jul products and placeholder FixedBuild」07-15 09:25)があるが、diff は SQL Server 2022 CU25 / 2025 CU6・VS 2026 18.7 の製品名リスト追加と CVE-2026-50480(WS2012/2012R2)の placeholder FixedBuild "1.000" 除去のみで、Added 316〜393 件(全て新規 July CVE ID の新規ファイル)の原因たり得ない。むしろ 2026-Jul 製品対応の enabling fix で、cvrf extraction が raw 到着(07-15 01:13)から 21:16 まで遅れた説明になる。この遅延により 07-15 の nightly(13:39 / 19:07)は July CVRF 未取り込みの extracted(`efc33ad`)のまま PASS し、07-16 02:28 の本 run が**最初の取り込み**となって月次バッチが一括ヒットした
- **判定**: **upstream-driven (a)**(月例 Patch Tuesday。A-18 の msuc/KB 波に続く cvrf/detection 波 — 同一上流イベントの extraction 遅延による時間差発現)
- **対応**: promote 推奨(コマンド提示、実行は人間)。windows_server_2019/2016/2012/2012_r2 は override 10 のまま月例イベントで 15〜23% を記録し、05-13(15.6〜18.3%)・06-06〜08(max 76.3%)・07 月と反復性が確立 — 次回 grooming で server 系 detection override の 20〜25 への引き上げを検討(A-18 の microsoft=35 見直しと同時に)

#### A-20. 2026-07-22 — VulnCheck NVD2: Cisco ASA CPE part 修正(A-16 検知退行の回復)+ 2026 kernel CVE への CPE 一括付与

- **Run**: DB [29882532080](https://github.com/vulsio/vuls-data-db/actions/runs/29882532080)(07-22 01:14、schedule)。det_master のみ FAIL(det_old は cpe 系 scan-result を持たず PASS、db も PASS — `cpe / vulncheck-nist-nvd2` は Detection 1.2% / KB 0.0% で per-source 化後の希釈問題なく通過)
- **FAIL**: Dn `cpe_cisco / vulncheck-nist-nvd2` **204.5% > 5.0%**(22 → 67、Added 45 / Removed 0)+ Dn `cpe_kernel / vulncheck-nist-nvd2` **18.4% > 5.0%**(1000 → 1184、Added 184 / Removed 0)
- **Anchors**: baseline `sha256:b3f72f2167e617f781fd310c68cc6ddf5c6ee6f359975196f3ecdff5fbe3649b`(07-21 20:29 に run 29859526698 が promote した :0 / :latest)/ target `sha256:fce6955477585da6b7e40976c5c127ba7f387e7e606ae8e93c3a4a3b7504b81a`。`created_by` 両 DB 一致(`vuls v0.0.1-alpha.0.20260714011358-2af27b6858b4`)→ builder 除外。窓(extracted `3c63eeb` 07-21 07:29Z → `ead1929` 07-21 20:45Z)内に `pkg/{extract,fetch}/vulncheck` のコミットなし(vuls-data-update 全体でも rocky updateinfo fetcher の #890 1 件のみ)→ extractor 除外
- **Smoking gun(cisco)**: raw `7e462d1..1f21242`(単一コミット、07-21 13:12Z、5,925 files / +744,008 行)で 48 ファイルの ASA 系 CVE が `cpe:2.3:o:cisco:adaptive_security_appliance_software` → `cpe:2.3:a:…` に part 修正(例: `2013/CVE-2013-5510.json`、`2012/CVE-2012-5010.json`、`2017/CVE-2017-6610.json`)。A-16(07-08 vcConfigurations ロールアウト)で 67 → 24 に退行していた cpe_cisco 検知が **67 に完全回復**(baseline 22 は退行後の値)。Added 45 件は全て 2012〜2017 年の ASA CVE
- **Smoking gun(kernel)**: 同じ raw コミットで `2026/` 配下 **3,147 ファイル(+728,770 行)**に `cpe:2.3:o:linux:linux_kernel` の versionEndExcluding 付き criteria を一括付与(例: `2026/CVE-2026-63912.json` +1,660 行)。kernel CNA 発番で CPE 未整備だった 2026 年 CVE 群への VulnCheck 生成 CPE エンリッチで、cpe_kernel fixture に 184 件が新規ヒット。extracted `3c63eeb..ead1929`(4,295 files / +267,270 行)に忠実に伝播(`data/2013/CVE-2013-5510.json` で同じ o:→a: 差分を確認)
- **判定**: **upstream-driven (a)**。cpe_cisco 側は A-16 で promote に混入した検知退行の**上流側修正による回復**(検知能力の改善)、cpe_kernel 側は純増エンリッチ
- **対応**: 07-22 06:01 に人間が target digest を `:0` へ手動 promote([run 29895474297](https://github.com/vulsio/vuls-data-db/actions/runs/29895474297))。`:latest` は同時点では旧 baseline のまま。cpe_cisco/vulncheck-nist-nvd2 は baseline 22 の極小 fixture で 1 バッチ 200% 超えは構造的だが、今回は回復イベントで反復性未確立のため原則どおり override 見送り。Nightly [29886026482](https://github.com/vulsio/vuls-data-db/actions/runs/29886026482)(07-22 02:30 開始)は調査時点で diff guard 実行中

#### A-21. 2026-07-26 — Cisco openVuln API: advisory↔version マッピングのサイレント再生成(productNames 大規模入れ替え)

- **Run**: DB(Nightly) [30216168106](https://github.com/vulsio/vuls-data-db/actions/runs/30216168106)(07-26 19:06、schedule)
- **FAIL**: Dn `cpe_kernel / vulncheck-nist-nvd2` **16.9% > 5.0%**(1149 → 1317、Added 181 / Removed 13 — A-20 の kernel CPE エンリッチ継続で既知)+ DB `cpe / cisco-json` **10.9% > 10.0%**(KB 0.0%)
- **Anchors**: baseline `:nightly` = `sha256:374ad451f62c31e03407d8dcb62796fc6a8686774906a65718b83fe17a7badce`(07-23 の成功 nightly run 30037081591 が自動 promote)/ target = `sha256:39516634a7c1c5f4da2ede69d4d4906a429902ed2d2e74483ecdab65bc40a51c`(20:23:09 push。並走してキャンセルされた DB run 30215503643 の候補 `3c53dea4…` が 22 秒前に push されており GHCR 突合時に紛らわしい)。`created_by` 同一(`vuls v0.0.1-alpha.0.20260714011358-2af27b6858b4`)→ builder 除外。窓内に `pkg/{extract,fetch}/cisco` のコミットなし(main / nightly 両ブランチ)→ extractor 除外
- **Smoking gun**: raw cisco-json `294641e8`(07-23 01:25Z)→ `5591d648`(07-25 12:55Z)の 4 コミットで 114 files / +1,570 −2,111 行。**93 advisory で productNames が計 2,022 件削除 / 1,481 件追加(純減 541)**。代表例 `2014/cisco-sa-20140326-sip.json` は productNames **149 → 36** — 削除は全て `15.3(3)JD/JDA/JF/JG/JH/JI/JK/JN/JP*` 系(**autonomous AP 用 IOS train**)。削除の族別内訳: Cisco IOS XE 1,044(ほぼ同数の 1,023 追加 = advisory 間の付け替え。例: `16.6.10` が smi2 から消え 20180926-cmp に追加)、Cisco IOS 918(AP train の削除が支配的、追加は 458)、WLC 8.x 60(sisf-dos の 1 advisory から全削除)。extracted `5595b926..7c3ad7d0` に忠実に伝播(同 advisory の criteria から `cpe:2.3:o:cisco:ios:15.3\(3\)jd12` 等が削除)→ cpe fixture の cisco-json 検知 85 advisory が変動
- **上流イベントの性質**(深掘り調査): 影響 advisory の `lastUpdated` / `version` / `status` は**一切変わっていない** — 再公開ではなく、openVuln API がサーバ側で生成する advisory↔affected version マッピングの**サイレント再生成**。この日次 churn は 07-17 頃から継続(07-17: 110 files / 07-18: 72 / 07-19: 42、07-20〜22 は静穏、07-23 13:19Z 以降再開。毎日 12:45〜13:15Z 頃)。削除は flap ではなく持続的(07-26 HEADB `d3f1e04a` 時点で 2,022 件中 39 件しか復活せず)。API changelog・CiscoPSIRT/openVulnAPI issue にアナウンスなし。2014 年の IOS SIP advisory に 2020 年代の AP train が載っていた等の過剰マッピングの整理とみられ、データ品質改善の側面が強いが、AP/WLC 系 version を CPE スキャンしている利用者には検知消失になる
- **判定**: **upstream-driven (a)**(4 日分の窓に日次 churn が蓄積して 10% 閾値を 0.9pt 超過。baseline が動けば 1 日分の窓に戻り通過見込み)
- **対応**: 候補は上流データを忠実に反映しており promote 可(判断・実行は人間)。churn 継続中のため override(`db_change_rate_threshold_overrides` に `cpe=15` 等)は「promote 停滞で窓が伸びた時だけ再発する」性質を見極めてから

#### A-22. 2026-07-28 — A-21 継続: promote 停滞 5 日で debian_12 も閾値超え(kernel CNA の CVE 一括発番が 2 ソースに同時伝播)

- **Run**: DB(Nightly) [30391488230](https://github.com/vulsio/vuls-data-db/actions/runs/30391488230)(07-28 19:20、schedule)。det_master / det_old / db の 3 チェックすべて FAIL
- **FAIL**: Dn `cpe_kernel / vulncheck-nist-nvd2` **17.3% > 5.0%**(1149 → 1322、Added 186 / Removed 13)+ Dn・Do `debian_12 / debian-security-tracker-salsa` **5.2% > 5.0%**(4564 → 4797、Added 235 / Removed 2)+ DB `cpe / cisco-json` **16.3% > 10.0%**(KB 0.0%。keys 1317 → 1317 で Added/Removed 0・**Changed 121**、criterions 1672 → 1672・matched 1536 = 内容の入れ替えのみ)
- **Anchors**: baseline `:nightly` = `sha256:374ad451f62c31e03407d8dcb62796fc6a8686774906a65718b83fe17a7badce`(**A-21 と同一** — 07-23 の成功 nightly run 30037081591 の promote 以降 :nightly は 5 日間不動。07-24 02:32 の run 30061897399 が fedora:45 / fedora-api **269.6% > 50.0%**(DB)で FAIL して以降、全 nightly run が連続 FAIL のストリーク中)/ target = `sha256:44fb64511c450a9feb3279dd4e77330dd1f849d1c49743bfec3b4c1959d227c0`(20:55:27 push、untagged)。`created_by` 同一(`vuls v0.0.1-alpha.0.20260714011358-2af27b6858b4`)→ builder 除外。窓(07-23 〜 07-28)内に `pkg/{extract,fetch}/{vulncheck,debian,cisco}` のコミットなし → extractor 除外
- **Smoking gun(cpe_kernel / debian_12 — 同一上流イベント)**: Linux kernel CNA が 07-24 〜 07-25 に 2026 年 CVE を一括発番(CVE-2026-64187〜64317 ほか)。debian_12 の Added 235 件中 **213 件が CVE-2026-64xxx**
  - VulnCheck NVD2 側: raw `82864256..ea602cc1`(12,320 files / +652,808 −51,656)のうち当該バッチ系連番が 850 files。例 `2026/CVE-2026-64214.json`(published 2026-07-24T16:16Z、raw commit `73158baf33c` 07-25 01:23Z で追加)は `cpe:2.3:o:linux:linux_kernel` の versionEndExcluding 付き vcConfigurations(6.1.175 / 6.6.142 / 6.12.92 / 6.18.34 等)を発番直後から持ち、cpe_kernel fixture に直撃(A-20 で観測した VulnCheck 生成 CPE エンリッチが新規発番分にも即日適用される構造)
  - debian salsa 側: raw `c00c9b43..8a623766`(3,273 files / +46,750 −18,036)に同一 CVE 群が流入。同じ `CVE/2026/CVE-2026-64214.json` が raw commit `81750f6de62`(07-25 01:36Z)で追加され、`[bookworm] - linux 6.1.176-1`(fixed)の annotation で debian_12 検知に加算。extracted `b72a9134..c448abf4`(2,623 files / +226,386)へ忠実に伝播(`data/CVE/2026/CVE-2026-64214.json` は extracted commit `a2f241d75e` 07-25 で追加)
- **Smoking gun(cisco)**: A-21 の productNames サイレント再生成 churn が**継続・蓄積**。raw `294641e8..e27f02c5`(6 daily commits、151 files / +1,936 −2,542)。代表例 `2014/cisco-sa-20140326-ios-sslvpn.json`(raw commit `5591d648` 07-25 12:55Z)で `15.3(3)JF/JI/JK/JPI/JPJ/JPK` 系 AP train version が大量削除。窓拡大により A-21 の 10.9% → **16.3%** に上昇
- **判定**: **upstream-driven (a)**(3 ペアとも)。本質は promote 停滞による窓の伸長(4 日 → 5 日)で、debian_12 の 5.2% は kernel CVE 一括発番という単発イベントが 5 日窓でぎりぎり global 閾値 5% を踏んだもの。baseline が動けば 3 ペアとも 1 日窓に戻り通過見込み
- **対応**: 候補は上流データを忠実に反映しており promote 可(判断・実行は人間): `gh workflow run promote-digest.yml -R vulsio/vuls-data-db -f digest=sha256:44fb64511c450a9feb3279dd4e77330dd1f849d1c49743bfec3b4c1959d227c0 -f tag=nightly`。kernel CNA は今後もバッチ発番を繰り返す(A-20 の 18.4%、A-21 の 16.9%、今回 17.3% と cpe_kernel は 3 連続で 5% 閾値を大幅超過、baseline 1149 に対し 1 バッチ 180 件超 ≒ 16% は 1 日窓でも FAIL する規模)ため、`detection_change_rate_threshold_overrides` への `cpe_kernel=25` 等の追加を検討する段階

#### A-23. 2026-07-31 〜 08-03 — Fortinet CSAF の製品 whitelist 追加 + 8 月初旬の windows 月次 churn

- **Run**: DB [30617502603](https://github.com/vulsio/vuls-data-db/actions/runs/30617502603)(07-31 08:46)ほか、08-03 01:20 まで両系統で継続
- **FAIL**: Dn `cpe_fortinet / fortinet-csaf` **8.1% > 5.0%**(37 → 40、Added 3)。08-01 12:45 の run 以降は Dn `windows_11_21h2 / microsoft-cvrf` **25.9% > 10.0%**(1484 → 1868、Added 384 / Removed 0)を筆頭に windows 系 6 target が同時 FAIL(21h2 25.9% / 22h2 25.4% / 10_20h2 22.2% / 11_23h2 20.6% / 10_21h1 11.5% / 10_22h2 10.6%、いずれも純増)
- **判定**: fortinet 側は **extractor-driven(意図的変更)** — 窓内に vuls-data-update `6217065`(07-31 03:34、#901 "fix(extract/fortinet): add FortiSIEMWindowsAgent to the product whitelist")があり、whitelist 追加により検知対象製品が増えた。windows 側は **upstream-driven (a)**(A-13 と同型の月初 Edge / MSRC churn。窓内に `pkg/{extract,fetch}/microsoft` のコミットなし)
- **対応**: promote(判断・実行は人間)。windows 系は 05-13・06 月・07 月に続き 4 か月連続で月次イベントが 10〜25% を記録しており、A-19 で提案した server 系 override 20〜25 への引き上げは 8 月 grooming(#209)で再導出の対象となった

#### A-24. 2026-08-06 — msuc seed の一括登録(**orchestration-driven の初事例**)

- **Run**: DB [31083666812](https://github.com/vulsio/vuls-data-db/actions/runs/31083666812)(08-06 08:08、schedule)。候補 `sha256:b98e112f97dd703d…`
- **FAIL**: DB `microsoft / microsoft-msuc` **KB 55.9% ではなく KB 211.3% > 35.0%**(Detection 0.0%)
- **判定**: **orchestration-driven**。上流も抽出器も変わっておらず、原因は我々自身が取得対象の seed を拡張したこと。窓内の vuls-data-db コミットは #211(08-05 05:51、supersedes リストにしか現れない KB の backfill seed、+513 行)、#214(.NET Framework)、#215(SQL Server / servicing stack / Exchange)、#216(08-05 11:51、live catalog の Windows KB、+1,380 行)、#217(08-06 01:44、Office KB、+1,974 行)。最後の #217 マージの 6 時間後に発動しており、KB 集合の急拡大がそのまま KB Change Rate に出た
- **意義**: 「上流でもコードでもなく、**何を取りに行くかの設定**が原因」というカテゴリが初めて顕在化した。これを機に triage 手順へ orchestration 除外ステップを追加(vuls-data-db #222、08-07)。ガードは自分たちの取得範囲拡張も検知するという当然の帰結だが、手順書がそれを想定していなかった

#### A-25. 2026-08-06 〜 08-10 — Fortinet CVRF の履歴的アドバイザリへの検知補完(**extractor-driven の意図的変更**)

- **Run**: DB(Nightly) [31085326818](https://github.com/vulsio/vuls-data-db/actions/runs/31085326818)(08-06 08:32)以降、08-10 18:37 まで継続(14 run / 106h)。候補 `sha256:762a64e61022fdad…`
- **FAIL**: Dn `cpe_fortinet / fortinet-cvrf` **73.6% > 5.0%**(163 → 283、Added 120 / Removed 0)+ DB `cpe / fortinet-cvrf` **135.5% > 10.0%**
- **Smoking gun**: vuls-data-update #892(`5daab53`、08-06 01:14 マージ)"feat(extract/fortinet/cvrf): supplement detection for historical advisories without product_statuses"。Fortinet は 2022 年以前の CVRF に `product_statuses` / `product_tree` を持たず、当該期間のアドバイザリは content-only で抽出されていた。この PR が埋め込みの補完テーブルを追加し、statuses 空の 465 件のうち **422 件が検知を獲得(693 product 行)**、検知を持つファイルが **643 → 1,065 件**に増加。マージの 7 時間後に初 FAIL
- **判定**: **extractor-driven(意図的変更)**。A-8(CPE match quality 分類)と同型で、退行ではなく検知能力の向上。ガードは「意図した拡張であっても規模が大きければ人間に見せる」設計どおりに動作した

#### A-26. 2026-08-10 〜 08-11 — microsoft-servicing データソースの新規追加(orchestration-driven)

- **Run**: DB(Nightly) [31390913505](https://github.com/vulsio/vuls-data-db/actions/runs/31390913505)(08-10 13:02)ほか。候補 `sha256:1b54707505ebc143…`
- **FAIL**: DB `microsoft / microsoft-servicing` **KB 100.0% > 10.0%**(Detection 0.0%)
- **判定**: **orchestration-driven**。vuls-data-db #219(`2f33d2e`、08-10 06:39)が `microsoft-servicing` ソースを新設(10 シャード / 201 seed)、依存する vuls-data-update #919(fetch)・#921(extract、`5351d5e` 08-10 06:39)と同時に有効化された。baseline 側に当該ソースが存在しないため変動率は定義上 100% になる
- **意義**: 新規ソース追加は「baseline 不在 → 100%」で必ず発動する。A-24 と併せ、**自分たちのパイプライン拡張は 2 通りの経路(seed 拡張・ソース新設)でガードを発動させる**ことが確認できた。運用としては事前に想定できるイベントであり、閾値ではなく「拡張時は 1 回 promote する」で吸収するのが妥当

#### A-27. 2026-08-13 〜 08-16 — fedora:46 の立ち上がり(**観測史上最大 3433.3%**)と 8 月中旬の複合 churn

- **Run**: DB(Nightly) [31703167579](https://github.com/vulsio/vuls-data-db/actions/runs/31703167579)(08-13 13:05)ほか、08-16 18:25 まで継続。候補 `sha256:18f07c76d17c3e9e…`
- **FAIL**: DB `fedora:46 / fedora-api` が 08-13 00:49 の **66.7%** → 12:36 の **2020.0%** → 13:05 の **3433.3%** と 1 日で 2 桁上昇(いずれも > 10.0%)。同時に `fedora:45` 12.4〜12.6%。以降 08-15 に Dn `cpe_cisco / vulncheck-nist-nvd2` 30.0%(30 → 21、Removed 9 の純減)、08-16 に Dn・Do `debian_12 / debian-security-tracker-salsa` 8.7% → 10.5%(5097 → 5631、Added 535)、`debian_10` 5.2〜6.3%、`debian_9` 5.2%
- **判定**: **upstream-driven (a)** + **threshold-only(構造要因)**。fedora:46 は新リリースの立ち上がりで baseline が極小(数十件規模)のため、上流が advisory を投入するたびに変動率が桁で跳ねる。P-2 期の新ディストリ立ち上がり(ubuntu:26.04 等)と同型で、データとしては正常。debian は kernel CVE の継続流入(A-22 と同系)、cisco は A-21 の productNames 再生成 churn の継続
- **意義**: **小 baseline 問題の極端例**。3433.3% という値は「異常の大きさ」ではなく「分母の小ささ」を測っている。新リリース検知を追加した直後は per-target override かガード対象からの一時除外が要る、という運用則を再確認した

---

## 5. 集計と考察

### 5.1 全数統計(2026-04-23 〜 2026-08-16 の 116 日間)

- 総 run 数: **943**(DB 477 + DB(Nightly) 466、6 時間おき cron)。窓は 2026-04-23T00:00Z 〜 08-17T00:00Z(= 08-16 まで)の 116 日間。08-17 00:25 の DB run 31981986529(ガード FAIL)は窓外
- failed run: **476**、うち **"Run diff guard" ステップでの失敗 420**
- 420 の内訳: **threshold trip 418** + ガード内インフラ障害 2(07-08 の baseline fetch `invalid descriptor size` ×2)
- **有意な発動回数(fail sequence 数): 104**(DB 52 + DB(Nightly) 52) — promote 介入まで連続する FAIL を 1 つと数えたもの(隣接間隔 ≤9h で連結。中央値 2〜3 run / 最長 19 run、持続時間は中央値 11h / p90 48h / 最長 108h、単発で終息 29)。さらに main / nightly を束ね、sequence 内の source の出入りまで分解したイベントの正準単位が **69 source-episode**(§5.6)、triage 記録に基づく事例カタログとしては **約 41 イベント**(§4)
- FAIL したチェックの組合せ分布(Dn=detection master / Do=detection old / DB=diff db): **Dn のみ 133、DB のみ 100、Dn+Do+DB 85、Dn+Do 53、Dn+DB 47、infra 2**
- 週末(土日 UTC)の FAIL run は 209/418 = **50%** — 上流ではなく promote が平日日中に限られることの反映(§5.6)
- **手動 promote: 101 run / 92 unique digest(2026-04-27 〜 08-17)。92 digest 全てがガード FAIL run の候補 digest と一致** — この repo の手動 promote は 100% 「ガード FAIL をオペレータがレポート確認の上で override した」操作である。actor は shino(71)および MaineK00n(30)
- 前半窓(〜07-14T07:40Z)単独の値は 674 run(DB 343 + Nightly 331)/ 295 ガード失敗 / 1,040 FAIL 行 / 66 sequence / 50 episode / promote 59 digest であった。後半窓(07-14 〜 08-16)で 269 run(DB 134 + Nightly 135)・125 ガード失敗・425 FAIL 行・19 episode・promote 33 digest が加わっている(674 + 269 = 943)
- 全 run の詳細は付録: [`diff-guard-incidents-data/`](diff-guard-incidents-data/)(run 表 02a〜02e、promote 履歴 03、機械可読 TSV、per-run ログ抜粋)

### 5.2 判定の分布(発動イベント単位)

**注**: 本節は事例カタログ(§4)単位の分布。69 source-episode 単位の帰属と証拠水準は [`04-episode-verdicts.md`](04-episode-verdicts.md) を正とする(episode 単位では 上流59 / 自前10 = 55+2+2 / 1+3+4+2)。

| 判定 | 件数 | 事例 |
|---|---|---|
| upstream-driven (a) 正当な上流変更 | 31+ | P-1, P-2(大半), P-3, P-5, A-1〜A-3, A-5, A-7, A-9〜A-11, A-13, A-15〜A-17, A-20〜A-23, A-27 ほか |
| upstream-driven (b) 一時的データ障害(**promote 阻止**) | 2 | A-4, A-12(いずれも MSRC CVRF 消失) |
| upstream-driven (c) 恒久的データ品質イベント | 2 | P-4, A-14(いずれも AlmaLinux errata 骨抜き) |
| extractor-driven(真のコードバグ、**promote 阻止**) | 1 | A-6(fedora-api の Sort 未実行) |
| extractor-driven(意図的変更) | 3 | A-8(CPE match quality 分類), A-23(fortinet whitelist), A-25(fortinet-cvrf 検知補完) |
| **orchestration-driven(取得設定の変更)** | 2 | A-24(msuc seed 一括登録), A-26(microsoft-servicing 新設) |
| vuls2-builder-driven | **0** | (A-8, A-10 で builder を精査したがいずれも無罪) |
| threshold-only(構造要因) | 混在 | P-2 の小 baseline 群、A-1(閾値非対称)、A-17 の tumbleweed 非対称、A-27(fedora:46 の 3433.3%) |

※ ストリークは 1 イベントとして数えている。1 つの発動に複数系統が同時に含まれる事例あり(P-1, A-9, A-10, A-14, A-17, A-23, A-27)。

**証拠水準について**: 前半窓(〜07-14)の事例と、後半窓で非上流と判定した事例(A-23 の fortinet 側 / A-24 / A-25 / A-26)は、原因となったコミットや PR の差分を直接の証拠として特定している。後半窓で upstream-driven と判定した事例は、builder(vuls2 のコミット有無)・extractor(`pkg/{extract,fetch}/<source>` のコミット有無)・orchestration(vuls-data-db のコミット)の 3 者をコミット履歴の走査で除外した上での帰属であり、raw 差分の smoking gun まで確認したのは A-20〜A-22 等の代表事例に限られる。

### 5.3 ガードが「実害を防いだ」事例

設計目的(壊れた DB の公開防止)を直接達成したのは以下:

1. **A-4 / A-12(MSRC CVRF 消失、2 回)**: 上流 API の一時障害で Windows の月次 CVE 全体(1,200 件超)が欠落した DB を公開寸前で阻止。公開されていれば動機インシデント 1 と同型の大量 false negative
2. **A-6(fedora-api Sort バグ)**: extractor の非決定性バグを DB 構造ドリフトとして検出し、修正 PR(vuls-data-update#854)につなげた。「上流のせいではないコード起因の異常」をガードが実際に捕まえた唯一の事例
3. **(限定的)A-16(VulnCheck rollout)**: 当時のガードは FAIL を出したが分解能不足で「28.9% の cpe 変動」としか言えず promote された。事後の per-source 分析で実検知退行(vulncheck 経由 CPE 検知 60〜75% 消失)が判明し、ガード側の改良(per-source 化)に帰結。「発動したが判定を誤りかけた」教訓事例

### 5.4 false positive 論 — 「正当な変更で FAIL する」ことの扱い

発動イベントの大半(約 15/21)は正当な上流変更である。これを「ガードの false positive」と見るかは設計思想による:

- 本ガードは fool-proof の**安全ネット**であり、「大きく動いたら人間が見る」が仕様。正当な変更でも 822 CVE の UEK advisory(A-15)や 5,312 criterions のマスアップデート(A-3)は「見るに値する」イベントであり、レポートを確認して promote する運用は設計どおり
- 一方で、**繰り返し発生する既知の churn**(Patch Tuesday / Edge 月次、新ディストリ立ち上がり、rolling release)で毎回止まるのは運用コスト。対策が per-target(→ per-source)override(観測ピーク + ヘッドルームで設定し、真の異常はなお捕捉)と grooming 運用
- FAIL 中は promote が止まるため **baseline が停滞し、同じ差分で 6 時間おきの cron が再 FAIL し続ける**。295 という run 数はこの増幅を含む(イベント数は約 21)。ストリーク長は「発動頻度」ではなく「復旧までの人間の応答時間」を反映する(最長は P-2 期の数日規模、平常時は半日〜1 日)
- 手動 promote 59 digest がすべてガード FAIL 候補だったという事実は、「ガード + 人間 review + 監査証跡付き override」という運用ループが実際に一貫して回っていたことを示す

### 5.5 発見されたガードの盲点(と対策)

| 盲点 | 発見事例 | 対策 |
|---|---|---|
| KB Change Rate は KB キー集合しか見ず、CVE エントリ大量消失で 0% を返す | A-4 | triage skill に警告として成文化(「KB 0% ≠ 変化なし」) |
| detection(old)は windows fixture を除外しており microsoft データを評価しない | A-4 | 既知の制約として明記(vuls0_old_ref bump で解除予定) |
| ecosystem 一括の変動率は大 source がノイズフロアになり小 source の異常を希釈 | A-16 | per-source 閾値 + CPE fixtures(PR #196、07-14 導入) |
| baseline は「タグの現在値」ではなく「FAIL 時点の指し先」— 自動 promote と手動 promote の 2 経路があり取り違えやすい | A-2 ほか多数 | triage skill の手順に成文化 |
| 一時障害型(A-4/A-12)は上流回復を待つしかなく、fetch 側に「月ドキュメント丸ごと消失時は commit しない」ガードがない | A-12 | 検討事項として記録(未実装) |
| override の main/nightly 非対称が片系統だけの慢性 FAIL を生む | A-11→A-17(tumbleweed) | grooming で両系統を同時に見る(運用課題として顕在化中) |
| 導入初期はガードが最初の FAIL で停止し、後段チェックのシグナルが隠れた | P-1(debian_13 が ubuntu:26.04 を隠蔽) | PR #144(05-08)で全チェック実行 + 集約方式に変更 |

### 5.6 定量分析 — ecosystem / source 別・時系列特性

`guard-failures.tsv` の全 FAIL 行(**1,465 行 / 418 run**)を 4 つの粒度で集計した(スクリプトと完全な出力は付録 `stats.py` / `stats-output.txt`。sequence / episode の全リストも `stats-output.txt` に収録)。粒度の定義:

- **run 行**: FAIL レポートの 1 行(ストリークで増幅される)
- **fail sequence**: 同一 workflow 内で promote 介入まで連続した FAIL の塊(**104 件** = DB 52 + Nightly 52。§冒頭参照)。main / nightly の対発火は 2 件と数えてしまい、1 sequence に別イベントが相乗りもする
- **source-episode(イベントの正準単位)**: source ごとに main / nightly を束ねた FAIL 出現時系列を作り、出現が 24h 以上途切れたら別エピソードとする(**69 件** / 116 日)。sequence の弱点を両方解消する — 対発火は 1 件に束ねられ、sequence 内での source の途中参入・再燃は別エピソードに分解される(例: 初発動ストリーク P-1 は microsoft / ubuntu / debian の 3 エピソードに、A-17 の複合クラスタは 5 エピソードに分解される)
- (補助)**target-event**: 同一ターゲット単位で同様に数えたもの(**191 件**。windows_* のような multi-target 同時発火で膨らむ)

**注記(2026-08-17 更新)**: 本節の per-source 表と曜日・月内分布の詳細分析は前半窓(〜07-14、50 episode)時点の記述である。後半窓を含む全期間(69 episode)の再集計は `stats-output.txt` に反映済みで、episode 首位は cpe 系 14(うち後半 7 — per-source 化で分解能が上がった効果を含む)、microsoft-cvrf 13、suse-oval 8。傾向(microsoft の月次集中、週末滞留、上位 max% の桁分離)は全期間でも変わらない。後半窓では新たに orchestration-driven(A-24, A-26)と extractor 意図的変更(A-23, A-25)が加わった。

#### (1) source 別

**source 帰属の方法**: ガードレポートに source 列があるのは per-source 化(#196)後の 07-14 の 1 run のみで、それ以前の全行は **target 名 → source の静的マッピング**(`stats.py` の `src_of()`)による帰属である。その確度は 3 段階ある — ① ubuntu / debian / suse / rocky / alma / oracle / amazon / fedora の 8 家族は db-main.mk で **detection source が家族あたり 1 つしか有効でない**ため決定的。② redhat 系(redhat-cve / redhat-vex-v1-rhel の 2 source 有効)と windows_* detection(microsoft-* 4 source 有効)は名前だけでは曖昧だが、該当 episode は triage で source を個別確認済み(redhat → vex: A-9/A-10、windows → cvrf: A-1/A-4/A-12/A-13)。③ `microsoft` ecosystem の KB 系(triage 記録のない 4/24 の 134.3% 等)は msuc / wsusscn2 の可能性が残り、厳密には「microsoft-*」。`cpe` は多 source 集約のため汎用ラベルとした — ecosystem 単位で source を特定できないこと自体が A-16 の教訓であり #196 の動機。

episode がイベント数の正準。「main 関与」= DB(main)側が FAIL した episode 数(Dn のみ + 両 wf)。**表は main 関与 episode 数の降順**(同数は episodes 総数 → FAIL 行数で決着)。sequence 側は「相乗り」の観察に使う — 「関与 seq」= その source の FAIL 行を含む sequence 数(main/nightly 別々に数える)、「発火時」= sequence の最初の run から FAIL していた(= 発火主因側だった)sequence 数。

| source | **main 関与 ep** | episodes(両wf同時) | FAIL 行 | episode 持続 med/max | 関与 seq(うち発火時) | max rate |
|---|---:|---:|---:|---:|---:|---:|
| ubuntu-cve-tracker | **7** | 7(7) | 93 | 12h / 78h | 18 (17) | 53.3% |
| microsoft-cvrf | **6** | 10(5) | **479 (46%)** | 24h / 78h | 21 (14) | 134.3% |
| suse-oval | 4 | 5(3) | 47 | 7h / 67h | 9 (6) | 100.0% |
| rocky-errata | 4 | 4(4) | 116 | 44h / 78h | 10 (10) | 34.4% |
| amazon | 4 | 4(4) | 55 | 35h / 44h | 8 (6) | 12.4% |
| fedora-api | 4 | 4(4) | 19 | 10h / 16h | 7 (6) | 274.5% |
| cpe(nvd/vulncheck/jvn 等) | 2+1 | 7+1(2) | 43+4 | 15h / 72h | 13+1 (9) | 305.9% |
| debian-security-tracker | 3 | 3(3) | 55 | 42h / 114h | 7 (5) | 14.1% |
| alma-errata | 2 | 2(2) | 49 | 19h / 19h | 4 (4) | **428.3%** |
| oracle-linux | 2 | 2(2) | 44 | 35h / 35h | 4 (2) | 132.9% |
| redhat-vex | 1 | 1(1) | 36 | 42h / 42h | 2 (1) | 21.9% |

(cpe 行の `+1` は per-source 化後の `cpe_*/vulncheck-nist-nvd2` 分。main 関与で数えると 2+1=3 で debian と同数だが、内訳が曖昧になるため行としては分けたまま debian の上に置いている。**nightly のみで発火した episode が多いのは microsoft(10 中 4)と cpe(8 中 5)** — 前者は KB 差分・`:nightly` baseline 停滞、後者は nightly 先行の実験的変更が理由で、main だけ見ると存在感が大きく下がる)

episode 粒度で見たときの要点:

- **microsoft-cvrf は FAIL 行の 46% を占めるが、episode では 10/50(20%)** — 1 イベントが windows_* 最大 13 ターゲット × main/nightly 両方を同時に倒す multi-target 増幅の分だけ、行数ベースは過大評価
- **rocky-errata は 116 行 / わずか 4 episode**、episode 持続中央値 44h と最長級 — イベントが多いのではなく、override 導入(6/15 #169)まで 1 つのイベントが止まり続けた。「持続時間 = 対応までの時間」の典型
- **episode 頻度の首位は microsoft(10)、次いで ubuntu-cve-tracker / cpe 系(各 7)** — 月次サイクル・新ディストリ triage・フィード churn という発火様式の違いがそのまま頻度に出る
- **持続時間の source 別中央値**: rocky 44h / debian 42h / amazon 35h / oracle 35h vs microsoft 24h / cpe 15h / ubuntu 12h / suse 7h — 前者ほど「override も promote もされずに粘った」発動
- sequence 側の補足: microsoft は関与 21 seq 中 7 つが途中参加で相乗り率最大 — 月次 churn が常時くすぶっており、別イベントで止まっている sequence に窓を跨いで合流する。ubuntu(17/18)と rocky(10/10)はほぼ常に発火主因側
- **両 workflow 同時発火は 50 episode 中 37** — main/nightly が同じ上流データを共有する以上ほぼ必然。N のみの 10 件は nightly 先行変更(6 月の cpe 系列 ×5)や `:nightly` baseline の停滞・KB 差分(microsoft ×4)、Dn のみの 3 件は override 非対称(tumbleweed)と per-source 化初回 run 等の系統差
- **max rate 上位は alma 428.3% / cpe_jvn 305.9% / fedora:45 274.5%** — 上流の再キュレーション・一括ロールアウト・マスアップデートという「構造イベント」は桁が違い、日常 churn(5〜20%)と明確に分離できる。閾値ガードの成立根拠がここにある

#### (2) 時系列特性

**曜日(UTC)**:

| 粒度 | Mon | Tue | Wed | Thu | Fri | Sat | Sun | 解釈 |
|---|--:|--:|--:|--:|--:|--:|--:|---|
| run 単位 | 33 | 25 | 37 | 26 | 20 | **69** | **83** | 土日が全体の 52%。ただしこれは上流ではなく**人間側の信号** — promote は JST 平日日中にしか行われないため、金曜夕方以降のイベントが週末じゅう再 FAIL し続ける(滞留) |
| sequence onset (n=66) | 5 | 6 | 13 | 10 | 10 | **20** | **2** | Sat 突出 / Sun 枯渇は**打ち切り効果**が主因: 週末は promote されないため、土曜に始まった sequence が日曜も継続中で、日曜には「新規 onset」が定義上発生しにくい(FAIL 中の workflow に新イベントが来ても同じ sequence に吸収される) |
| **source-episode (n=50)** | 3 | 7 | 10 | 6 | 6 | 13 | 5 | 正準単位。source の途中参入・再燃を別カウントするため打ち切り効果は sequence より軽いが Sat 13(期待値 7.1、~2σ)はなお残る — 実勢(上流の金〜土公開)と打ち切り残差の混合で、現時点では分離不能。**他曜日に有意差なし** |

**sequence の長さ・持続時間(n=66)**: run 数は中央値 3 / p90 9 / 最長 19。first-fail → last-fail は中央値 **11h** / p90 **48h** / 最長 **108h**(Nightly 5/2〜5/6)。単発(1 run)で終わった sequence は 17/66 — 次の cron までに promote されたか、次ビルドで差分が baseline 側に回って自然解消したもの。持続時間はガードの検出性能ではなく**オペレータの応答時間の分布**を測っている点に注意(週末を跨ぐと p90 側に乗る)。

**月内分布(source-episode 単位)**: 01–10 日 = 16、11–20 日 = 21、21–31 日 = 13 — ほぼ一様で「月初に多い」とは言えない(sequence onset 単位でも 26/22/18 で同傾向)。ただし **microsoft-cvrf に限れば月前半に集中**(10 エピソード中 8 つが 1〜16 日: 5/13, 6/2, 6/6, 6/10, 6/12, 6/16, 7/2, 7/12。残る 2 つは 4/24 と 5/18)。Patch Tuesday ぴったり(PT+1: 5/13, 6/10)だけでなく、月初の Edge "Early Security Updates"(7/2〜04)、月中の KB 整理・データフラップ(6/16)と、**「月次サイクルが月前半に複数回の別イベントとして現れる」**のが実態

**サンプルサイズについて**: per-target / per-source 統計は 1,465 行・191 target-event あり十分固い。一方、曜日・月内分布の推論単位は source-episode 69 件(116 日 ≈ 17 週)しかなく、**曜日あたり n≈7 では ±2σ の帯が広すぎて微細なパターンは検出不能**。現時点で統計的に主張できる時系列特性は次の 2 つに絞られる:

1. **週末滞留効果**(run 単位 52% が土日) — 上流ではなく運用(promote の人間依存)の関数。自動化・オンコールの費用対効果を見積もる際の直接の根拠になる
2. **Microsoft 月次サイクル**(月前半集中、multi-target 増幅、事実上の月例イベント) — per-target override の 2 段階設計(#167)の妥当性を裏付ける

曜日・月齢の細かい議論をするなら、あと 3〜6 ヶ月分(episode 100 件超)の蓄積が必要。集計は `stats.py` を `guard-failures.tsv` に対して再実行するだけで更新できる(全 50 episode のリスト — onset / 終端 / run 数 / 持続時間 / 関与 workflow / target 数 / max rate — は `stats-output.txt` 収録)。

### 5.7 対応策の体系(まとめ)

1. **promote-digest workflow**(PR #139): FAIL 後にレポートを人間が確認し、正当なら候補 digest に手動でタグ付け。監査証跡(actor / digest / tag)が run 履歴に残る。AI エージェントには実行させない(絶対ルール、06-18 成文化)
2. **per-target / per-source 閾値 override**(PR #146 → #196): 繰り返し発生する正当 churn の恒久緩和。「観測ピーク + ヘッドルーム」「最も狭いキーを使う」「単発スパイクは override しない」が設計原則
3. **grooming 運用**(issue #154 / runbook): 約 2 ヶ月周期で override リストを全再導出し、陳腐化(不要な緩和の残存)を防ぐ
4. **データソースのピン留め / アンピン**(P-4 → A-14): 上流の恒久劣化には Makefile レベルで extracted commit をピンして取り込みを停止し、代替(alma-oval 復活)を整備してから計画的にアンピン
5. **extractor 修正**(A-6): コードバグは vuls-data-update 側で修正 PR
6. **再実行のみ**(A-4 / A-12): 上流の一時障害は候補を破棄し、回復後の cron / 再実行に任せる

---

## 6. 付録・参照資料

### 付録データ([`diff-guard-incidents-data/`](diff-guard-incidents-data/))

| ファイル | 内容 |
|---|---|
| `02a-runs-apr-may.md` 〜 `02e-runs-jul-aug.md` | ガード FAIL 全 420 run の表(日時 / workflow / run ID / 失敗チェック M-O-D / FAIL 行と変動率 / 候補 digest)。2026-04-24 〜 08-16。`02e` は per-source 化後の窓で、target 名の後に `[source]` を併記 |
| `03-promote-history.md` | promote-digest.yml 全 101 run(日時 / digest → tag / actor)。92 unique digest 全てがガード FAIL 候補と一致することの照合結果込み |
| `guard-failures.tsv` | 上記 run 表の機械可読版(run_id, workflow, created_at, event, kind, failed_checks, fail_rows, digest) |
| `log-extracts/<run_id>.txt` | 各 run のログ抜粋(FAIL 行・集約 rc 行・エラー行) |

収集方法のメモ: 候補 digest は run ログに現れないため、"Push vuls.db to GHCR (tagless, digest-only)" ステップの実行時刻と GHCR package versions の created_at の突合で復元した(前半窓は 6,515 版に対し 293/295 が一意一致、2 件は completed_at の完全一致で解決。後半窓は 6,781 版に対し 125/125 が誤差 0〜1 秒で一意一致)。ログは 90 日保持期間内のため全 295 run で取得できており、欠損はない。runner 死亡でガード判定が不明の run が 4 件ある(05-gaps 相当の情報は上記 §5.1 に記載)。

### 参照資料

- 設計・検証: `diff-guard.md`(Guard 1/2 の設計、回帰テスト、44 日ベンチマーク)、`verification-playbook.md`(いずれも maintainer ローカル workspace)
- 初期ストリークのローカル再現一式: `vuls-data-db/local-diff-guard.lo/20260427-vuls-nightly-db-2796a350-vs-0/`(diff-guard-status.md / diff-report.md / diff-detection-report.md)
- triage 手順: `vuls-data-db/.claude/skills/diff-guard-triage/SKILL.md`
- 運用 runbook: `vuls-data-db/.github/diff-guard-override-grooming-runbook.md`、grooming issue テンプレート `diff-guard-override-grooming-issue.md`
- 主要 PR(vulsio/vuls-data-db): #134, #137, #139, #142, #144, #146, #152, #153, #156, #158, #165, #166, #167, #169, #191, #192, #196, #198
- 関連 PR(他 repo): MaineK00n/vuls2#342, #371, #400 / MaineK00n/vuls-data-update#850, #854, #882 / vulsio/integration#43
