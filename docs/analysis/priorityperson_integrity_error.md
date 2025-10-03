# PriorityPerson IntegrityError 調査レポート

## 概要
`PriorityPerson` テーブルに対する一覧取得後のレスポンス生成過程で、`address_id` を `NULL` に更新しようとする不正な `UPDATE` が発行され、`NOT NULL constraint failed: priorityperson.address_id` が発生しました。本レポートでは再現手順・原因・実施した対策・残る懸念点と推奨アクションを整理します。

## 事象詳細
- 発生ログ（抜粋）:
  ```text
  (sqlite3.IntegrityError) NOT NULL constraint failed: priorityperson.address_id
  [SQL: UPDATE priorityperson SET updated_at=?, address_id=? WHERE priorityperson.id = ?]
  ```
- 影響範囲: `/rules/addresses` 取得エンドポイント。
- 初回 1 件登録後の取得は成功するが、2 件目を追加した後の取得で失敗しました。

## 再現手順
1. 新規 `PriorityPerson` (優先アドレス) を登録。
2. 一覧取得 (成功)。
3. 2 件目を登録。
4. 一覧取得 (失敗 / IntegrityError)。

## 検証観察
| 観察 | 結果 | 補足 |
|------|------|------|
| `no_autoflush` を使用 | 成功 | 自動 flush がトリガである示唆 |
| レコード 1 件のみ | 成功 | 2 件以上で flush タイミング差異 |
| 直接 `address_id` を None にするコード | 未検出 | ORM 内部生成 UPDATE |

## 根本原因 (Root Cause)
`BaseDBManager.read` が `with Session(...)` ブロック内で ORM オブジェクトを取得し、セッション終了 (close) 後に **detached** 状態のインスタンスを返却していました。レスポンス生成で `person.address.email_address` にアクセスする際、`address` リレーションが lazy load で解決される必要があります。しかしオブジェクトは既にセッションから切り離されているため、SQLAlchemy が内部で再同期 / flush 処理を行おうとする過程で、`address_id` が未解決状態 (None) と評価されたまま `UPDATE` が構築され、`NOT NULL` 制約違反となりました。

ポイント:
- Detached オブジェクトで lazy relationship にアクセス → 追加クエリが発行できず、属性再同期の異常な副作用。
- 2 件以上存在時のみ再現 → identity map / autoflush のトリガ差異により問題コードパスへ到達しやすくなる。

## 対策 (実装済み)
| 区分 | 内容 | 目的 |
|------|------|------|
| コード追加 | `PriorityPersonDBManager.read_with_address` を新設し `selectinload(address)` で eager load | Detached 後の lazy load 排除 |
| ルータ修正 | `/rules/addresses` が `read()` から `read_with_address()` を利用 | 安定した関連取得 |
| 検証 | スニペットで複数件取得・`address.email_address` アクセス | 例外発生しないことを確認 |

## 効果
- 一覧取得時に `priorityperson` → `address` のリレーションが事前ロードされ、レスポンス生成時に追加 flush / lazy load が発生しません。
- IntegrityError の再現が解消しました。

## 残る懸念点 / リスク
| 懸念 | 内容 | 対応案 |
|------|------|------|
| 再発 (他モデル) | 他のエンドポイントでも detached + lazy load パターンが存在する可能性 | 汎用 eager load 機構 / DTO 化 |
| `BaseDBManager` の責務 | セッションを内部で閉じる設計がリレーション参照と相性不良 | セッション管理を呼び出し側 (依存注入) に移譲検討 |
| 乱雑な ignore コメント | `selectinload` の型警告抑止 (`# type: ignore[...]`) | 共通 mypy/pyright 設定 or 型スタブ導入 |
| exists 判定効率 | `is_registered` が全件 SELECT を返す (`read`) | `exists()` / `select(1)` 最適化 |
| 仕様ドキュメント | Detached オブジェクト利用禁止方針が未明文化 | 開発ガイド追記 |

## 推奨追加アクション
優先度 (高→低):
1. `BaseDBManager.read` に `eager: list[str]` などの簡易指定を追加し、`selectinload` を一括適用可能にする。
2. CRUD レイヤで ORM エンティティを直接返さず Pydantic DTO に明示変換 (シリアライズされた純データ) → ORM ライフサイクル遮断。
3. FastAPI 依存関数でリクエストスコープ Session を提供し、Manager は受け取った Session を利用 (Unit of Work 風)。
4. 回帰テスト: 2 件以上の `PriorityPerson` を登録 → `/rules/addresses` 取得で 500/IntegrityError が発生しないことを保証。
5. `is_registered` の最適化実装。
6. 開発ドキュメント (例: `docs/app/overview.md` か新規 `docs/app/dev_guidelines.md`) に「detached オブジェクトに対する lazy load を禁止、必要なら eager load か DTO化」と追記。

## 代替案の検討 (要検討タスク)
| 案 | 概要 | 長所 | 短所 |
|----|------|------|------|
| A: Eager 専用メソッド (現行) | 必要な箇所だけ手動 | 影響局所化 | メソッド増殖リスク |
| B: read 拡張 | 汎用 eager オプション | コード重複削減 | API 複雑化 |
| C: Session 外部注入 | UoW 風で再利用容易 | ORM パターン整備 | 既存呼び出し全面修正 |
| D: DTO 化 | ORM ライフサイクル排除 | 安定した I/F | 変換コスト/実装追加 |

## 結論
本件の直接原因は「セッション終了後の detached ORM インスタンスに対する lazy relationship アクセス」でした。第一段の対策として必要リレーションを eager load することで問題は解消しました。再発防止と今後の拡張性向上のため、DTO 化またはセッションスコープ整理 (UoW パターン) の導入を段階的に検討することを推奨します。

---
更新日: 2025-09-29
作成者: Github Copilot (GPT-5)
