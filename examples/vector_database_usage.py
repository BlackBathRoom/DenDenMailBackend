"""VectorDatabaseの使用例."""

from services.ai.rag.vectordatabase import ChromaVectorManager, SearchResultItem, VectorDocument


def example_usage() -> None:
    """VectorDocumentを使った基本的な使用例."""
    # マネージャーの初期化
    manager = ChromaVectorManager(collection_name="example_collection")

    # ドキュメントの作成（IDは自動生成される）
    doc1 = VectorDocument(
        embedding=[0.1, 0.2, 0.3, 0.4, 0.5],
        message_id="msg_001",
        section_number=1,
        document="これは最初のセクションです。",
    )

    doc2 = VectorDocument(
        embedding=[0.2, 0.3, 0.4, 0.5, 0.6],
        message_id="msg_001",
        section_number=2,
        document="これは2番目のセクションです。",
    )

    doc3 = VectorDocument(
        embedding=[0.3, 0.4, 0.5, 0.6, 0.7],
        message_id="msg_002",
        section_number=1,
        document="別のメッセージの最初のセクションです。",
    )

    # ドキュメントを一括追加
    added_ids = manager.add_documents([doc1, doc2, doc3])
    print(f"追加されたドキュメントID: {added_ids}")

    # 検索（全メッセージ対象）
    query_vector = [0.15, 0.25, 0.35, 0.45, 0.55]
    results = manager.query_documents(query_embedding=query_vector, n_results=2)

    print("\n=== 全メッセージから検索 ===")
    for result in results:
        print(f"ID: {result.id}")
        print(f"距離: {result.distance:.4f}")
        print(f"メッセージID: {result.message_id}")
        print(f"セクション番号: {result.section_number}")
        print(f"内容: {result.document}")
        print("---")

    # 特定のメッセージIDでフィルタして検索
    results_filtered = manager.query_documents(
        query_embedding=query_vector,
        n_results=5,
        message_id="msg_001",
    )

    print("\n=== msg_001のみから検索 ===")
    for result in results_filtered:
        print(f"ID: {result.id}")
        print(f"距離: {result.distance:.4f}")
        print(f"メッセージID: {result.message_id}")
        print(f"セクション番号: {result.section_number}")
        print(f"内容: {result.document}")
        print("---")

    # カスタムIDを指定することも可能
    custom_doc = VectorDocument(
        embedding=[0.5, 0.6, 0.7, 0.8, 0.9],
        message_id="msg_003",
        section_number=1,
        document="カスタムIDのドキュメント",
        id="custom_id_123",  # 明示的にIDを指定
    )

    manager.add_documents([custom_doc])
    print(f"\nカスタムIDで追加: {custom_doc.id}")


if __name__ == "__main__":
    example_usage()
