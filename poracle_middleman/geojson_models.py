from __future__ import annotations

from pydantic import BaseModel


class PolygonProperties(BaseModel):
    name: str


class PolygonGeometry(BaseModel):
    coordinates: tuple[list[tuple[float, float]]]


class PolygonFeature(BaseModel):
    properties: PolygonProperties
    geometry: PolygonGeometry


class PolygonGeojson(BaseModel):
    features: list[PolygonFeature]
