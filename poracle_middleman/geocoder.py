from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum

import aiohttp
import shapely
from aiohttp import web
from pydantic import BaseModel, ValidationError, Field

from .config import config
from .geojson_models import PolygonGeojson


@dataclass
class Address:
    street: str | None = None
    suburb: str | None = None
    city: str | None = None
    poi: str | None = None

    def __bool__(self) -> bool:
        return bool(self.street)

    def get_full(self) -> str:
        street = ": " + self.street if self.street else ""
        city = self.city if self.city else ""
        poi = " " + self.poi if self.poi else ""

        if self.suburb:
            return f"{self.suburb}{poi}{street}, {city}"
        else:
            return f"{city}{poi}{street}"


@dataclass
class NamedPolygon:
    polygon: shapely.Polygon
    name: str


class PlaceType(str, Enum):
    ADDRESS = "address"
    LOCALITY = "locality"
    PLACE = "place"


class Feature(BaseModel):
    place_type: list[str]
    text: str | None
    address: str | None


class MapboxResponse(BaseModel):
    features: list[Feature]


class NomiAddress(BaseModel):
    house_number: str | None
    road: str | None
    suburb: str | None = Field(alias="city_district")
    city: str | None


class NomiResponse(BaseModel):
    address: NomiAddress


class Geocoder:
    def __init__(self):
        self.pois: list[NamedPolygon] = []
        self.suburbs: list[NamedPolygon] = []

        if config.geocoder.poi_geojson:
            self._make_named_polygon(config.geocoder.poi_geojson, self.pois)

        if config.geocoder.suburb_geojson:
            self._make_named_polygon(config.geocoder.suburb_geojson, self.suburbs)

    @staticmethod
    def _make_named_polygon(path: str, polygons: list[NamedPolygon]) -> None:
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)

        try:
            geojson = PolygonGeojson(**raw)
        except ValidationError as e:
            print(f"{path} is an invalid Geojson: {e}")
            return

        for feature in geojson.features:
            polygons.append(
                NamedPolygon(name=feature.properties.name, polygon=shapely.Polygon(*feature.geometry.coordinates))
            )

    async def endpoint(self, request: web.Request) -> web.Response:
        def get_coord(key: str) -> float:
            coord = request.query.get(key)

            if coord is None:
                raise web.HTTPBadRequest(reason=f"Missing argument: {key}")

            try:
                return float(coord)
            except ValueError:
                raise web.HTTPBadRequest(reason=f"Bad value for {key}")

        lat = get_coord("lat")
        lon = get_coord("lon")

        addr = await self.query_mapbox(lat, lon)
        if not addr:
            addr = await self.query_nominatim(lat, lon, addr)

        point = shapely.Point(lon, lat)

        for polygon in self.suburbs:
            if not polygon.polygon.contains(point):
                continue
            addr.suburb = polygon.name

        for polygon in self.pois:
            if not polygon.polygon.contains(point):
                continue
            addr.poi = polygon.name

        return web.json_response(
            {
                "license": "",
                "display_name": addr.get_full(),
                "address": {
                    "house_number": "",
                    "road": "",
                    "suburb": "",
                    "town": "",
                    "county": "",
                    "state": "",
                    "postcode": "",
                    "country": "",
                    "country_code": "--",
                },
            }
        )

    @staticmethod
    async def _query(url) -> dict | list | None:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    return await resp.json()
        except Exception as e:
            print(f"Exception while fetching Mapbox: {e}")
            return None

    async def query_mapbox(self, lat: float, lon: float) -> Address:
        address = Address()

        if not config.geocoder.mapbox_key:
            return address

        url = (
            f"https://api.mapbox.com/geocoding/v5/mapbox.places/"
            f"{lon},{lat}"
            f".json?language={config.geocoder.language}&access_token="
            f"{config.geocoder.mapbox_key}"
        )

        raw_data = await self._query(url)
        if raw_data is None:
            return address

        try:
            data = MapboxResponse(**raw_data)
        except ValidationError as e:
            print(f"Mapbox Response wasn't the right format: {e}")
            return address

        for feature in data.features:
            if PlaceType.ADDRESS.value in feature.place_type and feature.text:
                address.street = feature.text

                if feature.address:
                    address.street += " " + feature.address
            if PlaceType.LOCALITY.value in feature.place_type and feature.text:
                address.suburb = feature.text
            if PlaceType.PLACE.value in feature.place_type and feature.text:
                address.city = feature.text

        return address

    async def query_nominatim(self, lat: float, lon: float, addr: Address) -> Address:
        url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json&accept_language=de"

        raw = await self._query(url)
        if raw is None:
            return addr

        try:
            data = NomiResponse(**raw)
        except ValidationError as e:
            print(f"Nominatim Response wasn't the right format: {e}")
            return addr

        if data.address.road:
            addr.street = data.address.road

            if data.address.house_number:
                addr.street += " " + data.address.house_number
        if data.address.suburb:
            addr.suburb = data.address.suburb
        if data.address.city:
            addr.city = data.address.city

        return addr
