import data_services_library as dsl

from flask import Blueprint, render_template, abort

api = Blueprint('v1', __name__, template_folder='templates')


@api.route("/")
def index():
    html = """
                <!DOCTYPE html>
                  <html>
                    <body>
                      <h1>Data Service Library Web API</h1>
                        <ul> 
                          <li> <b>http://127.0.0.1:5000/services</b> : List of available services </li>
                          <li> <b>http://127.0.0.1:5000/locations/&ltservice_uid&gt</b> : Get locations full bbox extent</li>
                          <li> <b>http://127.0.0.1:5000/locations/&ltservice_uid&gt/bbox/&ltxmin,ymin,xmax,ymax&gt</b> : Get locations, specifying bbox extent</li>
                    </body>
                  </html>
            """
    return html


@api.route("/services")
def services():
    js = dsl.api.get_services(as_json=True)
    return Response(js, status=200, mimetype='application/json')


@api.route("/locations/<dataset>")
@api.route("/locations/<dataset>/bbox/<bbox>")
def locations(dataset, bbox=None):
    if bbox:
        bbox = [float(x) for x in bbox.split(',')]
    js = dsl.api.get_locations(dataset, bbox=bbox)
    return Response(js, status=200, mimetype='application/json')
