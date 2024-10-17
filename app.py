from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# Configurations
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'supersecretkey'

db = SQLAlchemy(app)
jwt = JWTManager(app)

# User Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    name = db.Column(db.String(100), nullable=False)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

# Post Model
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    image = db.Column(db.String(200), nullable=True)
    caption = db.Column(db.String(255), nullable=True)
    user = db.relationship('User', backref=db.backref('posts', lazy=True))

# Comment Model
class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    text = db.Column(db.String(255), nullable=False)
    user = db.relationship('User', backref=db.backref('comments', lazy=True))
    post = db.relationship('Post', backref=db.backref('comments', lazy=True))

# Initialize the database
with app.app_context():
    db.create_all()

# Route for user registration
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if User.query.filter_by(email=data['email']).first():
        return jsonify(message="User with that email already exists"), 400
    new_user = User(email=data['email'], name=data['name'])
    new_user.set_password(data['password'])
    db.session.add(new_user)
    db.session.commit()
    return jsonify(message="User registered successfully"), 201

# Route for user login
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(email=data['email']).first()
    if user and user.check_password(data['password']):
        access_token = create_access_token(identity=user.id)
        return jsonify(access_token=access_token), 200
    return jsonify(message="Invalid credentials"), 401

# Create a post (requires authentication)
@app.route('/post', methods=['POST'])
@jwt_required()
def create_post():
    user_id = get_jwt_identity()
    data = request.get_json()
    new_post = Post(user_id=user_id, image=data.get('image'), caption=data.get('caption'))
    db.session.add(new_post)
    db.session.commit()
    return jsonify(message="Post created successfully"), 201

# Create a comment on a post (requires authentication)
@app.route('/comment', methods=['POST'])
@jwt_required()
def create_comment():
    user_id = get_jwt_identity()
    data = request.get_json()
    new_comment = Comment(user_id=user_id, post_id=data['post_id'], text=data['text'])
    db.session.add(new_comment)
    db.session.commit()
    return jsonify(message="Comment added"), 201

# Edit a post (requires authentication)
@app.route('/post/<int:id>', methods=['PUT'])
@jwt_required()
def edit_post(id):
    user_id = get_jwt_identity()
    post = Post.query.get_or_404(id)
    if post.user_id != user_id:
        return jsonify(message="Unauthorized"), 403
    data = request.get_json()
    post.caption = data.get('caption', post.caption)
    db.session.commit()
    return jsonify(message="Post updated"), 200

# Delete a post (requires authentication)
@app.route('/post/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_post(id):
    user_id = get_jwt_identity()
    post = Post.query.get_or_404(id)
    if post.user_id != user_id:
        return jsonify(message="Unauthorized"), 403
    db.session.delete(post)
    db.session.commit()
    return jsonify(message="Post deleted"), 200

# Root route
@app.route('/')
def home():
    return "Hello, Flask!"

if __name__ == '__main__':
    app.run(debug=True)

#access token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTcyOTEzOTQxNCwianRpIjoiOThiM2ZiNjgtM2ZhNi00NTQyLWE0NDItNWM3YzFmZDZkNTE0IiwidHlwZSI6ImFjY2VzcyIsInN1YiI6MSwibmJmIjoxNzI5MTM5NDE0LCJjc3JmIjoiYjJiMzBjZDktZDA3Yy00OTBiLWEwMDAtMzQzZGRjODkwNmNmIiwiZXhwIjoxNzI5MTQwMzE0fQ.e1p36IOmgRxMZckeh2SDFO4fFH_vniRzz_suNfuq-Ys