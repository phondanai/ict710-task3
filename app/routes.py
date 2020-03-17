import json
from threading import Thread
import time

from flask import request, url_for, jsonify, abort, Response, render_template
from flask_socketio import emit

import numpy as np
import paho.mqtt.subscribe as subscribe

from app import app, db, socketio
from app.models import Humidity, Temperature, Sensors
from app.utils import get_location

thread = None


classes = {
    0: "Outside",
    1: "Inside"
}

def predict(rssi):
    d1,d2,d3 = rssi
    all_device = np.array([[d1,d2,d3]])
    predicted = app.config.model.predict_classes(all_device)[0][0]

    return classes.get(predicted),


def extract(mqtt_msg):
    msg = mqtt_msg
    board_no = int(msg.topic.split('/')[-1])
    json_str = str(msg.payload.decode('ascii')).replace('\x00', '')
    data = json.loads(json_str)

    return board_no, data["data"]


def background_thread():
    """Example of how to send server generated events to clients."""
    count = 0
    CLIENT_ID = app.config.get('MQTT_CLIENT_ID')
    NETPIE_TOKEN = app.config.get('MQTT_TOKEN')
    board = [-99,-99,-99]
    while True:
        count += 1
        msg = subscribe.simple('@msg/taist2020/board/#', hostname='mqtt.netpie.io', port=1883, client_id=CLIENT_ID, auth={'username':NETPIE_TOKEN, 'password':None}, keepalive=600)
        board_no, rssi = extract(msg)
        board[board_no-1] = rssi

        predicted = predict(board)

        socketio.emit('my response',
                     {'data': predicted, 'board_1': board[0], 'board_2': board[1], 'board_3': board[2]},
                      namespace='/test')


@app.before_first_request
def load_model():
    print("Loading model")
    from keras.models import load_model
    app.config.model = load_model(app.config.get("MODEL_FILE"))


@app.route('/track')
def track():
    global thread
    if thread is None:
        thread = Thread(target=background_thread)
        thread.daemon = True
        thread.start()
    return render_template('index.html')


@app.route("/")
def index():
    response = {
        "sensors": {
            "humidity": url_for("query", sensor_type="humidity", _external=True),
            "temperature": url_for("query", sensor_type="temperature", _external=True),
        }
    }
    return jsonify(response)

@app.route("/sock")
def sock():
    return render_template('index.html', async_mode=socketio.async_mode)


#@app.route("/predict")
#def predict():
#    d1,d2,d3 = request.args.get('d1', -99),\
#               request.args.get('d2', -99),\
#               request.args.get('d3', -99)
#    all_device = np.array([[d1,d2,d3]])
#    print(all_device)
#    predicted = app.config.model.predict_classes(all_device)[0][0]
#    response = {
#        "predict": classes.get(predicted),
#    }
#
#    return jsonify(response)


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


@app.route("/gen", methods=["GET"])
@app.route("/gen/<sensor_type>", methods=["GET"])
def gen(sensor_type="all"):

    if sensor_type not in ("humidity", "temperature", "all"):
        abort(404)

    def generate():
        sensors = Sensors.query.all()
        datas = iter(sensors)
        yield '{"data": ['
        while True:
            try:
                data = next(datas)
                if sensor_type == "all":
                    yield '{"humidity":' + str(
                        data.humidity
                    ) + "," + '"temperature":' + str(
                        data.temperature
                    ) + "," + '"timestamp": ' + '"' + str(
                        data.timestamp
                    ) + '"' + "},"
                elif sensor_type == "humidity":
                    yield '{"humidity":' + str(
                        data.humidity
                    ) + "," + '"timestamp": ' + '"' + str(data.timestamp) + '"' + "},"
                else:
                    yield '{"temperature":' + str(
                        data.temperature
                    ) + "," + '"timestamp": ' + '"' + str(data.timestamp) + '"' + "},"
            except StopIteration:
                if sensor_type == "all":
                    yield '{"humidity":' + str(
                        data.humidity
                    ) + "," + '"temperature":' + str(
                        data.temperature
                    ) + "," + '"timestamp": ' + '"' + str(
                        data.timestamp
                    ) + '"' + "}"
                    break
                elif sensor_type == "humidity":
                    yield '{"humidity":' + str(
                        data.humidity
                    ) + "," + '"timestamp": ' + '"' + str(data.timestamp) + '"' + "}"
                    break
                else:
                    yield '{"temperature":' + str(
                        data.humidity
                    ) + "," + '"timestamp": ' + '"' + str(data.timestamp) + '"' + "}"
                    break
        yield "]}"

    return Response(generate(), content_type="application/json")

    # elif sensor_type == "humidity":

    #    def generate():
    #        humidity = Sensors.query.with_entities(Sensors.humidity).all()
    #        datas = iter(humidity)
    #        yield '{"data": ['
    #        while True:
    #            try:
    #                data = next(hiter)
    #                yield '{"humidity":' + str(data.humidity) + "},"
    #            except StopIteration:
    #                yield '{"humidity":' + str(data.humidity) + "}"
    #                break
    #        yield "]}"

    #    return Response(generate(), content_type="application/json")

    # def generate():
    #    humidity = Humidity.query.all()
    #    print(len(humidity))
    #    hiter = iter(humidity)
    #    yield '{"data": ['
    #    while True:
    #        try:
    #            data = next(hiter)
    #            yield '{"humidity":' + str(data.humidity) + "},"
    #        except StopIteration:
    #            yield '{"humidity":' + str(data.humidity) + "}"
    #            break
    #    yield "]}"

    # return Response(generate(), content_type="application/json")


@app.route("/update", methods=["POST"])
def update_all():
    if request.headers.get("X-API-KEY") != app.config["API_KEY"]:
        abort(401)

    if not request.json or not "data" in request.json:
        abort(400)

    humidity = request.json.get("data").get("humidity")
    temperature = request.json.get("data").get("temperature")

    if not humidity or not temperature:
        abort(404)

    lat, lon = get_location(request)
    sensor_data = Sensors(humidity=humidity, temperature=temperature, lat=lat, lon=lon)

    db.session.add(sensor_data)
    db.session.commit()

    return jsonify({"status": "ok"})


@socketio.on('my event', namespace='/test')
def test_message(message):
    emit('my response', {'data': message['data']})

@socketio.on('my broadcast event', namespace='/test')
def test_message(message):
    emit('my response', {'data': message['data']}, broadcast=True)

@socketio.on('connect', namespace='/test')
def test_connect():
    emit('my connected', {'data': 'Connected!!'})

@socketio.on('disconnect', namespace='/test')
def test_disconnect():
    print('Client disconnected')
