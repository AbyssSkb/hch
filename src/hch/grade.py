from typing import Self

import httpx
import typer
from pydantic import BaseModel
from rich.table import Table

from .config import load_config
from .console import console
from .error import CookieExpiredError, GetGradeError, MaxRetriesError
from .login import get_cookies, get_headers
from .spinning import run_spinning


class Grade(BaseModel):
    score: str
    course_type: str | None
    course_name: str
    rank: str
    total_students: str

    @classmethod
    def get(cls, cookies: str) -> list[Self]:
        headers = get_headers(cookies)
        url = "http://jw.hitsz.edu.cn/cjgl/grcjcx/grcjcx"
        data = {
            "pylx": "1",
            "current": 1,
            "pageSize": 100,
        }

        response = httpx.post(url, json=data, headers=headers, follow_redirects=True)
        if response.status_code == 200:
            if "application/json" in response.headers["Content-Type"]:
                response_json = response.json()
                try:
                    elements: list[dict[str, str]] = response_json["content"]["list"]
                    grades: list[Self] = []
                    for element in elements:
                        grades.append(
                            cls(
                                score=element["zzcj"],
                                course_type=element["khfs"],
                                course_name=element["kcmc"],
                                rank=element["pm"],
                                total_students=element["zrs"],
                            )
                        )
                    return grades
                except TypeError:
                    message = response_json["msg"]
                    raise GetGradeError(message)
            elif "text/html" in response.headers["Content-Type"]:
                raise CookieExpiredError()
            else:
                raise GetGradeError("[red]响应内容不是有效的 JSON 格式")
        else:
            raise GetGradeError(f"[red]请求失败，状态码：{response.status_code}")


app = typer.Typer()


def display_grades(grades: list[Grade]) -> None:
    table = Table()
    table.add_column("课程", style="cyan")
    table.add_column("类别", style="magenta")
    table.add_column("成绩", style="green")
    table.add_column("排名", style="yellow")
    for grade in grades:
        table.add_row(
            grade.course_name,
            grade.course_type,
            grade.score,
            f"{grade.rank}/{grade.total_students}",
        )
    console.print(table)


get_grades = run_spinning(Grade.get, description="Fetching Grades")


@app.command(name="grade")
def main() -> None:
    """
    获取成绩
    """
    config = load_config()
    assert config.cookies is not None
    retries = 0
    try:
        grades = None
        while retries < config.max_retries and grades is None:
            try:
                grades = get_grades(config.cookies)
            except CookieExpiredError:
                get_cookies(config)
                retries += 1
        if grades is None:
            raise MaxRetriesError()

        display_grades(grades)
    except MaxRetriesError:
        console.print("尝试次数已达最大限制", style="red")
        raise typer.Exit(code=1)
    except KeyboardInterrupt:
        console.print("\n正在退出...", style="yellow")
    finally:
        config.save()
