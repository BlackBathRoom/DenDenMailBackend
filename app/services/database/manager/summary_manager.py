from models.summary import Summary, SummaryCreate, SummaryUpdate
from services.database.manager.base import BaseDBManager


class SummaryDBManager(BaseDBManager[Summary, SummaryCreate, SummaryUpdate]):
    def __init__(self, model: type[Summary] = Summary) -> None:
        super().__init__(model)
