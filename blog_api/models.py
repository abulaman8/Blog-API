
from . import db
from sqlalchemy.sql import func

# MANY TO MANY relationship table bw post and tags
post_tag_rel = db.Table('post_tag_rel', 
    db.Column('post', db.Integer, db.ForeignKey('post.id')),
    db.Column('tag', db.Integer, db.ForeignKey('tag.id'))
    )


#ONE TO MANY relationship table bw post and comments
post_comment_rel = db.Table('post_comment_rel',
    db.Column('post', db.Integer, db.ForeignKey('post.id')),
    db.Column('comment', db.Integer, db.ForeignKey('comment.id'))
    )


class Author(db.Model):
    __tablename__ = 'author'
    id = db.Column(db.Integer, primary_key = True)
    email = db.Column(db.String(60), unique=True, nullable = False)
    username = db.Column(db.String(30), unique=True, nullable = False)
    password = db.Column(db.String(300), nullable=False)
    post_rel = db.relationship('Post', cascade='all, delete-orphan', backref='author') #relationship with post table for the foreign key - author_name

    def __repr__(self) -> str:
        return f'<Author: {self.username}>'

class Post(db.Model):
    __tablename__ = 'post'
    id = db.Column(db.Integer, primary_key = True)
    post_title = db.Column(db.String(150))
    post_body = db.Column(db.String(80000))
    author_name = db.Column(db.String, db.ForeignKey('author.username'), nullable=False) #Foreign key from author table
    date_created = db.Column(db.DateTime(timezone=True), default=func.now())
    comments = db.relationship('Comment', secondary=post_comment_rel, single_parent=True ,cascade='all, delete-orphan', backref='posts')
    # comments relationship and set to delete all related comments
    tags = db.relationship('Tag', secondary=post_tag_rel, backref='posts')
    #tags relationship 

    def __repr__(self) -> str:
        return f'<post: {self.post_title}, {self.post_body}>'

class Comment(db.Model):
    __tablename__ = 'comment'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30))
    comment_text = db.Column(db.String(280))

class Tag(db.Model):
    __tablename__ = 'tag'
    id = db.Column(db.Integer, primary_key=True)
    tag_text = db.Column(db.String(100))

    def __repr__(self) -> str:
        return f'<tag: {self.tag_text}>'
    

    



    
