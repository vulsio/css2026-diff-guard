# 論文後の事例と追加調査(2026-08-17 以降)

**論文とは別のデータ。** 論文(CSS 2026 / OWS 2026 投稿版)の全数調査は 2026-04-23 〜 08-16 の
116 日間で、その正本は [`diff-guard-incidents.md`](diff-guard-incidents.md) と `guard-failures.tsv` である。
このファイルは、発表スライド(`../slide/`)が使っている**観測窓の後の出来事**と、
論文の窓内の事例に対して**論文投稿後に行った追加調査**の出所をまとめたもの。
論文の数値には一切影響しない。`stats.py` の集計対象でもない。

記法: 日時は UTC。commit は dotgit(`ghcr.io/vulsio/vuls-data-db:vuls-data-raw-<source>` など)の短縮 hash。
run は vulsio/vuls-data-db の GitHub Actions run ID。

---

## B-1. 2026-08-20 — Fortinet CSAF: Cloudflare の確認画面で残り 181 件を全削除(観測窓の 4 日後)

- **Run**: Fetch All [32317321410](https://github.com/vulsio/vuls-data-db/actions/runs/32317321410)(08-20)
- **何が起きたか**: `fortiguard.fortinet.com/psirt/<ID>` が全クライアントに Cloudflare の interstitial を **HTTP 200** で返すようになった。fetcher は CSAF の download リンクを見つけられず「CSAF 無し」と判定し、何も書かずに exit 0 → ワークフローが「上流が全部取り下げた」として削除を commit
- **raw の動き**(`vuls-data-raw-fortinet-csaf` の `git log --diff-filter=D`): 2026-01-22 の f4f1d3d(2 件)から 1 件ずつ消え(02-06, 02-21, 02-28, 03-08, 04-07, 04-29, 06-28)、08-20 の 56fc622 で残り 181 件を一括削除(181 files / −59,632 行)。ガードは run が緑のまま通過し、次の run で `dotgit pull --restore` が空ツリーに失敗して初めて露見
- **修正**(09-10〜11): vuls-data-update #955(タイトルから CSAF URL を導出、/psirt を見ない)、#960(空ツリーを pull できるように)、#961(DocumentTitle 無し CVRF を拒否)、vuls-data-db #240(fortinet-csaf 専用の seed / guard)、#250(23 本の取得 workflow に「空になった repo を commit しない」ガード)
- **副産物**: seed を CVRF 1,127 件から組み直したら、最初から取得可能なのに一度も要求されていなかった advisory が 351 件(187 → 546 件)
- **後日談**: raw が増えた分 extractor が未知の文法で hard error。Extract は 08-20 以降失敗が続き、2026-10-08 時点でも `unexpected remediation category "mitigation"`(FG-IR-26-157)。修正 PR を vuls-data-update に積んでいる
- **2026-10-09 の確認**: `curl -i https://fortiguard.fortinet.com/psirt/FG-IR-25-250` は HTTP/2 500 の "The URL you requested has been blocked"(8 月時点は interstitial で 200)
- **スライド**: 予備「観測が終わった 4 日後、Fortinet」

## B-2. 2026-09 — Fedora: Bugzilla の閲覧制限で advisory から CVE ID が消える

- **何が起きたか**: Red Hat Bugzilla が Fedora のセキュリティ bug を `NotPermitted`(REST: code 102 "You are not authorized to access bug #N")で返すようになった。CVE ID は bugzilla.alias から blocked chain を辿って取っているため、拒否された bug に紐づく CVE が advisory から消える
- **規模**: 拒否件数 54,169(09-07)→ 58,767(09-09)。F42 の 310 advisory が 1 回の extract で 17,533 行を失い、検知(新)が `fedora_42 | fedora-api | 192 -> 180 | 13.5%` で FAIL し続けた
- **対応**: stopgap PR vuls-data-update #966(Bodhi の bug title から CVE ID を拾う)は CLOSED(未採用。title は切れるので alias 比で CVE ID が 20% 少ない)
- **前史**: 2025-11-25 に Fedora が Anubis(AI クローラ対策の PoW challenge)を入れ、fetch が challenge ページを掴んで全滅。vuls-data-update #634(11-26)で `Accept` ヘッダを付けて回避
- **注意**: bug 2398586 は 2026-10-09 時点では REST で読める(制限は解除された模様、delta_ts 09-23)。2026-10-08 の fedora-api fetch 失敗は別件(`connection reset by peer` from 38.145.32.21)
- **スライド**: 予備「取得の段階で見える壊れ方」

## B-3. 2026-09-26 — JVN feed RSS: 500 件の窓と年次ファイルの隙間(据え置きの実例)

- **Run**: DB [36268803915](https://github.com/vulsio/vuls-data-db/actions/runs/36268803915)(09-26 20:14)/ DB(Nightly) [36270269281](https://github.com/vulsio/vuls-data-db/actions/runs/36270269281)(20:39)
- **FAIL**: 検知(新)`cpe_nvd / jvn-feed-rss` 71 → 56(Removed 15、21.1%、閾値 5%)
- **除外**: builder は created_by 同一 / extractor・fetcher は 09-20 以降コミットなし / vuls-data-db は 09-24〜27 コミットなし
- **raw**(`vuls-data-raw-jvn-feed-rss`): d37d1eda43(09-25 16:39、A:436)→ ac66be6273(09-26 16:02、A:490 / M:1 / D:426)→ 8a1b1edc8e(09-27 01:33、手動 fetch-main、A:736)。削除 426 件は全件 modified が 2026-09-25 で JVNDB-2026-034354〜034784 の連番ブロック。JVNDB-2026-034784(Apache Tomcat)は あり → なし → あり
- **原因**: jvndb_new.rdf は直近 500 件の窓。9/25 は 1,224 件公開され前半 426 件が窓から押し出され、年次 jvndb_2026.rdf(毎日 09:00 JST 再生成、前日分は翌日)にまだ載っていない隙間に fetch が当たった。09-27 09:01 JST の再生成で 423 件が復活
- **判定・対応**: upstream-driven(一時的な欠落)。候補 sha256:77f6f6c3… / df3de244… は promote せず据え置き。翌朝の再生成と同日 01:33Z の手動 fetch で raw が復元
- **出所**: triage 報告(セッション 12bbabd8-af75-46bd-8050-80ac97ade4fd、2026-09-27 00:37Z)。詳細は maintainer のローカルメモ
- **スライド**: 予備「上流の一時的な欠落 → promote しない」

## B-4. 2026-10-01〜08 — 取得段階で連続失敗している上流

Fetch All の履歴(10-01〜10-08 の 14 run)で毎回失敗: fedora-api / openeuler-csaf / wrlinux。enisa-euvd-list もほぼ毎回。

- **Wind River**(windriver-cve-tracker、DB 未収載): CVE tracker に `{recipe_rcpl}_{package}: {status}` というテンプレートのプレースホルダがそのまま入っている(例: `active/CVE-2010-5312`、17 ファイル)
- **openEuler CSAF**(DB 未収載): `product_ids` が配列ではなくオブジェクト(`json: cannot unmarshal JSON object into Go []csaf.ProductID`、Fetch All 37663389221 のログ)
- **ENISA EUVD list**(DB 収載): `GET .../api/search?page=201&size=100` が `403 Forbidden`(giving up after 6 attempts)。取得が止まり更新も止まる
- **Microsoft CVRF 2026-Sep**: extract を unblock する修正(vuls-data-update #978、10-02)
- **スライド**: 予備「取得の段階で見える壊れ方」

## B-5. 2026-10-12 — AlmaLinux 10 errata から x86_64_v2 が消え、翌日戻る

- **raw**(`vuls-data-raw-alma-errata`): 0d591540ed(10-12 20:40)で 10/ の 421 files、+48,657 / −67,731 行。`x86_64_v2` のエントリ 5,660 → 3,864。806 advisory 中 366 件で減少(159 件は 0 に、207 件は一部)。`x86_64` が 0 になった advisory は無し。updated_date は変わらず(秒単位の揺れのみ)
- **例**: ALSA-2026:19009(postgresql18、Important)の packages を arch 別に数えると aarch64 13 / ppc64le 13 / s390x 13 / x86_64 13 / x86_64_v2 13 → x86_64_v2 だけ 0(updated_date 1779798852 は不変)。repo.almalinux.org の `10/AppStream/x86_64_v2/os/Packages/` には postgresql18-server-18.3-1.el10_2.x86_64_v2.rpm がある(10-13 確認)→ 消えたのは errata の記述だけ
- **ガード**: DB run [38324240469](https://github.com/vulsio/vuls-data-db/actions/runs/38324240469)(10-12 23:50)alma:10 46.6% FAIL(単一閾値、criterions 8,040 → 8,123、matched 6,210)。DB(Nightly) [38325837023](https://github.com/vulsio/vuls-data-db/actions/runs/38325837023)(10-13 00:09)は軸別で added 1.0% / changed 22.8% / removed 0.0%(added 83 / changed 1,830 / removed 0)で FAIL。検知(新)alma_10 は 774 → 776 で PASS(検知入力が x86_64 のため)
- **判断**: 10-13 05:44 に :0 / :nightly へ promote(shino)。5 月の minor 全削除(P-4)とは違い、x86_64_v2 の見逃しと、止め続けて新しい CVE が届かない遅れを天秤にかけた判断
- **復旧**: ee83c674cf(10-13 18:35)で x86_64_v2 が 5,759 エントリに戻る(10-14 の 17e5a9673e で 5,804)。上流の説明は未発見
- **背景**: AlmaLinux 10.2 は 2026-05-26 リリース。P-4(05-27)の再キュレーションはこれに伴う 10.1 向けパッケージの削除
- **スライド**: 本編「骨抜き、その 2: x86_64_v2 が消えた」

## B-6. 論文後の実装・運用変更

- **変動率の軸分離**(vuls2 #449、2026-10-09 merge): `diff db --rate-threshold added:30,changed:10,removed:10` / `diff detection --rate-threshold added:30,removed:5`。override は軸を名指ししないと緩まない(例: `--rate-threshold-override cpe/cisco-json=removed:25`)。vuls-data-db 側の既定値は db-main.yml の `DB_RATE_THRESHOLDS` / `DETECTION_RATE_THRESHOLDS`
- **3 観点の集約表**(vuls-data-db #236、2026-08-24): ジョブ要約の「Diff guard summary」表。それ以前は `diff guard failed: detection(master)=1 ...` の 1 行
- **空リポジトリの commit 拒否**(vuls-data-db #250、2026-09-12): 23 本の取得 workflow(B-1 の再発防止)
- **ソース単位の据え置き(hold-back)**: 設計中・実装中(2026-10 時点)。だめなソースだけ前回版に戻して DB 全体は公開する。設計は maintainer のローカルノート
- **AlmaLinux errata の履歴復元**(vuls-data-db #191、2026-07-07): 窓内の対応だが、スライドでは「履歴管理の効用」として本編で触れる。縮退前 snapshot commit と対象 advisory を workflow に明記して fetch のたびに復元(1 回目 143 件、2 回目 102 件)。alma-oval の取得は復活させた(vuls-data-update #882)が DB では未使用。DB はいまも errata で、updateinfo への切り替えを検討中

---

## 追加調査(論文の窓内の事例を、投稿後に深掘りしたもの)

### C-1. VulnCheck 一斉付与(A-16)で検知が消えた機序 — 2026-10-14 調査

- raw `vuls-data-raw-vulncheck-nist-nvd2` の 0bab5f54afd(07-08 13:24)前後で比較
- **例 CVE-2012-5010(Cisco ASA)**: vcConfigurations が `cpe:2.3:a:cisco:adaptive_security_appliance_software:-:*:*:*:*:*:*:*` → `cpe:2.3:o:cisco:adaptive_security_appliance_software:*:*:*:*:*:*:*:*`。lastModified は 2026-06-16T23:46:03 のまま。検知入力(vulsio/integration `data/results/cpe_cisco.json`)は `cpe:/a:cisco:adaptive_security_appliance_software:9.8.1` など `a:` なので、`part:vendor:product` で引く索引から外れる
- `a:cisco:adaptive_security_appliance_software` を criteria に持つファイル: 82 → 46。Cisco の vendor:product の集計(criteria 単位): `a:adaptive_security_appliance_software` 95 → 80、`a:ios_xe` 85 → 50、`o:ios` 94,154 → 124,364(`ios:-` 419 件が `ios:12.4` / `12.2` / `15.1` などの明示版に)
- legacy CVE(例: CVE-2005-3669、CVE-2007-2461)は vcConfigurations が無かったところに configurations と同内容の vcConfigurations と vcVulnerableCPEs が付与された
- スライド 19 枚目の例の表記は、検知入力の 2.2 形式(`cpe:/a:…`)を 2.3 形式に揃えて表示している

### C-2. VulnCheck の半日ごとの往復(A-17 周辺)— 2026-10-13 調査

- raw の commit: 0bab5f54afd(07-08 13:24、145,672 files)→ b2d593f6c56(07-10 13:53、101,264)→ ae7c83caf56(07-11 01:21、99,986)→ 8e030dba52d(07-11 12:48、99,196)。後ろ 2 つは、変更ファイルから 3,000 件を抽出して 2 つ前の commit の blob と比較すると 100% 一致(= 2 版の往復)
- CVE-2013-5510(Cisco ASA)の CPE 本数は 255(blob 9cb39eb391)↔ 171(eb2f5bf212)。part はどちらも `o:`。lastModified は 2026-06-16T23:58:56 のまま。09-22 に第 3 の版(c8326b45be)
- `a:cisco:adaptive_security_appliance_software:-` を持つファイル数: 07-11 37 → 07-21 13:12(1f21242a634、5,925 files)82 → 07-22 01:19(c2c205a79ae、3,579 files)37 → 08-12 46 → 09-22 37。カタログ A-20 の「48 ファイルで o: → a:」は part が変わったファイル数で、82 は `a:` を持つファイルの総数(07-11 時点で 37)
- 検知(新)cpe_cisco / vulncheck-nist-nvd2: 07-14 24 → 22、07-22 01:14 22 → 67(added 45、204.5% FAIL)、07-22 08:01 67 → 22(removed 45、67.2% FAIL)、08-07 22 → 34、08-13 34 → 36 → 30、08-15 30 → 21。2026-09-26〜10-14 の DB run では 10 → 10 で PASS
- 出所: `guard-failures.tsv`(cpe_cisco 行)と gh run log(直近 60 run)

### C-3. Cisco openVuln API の再生成(A-21)の diff — 2026-10-09 調査

- raw cisco-json f5b5023d(07-24)の `2014/cisco-sa-20140326-sip.json`: −114 / +1 行、productNames 149 → 36。消えた 113 件は `Cisco IOS 15.3(3)JN14` など JD/JDA/JF/JG/JH/JI/JK/JN/JP* 系(autonomous AP 用 IOS train)。+1 は残った最後の要素の末尾カンマの付け替え(149 − 113 = 36)。firstPublished 2014-03-26 / lastUpdated 2014-03-31T13:46:00 / version 1.1 / status Final は不変

### C-4. AlmaLinux 再キュレーション(P-4)の diff — 2026-10-09 調査

- raw alma-errata `10/ALSA/2026/ALSA-2026:2721.json`: 47a66696b(05-20)= packages 202 エントリ(パッケージ名 75 種)→ e64c5ca88(05-27)= 2 エントリ(kernel-doc、kernel-abi-stablelists の noarch)。−2,406 / +6 行。消えたのは kernel / kernel-core / kernel-rt-64k-debug など 73 種。updated_date 1771853654 → 1771853624(どちらも 2026-02-23)。論文の「73 パッケージ → 2」は消えた種数、スライドの「75 種 → 2 種」は前後の種数
