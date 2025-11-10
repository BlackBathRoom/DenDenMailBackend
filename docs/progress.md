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
- [x] FOLDERS初期データシード（Inbox, Trash 自動投入）
	- 現状: アプリ起動時 `lifespan` で `create_all` 後に未存在なら挿入します。
- [ ] マイグレーション方針（初期版は自動生成でもOK、YAGNIで最小）
	- 現状: 未決定です。
- DoD: 全テーブルを作成でき、基本CRUDがスキーマどおりに動作し、ユニーク/外部キー制約が期待どおりに機能します。
- （重複削除）
- [x] プロファイル探索（WindowsのTB既定パス対応）
	- 現状: `ThunderbirdPath` がプロファイルとメールボックスを検出します。
- [~] MBOX/mbox-likeの解析と正規化（Message-ID必須、重複排除）
	- 現状: `ThunderbirdClient` で mbox 解析と Message-ID 取得は実装済みです。取り込み時に `rfc822_message_id` による事前スキップで重複挿入を回避します。DBでの一意制約による重複排除は未対応です（今後対応）。
- [~] MIMEパーツ抽出（本文text/plain, text/html、添付、CID対応）
	- 現状: 取得時に MIME パーツへ分割して返却します。ネストはフラットにし `part_order` と `parent_part_order` で親子復元可能。パーツのバイナリ（添付・インライン画像含む）は `MESSAGE_PARTS` に保存します。本文再構成では BeautifulSoup + bleach による CID 置換・HTMLサニタイズを実装済みで、`GET /api/messages/{vendor_id}/{folder_id}/{message_id}` から取得できます（所有チェック付き）。
- [~] DB保存（MESSAGES, MESSAGE_PARTS, ADDRESSES, MESSAGE_ADDRESS_MAP）
	- 現状: `app/usecases/message.py` の `save_message`/`save_messages` で MESSAGES と MESSAGE_PARTS の保存を実装し、パーツの親子関係は order から解決して `parent_part_id` を設定します。さらに `ADDRESSES` と `MESSAGE_ADDRESS_MAP` の保存も実装済みです（既存のアドレスは表示名の補完をベストエフォートで実施）。補足: 所有チェックとユースケース例外を導入し、APIレイヤでは 404/400/409 に正規化して応答します。
- DoD: サンプルプロファイルから一定件数（例: 100通）を安定して取り込みでき、再実行しても重複挿入が発生しません。
- [ ] MBOX/mbox-likeの解析と正規化（Message-ID必須、重複排除）
- [ ] MIMEパーツ抽出（本文text/plain, text/html、添付、CID対応）
- [x] DB保存（SUMMARIES）
	- 現状: ユースケース `create_summary` により text/plain 本文から要約を生成し `Summary` に保存します。既存サマリがある場合は再利用します。

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
- 完了: M0（ドキュメント土台）、M1（モデル定義）、M3追加（ベクトル化ワークフロー・実験検証）
- 進行中: M2（取得/解析 一部）、M5（API）、M7（ログ・永続化）
- ブロック: なし
- DoD: 指定条件で安定して並べ替えが可能で、ベンチマークで1000通規模でも体感的に速いです。
総合進捗（目安）: 6/10 マイルストーン + 1追加マイルストーン完了
### M5: API（FastAPI）

- [x] メッセージ一覧/詳細/本文パーツ取得
- [x] サマリ取得/生成エンドポイント（GET/POST /summary/{message_id}）
    - 現状: GET は既存サマリを返却（未存在は404）。POST はユースケースを呼び出し、既存があれば再利用、未生成なら text/plain 本文から要約生成→保存→返却します。text/plain が無い場合は 400 を返します。
- [x] データベース設計
	- [x] ER図の作成
	- [x] 各テーブルのカラム定義
- [ ] 開発環境の整備

