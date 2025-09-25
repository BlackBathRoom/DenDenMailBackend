## APIエンドポイント一覧（現行実装に準拠）

本ドキュメントは、現在の実装状況に合わせたAPIエンドポイントの一覧です。ベースURLは `/api` です。サンプルのレスポンス/リクエストは簡略化した例を示します。

なお、元の仕様に存在して未実装のエンドポイントや、名称・入出力が異なる項目は「仕様との差分・未実装事項」にまとめています。

---

## メッセージ（messages）

### メッセージ一覧取得（ベンダー／フォルダ単位）

- エンドポイント：`GET /api/messages/{vendor_id}/{folder_id}`
- クエリパラメータ：
  - `offset`（デフォルト: 0）
  - `limit`（デフォルト: 50）
  - `is_read`（true/false, 省略可）
- レスポンス（例）：

```json
[
  {
    "message_id": "123",
    "subject": "件名A",
    "date_received": "2025-08-01T09:00:00+09:00",
    "is_read": false
  },
  {
    "message_id": "124",
    "subject": "件名B",
    "date_received": "2025-08-01T08:30:00+09:00",
    "is_read": true
  }
]
```

型定義（TypeScript）：

```typescript
// Query
type GetMessagesQuery = {
  offset?: number; // default 0
  limit?: number;  // default 50
  is_read?: boolean;
};

// Response
type GetMessagesResponse = {
  message_id: string;
  subject: string;
  /** ISO 8601 date-time string */
  date_received: string;
  is_read: boolean;
}[];
```

---

### メッセージ本文・添付メタ取得

- エンドポイント：`GET /api/messages/{vendor_id}/{folder_id}/{message_id}`
- 概要：本文（text/html）と添付メタデータ（実体URL含む）を返します。
- レスポンス（例）：

```json
{
  "message_id": 123,
  "text": "プレーンテキスト本文...",
  "html": "<p>HTML本文（CIDはURLに書き換え済み）</p>",
  "encoding": "utf-8",
  "attachments": [
    {
      "part_id": 10,
      "filename": "image.png",
      "mime_type": "image",
      "mime_subtype": "png",
      "size_bytes": 43210,
      "content_id": "<cid-123>",
      "is_inline": true,
      "content_url": "/api/messages/1/1/123/parts/10"
    }
  ]
}
```

型定義（TypeScript）：

```typescript
// Path Params
type GetMessageBodyParams = {
  vendor_id: number;
  folder_id: number;
  message_id: number;
};

// Response
type GetMessageBodyResponse = {
  message_id: number;
  text?: string | null;
  html?: string | null;
  encoding?: string | null;
  attachments: {
    part_id: number;
    filename?: string | null;
    mime_type: string;
    mime_subtype: string;
    size_bytes?: number | null;
    content_id?: string | null;
    is_inline: boolean;
    content_url: string;
  }[];
};
```

---

### メッセージパート実体取得（添付/インライン画像など）

- エンドポイント：`GET /api/messages/{vendor_id}/{folder_id}/{message_id}/parts/{part_id}`
- 概要：指定パートのバイナリ実体を返します（`Content-Type`/`Content-Disposition`等のヘッダが適切に設定されます）。
- レスポンス：バイナリ

---

### 登録済みベンダー一覧

- エンドポイント：`GET /api/messages/vendors`
- レスポンス（例）：

```json
[
  { "id": 1, "name": "Thunderbird" }
]
```

リクエスト型（TypeScript）：

```typescript
// Body
type RegisterVendorRequest = {
  vendor: string; // 例: "Thunderbird"
};
```

レスポンス型（TypeScript）：

```typescript
// GET /api/messages/vendors
type GetVendorsResponse = {
  id: number;
  name: string;
}[];
```

---

### ベンダー登録（取り込みトリガー）

- エンドポイント：`POST /api/messages/vendors`
- リクエスト（例）：

```json
{ "vendor": "Thunderbird" }
```

- 概要：対応ベンダーを登録し、最新約100件の取り込みを試行します。登録自体が成功した場合は201を返します（保存失敗はログに記録します）。
- レスポンスコード：201 Created
  - レスポンス本文は `text/plain` です（JSONではありません）。

---

### 登録済みフォルダ一覧

- エンドポイント：`GET /api/messages/folders`
- レスポンス（例）：

```json
[
  { "id": 1, "name": "Inbox" },
  { "id": 2, "name": "Trash" }
]
```

レスポンス型（TypeScript）：

```typescript
// GET /api/messages/folders
type GetFoldersResponse = {
  id: number;
  name: string;
}[];
```

---

### アドレス一覧（連絡先）

- エンドポイント：`GET /api/messages/addresses`
- レスポンス（例）：

```json
[
  { "id": 10, "display_name": "山田 太郎", "email_address": "taro@example.com" }
]
```

レスポンス型（TypeScript）：

```typescript
// GET /api/messages/addresses
type GetAddressesResponse = {
  id: number;
  display_name?: string | null;
  email_address: string; // RFC 5322 形式
}[];
```

