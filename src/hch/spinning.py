from typing import Callable, ParamSpec, TypeVar

import typer
from rich.progress import Progress, SpinnerColumn, TextColumn

from .config import Config
from .console import console
from .error import GetCookieError
from .login import get_cookies
from .time_info import TimeInfo
from .tools import get_course_categories

T = TypeVar("T")
P = ParamSpec("P")


def run_spinning(func: Callable[P, T], description: str) -> Callable[P, T]:
    def warp(*args, **kwargs):
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True,
        ) as progress:
            progress.add_task(description)
            return func(*args, **kwargs)

    return warp


get_time_info = run_spinning(TimeInfo.get, description="Fetching Time Info")
get_cookies = run_spinning(get_cookies, description="Fetching Cookies")
get_course_categories = run_spinning(
    get_course_categories, description="Fetching Course Categories"
)


def check_cookies(config: Config):
    try:
        if config.cookies is None:
            get_cookies(config)
    except GetCookieError as e:
        console.print(f"{e}", style="red")
        raise typer.Exit(code=1)