- [x] ベンダー登録/取り込みトリガーの提供（POST /api/messages/vendors）
	- 現状: リクエストボディでベンダーを指定して登録します（Thunderbird 対応）。登録後にローカル mbox から最新 ~100 件を取得し、`save_messages` で DB に保存します。
	- 備考: ルーターは `/api` プレフィックス配下です（`app/main.py` で共通付与）。

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
	- 現状: 取り込み時の保存はユースケース（`app/usecases/message.py`）で動作し、`rfc822_message_id` による重複スキップも行います。本文取得時は vendor/folder の所有チェックを追加しました。`ADDRESSES` と `MESSAGE_ADDRESS_MAP` の保存も対応しました。
- [ ] **1-4: API エンドポイントの作成**
	- [x] 本文・パーツコンテンツの GET エンドポイントを実装し、ユースケース例外に応じて 404/400/409 を返却します。
	- [x] メッセージ一覧（ページング/既読フィルタ/受信日時降順）を実装しました。
	- [x] ベンダー一覧/登録、フォルダー一覧、アドレス一覧/更新のエンドポイントを実装しました。
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
	- 現状: `services/ai/summarize/agent.py` の SummarizeAgentGraph をユースケース `create_summary` から利用し、text/plain 本文を入力として要約生成・保存まで動作します。件名の連結や HTML 本文統合は未対応です（今後対応予定）。
- 進行中: なし
- ブロック: なし

- [~] **2-3: サマリーデータの永続化処理**
	- [x] `app/services/database/summary_crud.py` で `Summary` モデルの CRUD 処理を実装
	- [ ] テスト: `summary_crud` の各関数が正しく動作するか単体テストを作成
	- 現状: ユースケース `create_summary` にて `SummaryDBManager.add_summary` を通じて保存します（既存があれば再利用）。
- [x] **2-4: API エンドポイントの作成**
    - 現状: `GET /summary/{message_id}` と `POST /summary/{message_id}` を実装しました。ユースケース例外を 404/400/409 に正規化して応答します。text/plain を持たないメールは 400（PlainTextRequiredError）となります。

### M3追加: ベクトル化ワークフロー（実験・検証）
- [x] **3-1: EMLデモファイル用ユーティリティ**
	- [x] `demo/generator.py` でデモEML生成（日本語Base64対応）
	- [x] `demo/eml_reader.py` でEML読み込み・解析機能
	- 現状: 3種類のサンプルメール（新機能リリース、会議、メンテナンス）を生成・読み込み可能
- [x] **3-2: LangChain Document変換実装（Step 1-4, 1-5）**
	- [x] `demo/document_processor.py` で `EMLDocumentProcessor` クラス実装
	- [x] Step 1-4: `format_page_content()` でメールデータを検索用テキストに整形
	- [x] Step 1-5: `create_document()` でLangChain Documentオブジェクト作成
	- [x] 日本語Base64ヘッダーのデコード対応（件名・送信者情報）
	- [x] 統合テスト完了: `demo/integration_test.py` で全工程テスト済み
	- DoD: EMLファイル3件すべてでDocument変換が成功し、日本語コンテンツが正しく整形されることを確認
- [x] **3-3: OpenVINO RURI_v3埋め込みサービス実装**
	- [x] `app/services/ai/rag/embedding/openvino_ruri_v3_embedding.py` でOpenVINO最適化埋め込みサービス実装
	- [x] OpenVINORURIv3EmbeddingService クラス: 単一/バッチドキュメント埋め込み、類似度計算、性能ベンチマークを提供
	- [x] Hugging Face → OpenVINO 自動変換: multilingual-e5-base モデル (768次元) をOpenVINO形式に最適化
	- [x] デバイス最適化: CPU/GPU/AUTO選択、パフォーマンスヒント設定
	- [x] 統合テスト完了: `app/services/ai/rag/embedding/test_openvino_ruri_v3.py` で全機能テスト済み (3/3テスト成功)
	- DoD: OpenVINO最適化によりCPU上で高速な埋め込み処理が可能、文字列ドキュメントから768次元ベクトルへの変換機能が完全動作

補足（M4との関係）
- [~] クエリAPIの設計（ページング/並び替え/既読フィルタ）
	- 現状: `GET /api/messages/{vendor_id}/{folder_id}` で `offset`/`limit` と `is_read` フィルタ、受信日時降順のソートを実装済みです。さらなる条件追加は今後のスコープで対応します。
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
