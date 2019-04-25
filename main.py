from flask import Flask, request, redirect, render_template, session, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc
from datetime import datetime

app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://blogz:password@localhost:8889/blogz'
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)
app.secret_key = 'secretkey'

class Blog(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120))
    body = db.Column(db.String(400))
    date = db.Column(db.DateTime)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __init__(self, title, body, user, date=None):

        self.title = title
        self.body = body
        if date is None:
            date = datetime.utcnow()
        self.date = date
        self.user = user

class User(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(16))
    blogs = db.relationship('Blog', backref='user')

    def __init__(self, username, password):

        self.username = username
        self.password = password

@app.before_request
def require_login():
    allowed_routes = ['login', 'signup', 'logout', 'blog', '/']
    if request.endpoint not in allowed_routes and 'username' not in session:
        flash('Please log in to view this page.')
        return redirect('/login')

@app.route('/login', methods=['POST', 'GET'])
def login():

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            session['username'] = username
            flash('Logged in!')
            return redirect('/newpost')
        elif not user:
            flash('User does not exist.')
            return render_template('login.html', username=username)
        elif user.password != password:
            flash('Incorrect password.')
            return render_template('login.html', username=username)

    return render_template('login.html')

@app.route('/signup', methods=['POST', 'GET'])
def signup():

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        verify = request.form['verify']
        if not username or ' ' in username or len(username) < 3 or len(username) > 120:
            flash('Please enter a valid username.')
            return render_template('signup.html', username = username)
        elif not password or len(password) > 16 or len(password) < 3 or ' ' in password:
            flash('Please enter a valid password.')
            return render_template('signup.html', username = username)
        elif not verify:
            flash('Please re-enter the password.')
            return render_template('signup.html', username = username)
        elif verify != password:
            flash('Please re-enter the password correctly.')
            return render_template('signup.html', username = username)
        else:
            existing_user = User.query.filter_by(username=username).first()
            if not existing_user:
                new_user = User(username, password)
                db.session.add(new_user)
                db.session.commit()
                session['username'] = username
                flash('Username created!')
                return redirect('/newpost')
            else:
                flash('User already exists!')
                return redirect('/signup')

    return render_template('signup.html')

@app.route('/logout')
def logout():
    del session['username']
    return redirect('/blog')

@app.route('/')
def index():
    sql_dict = User.query.all()
    users = []
    for i in sql_dict:
        users.append(i.username)
    users.sort(key = str.lower)
    return render_template('index.html', users=users)

@app.route('/newpost', methods=['POST', 'GET'])
def new_post():

    user = User.query.filter_by(username=session['username']).first()

    if request.method == 'POST':

        title_error = ''
        body_error = ''
        post_title = request.form['title']
        post_body = request.form['body']

        if post_title == '':

            title_error = 'Please enter a title!'

        if post_body == '':

            body_error = 'Please enter your post!'

        if not title_error and not body_error:

            new_post = Blog(post_title, post_body, user)
            db.session.add(new_post)
            db.session.commit()
            return redirect('/blog?id=' + str(new_post.id))

        else:

            return render_template('newpost.html', title = 'New Post', post_title = post_title, post_body = post_body,
             title_error = title_error, body_error = body_error)

    return render_template('newpost.html', title = 'New Post')

@app.route('/blog', methods=['POST', 'GET'])
def blog():

    pagination = Blog.query.order_by(desc(Blog.date)).paginate(1, 5, False)

    if request.method == 'GET':
        if request.args.get('id'):
            post_id = int(request.args.get('id'))
            current_post = Blog.query.get(post_id)
            return render_template('current.html', post=current_post)
        if request.args.get('user'):
            user = User.query.filter_by(username=request.args.get('user')).first()
            pagination = Blog.query.filter_by(user=user).order_by(desc(Blog.date)).paginate(1, 5, False)
            posts = pagination.items
            return render_template('user.html', posts=posts, username=user.username, pagination = pagination)
        if request.args.get('page'):
            page = int(request.args.get('page'))
            pagination = Blog.query.order_by(desc(Blog.date)).paginate(page, 5, False)
            posts = pagination.items
            return render_template('blog.html', posts=posts, pagination=pagination)

    posts = pagination.items
    return render_template('blog.html', posts=posts, pagination=pagination)

if __name__ == '__main__':
    app.run()