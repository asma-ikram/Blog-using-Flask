from datetime import datetime
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flaskblog import db, login_manager, app
from flask_login import UserMixin

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# to generate time sensitive token for changing passwords, we use package itsdangerous
# which gets installed when we install python
# from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
# now we are gonna use this serializer to pass a secret key and an expiration time of 30sec
 # s = Serializer('secret', 30)
 # now to generate a token we can use dumps (dump S) method and we are gonna send in a payload
 # that is just gonna be our user_id
 # token = s.dumps({'user_id': 1}).decode('utf-8')
 # 1 is taken as example
 # decode with utf-8 else it'll be in bytes
 # now to check our token, we can use: s.loads(token)
 # if it has been less than 30 seconds, it'll show: {'user_id': 1}
 # if it has been more than 30 seconds, it'll show: Signature expired

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default='default.jpg')
    password = db.Column(db.String(60), nullable=False)
    posts = db.relationship('Post', backref='author', lazy=True)

    def get_reset_token(self, expires_sec=1800):
        s = Serializer(app.config['SECRET_KEY'], expires_sec)
        return s.dumps({'user_id': self.id}).decode('utf-8')

    @staticmethod
    # we are basically telling python not to be expecting the self argument
    # and we are only going to be taking token as an argument
    def verify_reset_token(token):
        s = Serializer(app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token)['user_id']
        except:
            return None
        # we are able to get the user ID without an exception
        return User.query.get(user_id)

    def __repr__(self):
        return f"User('{self.username}', '{self.email}', '{self.image_file}')"


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"Post('{self.title}', '{self.date_posted}')"
