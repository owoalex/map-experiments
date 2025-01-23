from flask import Blueprint, request, Response, make_response, send_file, redirect
import json
from renderer import AreaRenderer
import traceback


tile_serving_api = Blueprint("tile_serving_api", __name__)

@tile_serving_api.route("/slippytiles/<zoom>/<x>/<y>", methods=['GET'])
def serve_tile(zoom, x, y):
    try:
        ys = y.split(".")
        ext = "png"
        if len(ys) > 1:
            y = ys[0]
            ext = ys[1]
        if not (ext == "png" or ext == "svg"):
            return Response(json.dumps({
                    "error": "badRequest",
                    "msg": "Can only generate .svg and .png tiles"
                }), status=400, mimetype='application/json')
            
        renderer = AreaRenderer()
        renderer.set_slippy_area(x, y, zoom)
        tile_id = renderer.render_area()
        if tile_id is None:
            return Response(json.dumps({
                    "error": "badRequest",
                    "msg": "Could not generate tile " + x + "," + y + " (" + zoom + "x)"
                }), status=400, mimetype='application/json')
        else:
            return send_file("cache/temp/" + tile_id + "." + ext)
    except Exception as e:
        return Response(json.dumps({
                "error": "unknownError",
                "msg": str(e),
                "trace": traceback.format_exc()
            }), status=500, mimetype='application/json')
