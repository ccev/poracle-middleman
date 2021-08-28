import re
import time
import json
import math
import pymysql
import discord
import requests

from io import BytesIO
from flask import Flask, request

with open("config.json", "r") as config_file:
    config = json.load(config_file)

webhooks = []
for webhook_url in config["webhooks"]:
    webhook = discord.Webhook.from_url(
        url=webhook_url,
        adapter=discord.RequestsWebhookAdapter()
    )
    webhooks.append(webhook)

pos = 0


def get_webhook():
    global pos
    pos += 1
    if pos > len(webhooks) - 1:
        pos = 0
    return webhooks[pos]


def test_vars(var):
    try:
        return float(var)
    except ValueError:
        pass
    try:
        return int(var)
    except ValueError:
        pass


def get_data(request):
    data = {}
    body_data = request.get_json()
    if body_data:
        data = body_data
    arg_data = request.args
    if arg_data:
        arg_data = {k: test_vars(v) for k, v in arg_data.items()}
        data = {**data, **arg_data}

    try:
        data.pop("pregenerate")
    except KeyError:
        pass
    try:
        data.pop("regeneratable")
    except KeyError:
        pass

    return data


def get_key(key, text):
    r = re.search(f"\"{key}\":( |)(\d*)", text)
    return int(r.group(2))


def gen_staticmap(request, map_kind, template_json=None, template=None):
    start = time.time()
    data = get_data(request)

    if template_json:
        kwargs = {
            "lat_center": data.get("lat", data.get("latitude", 0)),
            "lon_center": data.get("lon", data.get("longitude", 0)),
            "zoom": get_key("zoom", template_json),
            "width": get_key("width", template_json),
            "height": get_key("height", template_json)
        }

        data["middlejson"] = get_stops(**kwargs)

    extra_template = ""
    if template:
        extra_template = "/" + template
    response = requests.post(f"{config['tileserver_url']}{map_kind}{extra_template}", json=data)
    
    if response.status_code >= 400:
        return response.content

    stream = BytesIO(response.content)

    webhook = get_webhook()
    message = webhook.send(wait=True, file=discord.File(stream, filename="map.png"))
    stream.close()
    stop = time.time()
    print(f"Served tile in {stop-start} seconds")

    return message.attachments[0].url


def point_to_lat(lat_center, lon_center, zoom, width, height, wanted_points):
    # copied from https://help.openstreetmap.org/questions/75611/transform-xy-pixel-values-into-lat-and-long
    C = (256 / (2*math.pi)) * 2**zoom

    xcenter = C * (math.radians(lon_center) + math.pi)
    ycenter = C * (math.pi - math.log(math.tan((math.pi/4) + math.radians(lat_center) / 2)))

    xpoint = xcenter - (width / 2 - wanted_points[0])
    ypoint = ycenter - (height / 2 - wanted_points[1])

    C = (256 / (2 * math.pi)) * 2 ** zoom
    M = (xpoint / C) - math.pi
    N = -(ypoint / C) + math.pi

    fin_lon = math.degrees(M)
    fin_lat = math.degrees((math.atan(math.e**N)-(math.pi/4))*2)

    return fin_lat, fin_lon


def make_query(points, stop_type):
    if stop_type == "pokestop":
        search_columns_ = ""
    elif stop_type == "gym":
        search_columns_ = ", team_id as 'teamId'"
    return (
        f"SELECT latitude, longitude, '{stop_type}' as 'type'{search_columns_}"
        f"FROM {stop_type} "
        f"WHERE latitude >= {points[0]} "
        f"AND latitude <= {points[1]} "
        f"AND longitude >= {points[2]} "
        f"AND longitude <= {points[3]}"
    )


def query_stops(lats, lons):
    conn = pymysql.connect(
        host=config["db_host"],
        user=config["db_user"],
        password=config["db_pass"],
        database=config["db_name"],
        port=config["db_port"],
        autocommit=True,
        cursorclass=pymysql.cursors.DictCursor
    )
    cursor = conn.cursor()

    points = [
        min(lats),
        max(lats),
        min(lons),
        max(lons)
    ]

    stops = []
    for stop_type in ["pokestop", "gym"]:
        query = make_query(points, stop_type)
        cursor.execute(query)
        stops += cursor.fetchall()

    cursor.close()
    conn.close()
    return stops


def get_stops(**kwargs):
    width, height = kwargs["width"], kwargs["height"]
    lat1, lon1 = point_to_lat(**kwargs, wanted_points=(0, 0))
    lat2, lon2 = point_to_lat(**kwargs, wanted_points=(width, height))

    stops = query_stops([lat1, lat2], [lon1, lon2])
    if len(stops) == 0:
        return None

    stops = sorted(stops, key=lambda stop: (stop["latitude"], stop["longitude"]), reverse=True)

    """markers = []
    for lat, lon, stop_type in stops:
        markers.append({
            "url": f"https://raw.githubusercontent.com/ccev/stopwatcher-icons/master/tileserver-2/{stop_type}_grey.png",
            "latitude": lat,
            "longitude": lon,
            "width": 48,
            "height": 48,
            "y_offset": -32
        })

    final_json = json.dumps(markers)
    final_json = final_json.strip("[").strip("]") + ","
    
    return final_json
    """
    return stops


app = Flask(__name__)


@app.route('/<map_kind>/<template>', methods=['GET', 'POST'])
def templating(map_kind, template):
    template_json = None
    with open(config["templates_path"] + template + ".json", "r") as template_raw:
        template_text = template_raw.read()
        if "middlejson" in template_text:
            template_json = template_text
    return gen_staticmap(request, map_kind, template_json, template)


@app.route('/<map_kind>', methods=['GET', 'POST'])
def straight_map(map_kind):
    return gen_staticmap(request, map_kind)


app.run(port=config["port"])
