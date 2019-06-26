from flask import Flask, jsonify, request, current_app, Response, g
from flask.json import JSONEncoder
from sqlalchemy import create_engine, text
import bcrypt
import jwt
from functools import wraps
from datetime import datetime, timedelta
from flask_cors import CORS


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        access_token = request.headers.get('Authorization')
        print("======================================")
        print("decode해보자 : ", jwt.decode(access_token, current_app.config['JWT_SECRET_KEY'], 'HS256'))
        print("======================================")
        
        if access_token is not None: 
            try:
                print("======================================")
                print("지금 엑세스토큰 상태 : ",access_token)
                print("======================================")
                print("지금 컨피그 쳌 : ",current_app.config)
                
                payload = jwt.decode(access_token, current_app.config['JWT_SECRET_KEY'], 'HS256')
            except jwt.InvalidTokenError :
                payload = None
        
            print("payload 상태 보고 : ", payload)
            if payload is None: return Response(status=401)

            user_id = payload['user_id']
            g.user_id = user_id
            g.user = get_user(user_id) if user_id else None
        else :
            print("엑세스토큰 없대")
            return Response(status=401)

        return f(*args, **kwargs)
    return decorated_function


class CustomJSONEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, set):
            return list(obj)

        return JSONEncoder.default(self, obj)


def get_user(user_id):
    user = current_app.database.execute(text("""
        SELECT
            id,
            name,
            email,
            profile
        FROM users WHERE id = :user_id
    """), {
        "user_id": user_id 
    }).fetchone()
    print("what is fetchone : ", user)

    return {
        "id": user['id'],
        'name': user['name'],
        'email': user['email'],
        'profile': user['profile']
    } if user else None


def insert_user(new_user):
    new_data_id = current_app.database.execute(text("""
        INSERT INTO users (
            name,
            email,
            profile,
            hashed_password
        ) VALUE (
            :name,
            :email,
            :profile,
            :password
        )
    """), new_user).lastrowid
    print("new user is lastrowid : ",new_data_id)

    return new_data_id


def insert_tweet(new_tweet):
    new_data = current_app.database.execute(text("""
        INSERT INTO tweets (
            user_id,
            tweet
        ) VALUE (
            :id,
            :tweet
        )
    """), new_tweet).rowcount
    print("what is rowcount : ",new_data)

    return new_data


def insert_follow(user_follow):
    follow_data = current_app.database.execute(text("""
        INSERT INTO users_follow_list (
            user_id,
            follow_user_id
        ) VALUE (
            :id,
            :follow
        )
    """), user_follow).rowcount

    return follow_data


def insert_unfollow(user_unfollow):
    unfollow_data = current_app.database.execute(text("""
        DELETE FROM users_follow_list 
        WHERE user_id = :id
        AND follow_user_id = :unfollow
    """), user_unfollow).rowcount
    
    return unfollow_data


def get_timeline(user_id):
    timeline = current_app.database.execute(text("""
        SELECT
            tw.user_id,
            tw.tweet
        FROM tweets tw
        LEFT JOIN users_follow_list ufl ON ufl.user_id = :user_id
        WHERE tw.user_id = :user_id
        OR tw.user_id = ufl.follow_user_id
    """), {
        "user_id": user_id
    }).fetchall()
    print("this is fetchall !!! : ", timeline)

    return [{
        "user_id": tweet['user_id'],
        "tweet": tweet['tweet']
    } for tweet in timeline ]


def get_user_id_pw(email):
    user_data = current_app.database.execute(text("""
        SELECT
            id,
            hashed_password
        FROM users
        WHERE users.email = :email
    """), { "email": email }
    ).fetchone()

    return {
        "user_id": user_data['id'],
        "hashed_password": user_data['hashed_password']
    } if user_data else None


def create_app(test_config = None):
    app = Flask(__name__)
    
    CORS(app)

    app.json_encoder = CustomJSONEncoder

    if test_config is None:
        print("config check 1 ===> ", app.config)
        app.config.from_pyfile("config.py")
        print("config check 2 ===> ", app.config)
    else:
        app.config.update("찍어본다 config : ", test_config)

    print(app.config)

    database = create_engine(app.config['DB_URL'], encoding = 'utf-8', max_overflow = 0)
    app.database = database


    @app.route('/ping', methods=['GET'])
    def ping():
        return "pong"

    
    @app.route('/login', methods=['POST'])
    def login():
        credential = request.json
        email = credential['email']
        password = credential['password']
        user_data = get_user_id_pw(email)

        if user_data and bcrypt.checkpw(password.encode('UTF-8'), user_data['hashed_password'].encode('UTF-8')):
            user_id = user_data['user_id']
            payload = {
                'user_id': user_id,
                'exp': datetime.utcnow() + timedelta(seconds = 60 * 60 * 24)
            }
            token = jwt.encode(payload, app.config['JWT_SECRET_KEY'], 'HS256')
            print("토큰간다! : ",token)

            return jsonify({
                'access_token': token.decode('UTF-8'),
                'user_id': user_id
            })
        else :
            return '', 401

    
    @app.route('/sign-up', methods=['POST'])
    def sign_up():
        new_user = request.json
        new_user['password'] = bcrypt.hashpw(
            new_user['password'].encode('UTF-8'),
            bcrypt.gensalt()
        )
        new_user_id = insert_user(new_user)
        new_saved_id = get_user(new_user_id)

        return jsonify(new_saved_id)


    @app.route('/tweet', methods=['POST'])
    @login_required
    def tweet():
        new_tweet = request.json
        new_tweet['id'] = g.user_id

        if len(new_tweet['tweet']) > 300 :
            return '300자를 초과하였습니다.', 400
        
        insert_tweet(new_tweet)
        
        return '', 200


    @app.route('/follow', methods=['POST'])
    @login_required
    def follow():
        new_follow = request.json
        new_follow['id'] = g.user_id
        insert_follow(new_follow)

        return '', 200

    
    @app.route('/unfollow', methods=['POST'])
    @login_required
    def unfollow():
        payload = request.json
        payload['id'] = g.user_id
        insert_unfollow(payload)

        return '', 200

    @app.route('/timeline/<int:user_id>', methods=['GET'])
    def timeline():
        return jsonify({
            'user_id' : user_id,
            'timeline' : get_timeline(user_id)
        })

    
    @app.route('/timeline', methods=['GET'])
    @login_required
    def user_timeline():
        user_id = g.user_id

        return jsonify({
            'user_id' : user_id,
            'timeline' : get_timeline(user_id)
        })

    return app



