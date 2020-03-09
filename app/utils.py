from flask import abort, request
import requests

from app import app


def get_location(request):
    stm_ip = request.remote_addr
    ENDPOINT_SERVICE = "http://ip-api.com/json/"+stm_ip+"?fields=status,lat,lon,query"
    if request.headers.get("X-API-KEY") != app.config["API_KEY"]:
        abort(401)

    resp = requests.get(ENDPOINT_SERVICE)
    if resp.status_code != 200:
        abort(404)

    data = resp.json()
    if data["status"] != "success":
        abort(404)
    else:
        lat = float(data.get('lat'))
        lon = float(data.get('lon'))
        return lat, lon