---

### アドレスの表示名更新

- エンドポイント：`PATCH /api/messages/addresses/{address_id}`
- リクエスト（例）：

```json
{ "display_name": "新しい表示名" }
```

- レスポンスコード：204 No Content
  - レスポンス本文はありません。

リクエスト型（TypeScript）：

```typescript
// Path Params
type UpdateAddressParams = { address_id: number };

// Body
type UpdateAddressRequest = { display_name?: string | null };
```

---

## 優先度ルール（rules）

### 優先度辞書一覧

- エンドポイント：`GET /api/rules/dictionaries`
- レスポンス（例）：

```json
[
  { "id": 1, "word": "至急", "priority": 3 },
  { "id": 2, "word": "確認", "priority": 2 }
]
```

レスポンス型（TypeScript）：

```typescript
// GET /api/rules/dictionaries
type GetDictionariesResponse = {
  id: number;
  word: string;
  priority: 1 | 2 | 3;
}[];
```

---

### 優先度辞書の追加

- エンドポイント：`POST /api/rules/dictionaries`
- リクエスト（例）：

```json
{ "word": "重要", "priority": 2 }
```

- レスポンスコード：201 Created
  - レスポンス本文は `text/plain` です（JSONではありません）。

リクエスト型（TypeScript）：

```typescript
// Body
type CreateDictionaryRequest = {
  word: string;
  priority: 1 | 2 | 3;
};
```

---

### 優先度辞書の更新

- エンドポイント：`PATCH /api/rules/dictionaries/{dictionary_id}`
- 概要：現在は priority のみ更新できます（word の変更は未対応です）。
- リクエスト（例）：

```json
{ "priority": 1 }
```

- レスポンスコード：204 No Content
  - レスポンス本文はありません。

リクエスト型（TypeScript）：

```typescript
// Path Params
type UpdateDictionaryParams = { dictionary_id: number };

// Body（現状 priority のみ）
type UpdateDictionaryRequest = { priority: 1 | 2 | 3 };
```

---

### 優先度アドレス（人物）の追加

- エンドポイント：`POST /api/rules/addresses`
- 概要：既存のアドレスIDに対して優先度設定を紐づけます。アドレスIDが未登録の場合は400を返します。
- リクエスト（例）：

```json
{ "address_id": 10, "priority": 3 }
```

- レスポンスコード：201 Created
  - レスポンス本文は `text/plain` です（JSONではありません）。

リクエスト型（TypeScript）：

```typescript
// Body
type CreatePriorityAddressRequest = {
  address_id: number;
  priority: 1 | 2 | 3;
};
```

---

### 優先度アドレス一覧

- エンドポイント：`GET /api/rules/addresses`
- レスポンス（例）：

```json
[
  { "id": 10, "address": "boss@example.com", "name": "上司", "priority": 3 }
]
```

レスポンス型（TypeScript）：

```typescript
// GET /api/rules/addresses
type GetPriorityAddressesResponse = {
  id: number;
  address: string; // email
  name?: string | null;
  priority: 1 | 2 | 3;
}[];
```

---

### 優先度アドレスの更新

- エンドポイント：`PATCH /api/rules/addresses/{address_id}`
- 概要：現在は priority のみ更新します（name フィールドは受け付けますが無視されます）。
- リクエスト（例）：

```json
{ "priority": 2 }
```

- レスポンスコード：204 No Content
  - レスポンス本文はありません。

リクエスト型（TypeScript）：

```typescript
// Path Params
type UpdatePriorityAddressParams = { address_id: number };

// Body（現状 priority のみ）
type UpdatePriorityAddressRequest = { priority: 1 | 2 | 3 };
```

---

## サマリー（summary）

### サマリーテキスト取得

- エンドポイント：`GET /api/summary/{message_id}`
- レスポンス（例）：

```json
{ "content": "要約テキスト..." }
```

レスポンス型（TypeScript）：

```ts
type SummaryResponse = { content: string };
```

- 既存がない場合は 404 を返します。

---

### サマリーテキスト生成

- エンドポイント：`POST /api/summary/{message_id}`
- 概要：本文の text/plain からサマリーを生成して保存します。既存があれば再利用します。
- エラー：本文に text/plain が無い場合は 400、関連整合性で 409 を返すことがあります。
- レスポンス（例）：

```json
{ "content": "生成された要約テキスト..." }
```

レスポンス型（TypeScript）：

```ts
type SummaryResponse = { content: string };
```

リクエスト型（TypeScript）：

```ts
// Body なし（空）
type CreateSummaryRequest = undefined;
```

## 備考

- CORS は全許可で設定しています（開発用途）。
- 取り込みは現在 Thunderbird ベースの実装を提供し、ベンダー登録時に最新約100件の取り込みを試行します。
- 本ドキュメントは現行実装に追従して更新しています。今後の拡張に伴い、仕様との差分項目は順次解消していきます。
