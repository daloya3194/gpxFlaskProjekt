import os
import pathlib

import folium
import pandas as pd
from flask import Flask, render_template, request, redirect, flash, url_for
from flask_sqlalchemy import SQLAlchemy, Model
import gpxpy
import gpxpy.gpx
from sqlalchemy import text
from werkzeug.utils import secure_filename
from folium.plugins import BeautifyIcon
from pprint import pprint


project_folder_path = str(pathlib.Path().resolve())

app = Flask(__name__)
app.config['SECRET_KEY'] = 'somme password that only you know'

# MySQL
# app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://benutzername:passwort@hostname/datenbank_name'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/flask_db'

# SQLite
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(project_folder_path, 'database.db')

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

app.config['UPLOAD_FOLDER'] = project_folder_path + os.path.sep + 'uploads'


# def process_gpx_to_df(file_name):
#     gpx = gpxpy.parse(open(file_name, 'r'))
#
#     # (1)make DataFrame
#     track = gpx.tracks[0]
#     segment = track.segments[0]
#
#     # Load the data into a Pandas dataframe (by way of a list)
#     data = []
#     segment_length = segment.length_3d()
#     for point_idx, point in enumerate(segment.points):
#         pprint(segment.get_speed(point_idx))
#         data.append([point.longitude, point.latitude, point.elevation,
#                      point.time, segment.get_speed(point_idx)])
#
#     # pprint(data)
#     columns = ["Longitude", "Latitude", "Altitude", "Time", "Speed"]
#     gpx_df = pd.DataFrame(data, columns=columns)
#
#     # 2(make points tuple for line)
#     points = []
#     for track in gpx.tracks:
#         for segment in track.segments:
#             for point in segment.points:
#                 points.append(tuple([point.latitude, point.longitude]))
#
#     return gpx_df, points


def process_points_to_df(database_points):

    # Load the data into a Pandas dataframe (by way of a list)
    data = []
    points = []

    for point in database_points:
        data.append([point.lon, point.lat, point.ele,
                     point.zeitstempel])
        points.append(tuple([point.lat, point.lon]))

    columns = ["Longitude", "Latitude", "Altitude", "Time"]
    gpx_df = pd.DataFrame(data, columns=columns)

    return gpx_df, points


@app.route('/')
def index():
    # fahrten = Fahrt.query.all()

    fahrten = db.session.execute('SELECT ft.ftid AS ftid, ft.dateiname AS dateiname, f.name AS fname FROM fahrt ft JOIN fahrer f ON ft.fid = f.fid')

    # df = process_gpx_to_df(r"C:\Users\DALOYA\PycharmProjects\gpxFlaskProjekt\uploads\AA_WIT-AA000_001.gpx")
    # mymap = folium.Map(location=[df[0].Latitude.mean(), df[0].Longitude.mean()], tiles=None)
    # mymap.fit_bounds(df[1])
    # folium.TileLayer('openstreetmap', name='OpenStreet Map').add_to(mymap)
    # folium.PolyLine(df[1], color='red', weight=4.5, opacity=.5).add_to(mymap)

    return render_template('index.html', fahrten=fahrten)


@app.route('/show-map/<int:id>')
def show_map(id):
    fahrt = Fahrt.query.get(id)

    if fahrt is None:
        flash('Die Fahrt wurde nicht gefunden', 'error')
        return redirect('/')

    fahrtpunkte = Fahrtpunkt.query.filter_by(ftid=id).all()

    if not fahrtpunkte:
        flash('Die Fahrt hat keine Fahrtpunkte', 'error')
        return redirect('/')

    df = process_points_to_df(fahrtpunkte)
    mymap = folium.Map(location=[df[0].Latitude.mean(), df[0].Longitude.mean()], tiles=None)
    mymap.fit_bounds(df[1])
    folium.TileLayer('openstreetmap', name='OpenStreet Map').add_to(mymap)
    folium.PolyLine(df[1], color='red', weight=4.5, opacity=.5).add_to(mymap)

    # circle marker
    icon_circle = BeautifyIcon(
        icon_shape='circle-dot',
        border_color='green',
        border_width=10,
    )

    folium.Marker(df[1][0], tooltip='Departure', icon=icon_circle).add_to(mymap)

    folium.Marker(df[1][-1:][0], tooltip='Destination').add_to(mymap)

    return render_template('map-view.html', map=mymap._repr_html_(), fahrt=fahrt)


