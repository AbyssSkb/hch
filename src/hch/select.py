import typer
from pydantic import ValidationError
from rich.prompt import IntPrompt, Prompt

from .config import Config, load_config
from .console import console
from .course import Course
from .error import CookieExpiredError, LoadCourseError, MaxRetriesError
from .spinning import (
    check_cookies,
    get_cookies,
    get_course_categories,
    get_time_info,
    run_spinning,
)
from .time_info import TimeInfo
from .tools import display_categories, display_course, get_courses

retries = 0
app = typer.Typer()


def select_courses(
    categories: list[dict[str, str]],
    time_info: TimeInfo,
    config: Config,
    selected_courses: list[Course],
) -> None:
    """执行课程准备流程"""
    global retries
    assert config.cookies is not None
    while True:
        display_categories(categories)
        opt = IntPrompt.ask(
            "输入课程编号 (0 退出程序)",
            console=console,
            choices=[str(i) for i in range(len(categories) + 1)],
            show_choices=False,
        )
        if opt == 0:
            break

        selected_category = categories[opt - 1]
        while True:
            keyword = Prompt.ask(
                "输入课程关键词 (q 返回上一级，直接回车查找全部)", console=console
            )
            if keyword == "q":
                break

            get_courses_spinning = run_spinning(
                get_courses, description=f"Searching {keyword}"
            )

            pending_courses = None
            while retries < config.max_retries and pending_courses is None:
                try:
                    pending_courses = get_courses_spinning(
                        category=selected_category,
                        time_info=time_info,
                        cookies=config.cookies,
                        keyword=keyword,
                    )
                except CookieExpiredError:
                    get_cookies(config)
                    retries += 1

            if pending_courses is None:
                raise MaxRetriesError()

            filter_courses(pending_courses, selected_courses)


def filter_courses(
    pending_courses: list[Course], selected_courses: list[Course]
) -> None:
    """处理用户的课程选择过程

    遍历课程列表，让用户对每门课程进行选择：
    - y: 添加到选课列表
    - n: 跳过当前课程
    - q: 退出选课过程

    Args:
        pending_courses (list[Course]): 可选课程列表
        selected_courses (list[Course]): 已选课程列表
    """
    if len(pending_courses) == 0:
        console.print("未找到课程", style="yellow")
        return

    console.print(f"[green]共找到 [white]{len(pending_courses)} [green]门课程")
    for course in pending_courses:
        display_course(course)
        opt = Prompt.ask("是否选择该课程？", choices=["y", "n", "q"])
        if opt == "y":
            selected_courses.append(course)
            console.print("[green]已添加到待抢列表")
        elif opt == "q":
            return


@app.command(name="select")
def main() -> None:
    """
    选择课程
    """
    try:
        selected_courses = Course.load()
    except ValidationError as e:
        console.print(e)
        raise typer.Exit(code=1)
    except LoadCourseError:
        selected_courses = []

    config = load_config()

    check_cookies(config)
    assert config.cookies is not None

    global retries
    try:
        time_info = None
        while retries < config.max_retries and not time_info:
            try:
                time_info = get_time_info(config.cookies)
            except CookieExpiredError:
                get_cookies(config)
                retries += 1
        if time_info is None:
            raise MaxRetriesError()

        categories = None
        while retries < config.max_retries and categories is None:
            try:
                categories = get_course_categories(time_info, config.cookies)
            except CookieExpiredError:
                get_cookies(config)
                retries += 1
        if categories is None:
            raise MaxRetriesError()

        select_courses(categories, time_info, config, selected_courses)

    except MaxRetriesError:
        console.print("[red]尝试次数已达最大限制")
        raise typer.Exit(code=1)
    except KeyboardInterrupt:
        console.print("[yellow]\n正在退出...[/yellow]")
    finally:
        config.save()
        Course.save(selected_courses)
