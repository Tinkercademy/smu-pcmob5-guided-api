from flask import Flask,request, render_template, url_for, redirect
import os
import sqlite3
from flask_restful import Resource, Api
from flask_jwt import JWT,jwt_required

app = Flask(__name__)
app.config["SECRET_KEY"] = "mysecretkey"


############################################################


def get_db():
    db = sqlite3.connect("db.sqlite3")
    db.row_factory = sqlite3.Row
    return db

def create_db():
    db = get_db()
    db.execute("CREATE TABLE posts " + \
                "(id INTEGER PRIMARY KEY AUTOINCREMENT, " + \
                "title TEXT NOT NULL, " + \
                "content TEXT)")
    db.execute("CREATE TABLE users" + \
                "(id INTEGER PRIMARY KEY AUTOINCREMENT, " + \
                "username TEXT NOT NULL, " + \
                "password TEXT NOT NULL)")
    db.commit()
    db.close()


if not os.path.isfile('db.sqlite3'):
    create_db()

def json_posts(post):
    return {"id": post["id"], "title": post["title"], "content": post["content"]}

class User:

    def __init__(self,id,username,password):
        self.id = id
        self.username = username
        self.password = password
###########################################################


def authenticate(username,password):

    db = get_db()
    cursor = db.execute("SELECT * FROM users WHERE username = ?",(username,))
    user = cursor.fetchone()
    db.close()
    if user and password == user["Password"]:
        user_object = User(user["id"],user["username"],user["password"])
        return user_object

def identity(payload):

    user_id = payload["identity"]
    db = get_db()
    cursor = db.execute("SELECT * FROM users WHERE id = ?",(user_id,))
    user = cursor.fetchone()
    db.close()
    user_object = User(user["id"],user["username"],user["password"])
    return user_object


api = Api(app)
jwt = JWT(app,authenticate,identity)

###################################################


class IndivPosts(Resource):

    @jwt_required()
    def get(self,id):

        db = get_db()
        cursor = db.execute("SELECT * FROM posts WHERE id = ?",(id,))
        post = cursor.fetchone()
        db.close()
        return json_posts(post)


    @jwt_required()
    def delete(self,id):

        db = get_db()
        cursor = db.execute("DELETE FROM posts WHERE id = ?",(id,))
        db.commit()
        db.close()
        return {"note":"delete"}


    @jwt_required()
    def put(self,id):

        json_data = request.get_json(force=True)
        db = get_db()
        cursor = db.execute("UPDATE posts SET title=? WHERE id=?",(json_data["title"],id))
        cursor = db.execute("UPDATE posts SET content=? WHERE id=?",(json_data["content"],id))
        db.commit()
        db.close()
        return {"note": "updated"}


class CreatePosts(Resource):

    @jwt_required()
    def post(self):


        json_data = request.get_json(force=True)
        title = json_data["title"]
        content = json_data["content"]
        db = get_db()
        cursor = db.execute("INSERT INTO posts(title,content) VALUES(?,?)",(title,content))
        db.commit()
        db.close()
        return {"note": "created"}

class AllPosts(Resource):

    @jwt_required()
    def get(self):


        db = get_db()
        cursor = db.execute("SELECT * FROM posts")
        posts = cursor.fetchall()
        db.close()
        return [json_posts(post) for post in posts]



class NewUser(Resource):

    def post(self):

        json_data = request.get_json(force=True)
        new_username = json_data["username"]
        new_password = json_data["password"]

        db = get_db()
        cursor = db.execute("SELECT username FROM users")
        usernames = cursor.fetchall()
        if new_username in usernames:
            return {"note": "user already exist"}
        else:
            cursor = db.execute("INSERT INTO users(username,password) VALUES (?,?)",(new_username,new_password))
            db.commit()
            db.close()
            return {"note":"new user created"}

#################################################################

@app.route("/admin")
def admin():
    db = get_db()
    cursor = db.execute("SELECT COUNT(username) FROM users")
    user_count = cursor.fetchone()["COUNT(username)"]
    cursor = db.execute("SELECT COUNT(title) FROM posts")
    post_count = cursor.fetchone()["COUNT(title)"]
    cursor = db.execute("SELECT * FROM posts")
    posts = cursor.fetchall()
    cursor = db.execute("SELECT * FROM users")
    users = cursor.fetchall()
    db.close()
    return render_template("admin.html", user_count=user_count, post_count=post_count)

@app.route("/users_page", methods=["GET","POST"])
def users_page():
    db = get_db()
    cursor = db.execute("SELECT * FROM users")
    users = cursor.fetchall()
    db.close()
    return render_template("users.html", users=users)

@app.route("/posts_page")
def posts_page():
    db = get_db()
    cursor = db.execute("SELECT * FROM posts")
    posts = cursor.fetchall()
    db.close()
    return render_template("posts.html", posts=posts)

@app.route("/delete_user", methods=["GET","POST"])
def delete_user():

    id = request.args.get("id")
    db = get_db()
    cursor = db.execute("DELETE FROM users WHERE id = ?",(id,))
    db.commit()
    db.close()
    return redirect(url_for("users_page"))

@app.route("/delete_post", methods=["GET","POST"])
def delete_post():

    id = request.args.get("id")
    db = get_db()
    cursor = db.execute("DELETE FROM posts WHERE id = ?",(id,))
    db.commit()
    db.close()
    return redirect(url_for("posts_page"))



api.add_resource(IndivPosts,"/post/<int:id>")
api.add_resource(CreatePosts,"/create")
api.add_resource(AllPosts,"/posts")
api.add_resource(NewUser,"/newuser")

if __name__ == "__main__":
    app.run(debug=True)
