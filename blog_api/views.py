

import datetime
from flask import Blueprint, request, make_response, jsonify, current_app
from .models import Author, Comment, Post, Tag
from functools import wraps
import jwt
from werkzeug.security import generate_password_hash, check_password_hash

from . import db

views = Blueprint("views", __name__)

BASE = 'http://127.0.0.1:5000'

#a decorator fn to verify user login wherever necessary
def check_token(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('token')
        if token:
            try:
                data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
                
            except:
                return jsonify({'message': 'Invalid/Missing token'}), 401
        else:
            return jsonify({'message': 'Invalid/Missing token'}), 401
    return decorated







#login checks if user is in the db and responds with a jwt token if yes, or sends a 40x response.
@views.route('/login', methods = ['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.json
        username = data['username']
        password = data['password']

        user = Author.query.filter_by(username=username).first()
        if user:
            if check_password_hash(user.password, password):
                token = jwt.encode({'user': username, 'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)}, current_app.config['SECRET_KEY'])
                return jsonify({'token': token}), 200

            else:
                return make_response({'message':'Incorrect Password.... :-('}, 401)
                
                
        else:
            return make_response({'message':'Author name does not exist.... :-('}, 404)












#checks if user already exists, 40x if yes, else creates user in db
@views.route('/register', methods = ['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.json
        username = data['username']
        email = data['email']
        password = data['password']

        if Author.query.filter_by(username=username).first() or Author.query.filter_by(email=email).first():
            return make_response({'message': 'Account with same email or username already exists'}, 401)
        new_user = Author(username=username, email=email, password= generate_password_hash(password, method='sha256'))
        try:
            db.session.add(new_user)
            db.session.commit()
            return make_response({'message': 'Account created Succesfully'}, 200)
        except:
            return make_response({'message': 'Account Not Created'}, 401)










@check_token
@views.route('/create-post', methods=['POST'])
def create_post():
    token = request.headers.get('token')
    data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
    username = data['user'] #username encoded in the token
    body = request.json
    
    #if post with the same title exists from the same author
    if Post.query.filter_by(author_name = username, post_title = body['title']).first():
        return make_response({'message':'You already have a post with the same title...'}, 409)
    
    else:
        #creates a new post object
        new_post = Post(post_title = body['title'], post_body = body['body'], author_name = username)
        new_tags=[]
        #gets tags from the json, -- should be a comma seperated string
        body_tags= body['tags'].split(',')
        for tag in body_tags:
            for old_tag in Tag.query.filter_by(tag_text=tag).all():
                if old_tag.tag_text == tag: #if tag alraedy exists in db, adds it to post's tags and removes from the body_tags list
                    new_post.tags.append(old_tag)
                    body_tags.remove(tag)
        for tag in body_tags: #with only new tags in the list now -- we removed the existing ones in the last step, create new tag objects and then append them to the post object
            n=Tag(tag_text=tag)
            new_tags.append(n)
            print(new_tags)
        db.session.add_all(new_tags)
        db.session.commit()
                    
        try:# committing the new post object to the db
            # print('tags committed')
            for text in body['tags'].split(','):
                tag=Tag.query.filter_by(tag_text=text).first()
                if tag:
                    new_post.tags.append(tag)
                db.session.add(new_post)
                # print('tagged post added')
            db.session.commit()
            # print('tagged post commited')
        except:
            return make_response({'message':'Post creation Unsuccessful... :-('}, 403)
        return make_response({'message':'Post created succesfully.... ;-)'},201)









#returns post data for the post id encoded in the url, login not required
@views.route('/read-post/<int:post_id>', methods=['GET'])
def get_post(post_id):
    post = Post.query.filter_by(id=post_id).first()
    if post:
        print(post)
        body = {
            'post_id':post.id,
            'post_title':post.post_title, 
            'post_body':post.post_body, 
            'author':post.author_name, 
            'tags':[tag.tag_text for tag in post.tags], 
            'comments':[
                {
                    'comment':comment.comment_text,
                    'username':comment.username,
                    'id':comment.id
                    } for comment in post.comments if post.comments
                ]
            }
        return jsonify(body), 200
    else:
        return make_response({'message':'Post not found.... :-('}, 404)












@check_token
@views.route('/edit-post/<int:post_id>', methods=['POST'])
def edit_post(post_id):
    token = request.headers.get('token')
    data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
    username = data['user']
    body = request.json
    post = Post.query.filter_by(id=post_id).first()
    new_tags=[]
    if post and post.author_name == username:#checks if a post with the id in the url exists and the current useris the author.
        post.post_body = body['body']
        post.post_title = body['title']
        for tag in post.tags: #if the incoming data has some tags removed, it cross checks in a loop and removes those tag objects from the post's tags.
            if tag.tag_text not in body['tags'].split(','):
                post.tags.remove(tag)
        for tag in body['tags'].split(','): #if new tags come in, creates new tags and appends too the post.
            if tag not in [text.tag_text for text in post.tags]:
                new_tag = Tag(tag_text=tag)
                new_tags.append(new_tag)
        try:#commit all changes to the db
            db.session.add_all(new_tags)
            db.session.commit()
            for tag in new_tags:
                a_tag = Tag.query.filter_by(tag_text = tag.tag_text).first()
                post.tags.append(a_tag)
            db.session.commit()
        except:
            return make_response({'message': 'Edit Failed.... :-('}, 402)
        return make_response({'message':'Post editted successfully.... ;-)'}, 202)
    else:
        return make_response({'message': 'YOU ARE NOT AUTHORIZED TO PERFORM THIS ACTION...'}, 401)
        







#deletes post if post exists and the current user is the author.
@check_token
@views.route('/delete-post/<int:post_id>', methods=['POST'])
def delete_post(post_id):
    token = request.headers.get('token')
    data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
    username = data['user']
    post = Post.query.filter_by(id=post_id).first()
    if post and post.author_name == username:
        try:
            db.session.delete(post)
            db.session.commit()
        except:
            return make_response({'message':'Post Delete failed... :-('}, 400)
        return make_response({'message':'Post DELETED successfully.... ;-)'}, 201)
    else:
        return make_response({'message': 'YOU ARE NOT AUTHORIZED TO PERFORM THIS ACTION...'}, 401)










@check_token
@views.route('/add-comment/<int:post_id>', methods=['POST'])
def add_comment(post_id):
    token = request.headers.get('token')
    data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
    username = data['user']
    body = request.json
    post = Post.query.filter_by(id=post_id).first() #post corresponding to the id in url
    if post:
        new_comment=Comment(comment_text=body['comment'], username=username) #creates new comment object
        try:
            db.session.add(new_comment)
            db.session.commit()
            comment = Comment.query.filter_by(username=username, comment_text=body['comment']).first()
            post.comments.append(comment) #adds comment to post's comments
            db.session.commit()
        except:
            return make_response({'message':'Comment failed to post.... :-('}, 402)
        return make_response({'message':'Comment added successfully.... ;-)'},201)
    else:
        return make_response({'message':'Post does not exist'},404)










#deletes comment if it exists and the current user is the author of the comment
@check_token
@views.route('/delete-comment/<int:comment_id>', methods=['POST'])
def delete_comment(comment_id):
    token = request.headers.get('token')
    data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
    username = data['user']
    comment = Comment.query.filter_by(id=comment_id).first()
    if comment and comment.username == username:
        try:
            db.session.delete(comment)
            db.session.commit()
        except:
            return make_response({'message': 'Couldn\'t delete comment.... :-('}, 401)
        return make_response({'message':'Comment deleted succesfully..... ;-)'}, 201)
    else:
        return make_response({'message': 'YOU ARE NOT AUTHORIZED TO PERFORM THIS ACTION... :-('}, 401)








#edits comment corresponding to the id in url id it exists and the current user is the author

@check_token
@views.route('/edit-comment/<int:comment_id>', methods=['POST'])
def edit_comment(comment_id):
    token = request.headers.get('token')
    data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
    username = data['user']
    body = request.json
    comment = Comment.query.filter_by(id = comment_id).first()
    if comment and comment.username == username:
        comment.comment_text = body['comment']
        try:
            db.session.commit()
        except:
            return make_response({'message': 'Error editing comment.... :-('}, 402)
        return make_response({'message':'Comment editted successfully.... ;-)'},202)
    else:
        return make_response({'message': 'YOU ARE NOT AUTHORIZED TO PERFORM THIS ACTION... :-('}, 401)
    


    



    

    





