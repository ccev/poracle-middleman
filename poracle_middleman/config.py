from __future__ import annotations

import sys
from enum import Enum

import rtoml
from pydantic import BaseModel, ValidationError


class Geocoder(BaseModel):
    enable: bool = False
    language: str = "en"
    mapbox_key: str | None = None
    suburb_geojson: str | None = None
    poi_geojson: str | None = None


class Tileserver(BaseModel):
    enable: bool = False
    url: str = ""
    templates_path: str = ""
    webhooks: list[str] = []
    replace: dict[str, str] = {}


class Config(BaseModel):
    host: str = "0.0.0.0"
    port: int = 3031
    geocoder: Geocoder = Geocoder()
    tileserver: Tileserver = Tileserver()


try:
    with open("config.toml", mode="r") as _config_file:
        _raw_config = rtoml.load(_config_file)

    try:
        _config = Config(**_raw_config)
    except ValidationError as e:
        print(f"Config validation error!\n{e}")
        sys.exit(1)
except FileNotFoundError:
    _config = Config()

config = _config