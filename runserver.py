from flask import Flask, Response
import data_services_library as dsl
app = Flask(__name__)

@app.route("/")
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


@app.route("/services")
def services():
    js = dsl.api.get_services(as_json=True)
    return Response(js, status=200, mimetype='application/json')


@app.route("/locations/<dataset>")
@app.route("/locations/<dataset>/bbox/<bbox>")
def locations(dataset, bbox=None):
    if bbox:
        bbox = [float(x) for x in bbox.split(',')]
    js = dsl.api.get_locations(dataset, bbox=bbox)
    return Response(js, status=200, mimetype='application/json')


if __name__ == "__main__":
    app.run(debug=True)