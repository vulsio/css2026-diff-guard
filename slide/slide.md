---
marp: true
theme: css2026
size: 16:9
paginate: true
---

<!-- _class: lead -->
<!-- _paginate: false -->

# 脆弱性情報の上流は安定していない
## 公開前検査による116日間の全数観測

篠原 俊一・中岡 典弘・神戸 康多(フューチャー株式会社)

コンピュータセキュリティシンポジウム 2026 / OWS 2026 / 2F1-2

<!--
発表 15 分 + 質疑 5 分。いまは素材を多めに入れてある(31 枚)。リハ後に「削減候補」コメントの枚から削る。
-->

---

<!-- _class: takeaway -->

# まとめ

1) 脆弱性情報の上流は **2 日に 1 件**のペースで大きく動く。<br>消え、戻り、書き換わる。しかも**大半は正当な変更**。
2) でも自動ビルドでは、**本当にまずい DB**がたまにできる。<br>1 か月分の CVE がまるごと消える。**10 万ファイルが半日ごとに入れ替わる**。<br>公開前に**止めないといけない**。
3) 公開前に前回の DB との差を見て、**大きな差分はひとまず止める**ようにした。<br>116 日間、止めた全件の原因を履歴で特定し、**本当にまずい DB を 3 回捨てた**。<br>原因の特定はほぼ AI に任せ、公開の最終判断だけ人がする。

<!--
116 日・943 run の本番データ(2026-04-23〜08-16)と、その後の出来事からの結論。
-->

---

# 対象のしくみ: 脆弱性 DB を作って配る流れ

![w:1150](figs/fig-system.svg)

- ひとつ前の発表は**どのデータを取るか**。この発表は、その先の**できた DB を公開していいか**

- raw と extracted は**ソースごとの Git 履歴**、DB は **digest** で、GHCR に置く
- **どの時点の上流の姿も、あとから取り出せる**。原因調べはこの履歴をさかのぼる

---

# 第1幕: 2026年3月、壊れた DB を2回公開した

| | 2026-03-06 | 2026-03(同時期) |
|---|---|---|
| 上流 | Red Hat VEX | Ubuntu CVE Tracker |
| 何が | 壊れたデータ × 形式変更で**空のデータ**ができた | 新しい DB の印を**古いスキャナが読めない** |
| 結果 | redhat:9 の検知が **51.9% 消えた** | ubuntu 22.04 の検知が **倍になった**(+106.0%) |
| CI | **ビルドも公開も成功** | 同じ |

* 片方は見逃し、片方は誤検知。どちらも CI は緑
* CI が見るのは「ビルドが通ったか」で、「できたものが正しいか」ではない

---

# 何が起きたか: 使う側と、運用する側

- Vuls を使う商用サービスで、検知結果が一晩で変わった
- 問い合わせ → 運用チームが**前日のバックアップに戻す** → お詫び
- 迷惑をかけたのは使う側だけでなく、**運用チームにも**
- 「ビルドが通れば公開される」しくみは、「上流は安定していて、変化はほぼ追加だけ」と**決めつけていた**

> この決めつけはどのくらい正しいのか。116 日分の本番データで答える

---

# 作ったもの: 公開前検査 (diff guard)

![w:1150](figs/fig-guard.svg)

- できた DB を**前回の DB とくらべ**、動きが大きければ**止める**。正しいかどうかは判定しない
- 止めた DB はタグなしで残る。正当なら人が **promote**(公開に昇格)する。誰がいつ、は残る

<!--
3 チェックの呼び方: 検知(新)= 最新スキャナ、検知(旧)= 固定した旧スキャナ、DB 構造 = DB を直接比較。論文の Dn / Do / DB。
-->

---

# 実物: 止まったとき、人が見るもの

<div class="small">

GitHub Actions のジョブ要約、2026-06-16(あとで出てくる Microsoft の件)。3 つのチェックのまとめ:

| チェック | 結果 |
|---|---|
| 検知(新) | **FAIL** |
| 検知(旧) | PASS |
| DB 構造 | PASS |

検知(新)の内訳(13 件が FAIL、一部):

| scan result | baseline | target | added | removed | change rate | threshold | result |
|---|--:|--:|--:|--:|--:|--:|---|
| windows_11_21h2 | 879 | 472 | 0 | 407 | **46.3%** | 10.0% | **FAIL** |
| windows_11_25h2 | 1235 | 722 | 0 | 513 | **41.5%** | 20.0% | **FAIL** |
| windows_server_2025 | 1802 | 1285 | 0 | 517 | **28.7%** | 20.0% | **FAIL** |
| windows_10_22h2 | 2697 | 2198 | 0 | 499 | **18.5%** | 10.0% | **FAIL** |

</div>

- **added 0 / removed 407**: 増えずに減っただけ。6 月分の CVE が検知から消えた

<!--
まとめ表は 2026-08-24 以降の形式。この run 当時は 1 行のテキスト(diff guard failed: detection(master)=1 ...)。
TODO: 本物のスクショに差し替え候補(run 27646259547 の Summary タブ)。
-->

---

# 見込み: 「2週間に1回くらい見ればいい」

![w:820](figs/fig2-benchmark.svg)

- 入れる前に、となり合う日の DB 35 組で測った
- ふだんは中央値 **0.3%**。10% 超は **2 組**だけで、どちらも本物の上流の出来事
- ふだんと異常は桁で分かれる。**週に 1 回も鳴らないだろう**と思い、2026-04-23 に本番へ

---

# 第2幕: 翌日から止まった

- 翌日(2026-04-24)に止まり、最初の promote(04-27)まで **20 run 連続 FAIL**
- 続く 3 週間で promote **10 回**。ほぼ毎朝、まず結果を読んで promote
- 止まっているあいだ前回版は動かない → **同じ差分が 6 時間ごとにまた鳴る**
- 最初は 1 つ FAIL したら終わる作り → debian_13 が ubuntu:26.04 の FAIL を**隠していた**(05-08 に修正)

---

# 止まるのは上流のせいか、人のせいか

- 116 日間で 943 run 中 **420 run(44.5%)が FAIL**。promote は **1 日 0.79 回**
- FAIL した run の **52% が土日**。promote は平日昼にしかしないので、金曜夕方の出来事が週末じゅう鳴る
- つまり上流ではなく、**人の応答の速さ**を映している
- 止めているあいだは前回版を配り続ける = **新しい CVE が遅れる**

<!--
削減候補: 「52% が土日」の 1 文だけ口頭で。
-->

---

# 見方を変える: うるさい検査ではなく、上流の地震計

- 「止まりすぎ」を調べるうちに、FAIL の記録は**上流で何が起きたかの記録**だと気づいた
- 2026-04-23 〜 08-16 の **116 日・943 run を全部集めた**
- FAIL を「同じ上流の同じ出来事」ごとにまとめると **69 件**
- 69 件すべてに「なぜ動いたか」を付ける

---

# 原因のしぼり込み: 履歴で工程を消していく

1. **DB 構築**: ビルダーの版をくらべる
2. **収集・変換**: そのソースのコードの履歴を見る
3. **収集の設定**: 取る対象の変更を見る
4. **上流**: raw の Git 履歴から、件数と ID が合う変更を探す

* 69 件すべてに原因が付いた。**「原因不明」はゼロ**
* 全工程の履歴が残っているからできた。去年の基盤がここで効いた

<!--
削減候補: 次の「実物」と統合。
-->

---

# 実物: 1件の原因調べはこう終わる(2026-07-26)

