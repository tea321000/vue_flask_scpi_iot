from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_script import Manager
from flask_cors import *

app = Flask(__name__, static_folder="./dist/static", template_folder="./dist")
# app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root@127.0.0.1:3305/automation'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:1314mysql5354@127.0.0.1:3306/automation'
# app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root@127.0.0.1:3305/automation'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
# app.config['SQLALCHEMY_ECHO'] = True
app.config['USER_SECRET_KEY'] = 'automationProjectUser'
app.config['DEVICE_SECRET_KEY'] = 'automationProjectDevice'
from automation import automation
from automation.sql import db
db.init_app(app)

app.register_blueprint(automation, url_prefix='/automation')
CORS(app, supports_credentials=True)
manager = Manager(app)


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    return render_template("index.html")


if __name__ == "__main__":
    # app.run(port=80, debug=True)
    app.run(debug=True)
    # app.run(host='0.0.0.0', port=8080, debug=True)
    # manager.run()
