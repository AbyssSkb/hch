import typer
from pydantic import ValidationError
from rich.table import Table

from ..console import console
from ..course import Course
from ..error import LoadCourseError

app = typer.Typer()


def display_selected_courses(courses: list[Course]) -> None:
    table = Table(show_lines=True)
    table.add_column("课程名称", style="cyan", vertical="middle", justify="center")
    table.add_column("课程信息", style="magenta")
    for course in courses:
        table.add_row(course.name, course.information)
    console.print(table)


@app.command(name="selected")
def main() -> None:
    """
    列出已选择的课程
    """
    try:
        selected_courses = Course.load()
    except LoadCourseError as e:
        console.print(f"{e}")
        raise typer.Exit(code=1)
    except ValidationError as e:
        console.print(e)
        raise typer.Exit(code=1)

    display_selected_courses(selected_courses)