```
判定: upstream-driven(上流の正当な変更)

1. builder : created_by 同一(vuls v0.0.1-alpha.0.20260714011358-2af27b6858b4)→ 除外
2. extractor: 窓内に pkg/{extract,fetch}/cisco のコミットなし(main / nightly 両方)→ 除外
3. 収集設定: fetch-cisco の workflow / seed に変更なし → 除外
4. raw     : vuls-data-raw-cisco-json 294641e8 → 5591d648(2026-07-23 → 07-25、4 commits / 114 files)
   smoking gun: 2014/cisco-sa-20140326-sip.json  productNames 149 → 36
                lastUpdated 2014-03-31T13:46:00 / version 1.1 / status Final は不変

推奨: 候補 sha256:39516634… は上流を忠実に反映しており promote 可(判断・実行は人間)
      override(cpe/cisco-json)は churn の継続を見極めてから
```

- 手順書にしてあり、調べる作業の大半は AI エージェントに任せる
- **promote の判断と実行だけは人**。エージェントに workflow を動かす権限は渡さない

---

# 実物: 上流が一時的に壊れた → promote しない(2026-06-16)

<div class="cols cols-wide-left">
<div>

```
Triage 結果: upstream-driven(上流の一時的なデータ障害。promote しない)

FAIL 行: 検知(新)で windows 13 ターゲットが削除のみの大変動
         windows_11_21h2 879 → 472(Removed 407、46.3%)、windows_11_25h2 1235 → 722 ほか
除外: builder は created_by 同一 / fetcher(pkg/fetch/microsoft/cvrf)は窓内コミットなし。
      fail-hard 設計でスキップ機構も無い → 上流の返答そのものが変わった

raw の動き(smoking gun):
  4b5baa9 → 44181ca で 2026-Jun/ が丸ごと消失(723 → 0 ファイル)
  extracted 5e47f25 → b21d21d で CVE ファイル 777 本削除(うち 754 が CVE-2026、206,903 行)
  例: 2026-Jun/CVE-2026-48574.json(Windows Media RCE、published 2026-06-09)がファイルごと消失
  MSRC API は HTTP 200 のまま June のドキュメントを返さなくなったと判断

推奨: 候補 ff6889e1 / b8c1fee3 は promote しない。June の Windows 脆弱性を欠いた欠陥品
      上流の回復を待って再実行する。閾値も触らない
```

</div>
<div class="small">

raw vuls-data-raw-microsoft-cvrf の `git log`

| commit | 日時 (UTC) | 2026-Jun/ |
|---|---|--:|
| 4b5baa90ccf | 06-15 16:57 | 723 |
| 44181ca9cd1 | 06-16 03:02 | **0** |
| 34a4bd55a5f | 06-16 16:33 | 811 |

- 取得も変換も正常。上流が返すものが変わっただけ
- 候補は捨て、13 時間後の fetch で戻った
- 07-02〜03 にもう一度(18 枚目)

</div>
</div>

<!--
6 月当時の triage 原文は残っていないため、data/diff-guard-incidents.md A-4 の数値から同じ報告形式に再構成したもの。識別子は実データ。
口頭: このとき DB 構造チェックは PASS だった(KB の集合しか見ていない盲点)。
-->

---

# 実物: 上流の一時的な欠落 → promote しない(2026-09-26)

<div class="cols cols-wide-left">
<div>

```
Triage 結果: upstream-driven(JVN フィードの一時的な欠落。据え置き推奨)

FAIL 行: cpe_nvd / jvn-feed-rss  71 → 56, Removed 15, 21.1%(閾値 5%)
除外: builder は created_by 同一 / extractor・fetcher は 09-20 以降コミットなし
      / vuls-data-db は 09-24〜27 コミットなし

raw の動き(smoking gun):
  d37d1eda43 → ac66be6273 は A:490 / M:1 / D:426。前日は D:0 なので削除は異常
  削除 426 件は全件 modified が 2026-09-25。JVNDB-2026-034354〜034784 の連番ブロック
  代表 2026/JVNDB-2026-034784.json(Apache Tomcat)が削除 → 参照する 15 CVE が検知から消えた

原因: jvndb_new.rdf は直近 500 件の窓。9/25 は 1224 件公開され前半 426 件が窓から押し出され、
      年次 jvndb_2026.rdf にはまだ載っていない隙間に fetch が当たった
      (09-27 09:01 JST 再生成の jvndb_2026.rdf には 423 件が復活している)

推奨: 閾値変更は不要。promote もしない。候補 DB は 426 件を欠いた状態なので据え置きが正解
      次回 fetch で raw が復元され、次の DB run は Added 側に振れて PASS するはず
```

