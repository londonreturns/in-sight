from flask import Flask
from routes import routes
from dotenv import load_dotenv
from os import getenv
from datetime import timedelta
from flask_cors import CORS

load_dotenv()

app = Flask(__name__)
CORS(app)

app.config['SECRET_KEY'] = getenv('MY_SECRET_KEY')
app.config['MONGO_URI'] = getenv('DATABASE_CONNECTION_STRING')
app.permanent_session_lifetime = timedelta(minutes=4320)
app.register_blueprint(routes, url_prefix='')

if __name__ == '__main__':
    app.run(debug=True)
