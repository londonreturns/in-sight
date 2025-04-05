from flask import Flask
from routes import routes
from dotenv import load_dotenv
from os import getenv

load_dotenv()

app = Flask(__name__)

app.config['SECRET_KEY'] = getenv('MY_SECRET_KEY')
app.config['MONGO_URI'] = getenv('DATABASE_CONNECTION_STRING')
app.register_blueprint(routes, url_prefix='')

if __name__ == '__main__':
    app.run(debug=True)