</div>
<div class="small">

raw vuls-data-raw-jvn-feed-rss の `git log`

| commit | 日時 (UTC) | A | D | 034784 |
|---|---|--:|--:|:-:|
| d37d1eda43 | 09-25 16:39 | 436 | 0 | あり |
| ac66be6273 | 09-26 16:02 | 490 | **426** | **なし** |
| 8a1b1edc8e | 09-27 01:33 | 736 | 0 | あり |

- 取得側のコードは書かれたとおりに動いた。「窓 500 件で年次の遅れを埋められる」という決めつけが、1 日 500 件超の日に破れた
- 閾値も promote も触らず、翌朝の再生成を待った。調べているあいだに上流が直った

</div>
</div>

<!--
原文は 2026-09-27 09:37 JST の triage 報告。経緯の詳細は docs/jvn-feed-rss-rolling-window-loss.md(ローカルメモ)。
-->

---

# 結果: 69件のうち59件は上流が原因

| 原因 | 件数 | 例 |
|---|---|---|
| 上流: 正当な変更 | **55** | 月例パッチ、新しい OS の立ち上がり |
| 上流: 一時的な障害 | 2 | 月分のデータが消えた |
| 上流: ずっと続く品質の変化 | 2 | errata の作り直し |
| 自分: 変換コードのバグ / 意図した変更 | 1 / 7 | 出力順が不定 / CPE まわり |
| 自分: 収集の設定 | 2 | 取る対象の追加 |

* 上流が原因の 59 件 = **2 日に 1 件**、上流は閾値を超えて動く
* ほとんどが**正当な変更**。「異常だから止まる」のではない

---

# 116日間のタイムライン

![w:1150](figs/fig3-timeline.svg)

<div class="caption">69 件を上流ソースごとに並べたもの。横棒は最初の FAIL から解消まで</div>

<!--
削減候補: 前スライドに吸収。
-->

---

# 第3幕: 上流は消える — Microsoft CVRF

<div class="cols cols-wide-right">
<div>

- 6 月分の月例データ(723 ファイル)が raw から**丸ごと消え、戻り、また消えた**
- API は HTTP 200。取得も変換も**成功**
- できた DB には Windows の 6 月分 CVE 約 1,270 件が無い
- 検知(新)が windows 13 件の**減るだけ**の動きを捕まえた(7 枚目)

</div>
<div class="small">

raw(vuls-data-raw-microsoft-cvrf)の `git log`

| commit | 日時 (UTC) | 変更 | 2026-Jun/ |
|---|---|---|--:|
| 4b5baa90ccf | 06-15 16:57 | | 723 |
| 44181ca9cd1 | 06-16 03:02 | 1460 files, −251,429 行 | **0** |
| 34a4bd55a5f | 06-16 16:33 | +248,779 行 | 811 |
| 5a0dbb67385 | 07-01 14:17 | | 1273 |
| 55abc741d7d | 07-02 02:01 | 1273 files, −327,295 行 | **0** |
| 6dba0210f16 | 07-02 13:26 | +335,383 行 | 1273 |
| 07846b78042 | 07-03 01:42 | −327,838 行 | **0** |
| 0b4ba6131cc | 07-03 13:33 | +338,693 行 | 1278 |

</div>
</div>

---

# 上流は骨抜きになる — AlmaLinux errata

