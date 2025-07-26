import typer

from .config import app as config_app
from .hunted import app as hunted_app
from .selected import app as selected_app

app = typer.Typer(name="list", help="查看信息")

app.add_typer(config_app)
app.add_typer(hunted_app)
app.add_typer(selected_app)
