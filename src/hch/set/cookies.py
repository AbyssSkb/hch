import typer

from ..config import load_config

app = typer.Typer()


@app.command(name="cookies")
def main(value: str):
    """
    设置 Cookies
    """
    config = load_config()
    config.cookies = value
    config.save()