<div class="cols">
<div>

- 2026-05-27、過去の advisory の対象パッケージが一斉に減った
  - ALSA-2026:2721(kernel): **202 パッケージ(75 種)→ 2**
  - 136 件のうち 58% が半分以下に。CVE の 87% が検知から消えた
- `updated_date` は 2 月のまま。**更新とは扱われていない**
- 上流に聞くと「**仕様どおり**」。feed に載るのは**いまのマイナーの repo にあるパッケージだけ**。マイナーが上がるたびに起きる
- 対応: 取り込みを固定し、OVAL を用意して 2026-07-07 に解除

</div>
<div>

```diff
$ git log -- 10/ALSA/2026/ALSA-2026:2721.json
47a66696b 2026-05-20  packages: 202
e64c5ca88 2026-05-27  packages: 2     (−2406 / +6 行)

$ git show e64c5ca88 -- 10/ALSA/2026/ALSA-2026:2721.json
-    { "name": "kernel",
-      "filename": "kernel-6.12.0-124.38.1.el10_1.aarch64.rpm", ... },
-    { "name": "kernel-core", ... },
-    { "name": "kernel-rt-64k-debug", ... },
     ... 73 パッケージ名分を削除 ...
+    { "name": "kernel-doc",
+      "filename": "kernel-doc-6.12.0-124.38.1.el10_1.noarch.rpm", ... },
+    { "name": "kernel-abi-stablelists", ... }
     "updated_date": 1771853624    ← 2026-02-23(変わらず)
```

</div>
</div>

---

# 骨抜き、その後: x86_64_v2 が消えた(2026-10-12)<span class="badge">論文後</span>

<div class="cols cols-wide-left">
<div>

- 1 コミットで、AlmaLinux 10 の advisory **366 件**から x86_64_v2 が消えた(159 件は全部)。x86_64 は無傷
- rpm 本体は**いまもある**。消えたのは errata の記述だけ。`updated_date` も変わらず
- 検知チェックは PASS(スキャン結果は x86_64)。**DB 構造チェックだけが捕まえた**
- errata を信じるかぎり正しい DB。でも x86_64_v2 の機械では**検知が消える**

</div>
<div>

```diff
$ git show 0d591540ed --stat     (2026-10-12 20:40Z)
  10/: 421 files, +48,657 / −67,731 行
  x86_64_v2 のエントリ: 5660 → 3864

$ git show 0d591540ed -- 10/ALSA/2026/ALSA-2026:19009.json
-    { "arch": "x86_64_v2", "name": "postgresql18-server",
-      "filename": "postgresql18-server-18.3-1.el10_2.x86_64_v2.rpm", ... },
     ... x86_64_v2 13 件すべて削除。x86_64 13 件は残る ...

$ curl https://repo.almalinux.org/almalinux/10/AppStream/x86_64_v2/os/Packages/
  postgresql18-server-18.3-1.el10_2.x86_64_v2.rpm   ← ある
```

```
| alma:10 | alma-errata | 46.6% | 0.0% | 10.0% | FAIL |        DB 構造(単一閾値)
| alma:10 | alma-errata | 1.0% / 22.8% / 0.0% | ... | FAIL |   DB 構造(added/changed/removed)
| alma_10 | alma-errata | 774 | 776 | 2 | 0 | 0.3% | 5.0% | PASS |   検知(新)
```

</div>
</div>

<!--
発表 1 週間前の出来事。上流に照会中。DB 構造チェックと検知チェックの相補性の例でもある。
-->

---

# 上流は黙って書き換わる — Cisco openVuln API

<div class="cols">
<div>

- 2026-07 なかばから、advisory と影響する版の対応が**毎日 12:45Z ごろ書き換わる**
  - 4 日で 93 件、productNames が **2,022 消えて 1,481 増えた**
