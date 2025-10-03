"""アプリケーションのユースケース層.

アダプタ (mail clients) やリポジトリ (DB managers) をオーケストレーションする
薄いサービスを集約する。ビジネスルールはここでは極力持たない。
"""

from .get_list_obj import get_list_obj
from .update_by_id import update_by_id

__all__ = [
    "get_list_obj",
    "update_by_id",
]
