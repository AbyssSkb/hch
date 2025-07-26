import typer
from rich.table import Table

from ..config import Config, load_config
from ..console import console

app = typer.Typer()


def display_config(config: Config):
    table = Table()
    table.add_column("名称", style="cyan")
    table.add_column("值", style="magenta")
    for key, value in config.model_dump().items():
        table.add_row(str(key), str(value))

    console.print(table)


@app.command()
def config():
    """
    列出配置
    """
    config = load_config()
    display_config(config)
