import typer
from pydantic import ValidationError

from .console import console
from .course import Course
from .error import LoadCourseError
from .select import filter_courses

app = typer.Typer()


@app.command(name="change")
def main():
    """
    更改已选择的课程
    """
    try:
        pending_courses = Course.load()
    except LoadCourseError as e:
        console.print(f"{e}")
        raise typer.Exit(code=1)
    except ValidationError as e:
        console.print(e)
        raise typer.Exit(code=1)

    filtered_courses: list[Course] = []
    try:
        filter_courses(pending_courses, filtered_courses)
    except KeyboardInterrupt:
        filtered_courses = pending_courses
    finally:
        Course.save(filtered_courses)
