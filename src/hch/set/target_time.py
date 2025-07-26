from datetime import datetime

import typer

from ..config import load_config

app = typer.Typer()


@app.command(name="target-time")
def main(value: datetime):
    """
    设置目标时间
    """
    config = load_config()
    config.target_time = value
    config.save()
