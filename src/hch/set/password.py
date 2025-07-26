import typer

from ..config import load_config

app = typer.Typer()


@app.command(name="password")
def main(value: str):
    """
    设置密码
    """
    config = load_config()
    config.password = value
    config.save()