- **lastUpdated も version も status も変わらない**。お知らせもない
- 整理には見える。でも AP や WLC を CPE で見ている人には**検知が消える**

</div>
<div>

```diff
$ git show f5b5023d -- 2014/cisco-sa-20140326-sip.json
  (2026-07-24、−114 / +1 行、productNames 149 → 36)
-    "Cisco IOS 15.3(3)JN14",
-    "Cisco IOS 15.3(3)JN15",
-    "Cisco IOS 15.3(3)JD12",
-    "Cisco IOS 15.3(3)JD13",
-    "Cisco IOS 15.3(3)JDA12",
-    "Cisco IOS 15.3(3)JF2",
     ... 113 行削除 ...

  変わらないフィールド:
  "firstPublished": "2014-03-26T16:00:00",
  "lastUpdated":    "2014-03-31T13:46:00",
  "version": "1.1",  "status": "Final"
```

</div>
</div>

---

# 上流は揺れる — VulnCheck の CPE(2026-07-08)

<div class="cols cols-wide-left">
<div>

- **1 コミットで 145,672 ファイル**(+957 万行)。全年代の CVE に生成した CPE 条件を一斉に付けた
  - CVE-1999-0001 にまで `matchCriteriaId: ""` の条件が付く
- **DB 構造チェック**が cpe で FAIL。当時はまとめて比較で、cpe には 7 ソースが同居
- 「増やしただけだろう」と見て **promote した**

</div>
<div class="small">

翌日(2026-07-09)の DB 構造チェック

| ecosystem | detection change rate | KB change rate | threshold | result |
|---|--:|--:|--:|---|
| cpe | **28.9%** | 0.0% | 10.0% | **FAIL** |

内訳: root ID の added 587 / removed 64 / **changed 135,457**

</div>
</div>

---

# 後日、ソース単位で測り直すと

<div class="cols">
<div class="small">

同じ 2 つの DB を **DB 構造チェック**でソースごとに測り直す

| ecosystem | source | change rate | result |
|---|---|--:|---|
| cpe | nvd-api-cve | ≤ 5.4% | PASS |
| cpe | jvn-feed-detail | ≤ 5.4% | PASS |
| cpe | cisco-json | ≤ 5.4% | PASS |
| cpe | vulncheck-nist-nvd2 | **189.6%** | **FAIL** |

**検知チェック**に CPE のスキャン結果を足して再実行(検知した CVE 数)

| scan result | baseline | target | 変化 |
|---|--:|--:|--:|
| cpe_jvn | 69 | 17 | **−75.4%** |
| cpe_cisco | 67 | 24 | **−64.2%** |
| cpe_nvd | 24 | 19 | −20.8% |

</div>
<div>

- 28.9% の正体は **VulnCheck ひとつで 189.6%**。NVD の大きさに埋もれて薄まっていた
- CPE 経由の検知が **60〜75% 消えていた**。書き方が変わり、索引から外れた
- 「増えた」と「検知が減った」が同時に来る。公開した DB には検知の後退が入っていた
- → 閾値を**ソースごと**に。CPE のスキャン結果も検知チェックに足した(2026-07-14)

</div>
</div>

---

# 上流は揺れる(2): 10万ファイルが半日ごとに往復する

<div class="cols cols-wide-left">
<div>

- 一斉付与のあと、**約 10 万ファイルが 12 時間ごとに 2 つの版を行き来**した。07-11 の 2 コミットは**2 つ前と 100% 同じ**。`lastModified` は動かない
- CVE-2013-5510(Cisco ASA)では CPE が **255 本 ↔ 171 本**。part はどちらも `o:`
- 07-21 13:12 に `a:cisco:…:-` が 82 ファイルに現れ、07-22 01:19 に消えた。スキャン結果は `a:` → 検知が **22 → 67 → 22** と 7 時間で往復
- 2026-10 のいま、cpe_cisco の検知は **10 件**。VulnCheck 経由の Cisco の検知はほぼ失われた

