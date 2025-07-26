import typer

from ..config import load_config

app = typer.Typer()


@app.command(name="username")
def main(value: str):
    """
    设置用户名
    """
    config = load_config()
    config.username = value
    config.save()
