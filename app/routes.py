import json

from flask import request, url_for, jsonify, abort, Response
from app import app, db
from app.models import Humidity, Temperature, Sensors


@app.route("/")
def index():
    response = {
        "sensors": {
            "humidity": url_for("query", sensor_type="humidity", _external=True),
            "temperature": url_for("query", sensor_type="temperature", _external=True),
        }
    }
    return jsonify(response)


@app.route("/temperature", methods=["GET", "POST"])
def temperature():
    if request.method == "POST":
        if request.headers.get("X-API-KEY") != app.config["API_KEY"]:
            abort(401)
        if not request.json or not "data" in request.json:
            abort(400)
        else:
            if not request.json.get("data").get("temperature"):
                abort(404)
            t = Temperature(temperature=request.json.get("data")["temperature"])
            db.session.add(t)
            db.session.commit()
            return jsonify({"status": "ok"})
    temperatures = Temperature.query.all()
    return jsonify(temperature_data=[i.serialize for i in temperatures])


@app.route("/humidity", methods=["GET", "POST"])
def humidity():
    if request.method == "POST":
        if request.headers.get("X-API-KEY") != app.config["API_KEY"]:
            abort(401)
        if not request.json or not "data" in request.json:
            abort(400)
        else:
            if not request.json.get("data").get("humidity"):
                abort(404)
            h = Humidity(humidity=request.json.get("data")["humidity"])
            db.session.add(h)
            db.session.commit()
            return jsonify({"status": "ok"})
    humidity = Humidity.query.all()

    return jsonify(humidity_data=[i.serialize for i in humidity])


@app.route("/update/<sensor_type>", methods=["POST"])
def update(sensor_type):
    if sensor_type not in ("humidity", "temperature"):
        abort(404)

    if request.headers.get("X-API-KEY") != app.config["API_KEY"]:
        abort(401)

    if not request.json or not "data" in request.json:
        abort(400)

    if sensor_type == "humidity":
        if not request.json.get("data").get("humidity"):
            abort(404)
        h = Humidity(humidity=request.json.get("data")["humidity"])
        db.session.add(h)
        db.session.commit()
    else:
        if not request.json.get("data").get("temperature"):
            abort(404)
        t = Temperature(temperature=request.json.get("data")["temperature"])
        db.session.add(t)
        db.session.commit()

    return jsonify({"status": "ok"})


@app.route("/query/<sensor_type>", methods=["GET"])
def query(sensor_type):

    if sensor_type == "humidity":
        humidity = Humidity.query.all()
        return jsonify(humidity_data=[i.serialize for i in humidity])
    else:
        temperatures = Temperature.query.all()
        return jsonify(temperature_data=[i.serialize for i in temperatures])

@app.route("/gen/<sensor_type>", methods=["GET"])
def gen(sensor_type):

    def generate():
        humidity = Humidity.query.all()
        print(len(humidity))
        hiter = iter(humidity)
        yield '{"data": ['
        while True:
            try:
                data = next(hiter)
                yield '{"humidity":'+str(data.humidity)+'},'
            except StopIteration:
                yield '{"humidity":'+str(data.humidity)+'}'
                break
        yield ']}'

    return Response(generate(), content_type='application/json')


@app.route("/update", methods=["POST"])
def update_all():
    if request.headers.get("X-API-KEY") != app.config["API_KEY"]:
        abort(401)

    if not request.json or not "data" in request.json:
        abort(400)

    if not request.json.get("data").get("humidity"):
        abort(404)
    else:
        humidity = request.json.get("data").get("humidity")

    if not request.json.get("data").get("temperature"):
        abort(404)
    else:
        temperature = request.json.get("data").get("temperature")

    sensor_data = Sensors(humidity=humidity, temperature=temperature)

    db.session.add(sensor_data)
    db.session.commit()

    return jsonify({"status": "ok"})

