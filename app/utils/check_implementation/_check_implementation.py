from collections.abc import Callable


def check_implementation[**P, R](func: Callable[P, R]) -> Callable[P, R]:
    """メソッドが実装されていない場合に例外を投げるデコレータ."""

    def _wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        msg = f"{func.__name__} is not implemented."
        raise NotImplementedError(msg)

    return _wrapper
