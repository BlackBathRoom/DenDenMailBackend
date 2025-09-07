# 実装ロードマップ＆進捗

このドキュメントはでんでんメールのバックエンド実装を段階的に進めるためのチェックリストです。必要になったら項目を追加・削除して問題ありません（YAGNI/DRY/KISSを厳守します）。

## 記法

- '[ ] 未着手  / [~] 進行中  / [x] 完了  / [!] ブロック中（理由を書く）'
- 各ステップは「完了条件（Definition of Done）」を満たしたらチェックします。

## マイルストーン別ステップ

### M0: 企画・ドキュメント土台

- [x] 機能要件のドラフト（docs/app/functions.md）
- [x] 概要・技術選定（docs/app/overview.md）
- [x] データモデル方針（docs/app/tables.md）
- DoD: 3つのドキュメントに一貫性があり矛盾がありません。将来変更があっても差分で追える状態です。
- [x] モデル定義（MESSAGES, SUMMARIES, ADDRESSES, MESSAGE_ADDRESS_MAP, MESSAGE_PARTS, MESSAGE_WORDS, TAGS, MESSAGE_TAG_MAP, PRIORITY_WORDS, PRIORITY_PERSONS）
	- 現状: 全テーブルのSQLModelを実装。Message（MESSAGES）を正としてSummaryは1:1でMessage参照。主要FKにON DELETE CASCADEを付与し、必要なCHECK/INDEXも追加。既存のMailはlegacyとして残置。
- [x] セッション/エンジン初期化（SQLite、トランザクション方針）
	- 現状: `app/app_conf.py` で `create_engine` を初期化済みです。
- [ ] マイグレーション方針（初期版は自動生成でもOK、YAGNIで最小）
	- 現状: 未決定です。
- DoD: 全テーブルを作成でき、基本CRUDがスキーマどおりに動作し、ユニーク/外部キー制約が期待どおりに機能します。
- [ ] セッション/エンジン初期化（SQLite、トランザクション方針）
- [ ] マイグレーション方針（初期版は自動生成でもOK、YAGNIで最小）
- [x] プロファイル探索（WindowsのTB既定パス対応）
	- 現状: `ThunderbirdPath` がプロファイルとメールボックスを検出します。
- [~] MBOX/mbox-likeの解析と正規化（Message-ID必須、重複排除）
	- 現状: `ThunderbirdClient` で mbox 解析と Message-ID 取得は実装済みです。DBでの重複排除は未対応です。
- [~] MIMEパーツ抽出（本文text/plain, text/html、添付、CID対応）
	- 現状: 取得時に MIME パーツへ分割して返却します。ネストはフラットにし `part_order` と `parent_part_order` で親子復元可能。添付/CIDの保存は未対応です。
- [ ] DB保存（MESSAGES, MESSAGE_PARTS, ADDRESSES, MESSAGE_ADDRESS_MAP）
	- 現状: 保存ロジックは未実装です。保存時に order→ID 解決で `parent_part_id` を埋める方針です。
- DoD: サンプルプロファイルから一定件数（例: 100通）を安定して取り込みでき、再実行しても重複挿入が発生しません。
- [ ] MBOX/mbox-likeの解析と正規化（Message-ID必須、重複排除）
- [ ] MIMEパーツ抽出（本文text/plain, text/html、添付、CID対応）
- [ ] DB保存（SUMMARIES）
	- 現状: SummaryモデルとCRUDはありますが、要約生成との連携は未実装です。

- [~] サマライザIF定義（Sync/Async両対応のポート）
	- 現状: BaseGraph/SummarizeAgentGraph により同期パスは提供済み。非同期は未対応。
- [x] LLMモデル選定・実装（ローカル/オフライン、OpenVINO Phi-4-mini 初期想定）
	- 現状: OpenVINO Phi-4-mini-instruct のロード/推論パイプラインを実装（オフライン動作）。
- [ ] 設定管理（.env/pyprojectからの読込、上書きルール）
- [x] 構造化ログとローテーション（log/app.log）
	- 現状: 回転ファイル/コンソールのハンドラ構成で稼働します。
- [ ] 最低限のヘルスチェック
- DoD: 本番/開発の切り替えがシンプルで、ログから障害原因をたどれます。

