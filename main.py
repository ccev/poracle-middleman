from __future__ import annotations

from aiohttp import web

from poracle_middleman.config import config
from poracle_middleman.geocoder import Geocoder
from poracle_middleman.tileserver import Tileserver


def main():
    app = web.Application()

    if config.geocoder.enable:
        geocoder = Geocoder()
        app.add_routes([web.route("*", "/geocoder/reverse", geocoder.endpoint)])

    if config.tileserver.enable:
        tileserver = Tileserver()
        route = "/tileserver/{map_kind}"
        app.add_routes(
            [
                web.route("*", route, tileserver.endpoint_straight),
                web.route("*", route + "/{template}", tileserver.endpoint_template),
            ]
        )

    web.run_app(app, host=config.host, port=config.port)


if __name__ == "__main__":
    main()
