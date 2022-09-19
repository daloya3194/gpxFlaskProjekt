import os

from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy, Model
import gpxpy
import gpxpy.gpx
from werkzeug.utils import secure_filename

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

app.config['UPLOAD_FOLDER'] = 'C:/Users/DALOYA/PycharmProjects/gpxFlaskProjekt/uploads'


@app.route('/', methods=['GET', 'POST'])
def index():  # put application's code here
    if request.method == 'POST':

        input_files = request.files.getlist('files[]')

        if len(input_files) > 10:
            print('MAX 10 DATEIEN')
            return redirect('/')

        for input_file in input_files:
            if input_file.filename[-4:] != '.gpx':
                print('NUR GPX DATEIEN SIND ERLAUBT')
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
                            print('UPLOADING...')
                            fahrtpunkt = Fahrtpunkt(lat=point.latitude, lon=point.longitude, ele=point.elevation,
                                                    zeitstempel=point.time, ftid=fahrt_id)
                            db.session.add(fahrtpunkt)
                            db.session.commit()

                print('SUCCESS')
            else:
                print('ERROR')

        return redirect('/')
    else:
        return render_template('index.html')


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
