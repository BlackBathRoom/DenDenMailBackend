import re

from collections import Counter

from app.utils.logging import get_logger

# 定数定義
MIN_WORD_LENGTH = 2
DEFAULT_TEXT_LENGTH = 20


class QueryExtractionService:
    def __init__(self) -> None:
        self.stop_words = {"の", "に", "は", "を", "が", "で", "と", "から"}
        self.logger = get_logger(__name__)

    def extract_keywords(self, text: str, max_keywords: int = 10) -> list[str]:
        if not text.strip():
            return []
        words = re.findall(r"[ひらがな\u3040-\u309F]+|[カタカナ\u30A0-\u30FF]+|[漢字\u4E00-\u9FAF]+|[a-zA-Z0-9]+", text)
        filtered = [w for w in words if len(w) >= MIN_WORD_LENGTH and w not in self.stop_words]
        counts = Counter(filtered)
        return [word for word, _ in counts.most_common(max_keywords)]

    def generate_search_query(self, text: str, max_keywords: int = 5) -> str:
        keywords = self.extract_keywords(text, max_keywords)
        return " ".join(keywords) if keywords else text[:DEFAULT_TEXT_LENGTH].strip()


if __name__ == "__main__":
    logger = get_logger(__name__)
    logger.info("QueryExtractionService test")
    service = QueryExtractionService()
    test = "重要な会議の案内です。明日の午後2時から会議室Aで開催します。"
    keywords = service.extract_keywords(test)
    query = service.generate_search_query(test)
    logger.info("Keywords: %s", keywords)
    logger.info("Query: %s", query)
