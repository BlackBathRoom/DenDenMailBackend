### 未読メール一覧取得

- エンドポイント：`GET /api/mails?is_read=false`
- クエリパラメータ

| パラメータ | 型 | 説明 |
| --- | --- | --- |
| `unread` | `true/false` | 未読メールに限定 |
| `priority` | `1〜3` | 優先度で絞り込み |
| `from` | `string` | 送信者アドレス |
| `to` | `string` | 宛先 |
| `keyword` | `string` | 本文・件名のキーワード |
| `vendor` | `string` | outlook,Thunderbird |
- レスポンス例

```json
[
  {
    "id": "email_001",
    "subject": "至急確認してください",
    "sender_email": "boss@example.com",
    "receiver_email": ["me@example.com"],
 	  "your_role":"cc"
    "received_at": "2025-08-01T09:00:00+09:00",
    "priority": 3,
    "is_read": false
  },
  {
    "id": "email_002",
    "subject": "進捗報告",
    "sender_email": "team@example.com",
    "receiver_email": ["me@example.com","abcd@example.com"],
    "your_role":"bcc"
    "received_at": "2025-08-01T08:00:00+09:00",
    "priority": 1,
    "is_read": true
  }
]

```

```python
class MaillistDTO(BaseModel):
	id:str
	subject:str
	sender_email:EmailStr
	receiver_email:List[EmailStr]
  received_at: datetime
	your_role: Literal["to", "cc"]
	priority:Literal[1, 2, 3]
	is_read:bool
```

## `your_role`

- 「このユーザーにとって自分は To だったのか、Cc だったのか、だったのか」を明示
- UIで あなたはccとして受信していますなどを表示するため

---

### 本文/パーツ取得

- エンドポイント：`GET /api/mails/{id}`
- レスポンス例

```json
{
  "id": "email_001",
  "subject": "至急ご確認ください",
  "sender_email": "boss@example.com",
  "receiver_email": ["me@example.com", "team@example.com"],
  "your_role": "to",
  "received_at": "2025-08-01T09:00:00+09:00",
  "priority": 2,
  "is_read": false,
  "parts": [
    {
      "part_order": 0,
      "parent_part_order": null,
      "mime_type": "multipart",
      "mime_subtype": "alternative"
    },
    {
      "part_order": 1,
      "parent_part_order": 0,
      "mime_type": "text",
      "mime_subtype": "plain",
      "size_bytes": 1234
    },
    {
      "part_order": 2,
      "parent_part_order": 0,
      "mime_type": "text",
      "mime_subtype": "html",
      "size_bytes": 4321
    }
  ]
}

```

```python
class MailPartsDTO(BaseModel):
	id: str
	subject: str
	sender_email: EmailStr
	receiver_email: List[EmailStr]
	your_role: Literal["to", "cc", "bcc"]
	received_at: datetime
	priority: Literal[1, 2, 3]
	is_read: bool
  parts: List[MessagePartDTO]
	
class MessagePartDTO(BaseModel):
  part_order: int
  parent_part_order: Optional[int]
  mime_type: str
  mime_subtype: str
  filename: Optional[str]
  size_bytes: Optional[int]
```

### 優先度ルール取得

- エンドポイント：`GET /api/rules/email` /
- レスポンス例

```json
{
  "dictionary_rules": [
    {
      "id": "dict_001",
      "keyword": "至急",
      "priority": 3
    },
    {
      "id": "dict_002",
      "keyword": "確認",
      "priority": 2
    }
  ],
  "address_rules": [
    {
      "id": "addr_001",
      "email": "boss@example.com",
      "name": "上司",
      "priority": 3
    },
    {
      "id": "addr_002",
      "email": "team@example.com",
      "name": "チーム",
      "priority": 1
    }
  ]
}

```

```python
class DictionaryRuleDTO(BaseModel):
    id: str
    keyword: str
    priority: Literal[1, 2, 3]

class AddressRuleDTO(BaseModel):
    id: str
    email: EmailStr
    name: str
    priority: Literal[1, 2, 3]

```

### 優先度辞書取得

- エンドポイント：`GET /api/rules/dictionary`
- レスポンス例

```json
[
  {
    "id": "dict_001",
    "keyword": "至急",
    "priority": 3
  },
  {
    "id": "dict_002",
    "keyword": "確認",
    "priority": 2
  }
]

```

```python
class DictionaryDTO(BaseModel):
	id:str
	keyword:str
	priority:Literal[1,2,3]
```

---

### 辞書登録追加

- エンドポイント：`POST /api/rules`

```json
{
	"type":"dictionary"
	"keyword":"至急"
	"priority":2
}
```

```python
class BaseRuleDTO(BaseModel):
    type: Literal["email", "dictionary"]

class DictionaryCreateDTO(BaseRuleDTO):
    keyword: str
    priority: Literal[1, 2, 3]

class AddressRuleCreateDTO(BaseRuleDTO):
    email: EmailStr
    name: Optional[str] = None
    priority: Literal[1, 2, 3]

```

### 辞書登録削除

- エンドポイント：`DELETE /api/rules/dictionary/{id}` （単体）
- `DELETE /api/rules/dictionary` （一括）

一括削除用

```json
{
  "ids": ["dict_001", "dict_002", "dict_003"]
}

```

```python
class DictionaryDeleteDTO(BaseModel)
	ids:List[str]
```

### 優先度アドレスの追加

- エンドポイント：`POST /api/rules`

```json
{
	"type":"email"
  "email": "boss@example.com",
  "name":"社長"
  "priority": 2
}

```

```python
class BaseRuleDTO(BaseModel):
    type: Literal["email", "dictionary"]

class DictionaryCreateDTO(BaseRuleDTO):
    keyword: str
    priority: Literal[1, 2, 3]

class AddressRuleCreateDTO(BaseRuleDTO):
    email: EmailStr
    name: Optional[str] = None
    priority: Literal[1, 2, 3]

```

### 優先度アドレスの削除

- エンドポイント：`DELETE /api/rules/email/{id}`（単体）

```json
{
	"ids":["address001","address002"]
}
```

```python
class AddressDeleteDTO(Basemodel):
	ids:List[str]
```

### 優先度ルール変更

- エンドポイント：`PATCH /api/rules/email/{id}` /`PATCH /api/rules/dictionary/{id}`

```json
{
  "keyword": "重要",  
  "priority": 2        
}
{
  "name": "上司",      
  "priority": 3         
}
{
	"email":"boss@example.com",
	"priority":3
}
```

```python
PriorityLevel = Literal[1, 2, 3]

class DictionaryUpdateDTO(BaseModel):
    keyword: Optional[str] = None
    priority: Optional[PriorityLevel] = None

class AddressRuleUpdateDTO(BaseModel):
		email: Optional[EmailStr] = None 
    name: Optional[str] = None
    priority: Optional[PriorityLevel] = None
```

### 既読操作

- エンドポイント：`PUT /api/mails/{id}`
- is_readというフィールドで管理
- is_read:falseを送ることで未読に戻すことができるようにする

```json
{
  "is_read": true
}
```

```python
class MailReadUpdateDTO(BaseModel):
    is_read: bool
```