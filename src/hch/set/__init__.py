import typer

from .password import app as password_app
from .target_time import app as target_time_app
from .username import app as username_app
from .wait_time import app as wait_time_app
from .cookies import app as cookies_app
from .max_retries import app as max_retries_app

app = typer.Typer(name="set", help="修改配置")

app.add_typer(password_app)
app.add_typer(username_app)
app.add_typer(target_time_app)
app.add_typer(wait_time_app)
app.add_typer(cookies_app)
app.add_typer(max_retries_app)
