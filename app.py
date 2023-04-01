######################################
# author ben lawson <balawson@bu.edu>
# Edited by: Craig Einstein <einstein@bu.edu>
######################################
# Some code adapted from
# CodeHandBook at http://codehandbook.org/python-web-application-development-using-flask-and-mysql/
# and MaxCountryMan at https://github.com/maxcountryman/flask-login/
# and Flask Offical Tutorial at  http://flask.pocoo.org/docs/0.10/patterns/fileuploads/
# see links for further understanding
###################################################

import flask
from flask import Flask, Response, request, render_template, redirect, url_for
from flaskext.mysql import MySQL
import flask_login

# for image uploading
import os
import base64

mysql = MySQL()
app = Flask(__name__)
app.secret_key = 'super secret string'  # Change this!

# These will need to be changed according to your creditionals
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'M1ke1san1d1oT!'
app.config['MYSQL_DATABASE_DB'] = 'photoshare'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)

# begin code used for login
login_manager = flask_login.LoginManager()
login_manager.init_app(app)

conn = mysql.connect()
cursor = conn.cursor()
cursor.execute("SELECT email from Users")
users = cursor.fetchall()


def getUserList():

    cursor.execute("SELECT email from Users")
    return cursor.fetchall()


class User(flask_login.UserMixin):
    pass


@login_manager.user_loader
def user_loader(email):
    users = getUserList()
    if not (email) or email not in str(users):
        return
    user = User()
    user.id = email
    return user


@login_manager.request_loader
def request_loader(request):
    users = getUserList()
    email = request.form.get('email')
    if not (email) or email not in str(users):
        return
    user = User()
    user.id = email
    cursor = mysql.connect().cursor()
    cursor.execute(
        "SELECT password FROM Users WHERE email = '{0}'".format(email))
    data = cursor.fetchall()
    pwd = str(data[0][0])
    user.is_authenticated = request.form['password'] == pwd
    return user


'''
A new page looks like this:
@app.route('new_page_name')
def new_page_function():
	return new_page_html
'''


@app.route('/login', methods=['GET', 'POST'])
def login():
    if flask.request.method == 'GET':
        return '''
			   <form action='login' method='POST'>
				<input type='text' name='email' id='email' placeholder='email'></input>
				<input type='password' name='password' id='password' placeholder='password'></input>
				<input type='submit' name='submit'></input>
			   </form></br>
		   <a href='/'>Home</a>
			   '''
    # The request method is POST (page is recieving data)
    email = flask.request.form['email']
    cursor = conn.cursor()
    # check if email is registered
    if cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email)):
        data = cursor.fetchall()
        pwd = str(data[0][0])
        if flask.request.form['password'] == pwd:
            user = User()
            user.id = email
            flask_login.login_user(user)  # okay login in user
            # protected is a function defined in this file
            return flask.redirect(flask.url_for('profile'))

    # information did not match
    return "<h2>Login unsuccesful</h2>\
            <a href='/login'>Try again</a>\
			</br><a href='/register'>or make an account</a>"


@app.route('/logout')
def logout():
    flask_login.logout_user()
    return render_template('home.html', message='Logged out', loggedout=True)


@login_manager.unauthorized_handler
def unauthorized_handler():
    return render_template('unauth.html')

# you can specify specific methods (GET/POST) in function header instead of inside the functions as seen earlier


@app.route("/register", methods=['GET'])
def register():
    return render_template('register.html', supress='True')


