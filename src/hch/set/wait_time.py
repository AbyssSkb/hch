import typer
from typing_extensions import Annotated

from ..config import load_config

app = typer.Typer()


@app.command(name="wait-time")
def main(value: Annotated[int, typer.Argument(min=0)]):
    """
    设置等待时间
    """
    config = load_config()
    config.wait_time = value
    config.save()
