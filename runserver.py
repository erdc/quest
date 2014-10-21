from data_services_library.rest_api import v1

from flask import Flask

app = Flask(__name__)
app.register_blueprint(v1.api, url_prefix='/v1')


if __name__ == "__main__":
    app.run(debug=True)