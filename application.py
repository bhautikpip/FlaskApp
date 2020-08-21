import boto3
from flask import Flask
from aws_xray_sdk.core import xray_recorder, patch_all
from aws_xray_sdk.ext.flask.middleware import XRayMiddleware
from aws_xray_sdk.ext.flask_sqlalchemy.query import XRayFlaskSqlAlchemy
import requests

application = app = Flask(__name__)
application.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
application.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///db.sqlite3"

xray_recorder.configure(service='My Flask Web Application')
XRayMiddleware(app, xray_recorder)
patch_all()

db = XRayFlaskSqlAlchemy(app=application)


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True)


@app.route('/outgoing-http-call')
def callHTTP():
    requests.get("https://aws.amazon.com")
    return "Ok! tracing outgoing http call"


@app.route('/aws-sdk-call')
def callAWSSDK():
    client = boto3.client('s3')
    client.list_buckets()
    return 'Ok! tracing aws sdk call'


@app.route('/flask-sql-alchemy-call')
def callSQL():
    name = 'sql-alchemy-model'
    user = User(name=name)
    db.create_all()
    db.session.add(user)

    return 'Ok! tracing sql call'


# use the exact value (integration testing module will be using this values)
@app.route('/annotation-metadata')
def callCustomSegment():
    subsegment = xray_recorder.begin_subsegment('subsegment_name')

    subsegment.put_annotation('one', '1')
    subsegment.put_metadata('integration-test', 'true')

    xray_recorder.end_subsegment()

    return 'Ok! annotation-metadata testing'


if __name__ == "__main__":
    app.run(debug=True)