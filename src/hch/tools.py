import httpx
from rich.table import Table
from selectolax.parser import HTMLParser

from .console import console
from .course import Course
from .error import CookieExpiredError, GetCourseCategoryError, GetCourseError
from .login import get_headers
from .time_info import TimeInfo


def display_categories(categories: list[dict[str, str]]) -> None:
    """显示可选课程类别列表

    将课程类别打印到控制台。

    Args:
        categories (list[dict[str, str]]): 课程类别列表
    """
    table = Table()
    table.add_column("课程编号", style="cyan")
    table.add_column("课程类别", style="magenta")
    for i, category in enumerate(categories):
        table.add_row(f"{i + 1}", f"{category['name']}")
    console.print(table)


def display_course(course: Course) -> None:
    table = Table()
    table.add_column("课程名称", style="cyan", vertical="middle", justify="center")
    table.add_column("课程信息", style="magenta")
    table.add_column(
        "已选人数/总容量", style="yellow", vertical="middle", justify="center"
    )
    table.add_row(
        course.name,
        course.information,
        f"{course.enrolled}/{course.capacity}",
    )
    console.print(table)


def get_course_categories(time_info: TimeInfo, cookies: str) -> list[dict[str, str]]:
    """获取课程类别列表

    Args:
        time_info (dict[str, str]): 学年学期信息字典
        cookies (str)

    Returns:
        list[dict[str, str]]: 课程类别列表，每个元素是包含课程类别信息的字典

    Raises:
        CookieExpiredError: 当 Cookie 失效时抛出
        GetCourseCategoryError: 有其它错误时抛出
    """
    headers = get_headers(cookies)
    url = "http://jw.hitsz.edu.cn/Xsxk/queryYxkc"
    data = {"p_xn": time_info.academic_year, "p_xq": time_info.term}
    response = httpx.post(url=url, headers=headers, data=data, follow_redirects=True)
    if response.status_code == 200:
        if "application/json" in response.headers["Content-Type"]:
            response_json = response.json()
            try:
                categories = []
                elements = response_json["xkgzszList"]
                for element in elements:
                    code = element["xkfsdm"]  # 获取课程类别代码
                    name = element["xkfsmc"]  # 获取课程类别名称
                    categories.append({"code": code, "name": name})

                console.print("[green]成功获取课程类别")
                return categories
            except KeyError:
                message = response_json["message"]
                raise GetCourseCategoryError(f"[red]时间信息获取失败：{message}")
        elif "text/html" in response.headers["Content-Type"]:
            raise CookieExpiredError()
        else:
            raise GetCourseCategoryError("[red]响应内容不是有效的 JSON 格式")
    else:
        raise GetCourseCategoryError(f"[red]请求失败，状态码：{response.status_code}")


def get_courses(
    category: dict[str, str],
    time_info: TimeInfo,
    cookies: str,
    keyword: str,
) -> list[Course]:
    """根据类别和关键词搜索课程

    获取指定类别下符合关键词的可选课程列表。
    如果关键词为空字符串，则返回该类别下的所有课程。

    Args:
        category (dict[str, str]): 包含课程类别代码和名称的字典
        time_info (TimeInfo): 学年学期信息字典
        cookies (str)
        keyword (str): 搜索关键词

    Returns:
        list[Course]: 课程列表
    Raises:
        CookieExpiredError: Cookie 失效时抛出
        GetCourseError: 课程信息获取失败时抛出
    """
    headers = get_headers(cookies)
    url = "http://jw.hitsz.edu.cn/Xsxk/queryKxrw"
    data = {
        "p_pylx": "1",
        "p_gjz": keyword,
        "p_xn": time_info.academic_year,
        "p_xq": time_info.term,
        "p_dqxn": time_info.current_academic_year,
        "p_dqxq": time_info.current_term,
        "p_xkfsdm": category["code"],
    }

    response = httpx.post(url, data=data, headers=headers, follow_redirects=True)
    if response.status_code == 200:
        if "application/json" in response.headers["Content-Type"]:
            response_json = response.json()
            try:
                elements: list[dict[str, str]] = response_json["kxrwList"]["list"]
                courses: list[Course] = []
                for course in elements:
                    tree = HTMLParser(course["kcxx"])
                    information = tree.text(separator="\n")
                    courses.append(
                        Course(
                            id=course["id"],
                            name=course["kcmc"].strip() + course["tyxmmc"].strip(),
                            information=information.strip(),
                            code=category["code"],
                            academic_year=time_info.academic_year,
                            term=time_info.term,
                            capacity=course["zrl"],
                            enrolled=course["yxzrs"],
                            hunted_time=None,
                        )
                    )
                return courses
            except KeyError:
                message = response_json["message"]
                raise GetCourseError(f"[red]课程信息获取失败：{message}")
        elif "text/html" in response.headers["Content-Type"]:
            raise CookieExpiredError()
        else:
            raise GetCourseError("[red]响应内容不是有效的 JSON 格式")
    else:
        raise GetCourseError(f"[red]请求失败，状态码：{response.status_code}")