</div>
<div class="small">

raw vuls-data-raw-vulncheck-nist-nvd2 の `git log`(2026-07)

| commit | 日時 (UTC) | 変更 files | 2 つ前と一致 |
|---|---|--:|--:|
| 0bab5f54afd | 07-08 13:24 | 145,672 | |
| b2d593f6c56 | 07-10 13:53 | 101,264 | 0% |
| ae7c83caf56 | 07-11 01:21 | 99,986 | **100%** |
| 8e030dba52d | 07-11 12:48 | 99,196 | **100%** |
| 1f21242a634 | 07-21 13:12 | 5,925 | `a:` 出現 |
| c2c205a79ae | 07-22 01:19 | 3,579 | `a:` 消失 |

検知(新)の cpe_cisco / vulncheck-nist-nvd2 行

```
07-22 01:14  baseline 22 → target 67  added 45   204.5%  FAIL
07-22 08:01  baseline 67 → target 22  removed 45  67.2%  FAIL
```

</div>
</div>

<!--
「ムカつく」枚。往復の一致率は、各コミットの変更ファイル 3,000 件を抽出して 2 つ前の blob と比較。
削減候補: 時間が無ければ前の 2 枚に「07-22 に 22→67→22」の 1 行だけ残す。
-->

---

# 正当でも桁違いに動く

![w:820](figs/fig4-histogram.svg)

- 最大は fedora:46 の **3433.3%**: 末端条件が **6 → 212 件**。異常の大きさではなく**分母の小ささ**
- Oracle UEK は **1 つの advisory に CVE 822 件**。kernel CNA の一括発番(2026-07-24〜25)は Debian と VulnCheck に同じ日に流れ込んだ
- ふだんの 5〜20% と、100% 超の大きな出来事が裾を作る

<!--
削減候補: 図だけ見せて 3433% の 1 文で流す。
-->

---

# 第4幕: 検査は何を止めたか — 3件

<div class="cols">
<div>

- **Microsoft CVRF の全消失 × 2**: 約 1,270 CVE 分の検知が消える DB を**公開せずに捨てた**
- **自分の変換コードのバグ × 1**(fedora、2026-06-19)
  - DB 構造チェックが fedora:45 で **274.5%**
  - raw は 266 ファイルなのに extracted は **23,163** → 上流ではなく自分
  - 並べ替え漏れ。**コンパイルもテストも通る**バグが、出力の差分で初めて見えた

</div>
<div>

```
| fedora:45 | 274.5% | 0.0% | 50.0% | FAIL |
```

```diff
FEDORA-2026-54c7ad647e / package "bind" / architectures
(raw は 2 つの DB でバイト同一)
- ["aarch64","i686","ppc64le","s390x","src","x86_64"]
+ ["src","x86_64","aarch64","i686","ppc64le","s390x"]
```

```diff
// vuls-data-update pkg/extract/fedora/api/api.go
- util.Write(path, &data)   // *Data: case Data: に落ちず Sort() されない
+ util.Write(path, data)
```

</div>
</div>

---

# 止めきれなかった2件 → いちばん弱いのは承認する側

- **AlmaLinux の骨抜き**: たまった FAIL を片づける流れで promote → **数時間公開してしまった**
- **VulnCheck**: 薄まった 28.9% を見て promote → 検知が減った DB を公開した
- 2 件とも**見つけて止めるまではできた**。失敗したのは人の判断
  - 見せ方を細かく → ソースごと(2026-07-14)
  - **減る方向は厳しく** → 変動率を added / changed / removed に分けた<span class="badge">論文後</span>
  - 複数人で承認。promote は人だけ

```
# vuls2 diff の既定値(2026-10-09 merge)。override は軸を名指ししないと緩まない
diff db        --rate-threshold added:30,changed:10,removed:10
diff detection --rate-threshold added:30,removed:5
               --rate-threshold-override cpe/cisco-json=removed:25
```

