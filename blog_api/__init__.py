from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from os import path






db = SQLAlchemy()
DB_NAME = "project.sqlite3"

#factory set up
def create_app():
    app=Flask(__name__)
    app.config['SECRET_KEY']='this_is_a_well_kept_secret_lol'
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
    db.init_app(app)
    CORS(app) #to set cors headers in all responses by default

    from .views import views
    app.register_blueprint(views, url_prefix="/")
    from .models import Author, Post, Comment, Tag
    create_db(app)

    return app

def create_db(app):
    if not path.exists("blog_api/"+DB_NAME):
        db.create_all(app=app)
    else:
        print("DATABASE EXISTS")

