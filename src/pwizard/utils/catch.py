import click
import functools
import typing as t

_P = t.ParamSpec("_P")
_T = t.TypeVar("_T")


def catch_exception(
    *exception_types: type[BaseException],
) -> t.Callable[[t.Callable[_P, _T]], t.Callable[_P, _T]]:

    def inner(fn: t.Callable[_P, _T]) -> t.Callable[_P, _T]:
        @functools.wraps(fn)
        def wrapper(*args: _P.args, **kwargs: _P.kwargs) -> _T:
            try:
                return fn(*args, **kwargs)
            except exception_types as e:
                raise click.ClickException(str(e))

        return wrapper

    return inner
