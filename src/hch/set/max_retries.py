import typer
from typing_extensions import Annotated

from ..config import load_config

app = typer.Typer()


@app.command(name="max-retries")
def main(value: Annotated[int, typer.Argument(min=0)]):
    """
    设置最大重试次数
    """
    config = load_config()
    config.max_retries = value
    config.save()