@app.route('/tracks-import', methods=['GET', 'POST'])
def tracks_import():
    if request.method == 'POST':

        input_files = request.files.getlist('files[]')

        if input_files[0].filename == '' or len(input_files) > 10:
            print('MIN 1 UND MAX 10 DATEIEN')
            flash('Min 1 und Max 10 Dateien', 'error')
            return redirect('/')

        for input_file in input_files:
            if input_file.filename[-4:] != '.gpx':
                print('NUR GPX DATEIEN SIND ERLAUBT')
                flash('Nur GPX Dateien sind erlaubt', 'error')
                return redirect('/')

        for input_file in input_files:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(input_file.filename))

            infos = input_file.filename.split('_')

            fahrer_vorname = infos[0]
            fahrer_name = infos[0]
            fahrzeug_polkz = infos[1]
            dateiname_ohne_extension = input_file.filename[0:-4]

            fahrer = Fahrer.query.filter_by(vorname=fahrer_vorname, name=fahrer_name).first()
            if fahrer is None:
                fahrer_to_save = Fahrer(vorname=fahrer_vorname, name=fahrer_name)
                db.session.add(fahrer_to_save)
                db.session.flush()
                db.session.commit()
                fahrer_id = fahrer_to_save.fid
            else:
                fahrer_id = fahrer.fid

            fahrzeug = Fahrzeug.query.filter_by(polkz=fahrzeug_polkz).first()
            if fahrzeug is None:
                fahrzeug_to_save = Fahrzeug(polkz=fahrzeug_polkz)
                db.session.add(fahrzeug_to_save)
                db.session.flush()
                db.session.commit()
                fahrzeug_id = fahrzeug_to_save.fzid
            else:
                fahrzeug_id = fahrzeug.fzid

            fahrt = Fahrt.query.filter_by(dateiname=dateiname_ohne_extension).first()
            if fahrt is None:
                fahrt_to_save = Fahrt(dateiname=dateiname_ohne_extension, fid=fahrer_id, fzid=fahrzeug_id)
                db.session.add(fahrt_to_save)
                db.session.flush()
                db.session.commit()
                fahrt_id = fahrt_to_save.ftid

                input_file.save(file_path)
                gpx_file = open(file_path, 'r')

                gpx = gpxpy.parse(gpx_file)

                for track in gpx.tracks:
                    for segment in track.segments:
                        for point in segment.points:
                            fahrtpunkt = Fahrtpunkt(lat=point.latitude, lon=point.longitude, ele=point.elevation,
                                                    zeitstempel=point.time, ftid=fahrt_id)
                            db.session.add(fahrtpunkt)
                            db.session.commit()

                for waypoint in gpx.waypoints:
                    fahrtpunkt = Fahrtpunkt(lat=waypoint.latitude, lon=waypoint.longitude, ele=waypoint.elevation,
                                            zeitstempel=waypoint.time, ftid=fahrt_id)
                    db.session.add(fahrtpunkt)
                    db.session.commit()

                for route in gpx.routes:
                    for point in route.points:
                        fahrtpunkt = Fahrtpunkt(lat=point.latitude, lon=point.longitude, ele=point.elevation,
                                                zeitstempel=point.time, ftid=fahrt_id)
                        db.session.add(fahrtpunkt)
                        db.session.commit()

                flash(
                    'Die Datei <' + fahrt_to_save.dateiname + '.gpx> wurde erfolgreich importiert | Fahrer: ' + fahrer_name + ' | Fahrzeug: ' + fahrzeug_polkz,
                    'success')
            else:
                print('ERROR')
                flash('Die Datei <' + fahrt.dateiname + '.gpx> wurde schon importiert', 'error')

        return redirect(url_for("tracks_import"))
    else:
        return render_template('tracks-import.html')


if __name__ == '__main__':
    app.run()


class Fahrer(db.Model):
    fid = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    vorname = db.Column(db.String(100))

    def __init__(self, name, vorname):
        self.name = name
        self.vorname = vorname


class Fahrzeug(db.Model):
    fzid = db.Column(db.Integer, primary_key=True)
    polkz = db.Column(db.String(10))

    def __init__(self, polkz):
        self.polkz = polkz


class Fahrt(db.Model):
    ftid = db.Column(db.Integer, primary_key=True)
    dateiname = db.Column(db.String(255))
    fid = db.Column(db.Integer, db.ForeignKey('fahrer.fid'))
    fzid = db.Column(db.Integer, db.ForeignKey('fahrzeug.fzid'))

    def __init__(self, dateiname, fid, fzid):
        self.dateiname = dateiname
        self.fid = fid
        self.fzid = fzid


class Fahrtpunkt(db.Model):
    pid = db.Column(db.Integer, primary_key=True)
    lat = db.Column(db.Float)
    lon = db.Column(db.Float)
    ele = db.Column(db.Float)
    zeitstempel = db.Column(db.DateTime)
    ftid = db.Column(db.Integer, db.ForeignKey('fahrt.ftid'))

    def __init__(self, lat, lon, ele, zeitstempel, ftid):
        self.lat = lat
        self.lon = lon
        self.ele = ele
        self.zeitstempel = zeitstempel
        self.ftid = ftid


db.create_all()
