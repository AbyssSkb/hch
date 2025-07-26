import json
from datetime import datetime
from pathlib import Path
from typing import Self

import typer
from pydantic import BaseModel, ValidationError, Field

from .console import console


class Config(BaseModel):
    username: str | None = None
    password: str | None = None
    target_time: datetime | None = None
    wait_time: int = Field(default=2, ge=0)
    cookies: str | None = None
    max_retries: int = Field(default=3, ge=0)

    @classmethod
    def load(cls, path: str | Path | None = None) -> Self:
        try:
            if path is None:
                app_dir = typer.get_app_dir("hch")
                path = Path(app_dir) / "config.json"
            with open(path, "r") as f:
                config = json.load(f)

            assert type(config) is dict
            return cls.model_validate(config)
        except FileNotFoundError:
            return cls()

    def save(self, path: str | Path | None = None) -> None:
        if path is None:
            app_dir = typer.get_app_dir("hch")
            path = Path(app_dir) / "config.json"
            path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, mode="w") as f:
            f.write(self.model_dump_json(indent=4))


def load_config() -> Config:
    try:
        config = Config.load()
    except ValidationError as e:
        console.print(e)
        raise typer.Exit(code=1)

    return config
