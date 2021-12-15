from datetime import datetime
from flask import Blueprint, current_app, render_template, request, flash, redirect, url_for, jsonify,abort
from flask_login import login_required, current_user
from sqlalchemy.orm.session import Session
from .models import Post, User, Comment, Like
from . import db
from sqlalchemy.orm import sessionmaker


import os

import base64
from .forms import EditProfileForm
from werkzeug.utils import secure_filename
views = Blueprint("views", __name__)


@views.route("/")
@views.route("/home")
def home():
    postList = User.query\
    .join(Post, User.id==Post.author)\
    .add_columns(User.username, Post.title, Post.content, Post.timestamp, Post.body, Post.image,Post.id)\
    .order_by(Post.timestamp.desc())
    return render_template("home.html", user=current_user, posts= postList)


@views.route("/create-post", methods=['GET', 'POST'])
@login_required
def create_post():
    if request.method == "POST":
        body = request.form.get('body')
        title = request.form.get('title')
        content = request.form.get('content')
        category = request.form.get('category')
        image = request.files['inputImage']
        filename = secure_filename(image.filename)
        filepath = (os.path.join(current_app.config['UPLOAD_FOLDER'],filename))
        img_name = 'static/images/'+filename
        image.save(filepath)
        if not body:
            flash('Post cannot be empty', category='error')
        else:
            post = Post(title = title, content = content, category = category, author = current_user.id, body = body,image = img_name, timestamp = datetime.now())
            db.session.add(post)
            db.session.commit()
            flash('Post created!', category='success')
            return redirect(url_for('views.home'))

    return render_template('create_post.html', user=current_user)



@views.route("/delete-post/<id>")
@login_required
def delete_post(id):
    post = Post.query.filter_by(id=id).first()

    if not post:
        flash("Post does not exist.", category='error')
    elif current_user.id != post.id:
        flash('You do not have permission to delete this post.', category='error')
    else:
        db.session.delete(post)
        db.session.commit()
        flash('Post deleted.', category='success')

    return redirect(url_for('views.home'))

@views.route('/user/<username>')
def user(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        abort(404)
    # # display blogs for the user
    # posts = user.posts.order_by(Post.timestamp.desc()).all()
    return render_template('user.html', user=user)
 

@views.route("/posts/<username>")
@login_required
def posts_by_user(username):
    user = User.query.filter_by(username=username).first()

    if not user:
        flash('No user with that username exists.', category='error')
        return redirect(url_for('views.home'))

    posts = user.posts
    return render_template("posts.html", user=current_user, posts=posts, username=username)

@views.route("/posts/<int:post_id>")
@login_required
def posts_by_id(post_id):
    post = User.query\
    .join(Post, User.id==Post.author)\
    .add_columns(User.username, Post.title, Post.content, Post.timestamp, Post.body, Post.image,Post.id)\
    .filter_by(id = post_id).first()
    dateposted = post.timestamp.strftime('%B %d, %Y')
    if not post:
        flash('No user with that username exists.', category='error')
        return redirect(url_for('views.home'))
    name = post.image
    filename = "images/" + name
    filepath = url_for('static', filename = filename)
    return render_template("details.html", post = post, filepath = filepath, dateposted = dateposted)
    


@views.route("/create-comment/<post_id>", methods=['POST'])
@login_required
def create_comment(post_id):
    text = request.form.get('text')

    if not text:
        flash('Comment cannot be empty.', category='error')
    else:
        post = Post.query.filter_by(id=post_id)
        if post:
            comment = Comment(
                text=text, author=current_user.id, post_id=post_id)
            db.session.add(comment)
            db.session.commit()
        else:
            flash('Post does not exist.', category='error')

    return redirect(url_for('views.home'))


@views.route("/delete-comment/<comment_id>")
@login_required
def delete_comment(comment_id):
    comment = Comment.query.filter_by(id=comment_id).first()

    if not comment:
        flash('Comment does not exist.', category='error')
    elif current_user.id != comment.author and current_user.id != comment.post.author:
        flash('You do not have permission to delete this comment.', category='error')
    else:
        db.session.delete(comment)
        db.session.commit()

    return redirect(url_for('views.home'))


@views.route("/like-post/<post_id>", methods=['POST'])
@login_required
def like(post_id):
    post = Post.query.filter_by(id=post_id).first()
    like = Like.query.filter_by(
        author=current_user.id, post_id=post_id).first()

    if not post:
        return jsonify({'error': 'Post does not exist.'}, 400)
    elif like:
        db.session.delete(like)
        db.session.commit()
    else:
        like = Like(author=current_user.id, post_id=post_id)
        db.session.add(like)
        db.session.commit()

    return jsonify({"likes": len(post.likes), "liked": current_user.id in map(lambda x: x.author, post.likes)})

@views.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.name = form.name.data
        current_user.location = form.location.data
        current_user.about_me = form.about_me.data
        db.session.add(user)
        flash('Your profile has been updated.')
        return redirect(url_for('.user', username=current_user.username))
    form.name.data = current_user.name
    form.location.data = current_user.location
    form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', form=form)

@views.route("/details")
def details_post():
    return render_template("details.html")