### M4: スコアリング・検索
- [ ] クエリAPIの設計（ページング/並び替え/既読フィルタ）
- 完了: M0（ドキュメント土台）、M1（モデル定義）
- 進行中: M2（取得/解析 一部）、M7（ログ）
- ブロック: なし
- DoD: 指定条件で安定して並べ替えが可能で、ベンチマークで1000通規模でも体感的に速いです。
総合進捗（目安）: 3/10 マイルストーン
### M5: API（FastAPI）

- [ ] メッセージ一覧/詳細/本文パーツ取得
- [x] データベース設計
	- [x] ER図の作成
	- [x] 各テーブルのカラム定義
- [ ] 開発環境の整備

### M6: 通知・進捗配信（WebSocket）
- [~] 基本的な FastAPI アプリケーションのセットアップ
	- [x] `app/main.py` の作成
	- [x] `app/app_conf.py` での設定管理
	- [ ] `uvicorn` での起動確認

### M7: 設定・ログ・監視
- [~] **1-1: データベースモデルの定義**
	- [x] `app/models/mail.py` に `Mail` モデルを定義する
	- [x] `app/models/common.py` に共通で使うモデルがあれば定義する
	- [ ] テスト: `Mail` モデルが正しく定義されているか確認するテストを作成
- [~] **1-2: Thunderbird メール取得ロジックの実装**
	- [x] `app/services/mail/thunderbird/thunderbird_path.py` で Thunderbird のプロファイルパスを検出する機能を実装
	- [x] `app/services/mail/thunderbird/thunderbird.py` で mbox ファイルを読み込み、MessageData + MIME パーツを返却
	- 現状: `__main__` によるスモーク（最新1件の取得・メタ情報出力・パーツ一覧・本文プレビュー再構成）を確認済み
	- [ ] テスト: ダミーのプロファイルとメールファイルで、正しくパスが検出でき、メールが読み込めるかテスト
- [~] **1-3: メールデータの永続化処理**
	- [x] `app/services/database/base.py` でDBセッション管理/CRUD基盤を実装
	- [x] `app/services/database/mail_crud.py` で `Mail` モデルの CRUD (Create, Read) 処理を実装
	- [x] `app/services/database/message_crud.py` で `Message` の Read 処理を実装
	- [ ] テスト: `mail_crud` の各関数が正しく動作するか単体テストを作成
- [ ] **1-4: API エンドポイントの作成**
### M9: 配布/運用

- [ ] 起動スクリプト/README更新（uv基盤）
- [ ] サンプルデータ/デモ手順
- DoD: 新規環境で手順どおりに起動・利用でき、初回学習コストが低いです。

- [~] **2-1: データベースモデルの定義**
	- [x] `app/models/summary.py` に `Summary` モデルを定義
	- [x] `Message` モデルとの1:1リレーションを設定（Mailはlegacy）
	- [ ] テスト: `Summary` モデルとリレーションが正しく定義されているか確認
- [~] **2-2: サマリー生成ロジックの実装**
	- 仕様: 件名と本文（MIMEパーツから再構成）を入力し、短文要約を生成（ローカルLLM、オフライン）。
	- 現状: `services/ai/summarize/agent.py` の SummarizeAgentGraph でコア処理は実装・スモーク確認済み。件名+本文の組み立て入力とDB保存フロー連携は未実装。
- 進行中: なし
- ブロック: なし

- [~] **2-3: サマリーデータの永続化処理**
	- [x] `app/services/database/summary_crud.py` で `Summary` モデルの CRUD 処理を実装
	- [ ] テスト: `summary_crud` の各関数が正しく動作するか単体テストを作成
- [ ] **2-4: API エンドポイントの作成**
## 次アクション（提案）

1) M1のモデル定義は完了。インメモリ/一時DBでcreate_allとCRUDスモークテストを実施します。
2) MBOX正規化の重複排除ルールを確定し、DB保存（MESSAGES/MESSAGE_PARTS/ADDRESSES/MESSAGE_ADDRESS_MAP）の最小実装を追加。
3) M2のThunderbird取り込みを最小パスで1アカウント分だけ実装します。

---

## 更新ルール

- 実装が進むたびに該当チェックを更新します。ブロックがある場合は理由や期限も追記します。
- 大きな方針変更がある場合は先に docs/app/*.md を更新し、この進捗表へ反映します。

---

## Requirements coverage

- ステップ分割: Done（M0〜M9）
- 進捗の可視化: Done（チェックリストと進捗サマリを用意）
- 既存実装を無視: Done（コード状態に依存しない計画として定義）
