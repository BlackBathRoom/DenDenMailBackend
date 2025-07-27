"""サマリのCRUD操作."""

from typing import Optional, Sequence

from sqlmodel import Session, select, desc

from models.summary import Summary, SummaryCreate, SummaryUpdate


class SummaryCRUD:
    """サマリのCRUD操作クラス."""

    @staticmethod
    def create_summary(session: Session, summary_data: SummaryCreate, mail_id: int) -> Summary:
        """新しいサマリを作成する.
        
        Args:
            session: データベースセッション
            summary_data: 作成するサマリのデータ
            mail_id: 関連するメールのID
            
        Returns:
            Summary: 作成されたサマリオブジェクト
        """
        summary_dict = summary_data.model_dump()
        summary_dict["mail_id"] = mail_id
        summary = Summary.model_validate(summary_dict)
        session.add(summary)
        session.commit()
        session.refresh(summary)
        return summary

    @staticmethod
    def get_summary_by_id(session: Session, summary_id: int) -> Optional[Summary]:
        """IDでサマリを取得する.
        
        Args:
            session: データベースセッション
            summary_id: サマリのID
            
        Returns:
            Summary | None: サマリオブジェクト、見つからない場合はNone
        """
        statement = select(Summary).where(Summary.id == summary_id)
        return session.exec(statement).first()

    @staticmethod
    def get_summary_by_mail_id(session: Session, mail_id: int) -> Optional[Summary]:
        """メールIDでサマリを取得する.
        
        Args:
            session: データベースセッション
            mail_id: メールのID
            
        Returns:
            Summary | None: サマリオブジェクト、見つからない場合はNone
        """
        statement = select(Summary).where(Summary.mail_id == mail_id)
        return session.exec(statement).first()

    @staticmethod
    def get_summary_by_message_id(session: Session, message_id: str) -> Optional[Summary]:
        """メッセージIDでサマリを取得する.
        
        Args:
            session: データベースセッション
            message_id: メッセージID
            
        Returns:
            Summary | None: サマリオブジェクト、見つからない場合はNone
        """
        statement = select(Summary).where(Summary.message_id == message_id)
        return session.exec(statement).first()

    @staticmethod
    def get_summaries(
        session: Session,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[Summary]:
        """サマリ一覧を取得する.
        
        Args:
            session: データベースセッション
            skip: スキップする件数
            limit: 取得する最大件数
            
        Returns:
            Sequence[Summary]: サマリのリスト
        """
        statement = select(Summary).offset(skip).limit(limit).order_by(desc(Summary.created_at))
        return session.exec(statement).all()

    @staticmethod
    def update_summary(session: Session, summary_id: int, summary_data: SummaryUpdate) -> Optional[Summary]:
        """サマリを更新する.
        
        Args:
            session: データベースセッション
            summary_id: 更新するサマリのID
            summary_data: 更新データ
            
        Returns:
            Summary | None: 更新されたサマリオブジェクト、見つからない場合はNone
        """
        statement = select(Summary).where(Summary.id == summary_id)
        summary = session.exec(statement).first()
        
        if summary is None:
            return None
            
        summary_update_data = summary_data.model_dump(exclude_unset=True)
        for field, value in summary_update_data.items():
            setattr(summary, field, value)
            
        session.add(summary)
        session.commit()
        session.refresh(summary)
        return summary

    @staticmethod
    def delete_summary(session: Session, summary_id: int) -> bool:
        """サマリを削除する.
        
        Args:
            session: データベースセッション
            summary_id: 削除するサマリのID
            
        Returns:
            bool: 削除が成功した場合True、サマリが見つからない場合False
        """
        statement = select(Summary).where(Summary.id == summary_id)
        summary = session.exec(statement).first()
        
        if summary is None:
            return False
            
        session.delete(summary)
        session.commit()
        return True

    @staticmethod
    def delete_summary_by_mail_id(session: Session, mail_id: int) -> bool:
        """メールIDでサマリを削除する.
        
        Args:
            session: データベースセッション
            mail_id: メールのID
            
        Returns:
            bool: 削除が成功した場合True、サマリが見つからない場合False
        """
        statement = select(Summary).where(Summary.mail_id == mail_id)
        summary = session.exec(statement).first()
        
        if summary is None:
            return False
            
        session.delete(summary)
        session.commit()
        return True

    @staticmethod
    def count_summaries(session: Session) -> int:
        """サマリの件数を取得する.
        
        Args:
            session: データベースセッション
            
        Returns:
            int: サマリの件数
        """
        statement = select(Summary)
        results = session.exec(statement).all()
        return len(results)
