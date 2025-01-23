from flask import Flask, render_template, Response
from werkzeug.middleware.proxy_fix import ProxyFix
import json
import os

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app)

from tile_serving_api import tile_serving_api

app.register_blueprint(tile_serving_api)

@app.errorhandler(404)
def not_found_error_handler(e):
    return Response(json.dumps({
            "error": "notFound",
            "msg": "Endpoint not found"
        }), status=400, mimetype='application/json')

@app.route("/")
def index_route():
    return Response(json.dumps({
            "msg": "Welcome to GrippyMap"
        }), status=200, mimetype='application/json')

if __name__ == "__main__":
    app.run()
