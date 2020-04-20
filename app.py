from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Resource, Api
import os
from flask_jwt import JWT, jwt_required
from flask_migrate import Migrate

app = Flask(__name__)
app.config["SECRET_KEY"] = "mysecretkey"
basedir = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(basedir,"data.sqlite")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)
Migrate(app,db)

class User(db.Model):

    id = db.Column(db.Integer,primary_key=True)
    username = db.Column(db.String(20),unique=True)
    password = db.Column(db.String(20))

    def __init__(self,username,password):
        self.username = username
        self.password = password

class Post(db.Model):

    id = db.Column(db.Integer,primary_key=True)
    title = db.Column(db.String(30))
    content = db.Column(db.String(400))

    def __init__(self,title,content):
        self.title = title
        self.content = content

    def json(self):
        return {"id":self.id, "title":self.title, "content":self.content}

db.create_all()

def authenticate(username,password):

    user = User.query.filter_by(username=username).first()
    if user and password == user.password:
        return user

def identity(payload):

    user_id = payload["identity"]
    return User.query.filter_by(id=user_id).first()

api = Api(app)
jwt = JWT(app,authenticate,identity)

class IndivPosts(Resource):

    def get(self,id):

         post = Post.query.filter_by(id=id).first()
         return post.json()

    def delete(self,id):

        post = Post.query.filter_by(id=id).first()
        db.session.delete(post)
        db.session.commit()
        return {"note":"delete successful"}

    def put(self,id):

        post = Post.query.filter_by(id=id).first()
        json_data = request.get_json(force=True)
        title = json_data["title"]
        content = json_data["content"]
        post.title = title
        post.content = content
        db.session.commit()
        return {"note": "updated"}

class CreatePosts(Resource):

    def post(self):

        json_data = request.get_json(force=True)
        title = json_data["title"]
        content = json_data["content"]
        post = Post(title=title, content=content)
        db.session.add(post)
        db.session.commit()
        return post.json()

class AllPosts(Resource):

    @jwt_required()
    def get(self):

        posts = Post.query.all()
        return [post.json() for post in posts]

class NewUser(Resource):

    def post(self):

        json_data = request.get_json(force=True)
        new_username = json_data["username"]
        new_password = json_data["password"]
        usernames = []
        for u in User.query.all():
            usernames.append(u.username)
        if new_username in usernames:
            return {"note":"user already exist"}
        else:
            newuser = User(username=new_username, password=new_password)
            db.session.add(newuser)
            db.session.commit()
            return {"note":"new user created"}

api.add_resource(IndivPosts,"/post/<int:id>")
api.add_resource(CreatePosts,"/create")
api.add_resource(AllPosts,"/posts")
api.add_resource(NewUser,"/newuser")

if __name__ == "__main__":
    app.run(debug=True)
