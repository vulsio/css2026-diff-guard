# 04. episode 別判定表(69 source-episode → 原因帰属)

stats-output.txt の `## source-episodes` の 69 行(順序同一)に、事例カタログ(§4)の判定を対応付けたもの。
論文 表1 の episode 単位集計の根拠。証拠水準: **直接** = 原因コミット/PR/raw diff まで特定、
**除外** = builder/extractor/取得設定のコミット走査による消去法(raw smoking gun 未確認)、
**系列** = A-8 開発版系列への帰属(個別 triage 無し。工程は未確定)、**事後分類** = Phase 1〜2 期の run 表からの遡及分類。

集計: 上流(a) 55 / 上流(b) 2 / 上流(c) 2 / 抽出器(バグ) 1 / 抽出器(意図的) 3 / 自前(系列推定，工程未確定) 4 / 取得設定 2 = 69

捕捉列 = その episode で FAIL したチェックの集合(Dn/Do/DB)。単独捕捉の集計: DB のみ 23 / Dn のみ 16 / Do のみ 0 / 複数同時 30。

複数原因を含む episode は、公開可否を左右した原因を代表判定とした。優先順位は
一時障害・恒久的品質イベント > コード/設定変更 > 正当な上流変更(例: #41 は A-13(a) を含むが (b)、#58 は上流 churn を含むが抽出器)。

| # | onset (UTC) | source 族 | wf | max% | 捕捉 | 判定 | 根拠 | 証拠 |
|---|---|---|---|---|---|---|---|---|
| 1 | 2026-04-24 13:21 | microsoft-cvrf | N | 134.3 | DB | 上流(a) | P-1 microsoft KB 初発動(source は msuc/wsusscn2 の可能性が残る = microsoft-*) | 事後分類 |
| 2 | 2026-04-25 01:09 | ubuntu-cve-tracker | M+N | 19.8 | DB | 上流(a) | P-1 ubuntu:26.04 初期triage | 事後分類 |
| 3 | 2026-04-25 18:31 | debian-security-tracker | M+N | 6.0 | Dn | 上流(a) | P-1 debian_13 | 事後分類 |
| 4 | 2026-04-30 19:01 | ubuntu-cve-tracker | M+N | 38.8 | Dn | 上流(a) | P-2 | 事後分類 |
| 5 | 2026-05-02 07:14 | debian-security-tracker | M+N | 14.1 | Dn | 上流(a) | P-2 | 事後分類 |
| 6 | 2026-05-05 19:16 | suse-oval | N | 7.1 | Dn | 上流(a) | P-2 | 事後分類 |
| 7 | 2026-05-08 01:29 | ubuntu-cve-tracker | M+N | 14.5 | Dn+Do | 上流(a) | P-2 | 事後分類 |
| 8 | 2026-05-09 07:27 | debian-security-tracker | M+N | 5.9 | Dn | 上流(a) | P-2 | 事後分類 |
| 9 | 2026-05-10 01:28 | amazon | M+N | 7.0 | Dn | 上流(a) | P-2 | 事後分類 |
| 10 | 2026-05-10 18:40 | suse-oval | M+N | 100.0 | Dn | 上流(a) | P-2 opensuse seeding | 事後分類 |
| 11 | 2026-05-13 08:27 | oracle-linux | M+N | 7.0 | Dn+Do | 上流(a) | P-2 | 事後分類 |
| 12 | 2026-05-13 08:42 | microsoft-cvrf | N | 18.3 | DB | 上流(a) | P-2 5月Patch Tuesday | 事後分類 |
| 13 | 2026-05-16 07:43 | amazon | M+N | 12.4 | Dn | 上流(a) | P-2 | 事後分類 |
| 14 | 2026-05-18 10:00 | fedora-api | M+N | 39.3 | DB | 上流(a) | P-2 | 事後分類 |
| 15 | 2026-05-18 19:42 | microsoft-cvrf | N | 28.2 | DB | 上流(a) | P-2 | 事後分類 |
| 16 | 2026-05-20 08:47 | ubuntu-cve-tracker | M+N | 39.5 | DB+Dn+Do | 上流(a) | P-2 | 事後分類 |
| 17 | 2026-05-23 07:59 | ubuntu-cve-tracker | M+N | 21.7 | DB | 上流(a) | P-3 ubuntu:snap Go crypto一括開示 | 事後分類 |
| 18 | 2026-05-27 08:53 | alma-errata | M+N | 428.3 | DB+Dn+Do | 上流(c) | P-4 alma errata再編(feed/OSV/HTML三者一致) | 直接 |
| 19 | 2026-05-28 19:59 | rocky-errata | M+N | 5.4 | Dn+Do | 上流(a) | P-4後続 rocky単発 | 事後分類 |
| 20 | 2026-05-29 08:58 | suse-oval | M+N | 13.6 | DB+Dn | 上流(a) | P-4後続 opensuse seeding継続 | 事後分類 |
| 21 | 2026-05-30 08:11 | rocky-errata | M+N | 34.4 | DB+Dn+Do | 上流(a) | P-5 rocky_10 初期シーディング | 事後分類 |
| 22 | 2026-06-02 03:52 | microsoft-cvrf | M+N | 44.8 | Dn | 上流(a) | P-5 windows 6月初旬変動 | 事後分類 |
| 23 | 2026-06-04 19:49 | rocky-errata | M+N | 11.6 | Dn+Do | 上流(a) | P-5 rocky_10 減衰再発 | 事後分類 |
| 24 | 2026-06-06 18:58 | microsoft-cvrf | M+N | 76.3 | Dn | 上流(a) | P-5 windows 大変動 | 事後分類 |
| 25 | 2026-06-10 20:27 | microsoft-cvrf | N | 14.2 | Dn | 上流(a) | A-1 June Patch Tuesday(純増) | 直接 |
| 26 | 2026-06-11 20:19 | cpe(nvd/vulncheck/jvn...) | N | 25.3 | DB | 自前(工程未確定) | A-8系列 開発版先行のCPE関連変更(候補: vuls-data-update #827/#841=06-10，#850=06-18，vuls2側変更。個別triage無し) | 系列 |
| 27 | 2026-06-12 09:48 | microsoft-cvrf | M | 26.8 | Dn | 上流(a) | A-1続き windows_server_2008_r2 | 直接 |
| 28 | 2026-06-13 08:41 | rocky-errata | M+N | 10.7 | Dn+Do | 上流(a) | A-2 rocky_10 新規errataバッチ | 直接 |
| 29 | 2026-06-14 03:57 | cpe(nvd/vulncheck/jvn...) | N | 40.1 | DB | 自前(工程未確定) | A-8系列 開発版先行のCPE関連変更(候補: vuls-data-update #827/#841=06-10，#850=06-18，vuls2側変更。個別triage無し) | 系列 |
| 30 | 2026-06-15 11:36 | fedora-api | M+N | 268.8 | DB | 上流(a) | A-3 FEDORA-2026-54c7ad647e マスアップデート | 直接 |
| 31 | 2026-06-16 10:46 | microsoft-cvrf | M+N | 46.3 | Dn | 上流(b) | A-4 CVRF 2026-Jun全消失(raw 723→0) | 直接 |
| 32 | 2026-06-17 04:00 | cpe(nvd/vulncheck/jvn...) | N | 122.7 | DB | 自前(工程未確定) | A-8系列 開発版先行のCPE関連変更(候補: vuls-data-update #827/#841=06-10，#850=06-18，vuls2側変更。個別triage無し) | 系列 |
| 33 | 2026-06-17 10:19 | fedora-api | M+N | 72.5 | DB | 上流(a) | A-5 マスアップデート撤回(Bodhi) | 直接 |
| 34 | 2026-06-19 02:36 | fedora-api | M+N | 274.5 | DB | 抽出器(バグ) | A-6 ソート欠落による非決定出力(修正PR) | 直接 |
| 35 | 2026-06-19 10:23 | cpe(nvd/vulncheck/jvn...) | N | 18.6 | DB | 自前(工程未確定) | A-8系列 開発版先行のCPE関連変更(候補: vuls-data-update #827/#841=06-10，#850=06-18，vuls2側変更。個別triage無し) | 系列 |
| 36 | 2026-06-23 08:51 | amazon | M+N | 7.4 | Dn+Do | 上流(a) | A-7 Amazon 10日分バッチ | 直接 |
| 37 | 2026-06-24 03:29 | cpe(nvd/vulncheck/jvn...) | N | 18.0 | DB | 抽出器(意図的) | A-8 CPE match quality分類 #850 | 直接 |
| 38 | 2026-06-27 01:50 | ubuntu-cve-tracker | M+N | 53.3 | Dn+Do | 上流(a) | A-9 ubuntu 26.04 triage進行 | 直接 |
| 39 | 2026-06-28 02:00 | redhat-vex | M+N | 21.9 | DB+Dn+Do | 上流(a) | A-9/A-10 Red Hat VEX全再生成 | 直接 |
| 40 | 2026-07-01 02:01 | suse-oval | M+N | 15.6 | DB+Dn+Do | 上流(a) | A-11 SUSE OVAL大規模再発行 | 直接 |
| 41 | 2026-07-02 13:22 | microsoft-cvrf | M+N | 53.6 | Dn | 上流(b) | A-12 CVRF June再消失(A-13 Edge一括(a)を同一episodeに含む) | 直接 |
| 42 | 2026-07-07 06:53 | alma-errata | M+N | 146.5 | DB+Dn+Do | 上流(c) | A-14 alma計画的アンピン(骨抜き顕在化) | 直接 |
| 43 | 2026-07-07 13:58 | oracle-linux | M+N | 132.9 | Dn+Do | 上流(a) | A-15 Oracle UEK 822 CVE advisory | 直接 |
| 44 | 2026-07-08 13:19 | amazon | M+N | 6.3 | Dn+Do | 上流(a) | A-16 amazon部分 | 直接 |
| 45 | 2026-07-09 01:24 | cpe(nvd/vulncheck/jvn...) | M+N | 29.0 | DB | 上流(a) | A-16 VulnCheck vcConfigurations一斉付与 | 直接 |
| 46 | 2026-07-11 01:15 | ubuntu-cve-tracker | M+N | 47.8 | DB | 上流(a) | A-17 ubuntu:25.10 | 直接 |
| 47 | 2026-07-11 01:15 | cpe(nvd/vulncheck/jvn...) | M+N | 305.9 | DB+Dn | 上流(a) | A-17 cpe複合クラスタ | 直接 |
| 48 | 2026-07-11 12:43 | suse-oval | M | 6.0 | Dn+Do | 上流(a) | A-17 tumbleweed | 直接 |
| 49 | 2026-07-12 07:51 | microsoft-cvrf | M+N | 55.9 | DB+Dn | 上流(a) | A-17/A-18/A-19 July Patch Tuesday波 | 直接 |
| 50 | 2026-07-18 01:09 | suse-oval | M+N | 212.9 | DB | 上流(a) | suse-oval再発行(02e表・コミット走査除外) | 除外 |
| 51 | 2026-07-18 01:09 | cpe(nvd/vulncheck/jvn...) | M+N | 15.2 | DB | 上流(a) | kernel CVE churn(02e表・コミット走査除外) | 除外 |
| 52 | 2026-07-20 13:39 | debian-security-tracker | M+N | 5.8 | Dn+Do | 上流(a) | 02e表・コミット走査除外 | 除外 |
| 53 | 2026-07-22 01:14 | cpe(nvd/vulncheck/jvn...) | M+N | 204.5 | Dn | 上流(a) | A-20 Cisco ASA CPE part修正+kernel CPE付与 | 直接 |
| 54 | 2026-07-22 18:51 | redhat-vex | M+N | 10.3 | DB | 上流(a) | 02e表・コミット走査除外 | 除外 |
| 55 | 2026-07-24 02:32 | fedora-api | M+N | 273.2 | DB | 上流(a) | fedora マスアップデート同型(02e表・除外) | 除外 |
| 56 | 2026-07-25 19:04 | cpe(nvd/vulncheck/jvn...) | M+N | 17.3 | DB+Dn | 上流(a) | A-21 Cisco productNamesサイレント再生成 | 直接 |
| 57 | 2026-07-28 14:02 | debian-security-tracker | N | 5.2 | Dn+Do | 上流(a) | A-22 kernel CNA一括発番 | 直接 |
| 58 | 2026-07-31 08:46 | cpe(nvd/vulncheck/jvn...) | M+N | 10.6 | DB+Dn | 抽出器(意図的) | A-23 Fortinet whitelist追加 #901(他target churn(a)を含む) | 直接 |
| 59 | 2026-08-01 12:45 | microsoft-cvrf | M+N | 25.9 | Dn | 上流(a) | A-23 windows月次churn(コミット走査除外) | 除外 |
| 60 | 2026-08-04 19:13 | suse-oval | M+N | 16.1 | DB+Dn+Do | 上流(a) | 02e表・コミット走査除外 | 除外 |
| 61 | 2026-08-05 13:27 | amazon | M+N | 5.1 | Dn+Do | 上流(a) | 02e表・コミット走査除外 | 除外 |
| 62 | 2026-08-06 08:08 | microsoft-cvrf | M+N | 211.3 | DB | 取得設定 | A-24 msuc seed一括登録 #211/#216/#217 | 直接 |
| 63 | 2026-08-06 08:32 | cpe(nvd/vulncheck/jvn...) | M+N | 135.5 | DB+Dn | 抽出器(意図的) | A-25 fortinet-cvrf 検知補完 #892 | 直接 |
| 64 | 2026-08-10 12:36 | microsoft-cvrf | M+N | 100.0 | DB | 取得設定 | A-26 microsoft-servicing新規ソース追加 | 直接 |
| 65 | 2026-08-13 00:49 | fedora-api | M+N | 3433.3 | DB | 上流(a) | A-27 fedora:46 小baseline立ち上がり | 直接 |
| 66 | 2026-08-13 00:49 | cpe(nvd/vulncheck/jvn...) | M+N | 81.7 | DB+Dn | 上流(a) | A-27 8月中旬複合churn | 除外 |
| 67 | 2026-08-14 00:48 | suse-oval | M+N | 37.9 | DB+Dn+Do | 上流(a) | 02e表・コミット走査除外 | 除外 |
| 68 | 2026-08-15 01:07 | cpe(nvd/vulncheck/jvn...) | M+N | 30.0 | DB+Dn | 上流(a) | A-27 cisco churn継続 | 除外 |
| 69 | 2026-08-16 00:27 | debian-security-tracker | M+N | 10.5 | Dn+Do | 上流(a) | A-27 kernel CVE継続流入 | 除外 |
