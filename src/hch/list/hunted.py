import httpx
import typer
from rich.table import Table
from selectolax.parser import HTMLParser

from ..config import load_config
from ..console import console
from ..course import Course
from ..error import CookieExpiredError, GetHuntedCourseError, MaxRetriesError
from ..login import get_headers
from ..spinning import check_cookies, get_cookies, get_time_info
from ..time_info import TimeInfo

app = typer.Typer()
retries = 0


def display_hunted_courses(courses: list[Course]) -> None:
    table = Table()
    table.add_column("课程名称", style="cyan")
    table.add_column("已选人数/总容量", style="green")
    table.add_column("抢课时间", style="yellow")
    for course in courses:
        table.add_row(
            course.name,
            f"{course.enrolled}/{course.capacity}",
            course.hunted_time,
        )
    console.print(table)


def get_hunted_courses(time_info: TimeInfo, cookies: str) -> list[Course]:
    headers = get_headers(cookies)
    url = "http://jw.hitsz.edu.cn/Xsxk/queryYxkc"
    data = {
        "p_pylx": "1",
        "p_xn": time_info.academic_year,
        "p_xq": time_info.term,
        "p_dqxn": time_info.current_academic_year,
        "p_dqxq": time_info.current_term,
        "p_xkfsdm": "yixuan",
    }

    response = httpx.post(url, data=data, headers=headers, follow_redirects=True)
    if response.status_code == 200:
        if "application/json" in response.headers["Content-Type"]:
            response_json = response.json()
            try:
                elements: list[dict[str, str]] = response_json["yxkcList"]
                courses: list[Course] = []
                for course in elements:
                    tree = HTMLParser(course["kcxx"])
                    information = tree.text(separator="\n")
                    courses.append(
                        Course(
                            id=course["id"],
                            name=course["kcmc"].strip() + course["tyxmmc"].strip(),
                            information=information.strip(),
                            code=course["xkfsdm"],
                            academic_year=time_info.academic_year,
                            term=time_info.term,
                            capacity=course["zrl"],
                            enrolled=course["yxzrs"],
                            hunted_time=course["xksj"],
                        )
                    )
                return courses
            except KeyError:
                message = response_json["message"]
                raise GetHuntedCourseError(f"[red]课程信息获取失败：{message}")
        elif "text/html" in response.headers["Content-Type"]:
            raise CookieExpiredError()
        else:
            raise GetHuntedCourseError("[red]响应内容不是有效的 JSON 格式")
    else:
        raise GetHuntedCourseError(f"[red]请求失败，状态码：{response.status_code}")


@app.command(name="hunted")
def main():
    """
    列出已抢课程
    """
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

        hunted_courses = get_hunted_courses(time_info, config.cookies)
        display_hunted_courses(hunted_courses)

    except MaxRetriesError:
        console.print("[red]尝试次数已达最大限制")
        raise typer.Exit(code=1)
    except KeyboardInterrupt:
        console.print("[yellow]\n正在退出...[/yellow]")
    finally:
        config.save()
