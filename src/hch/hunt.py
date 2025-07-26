import time
from datetime import datetime

import typer
from pydantic import ValidationError
from rich.live import Live
from rich.progress import track
from rich.text import Text
from typing_extensions import Annotated

from .config import Config, load_config
from .console import console
from .course import Course
from .error import CookieExpiredError, HuntCourseError, LoadCourseError
from .spinning import get_cookies, run_spinning

retries = 0
app = typer.Typer()


def wait_until(target_time: datetime) -> None:
    """倒计时等待至指定时间

    Args:
        target_time (datetime): 目标开始时间
    """

    def remaining_time():
        text = Text()
        text.append("剩余 ", style="cyan")
        text.append(
            f"{int((target_time - datetime.now()).total_seconds())} ", style="white"
        )
        text.append("秒", style="cyan")
        return text

    with Live(remaining_time(), console=console, transient=True) as live:
        while True:
            if datetime.now() > target_time:
                break

            time.sleep(0.1)
            live.update(remaining_time())


def hunt_courses(pending_courses: list[Course], config: Config, wait_time: int) -> None:
    """执行选课流程

    Args:
        courses (list[Course]): 要选择的课程列表
        config (Config)
        wait_time (int): 每次尝试选课之间的等待时间（秒）
    """
    assert config.cookies is not None
    unsuccessful_courses: list[Course] = []
    num_courses = len(pending_courses)
    index = 0
    global retries
    try:
        while index < num_courses:
            if retries == config.max_retries:
                break
            course = pending_courses[index]
            try:
                console.print()
                hunt_spinning = run_spinning(
                    course.hunt, description=f"Hunting: [cyan]{course.name}"
                )
                hunt_spinning(config.cookies)
                console.print(f"[green]选课成功：[white]{course.name}")
                index += 1
            except CookieExpiredError:
                console.print("Cookie 过期，尝试重新获取", style="yellow")
                get_cookies(config)
                retries += 1
            except HuntCourseError as e:
                console.print(f"[red]选课失败：[cyan]{course.name}")
                console.print(f"{e}")
                retries += 1
                unsuccessful_courses.append(course)
                index += 1
            finally:
                if index < num_courses or unsuccessful_courses:
                    for _ in track(range(wait_time * 10), description="Waiting..."):
                        time.sleep(0.1)
    finally:
        for i in range(index, num_courses):
            unsuccessful_courses.append(pending_courses[i])
        pending_courses.clear()
        pending_courses.extend(unsuccessful_courses)


@app.command(name="hunt")
def main(
    is_immediate_hunt: Annotated[
        bool, typer.Option("--now", "-n", help="立即抢课")
    ] = False,
    wait_time: Annotated[
        int | None,
        typer.Option(
            help="课程抢课间隔时间（秒），优先级高于配置文件", show_default=False
        ),
    ] = None,
) -> None:
    """
    抢课
    """
    try:
        pending_courses = Course.load()
    except LoadCourseError as e:
        console.print(f"{e}")
        raise typer.Exit(code=1)
    except ValidationError as e:
        console.print(e)
        raise typer.Exit(code=1)

    config = load_config()

    try:
        if config.cookies is None:
            get_cookies(config)
        if wait_time is None:
            wait_time = config.wait_time

        target_time = config.target_time
        if target_time and not is_immediate_hunt:
            console.print(
                f"[cyan]计划开始时间: [white]{target_time.strftime('%H:%M:%S')}"
            )
            wait_until(target_time)
        console.print("开始抢课", style="green")

        while retries < config.max_retries and pending_courses:
            hunt_courses(pending_courses, config, wait_time)

        if pending_courses:
            console.print("尝试次数已达最大限制", style="red")

    except KeyboardInterrupt:
        console.print("\n退出程序", style="yellow")
    finally:
        config.save()
        Course.save(pending_courses)