@app.route("/register", methods=['POST'])
def register_user():
    try:
        email = request.form.get('email')
        password = request.form.get('password')
        gender = request.form.get('gender')
        dob = request.form.get('dob')
        hometown = request.form.get('hometown')
        fname = request.form.get('fname')
        lname = request.form.get('lname')
    except:
        # this prints to shell, end users will not see this (all print statements go to shell)
        print("couldn't find all tokens")
        return flask.redirect(flask.url_for('register'))

    test = isEmailUnique(email)
    if test:
        cursor.execute("INSERT INTO Users (email, password, gender, dob, hometown, fname, lname) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                       (email, password, gender, dob, hometown, fname, lname))
        conn.commit()
        # log user in
        user = User()
        user.id = email
        flask_login.login_user(user)
        return render_template('home.html', name=email, message='Account Created!')
    else:
        print("couldn't find all tokens")
        return "<h2>Email already in use</h2><a href='/login'>Log in </a> </br><a href='/register'>or register</a>"


def getUsersPhotos(uid):
    cursor.execute(
        "SELECT imgdata, photo_id, caption FROM Photos WHERE user_id = '{0}'".format(uid))
    # NOTE return a list of tuples, [(imgdata, pid, caption), ...]
    return cursor.fetchall()


def getUserIdFromEmail(email):
    cursor.execute(
        "SELECT user_id  FROM Users WHERE email = '{0}'".format(email))
    if cursor.rowcount == 0:
        return None
    return cursor.fetchone()[0]


def getEmailFromUserId(uid):
    cursor.execute(
        "SELECT email  FROM Users WHERE user_id = '{0}'".format(uid))
    if cursor.rowcount == 0:
        return None
    return cursor.fetchone()[0]


def isEmailUnique(email):
    # use this to check if a email has already been registered
    if cursor.execute("SELECT email FROM Users WHERE email = '{0}'".format(email)):
        # this means there are greater than zero entries with that email
        return False
    else:
        return True
# end login code

# START PROFILE PAGE FOR VIEWING OTHER USERS


def getNameFromId(uid):
    cursor.execute(
        "SELECT fname, lname FROM Users WHERE user_id = '{0}'".format(uid))
    return cursor.fetchone()


@app.route('/profile', methods=['GET'])
def profile():
    uid = flask.request.args.get('uid')
    if uid is None:
        # Viewing own profile
        return render_template('profile.html', name=flask_login.current_user.id, message="Here's your profile")
    else:
        # Viewing searched profile
        cursor.execute(
            "SELECT fname, lname FROM Users WHERE user_id = '{0}'".format(uid))
        profile_data = cursor.fetchone()
        profile_name = profile_data[0] + " " + profile_data[1]
        print(profile_name)
        return render_template('profile.html', search_profile_name=profile_name)


@app.route('/profile/<uid>', methods=['GET'])
def profile_user(uid):
    cursor.execute(
        "SELECT fname, lname FROM Users WHERE user_id = '{0}'".format(uid))
    profile_data = cursor.fetchone()
    email = getEmailFromUserId(uid)
    if flask_login.current_user.is_authenticated:
        current_user_id = getUserIdFromEmail(flask_login.current_user.id)
        return render_template('profile.html', profile_name=profile_data[0] + " " + profile_data[1], uid=uid, current_user_id=current_user_id, email=email)
    return render_template('profile.html', profile_name=profile_data[0] + " " + profile_data[1], uid=uid, email=email)
# END PROFILE PAGE


# begin photo uploading code
# photos uploaded using base64 encoding so they can be directly embeded in HTML
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


def getAlbumIdFromName(album_name):
    cursor.execute(
        "SELECT album_id FROM Albums WHERE album_name = '{0}'".format(album_name))
    return cursor.fetchone()[0]


@app.route('/upload', methods=['GET', 'POST'])
@flask_login.login_required
def upload_file():
    if request.method == 'POST':
        uid = getUserIdFromEmail(flask_login.current_user.id)
        imgfile = request.files['photo']
        caption = request.form.get('caption')
        photo_data = imgfile.read()
        album_id = request.form.get('album_id')
        cursor.execute(
            '''INSERT INTO Photos (imgdata, user_id, caption, album_id) VALUES (%s, %s, %s, %s )''', (photo_data, uid, caption, album_id))
        conn.commit()
        tag_name = request.form.get('tag_name')
        tags = tag_name.split(' ')
        cursor.execute("SELECT LAST_INSERT_ID() FROM Photos")
        photo_id = cursor.fetchone()[0]
        if len(tags) > 0:
            for tag in tags:
                if tagNotInTable(tag):
                    print("TAG CREATED")
                    cursor.execute(
                        "INSERT INTO Tags (tag_name) VALUES ('{0}')".format(tag))
                    conn.commit()
                # otherwise tag already exists in table so dont insert

                tag_id = getTagIdFromTagName(tag)
                cursor.execute("INSERT INTO Tagged (photo_id, tag_id) VALUES ('{0}', '{1}')".format(
                    photo_id, tag_id))
                conn.commit()
        return render_template('profile.html', name=flask_login.current_user.id, message='Photo uploaded!')

    # The method is GET so we return a  HTML form to upload the a photo.
    else:
        uid = getUserIdFromEmail(flask_login.current_user.id)

        cursor.execute(
            "SELECT album_name, album_id FROM Albums WHERE user_id = '{0}'".format(uid))
        album_data = cursor.fetchall()
        return render_template('upload.html', albums=album_data)
# end photo uploading code

# default page


@app.route("/", methods=['GET'])
def hello():
    if flask_login.current_user.is_authenticated:
        return render_template('home.html', name=flask_login.current_user.id, message='Welcome to Photoshare')
    return render_template('home.html', message='Welecome to Photoshare', loggedout=True)


if __name__ == "__main__":
    # this is invoked when in the shell  you run
    # $ python app.py
    app.run(port=5000, debug=True)


# friends page
@app.route('/addfriend', methods=['GET'])
@flask_login.login_required
def addfriend():
    return render_template('addfriend.html')


@app.route('/addfriend', methods=['POST'])
@flask_login.login_required
def addfriend_post():
    email = request.form.get('friendemail')
    uid = getUserIdFromEmail(flask_login.current_user.id)
    friendid = getUserIdFromEmail(email)
    print(friendid)
    if uid == friendid or not friendid:
        return render_template('home.html', name=flask_login.current_user.id, message='Email not found or already exists in your friends list')

    cursor.execute(
        '''INSERT INTO Friendship (UID1, UID2) VALUES (%s, %s)''', (uid, friendid))
    conn.commit()
    return render_template('home.html', name=flask_login.current_user.id, message='Friend added!')


@app.route('/friendslist', methods=['GET'])
@flask_login.login_required
def friendslist():
    uid = getUserIdFromEmail(flask_login.current_user.id)
    cursor.execute(
        "SELECT fname, lname FROM Users WHERE user_id IN (SELECT UID2 FROM Friendship WHERE UID1 = '{0}')".format(uid))
    friends_data = cursor.fetchall()
    print(friends_data)
    return render_template('friendslist.html', friends=friends_data)
# end friends page

# START USER ACTIVITY


@app.route('/useractivity', methods=['GET'])
def useractivity():
    if flask_login.current_user.is_authenticated:
        uid = getUserIdFromEmail(flask_login.current_user.id)
        cursor.execute(
            "SELECT fname, lname, (COUNT(DISTINCT Photos.photo_id) + COUNT(DISTINCT comment_id)) AS c_score, COUNT(DISTINCT Photos.photo_id), COUNT(DISTINCT comment_id), Users.user_id\
            FROM Users\
            LEFT JOIN Photos ON Users.user_id = Photos.user_id\
            LEFT JOIN Comments ON Users.user_id = Comments.user_id\
            GROUP BY Users.user_id\
            ORDER BY c_score DESC\
            LIMIT 10;")
        friends_data = cursor.fetchall()
        print(friends_data)
        return render_template('useractivity.html', friends=friends_data)
    return render_template('useractivity.html', message='Welecome to Photoshare', loggedout=True)

# END USER ACTIVITY


# START CREATE ALBUM
@app.route('/createalbum', methods=['GET'])
@flask_login.login_required
def createalbum():
    return render_template('createalbum.html')


@app.route('/createalbum', methods=['POST'])
@flask_login.login_required
def createalbum_post():
    album_name = request.form.get('album_name')
    uid = getUserIdFromEmail(flask_login.current_user.id)
    cursor.execute(
        '''INSERT INTO Albums (user_id, album_name) VALUES (%s, %s)''', (uid, album_name))
    conn.commit()
    return render_template('home.html', name=flask_login.current_user.id, message='Album created!')
# END CREATE ALBUM

# START SEARCH PROFILE


@app.route('/searchprofile', methods=['GET'])
def searchprofile():
    if flask_login.current_user.is_authenticated:
        current_user_id = getUserIdFromEmail(flask_login.current_user.id)
        return render_template('searchprofile.html', current_user_id=current_user_id)
    return render_template('searchprofile.html')


@app.route('/searchprofile', methods=['POST'])
def searchprofile_post():
    if request.form.get('email'):
        email = request.form.get('email')
        uid = getUserIdFromEmail(email)
        if not uid:
            return render_template('searchprofile.html', message='Email not found')
        return flask.redirect(flask.url_for('profile_user', uid=uid))
    else:
        # comments
        comment = request.form.get('comment')
        return searchByComments(comment)

# END SEARCH PROFILE
# SEARCH BY PROFILE BY COMMENTS


def searchByComments(comment):
    comment = request.form.get('comment')
    cursor.execute(
        "SELECT fname, lname, Users.user_id, COUNT(*) AS ccount FROM Users, Comments\
        WHERE Users.user_id = Comments.user_id AND text='{0}'\
        GROUP BY Users.user_id\
        ORDER BY ccount DESC".format(comment))
    user_data = cursor.fetchall()
    current_user_id = None
    if flask_login.current_user.is_authenticated:
        current_user_id = getUserIdFromEmail(flask_login.current_user.id)
    return render_template('viewsearchbycomments.html', users=user_data, comment=comment, current_user_id=current_user_id)
# END SEARCH BY COMMENTS


# START VIEW PHOTOS
def getAlbumIdFromName(album_name):
    cursor.execute(
        "SELECT album_id FROM Albums WHERE album_name = '{0}'".format(album_name))
    return cursor.fetchone()[0]


def getAlbumNameFromId(album_id):
    cursor.execute(
        "SELECT album_name FROM Albums WHERE album_id = '{0}'".format(album_id))
    return cursor.fetchone()[0]


def getCaptionFromPhotoId(photo_id):
    cursor.execute(
        "SELECT caption FROM Photos WHERE photo_id = '{0}'".format(photo_id))
    return cursor.fetchone()[0]


def getNumLikesFromPhotoId(photo_id):
    cursor.execute(
        "SELECT COUNT(*) FROM Likes WHERE photo_id = '{0}'".format(photo_id))
    return cursor.fetchone()[0]


def getPhotoDataFromAlbumId(album_id):
    cursor.execute(
        "SELECT imgdata, caption, photo_id FROM Photos WHERE album_id = '{0}'".format(album_id))
    photo_data = cursor.fetchall()
    return updatePhotoData(photo_data)


def getUsersWhoLikedPhoto(photo_id):
    cursor.execute(
        "SELECT fname, lname FROM Users WHERE user_id IN (SELECT user_id FROM Likes WHERE photo_id = '{0}')".format(photo_id))
    return cursor.fetchall()

# 0 = imgdata, 1 = caption, 2 = photo_id, 3 = numlikes, 4 = album_id, 5 = users who liked photo


def updatePhotoData(photo_data):
    photo_data = [[photo[0], photo[1], photo[2],
                   getNumLikesFromPhotoId(photo[2]), getAlbumIdFromPhotoId(photo[2]), getUsersWhoLikedPhoto(photo[2])] for photo in photo_data]
    print(photo_data[0][5])
    return photo_data


def getYourPhotoDataFromTagName(tag_name, uid):
    cursor.execute(
        "SELECT imgdata, caption, photo_id FROM Photos\
        WHERE photo_id IN (SELECT photo_id FROM Tagged WHERE\
        tag_id IN (SELECT tag_id FROM Tags WHERE\
        tag_name = '{0}')) AND user_id = '{1}'".format(tag_name, uid))
    photo_data = cursor.fetchall()
    return updatePhotoData(photo_data)


def getAllPhotoDataFromTagName(tag_name):
    cursor.execute(
        "SELECT imgdata, caption, photo_id FROM Photos\
        WHERE photo_id IN (SELECT photo_id FROM Tagged WHERE\
        tag_id IN (SELECT tag_id FROM Tags WHERE\
        tag_name = '{0}'))".format(tag_name))
    photo_data = cursor.fetchall()
    return updatePhotoData(photo_data)


def getAlbumIdFromPhotoId(photo_id):
    cursor.execute(
        "SELECT album_id FROM Photos WHERE photo_id = '{0}'".format(photo_id))
    return cursor.fetchone()[0]


@app.route('/viewphotos', methods=['GET'])
@flask_login.login_required
def viewphotos():
    uid = getUserIdFromEmail(flask_login.current_user.id)
    cursor.execute(
        "SELECT album_name, album_id FROM Albums WHERE user_id = '{0}'".format(uid))
    album_data = cursor.fetchall()
    return render_template('viewphotos.html', albums=album_data)


@app.route('/viewphotos', methods=['POST'])
@flask_login.login_required
def viewphotos_post():
    # Liking your photos with a specific tag
    uid = getUserIdFromEmail(flask_login.current_user.id)
    tag_name = request.form.get('tag_name')
    photo_id = request.form.get('photo_id')
    photo_data = getYourPhotoDataFromTagName(tag_name, uid)
    if request.form.get('view_all'):
        photo_data = getAllPhotoDataFromTagName(tag_name)
    album_id = getAlbumIdFromPhotoId(photo_id)
    album_name = getAlbumNameFromId(album_id)
    if request.form.get('like'):
        if checkAlreadyLiked(uid, photo_id):
            return "<p> You have already liked this photo</p> " + render_template('/viewphotos.html', tag_name=tag_name, current_user_id=uid, photos=photo_data, album_id=album_id, album_name=album_name, base64=base64)
        else:
            cursor.execute(
                "INSERT INTO Likes (photo_id, user_id) VALUES ('{0}', '{1}')".format(photo_id, uid))
            conn.commit()
            photo_data = getPhotoDataFromAlbumId(album_id)
            photo_data = updatePhotoData(photo_data)
            return "<p> Liked photo</p> " + render_template('/viewphotos.html',  current_user_id=uid, tag_name=tag_name, photos=photo_data, album_id=album_id, album_name=album_name, base64=base64)
    else:
        return render_template('/viewphotos.html', tag_name=tag_name, current_user_id=uid, photos=photo_data, album_id=album_id, album_name=album_name, base64=base64)


@app.route('/viewphotos/<album_id>', methods=['GET'])
@flask_login.login_required
def viewphotos_album(album_id):
    photo_data = getPhotoDataFromAlbumId(album_id)
    album_name = getAlbumNameFromId(album_id)
    uid = getUserIdFromEmail(flask_login.current_user.id)
    return render_template('viewphotos.html', current_user_id=uid, album_id=album_id, photos=photo_data, album_name=album_name, base64=base64)


@app.route('/viewphotos/<album_id>', methods=['POST'])
@flask_login.login_required
def viewphotos_album_post(album_id):
    # LIKE
    uid = getUserIdFromEmail(flask_login.current_user.id)

    photo_id = request.form.get('photo_id')
    photo_data = getPhotoDataFromAlbumId(album_id)
    album_name = getAlbumNameFromId(album_id)

    photo_id = request.form.get('photo_id')
    view_all = request.form.get('view_all')
    if request.form.get('like'):
        if checkAlreadyLiked(uid, photo_id):
            return "<p> You have already liked this photo</p> " + render_template('/viewphotos.html', current_user_id=uid, photos=photo_data, album_id=album_id, album_name=album_name, base64=base64, view_all=view_all)
        else:
            cursor.execute(
                "INSERT INTO Likes (photo_id, user_id) VALUES ('{0}', '{1}')".format(photo_id, uid))
            conn.commit()
            photo_data = getPhotoDataFromAlbumId(album_id)
            photo_data = updatePhotoData(photo_data)
            return "<p> Liked photo</p> " + render_template('/viewphotos.html',  current_user_id=uid, photos=photo_data, album_id=album_id, album_name=album_name, base64=base64)
    else:
        return render_template('/viewphotos.html', current_user_id=uid, photos=photo_data, album_id=album_id, album_name=album_name, base64=base64)
# END VIEW PHOTOS

# START DELETE PHOTO


@app.route('/deletephotos', methods=['GET'])
@flask_login.login_required
def deletephotos():
    uid = getUserIdFromEmail(flask_login.current_user.id)
    cursor.execute(
        "SELECT album_name, album_id FROM Albums WHERE user_id = '{0}'".format(uid))
    album_data = cursor.fetchall()
    return render_template('deletephotos.html', albums=album_data)


@app.route('/deletephotos/<album_id>', methods=['GET'])
@flask_login.login_required
def deletephotos_from_album(album_id):
    uid = getUserIdFromEmail(flask_login.current_user.id)
    album_name = getAlbumNameFromId(album_id)
    cursor.execute(
        "SELECT imgdata, caption, photo_id FROM Photos WHERE user_id = '{0}' and album_id = '{1}'".format(uid, album_id))
    photo_data = cursor.fetchall()
    photo_data = updatePhotoData(photo_data)
    return render_template('deletephotos.html', album_name=album_name, album_id=album_id, photos=photo_data, base64=base64)


@app.route('/deletephotos/<album_id>', methods=['POST'])
@flask_login.login_required
def deletephotos_from_album_post(album_id):
    if request.form.get('delete_album'):
        cursor.execute(
            "DELETE FROM Albums WHERE album_id = '{0}'".format(album_id))
        conn.commit()
        return render_template('home.html', name=flask_login.current_user.id, message='Album has been deleted')

    uid = getUserIdFromEmail(flask_login.current_user.id)
    album_name = getAlbumNameFromId(album_id)
    photo_id = request.form.get('photo_id')
    photo_caption = getCaptionFromPhotoId(photo_id)
    cursor.execute(
        "DELETE FROM Photos WHERE photo_id = {0}".format(photo_id))
    conn.commit()
    msg = "The photo \"" + photo_caption + \
        "\" from the album \"" + album_name + "\" has been deleted"
    return render_template('profile.html', message=msg)

# END DELETE PHOTOS

# START VIEW PHOTOS FOR FRIENDS


@app.route('/profile/<uid>/viewphotos', methods=['GET'])
def viewphotos_friend(uid):
    cursor.execute(
        "SELECT album_name, album_id FROM Albums WHERE user_id = '{0}'".format(uid))
    album_data = cursor.fetchall()
    name = getNameFromId(uid)
    current_user_id = None
    if flask_login.current_user.is_authenticated:
        current_user_id = getUserIdFromEmail(flask_login.current_user.id)
    return render_template('viewphotos.html', name=name[0]+" "+name[1], uid=uid, albums=album_data, current_user_id=current_user_id)


@app.route('/profile/<uid>/viewphotos', methods=['POST'])
def viewphotos_friend_post(uid):
    album_name = request.form.get('album_name')
    album_id = getAlbumIdFromName(album_name)
    name = getNameFromId(uid)
    if flask_login.current_user.is_authenticated:
        current_user_id = getUserIdFromEmail(flask_login.current_user.id)
    return flask.redirect(flask.url_for('viewphotos_friend_album', name=name[0]+" "+name[1], uid=uid, album_id=album_id, current_user_id=current_user_id))


@app.route('/profile/<uid>/viewphotos/<album_id>', methods=['GET'])
def viewphotos_friend_album(uid, album_id):
    message = request.args.get('message')
    photo_data = getPhotoDataFromAlbumId(album_id)
    album_name = getAlbumNameFromId(album_id)
    name = getNameFromId(uid)
    current_user_id = None
    if flask_login.current_user.is_authenticated:
        current_user_id = getUserIdFromEmail(flask_login.current_user.id)
    return render_template('viewphotos.html', name=name[0] + " "+name[1], uid=uid, album_id=album_id, photos=photo_data, album_name=album_name, base64=base64, current_user_id=current_user_id, message=message)


def checkAlreadyLiked(uid, photo_id):
    cursor.execute(
        "SELECT user_id FROM Likes WHERE user_id = '{0}' and photo_id = '{1}'".format(uid, photo_id))
    data = cursor.fetchone()
    if data is None:
        return False
    return True


@app.route('/profile/<uid>/viewphotos/<album_id>', methods=['POST'])
def viewphotos_friend_album_post(uid, album_id):
    current_uid = None
    if flask_login.current_user.is_authenticated:
        current_uid = getUserIdFromEmail(flask_login.current_user.id)
    photo_id = request.form.get('photo_id')
    name = getNameFromId(uid)
    name = name[0] + " " + name[1]
    photo_data = getPhotoDataFromAlbumId(album_id)
    print(album_id)
    album_name = getAlbumNameFromId(album_id)
    comment = request.form.get('comment')

    if request.form.get('comment'):
        # COMMENT
        comment = request.form.get('comment')
        if current_uid:
            cursor.execute(
                "INSERT INTO Comments (photo_id, user_id, text) VALUES ('{0}', '{1}', '{2}')".format(photo_id, current_uid, comment))
        else:
            # anonymous comment: so insert NULL for user_id
            cursor.execute(
                "INSERT INTO Comments (photo_id, text) VALUES ('{0}', '{1}')".format(photo_id, comment))
        conn.commit()
        return "<p> Comments added succesfully</p> " + render_template('/viewphotos.html', name=name, uid=uid, photos=photo_data, album_id=album_id, album_name=album_name, base64=base64, current_user_id=current_uid)
    else:
        # LIKE
        if checkAlreadyLiked(current_uid, photo_id):
            return "<p> You have already liked this photo</p> " + render_template('/viewphotos.html', name=name, uid=uid, photos=photo_data, album_id=album_id, album_name=album_name, base64=base64, current_user_id=current_uid)
        else:
            cursor.execute(
                "INSERT INTO Likes (photo_id, user_id) VALUES ('{0}', '{1}')".format(photo_id, current_uid))
            conn.commit()
            # need to update number of likes
            photo_data = getPhotoDataFromAlbumId(album_id)
            return "<p> Liked photo</p> " + render_template('/viewphotos.html', name=name, uid=uid, photos=photo_data, album_id=album_id, album_name=album_name, base64=base64, current_user_id=current_uid)

# END VIEW PHOTOS FOR FRIENDS


# TAG MANAGEMENT
def getTagIdFromTagName(tag_name):
    cursor.execute(
        "SELECT tag_id FROM Tags WHERE tag_name = '{0}'".format(tag_name))
    return cursor.fetchone()[0]


def getTagNameFromTagId(tag_id):
    cursor.execute(
        "SELECT tag_name FROM Tags WHERE tag_id = '{0}'".format(tag_id))
    return cursor.fetchone()[0]


def tagNotInTable(tag_name):
    cursor.execute(
        "SELECT tag_id FROM Tags WHERE tag_name = '{0}'".format(tag_name))
    return cursor.fetchone() == None


def getAllTagsFromUserId(uid):
    cursor.execute(
        "SELECT DISTINCT tag_name FROM Photos, Tags, Tagged WHERE Photos.photo_id = Tagged.photo_id and Tagged.tag_id = Tags.tag_id and Photos.user_id = '{0}'".format(uid))
    return cursor.fetchall()


@app.route('/photosbytag', methods=['GET'])
def photosbytag():
    # if user is logged in
    if flask_login.current_user.is_authenticated:
        current_user_id = getUserIdFromEmail(flask_login.current_user.id)
        # get all tags
        uid = getUserIdFromEmail(flask_login.current_user.id)
        tag_data = getAllTagsFromUserId(uid)
        return render_template('photosbytag.html', tags=tag_data, current_user_id=current_user_id)
    else:
        return render_template('photosbytag.html')


@app.route('/photosbytag', methods=['POST'])
def viewPhotosOfTagId():
    # if user is logged in
    uid = None
    if flask_login.current_user.is_authenticated:
        uid = getUserIdFromEmail(flask_login.current_user.id)
    if request.form.get('view_all'):
        # view all photos by tag name
        print("TEST1")
        tag_name = request.form.get('tag_name')
        my_list = tag_name.split(" ")
        my_quoted_list = ["'{}'".format(x) for x in my_list]
        my_string = ','.join(my_quoted_list)
        formatted_list = '(' + my_string + ')'
        cursor.execute(
            "SELECT imgdata, caption, Photos.photo_id\
                FROM Photos, Tags, Tagged\
                WHERE Photos.photo_id = Tagged.photo_id and Tagged.tag_id = Tags.tag_id and Tags.tag_name IN {0}\
                GROUP BY Photos.photo_id\
                HAVING COUNT(DISTINCT Tags.tag_name) = {1}".format(formatted_list, len(my_list)))
        photo_data = cursor.fetchall()
        photo_data = updatePhotoData(photo_data)

        if len(photo_data) == 0:
            return render_template('photosbytag.html', tags=getAllTagsFromUserId(uid), message="No photos found with the associated tags, please try again")
        return render_template('viewphotos.html', photos=photo_data, tag_name=tag_name, base64=base64, viewall=True)
    elif request.form.get('popular_tag'):
        # view the all tag names of the tags with the most photos
        print("TEST2")
        cursor.execute(
            "SELECT tag_name, COUNT(tag_name) FROM Tags, Tagged WHERE Tags.tag_id = Tagged.tag_id GROUP BY tag_name ORDER BY COUNT(tag_name) DESC LIMIT 3")
        tags = cursor.fetchall()
        return render_template('populartags.html', tags=tags)
    else:
        print("TEST3")
        # view your photos by tag name
        tag_name = request.form.get('tag_name')
        tag_id = getTagIdFromTagName(tag_name)
        cursor.execute(
            "SELECT imgdata, caption, Photos.photo_id FROM Photos\
                INNER JOIN Tagged ON Photos.photo_id = Tagged.photo_id\
                INNER JOIN Users ON Photos.user_id = Users.user_id\
                WHERE tag_id='{0}' and Users.user_id='{1}'".format(tag_id, uid)
        )
        photo_data = cursor.fetchall()
        photo_data = updatePhotoData(photo_data)
        return render_template('viewphotos.html', photos=photo_data, tag_name=tag_name, base64=base64)
    # END TAG MANAGEMENT

# START RECOMMENDATION


@app.route('/friendrecommendation', methods=['GET'])
@flask_login.login_required
def friendRecommendation():
    uid = getUserIdFromEmail(flask_login.current_user.id)

    cursor.execute(
        "SELECT DISTINCT Users.fname, Users.lname, Users.user_id\
            FROM Users, Friendship\
            WHERE Users.user_id = Friendship.UID1 and Friendship.UID2 IN\
                (SELECT UID2\
                    FROM Friendship\
                    WHERE UID1 = '{0}')\
                AND Users.user_id != '{0}'\
            GROUP BY Users.user_id\
            ORDER BY COUNT(DISTINCT Friendship.UID2) DESC".format(uid))
    friends = cursor.fetchall()
    return render_template('friendrecommendation.html', friends=friends)


@app.route('/youmayalsolike', methods=['GET'])
@flask_login.login_required
def youMayAlsoLike():
    uid = getUserIdFromEmail(flask_login.current_user.id)
    cursor.execute(
        "SELECT tag_id\
                FROM (\
                    SELECT tag_id, COUNT(*) AS tag_count\
                    FROM Photos\
                    INNER JOIN Tagged ON Photos.photo_id = Tagged.photo_id\
                    WHERE user_id = {0}\
                    GROUP BY tag_id\
                    ORDER BY tag_count DESC\
                    LIMIT 3\
                ) AS user_tags".format(uid))
    # Gets the top 3 tags of the user
    x = cursor.fetchall()
    user_tag_ids = [row[0] for row in x]
    y = "(" + ','.join(str(tag_id) for tag_id in user_tag_ids) + ")"

    # Gets all distinct photos containing the top 3 tags not including the user's photo
    cursor.execute(
        "SELECT DISTINCT imgdata, caption, Photos.photo_id,  COUNT(*) AS tag_count\
        FROM Photos\
        INNER JOIN Tagged ON Photos.photo_id = Tagged.photo_id\
        WHERE tag_id IN {0} AND user_id != {1}\
        GROUP BY photo_id\
        HAVING COUNT(*) >= 1\
        ORDER BY tag_count DESC, COUNT(DISTINCT tag_id) ASC\
        LIMIT 10".format(y, uid))
    photo_data = cursor.fetchall()
    photo_data = updatePhotoData(photo_data)

    return render_template('youmayalsolike.html', photos=photo_data, base64=base64)

# END RECOMMENDATION