---

# エピローグ(1): 観測が終わった4日後、Fortinet

<div class="cols">
<div>

- advisory のページが、誰にでも Cloudflare の確認画面を **HTTP 200** で返すようになった
- 取得側は「CSAF なし」と判断し、何も書かず **exit 0** → 「上流が取り下げた」として**削除を記録**
- 2026-01 から 1 件ずつ消え、**08-20 に残り 181 件を全部削除**。run は緑。次の run が空で落ちて気づいた
- 対策: 23 の workflow に「**空になった repo は記録しない**」

</div>
<div>

```
$ git log --diff-filter=D   (vuls-data-raw-fortinet-csaf)
f4f1d3d 2026-01-22  deleted   2   left  88
2dd3ea9 2026-02-06  deleted   1   left  89
d1ed230 2026-02-21  deleted   1   left  98
c79f291 2026-02-28  deleted   1   left  97
154c743 2026-03-08  deleted   1   left  96
ac1fda0 2026-04-07  deleted   1   left 119
25f9f6c 2026-04-29  deleted   1   left 146
5a8924a 2026-06-28  deleted   1   left 162
56fc622 2026-08-20  deleted 181   left   0
        181 files changed, 59632 deletions(-)
```

```
$ curl -i https://fortiguard.fortinet.com/psirt/FG-IR-25-250   (2026-10-09)
HTTP/2 500
<title> The URL you requested has been blocked </title>
```

</div>
</div>

---

# エピローグ(2): 取得の段階で見える壊れ方(2026-09〜10)

<div class="cols cols-wide-left">
<div>

DB に入っているソース

- **Fedora**: Bugzilla が security bug を `NotPermitted` で返す(**5.4 万 → 5.9 万件**)。CVE ID が advisory から消え、fedora_42 が 13.5% で FAIL
- **ENISA EUVD**: 201 ページ目で `403 Forbidden`。取得が止まり、更新も止まる

取っているだけのソース(DB には未収載)

- **Wind River**: **穴埋め前のひな形の行**がそのまま配信(17 ファイル)
- **openEuler**: CSAF の `product_ids` が配列ではなく object

</div>
<div>

```
# fedora-api raw(2026-09)
{"bug_id": "2398586", "error": "NotPermitted"}
# REST: code 102 "You are not authorized to access bug #2398586"
```

```
# enisa-euvd fetch(2026-10-07)
GET .../api/search?page=201&size=100
  giving up after 6 attempt(s): unexpected HTTP status 403 Forbidden
```

```
# windriver-cve-tracker  active/CVE-2010-5312
Patches_chromium-x11:
{recipe_rcpl}_{package}: {status}
```

```
# openeuler-csaf fetch(2026-10-07)
json: cannot unmarshal JSON object into Go []csaf.ProductID
```

</div>
</div>

<!--
Fedora の前史: 2025-11-25 に Fedora が AI クローラ対策(Anubis)を入れ、fetch が challenge ページを掴んで全滅。Accept ヘッダで回避(vuls-data-update #634)。
削減候補: Wind River / openEuler は DB 未収載なので、時間が無ければ落とす。
-->

---

# まとめ

* 上流は消え、戻り、さかのぼって書き換わり、知らせずに作り直される。**しかも大半は正当**
* 「ビルドが通ったか」ではなく「**前回とくらべてどう動いたか**」を見ないと事故は防げない
* 全工程の履歴があれば、止まった**全件に根拠つきで原因を付けられる**
* 検査が約束できるのは**自動で止めるまで**。最後の判断は人に残る。承認する側の設計が次の課題

---

<!-- _class: lead -->

# 公開しています

論文・データ(run 表、69 件の判定表、集計スクリプト)
**github.com/vulsio/css2026-diff-guard**

検査の実装: vuls2 / 閾値の設定: vulsio/vuls-data-db

ご質問・追試歓迎です
