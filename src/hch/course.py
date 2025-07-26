import json
from pathlib import Path
from typing import Self

import httpx
import typer
from pydantic import BaseModel

from .error import CookieExpiredError, HuntCourseError, LoadCourseError
from .login import get_headers


class Course(BaseModel):
    id: str
    name: str
    information: str
    code: str
    academic_year: str
    term: str
    capacity: str
    enrolled: str
    hunted_time: str | None

    @classmethod
    def load(cls, path: str | Path | None = None) -> list[Self]:
        error_message = "[red]没有课程，请先运行 [cyan]`hch select`"
        try:
            if path is None:
                app_dir = typer.get_app_dir("hch")
                path = Path(app_dir) / "courses.json"
            with open(path, "r") as f:
                courses = json.load(f)
                courses = [cls.model_validate(course) for course in courses]

            if len(courses) == 0:
                raise LoadCourseError(error_message)
            return courses
        except FileNotFoundError:
            raise LoadCourseError(error_message)

    @classmethod
    def save(cls, courses: list[Self], path: str | Path | None = None) -> None:
        if path is None:
            app_dir = typer.get_app_dir("hch")
            path = Path(app_dir) / "courses.json"
            path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            dump_courses = [cls.model_dump(course) for course in courses]
            json.dump(dump_courses, f, ensure_ascii=False, indent=4)

    def hunt(self, cookies: str) -> None:
        """尝试选课

        Args:
            cookies (str)

        Raises:
            HuntCourseError: 选课失败时抛出
            CookieExpiredError: Cookie 失效时抛出
        """
        headers = get_headers(cookies)
        url = "http://jw.hitsz.edu.cn/Xsxk/addGouwuche"
        data = {
            "p_xktjz": "rwtjzyx",
            "p_xn": self.academic_year,
            "p_xq": self.term,
            "p_xkfsdm": self.code,
            "p_id": self.id,
        }
        response = httpx.post(url, data=data, headers=headers)
        if response.status_code == 200:
            if "application/json" in response.headers["Content-Type"]:
                response_json = response.json()
                message = response_json["message"]
                if message == "操作成功":
                    return
                else:
                    raise HuntCourseError(f"[red]{message}")
            elif "text/html" in response.headers["Content-Type"]:
                raise CookieExpiredError()
            else:
                raise HuntCourseError("[red]响应内容不是有效的 JSON 格式")
        else:
            raise HuntCourseError(f"[red]请求失败，状态码：{response.status_code}")
