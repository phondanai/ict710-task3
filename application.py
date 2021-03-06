from app import app, db
from app.models import Humidity, Temperature, Sensors


@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'Temperature': Temperature, 'Humidity': Humidity, 'Sensors': Sensors}
