import typer

from .change import app as change_app
from .hunt import app as hunt_app
from .list import app as list_app
from .select import app as select_app
from .set import app as set_app
from .grade import app as grade_app

app = typer.Typer(help="Awesome HITSZ course hunter.")
app.add_typer(hunt_app)
app.add_typer(select_app)
app.add_typer(set_app)
app.add_typer(list_app)
app.add_typer(change_app)
app.add_typer(grade_app)
