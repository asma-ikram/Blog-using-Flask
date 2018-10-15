
import os
import secrets
from PIL import Image
# for pillow package to resize image before saving
from flask import render_template, url_for, flash, redirect, request, abort
from flaskblog import app, db, bcrypt, mail
from flaskblog.forms import RegistrationForm, LoginForm, UpdateAccountForm, PostForm, RequestResetForm, ResetPasswordForm
from flaskblog.models import User, Post
from flask_login import login_user, current_user, logout_user, login_required
from flask_mail import Message
# login_required puts restrictions on the access of certain pages, so that they
# can only be accesssed when a user is logged in
# DUMMY DATA
# posts = [
#     {
#         'author': 'Corey Schafer',
#         'title': 'Blog Post 1',
#         'content': 'First post content',
#         'date_posted': 'April 20, 2018'
#     },
#     {
#         'author': 'Jane Doe',
#         'title': 'Blog Post 2',
#         'content': 'Second post content',
#         'date_posted': 'April 21, 2018'
#     }
# ]


@app.route("/")
@app.route("/home")
def home():
    # creating a route to our posts
    # posts=Post.query.all()
    # posts per page = paginate
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.date_posted.desc()).paginate(page=page, per_page=5)
    return render_template('home.html', posts=posts)


@app.route("/about")
def about():
    return render_template('about.html', title='About')


@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password=bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user=User(username=form.username.data, email=form.email.data, password=hashed_password)
        # created user_id
        db.session.add(user)
        db.session.commit()
        flash('YOUR ACCOUNT HAS BEEN CREATED, YOU CAN NOW LOGIN', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            # if the user exists and the password that they entered is valid
            # log them in
            login_user(user, remember=form.remember.data)
            next_page=request.args.get('next')
            # args is dictionary
            return redirect(next_page) if next_page else  redirect(url_for('home'))
            # ternary conditional
            # so that if we come to some page that requires login, then after loggin in
            # we come back to that same page only
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)

@app.route("/logout",)
def logout():
    logout_user()
    return redirect(url_for('home'))

# to save out image to file system
def save_picture(form_picture):
    # we want the name to be something that cannot collide with user file
    random_hex = secrets.token_hex(8)
    # we are passing 8 bytes
    # we are grabbing file extension from what the user used
    # this os function returns 2 values, filename without the extention and then extention itself
    # f_name, f_ext = os.path.splitext(form_picture.filename)
    # if we dont want to use any variable, just use underscore
    _, f_ext = os.path.splitext(form_picture.filename)
    # fn for filename
    picture_fn = random_hex + f_ext #concatenation
    # using root path attribute
    # gives root path all the way to our package directory
    picture_path = os.path.join(app.root_path, 'static/profile_pics', picture_fn)

    # form_picture.save(picture_path)

    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn

@app.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Your account has been updated', 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file = url_for('static', filename = 'profile_pics/' + current_user.image_file)
    return render_template('account.html', title='Account', image_file=image_file, form= form)

@app.route("/post/new", methods=['GET', 'POST'])
# we are accepoting GET and POST requests
@login_required
# to make a post, the user should be loggedin
def new_post():
    form = PostForm()
    # getting form from our forms.py file and saving it in an instance 'form'
    if form.validate_on_submit():
        post = Post(title=form.title.data, content=form.content.data, author=current_user)
        # we are attaching the author's name to the post also
        db.session.add(post)
        db.session.commit()
        # we are adding the post to the database
        flash('Your post has been created!', 'success')
        return redirect(url_for('home'))
        # once post is successful posted, redirected to home
    return render_template('create_post.html', title='New Post',
                           form=form, legend='New Post')
# adding ability to update and delete Posts
# making routes so that a single post takes us to a specific route
# flask gives us the ability to add variables to our routes
@app.route("/post/<int:post_id>")
# the post_id is gonna is be an integer, so int:post_id
def post(post_id):
    post = Post.query.get_or_404(post_id)
# we are not using get(), we are using get_or_404, this is a method that
# asks for a post with the requested ID, and if the page doesnt exist, give error 404
    return render_template('post.html', title=post.title, post=post)


@app.route("/post/<int:post_id>/update", methods=['GET', 'POST'])
@login_required
def update_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
        # manually aborting
        # http response for a forbidden route
    form = PostForm()
    # if the current user is the author of the post
    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data
        db.session.commit()
        flash('Your post has been updated!', 'success')
        return redirect(url_for('post', post_id=post.id))
    elif request.method == 'GET':
        form.title.data = post.title
        form.content.data = post.content
    return render_template('create_post.html', title='Update Post',
                           form=form, legend='Update Post')

# deleting a post
@app.route("/post/<int:post_id>/delete", methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash('Your post has been deleted!', 'success')
    return redirect(url_for('home'))

def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message('Password Reset Request',
                  sender='noreply@demo.com',
                  recipients=[user.email])
    msg.body = f'''To reset your password, visit the following link:
{url_for('reset_token', token=token, _external=True)}
If you did not make this request then simply ignore this email and no changes will be made.
'''
    mail.send(msg)


@app.route("/reset_password", methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        send_reset_email(user)
        flash('An email has been sent with instructions to reset your password.', 'info')
        return redirect(url_for('login'))
    return render_template('reset_request.html', title='Reset Password', form=form)


@app.route("/reset_password/<token>", methods=['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    user = User.verify_reset_token(token)
    if user is None:
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user.password = hashed_password
        db.session.commit()
        flash('Your password has been updated! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('reset_token.html', title='Reset Password', form=form)
