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
from flask import Flask, Response, request, render_template, redirect, url_for, flash
from flaskext.mysql import MySQL
import flask_login

#for image uploading
import os, base64

mysql = MySQL()
app = Flask(__name__)
app.secret_key = 'super secret string'  # Change this!

#These will need to be changed according to your creditionals
app.config['MYSQL_DATABASE_USER'] = 'root'

with open('password.txt') as f:
    content = f.readlines()
password = content[0]
app.config['MYSQL_DATABASE_PASSWORD'] = password

app.config['MYSQL_DATABASE_DB'] = 'photoshare'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)

#begin code used for login
login_manager = flask_login.LoginManager()
login_manager.init_app(app)

conn = mysql.connect()
cursor = conn.cursor()
cursor.execute("SELECT email from Users")
users = cursor.fetchall()

def getUserList():
	cursor = conn.cursor()
	cursor.execute("SELECT email from Users")
	return cursor.fetchall()

class User(flask_login.UserMixin):
	pass

@login_manager.user_loader
def user_loader(email):
	users = getUserList()
	if not(email) or email not in str(users):
		return
	user = User()
	user.id = email
	return user

@login_manager.request_loader
def request_loader(request):
	users = getUserList()
	email = request.form.get('email')
	if not(email) or email not in str(users):
		return
	user = User()
	user.id = email
	cursor = mysql.connect().cursor()
	cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email))
	data = cursor.fetchall()
	pwd = str(data[0][0] )
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
	#The request method is POST (page is recieving data)
	email = flask.request.form['email']
	cursor = conn.cursor()
	#check if email is registered
	if cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email)):
		data = cursor.fetchall()
		pwd = str(data[0][0] )
		if flask.request.form['password'] == pwd:
			user = User()
			user.id = email
			flask_login.login_user(user) #okay login in user
			return flask.redirect(flask.url_for('protected')) #protected is a function defined in this file

	#information did not match
	return "<a href='/login'>Try again</a>\
			</br><a href='/register'>or make an account</a>"

@app.route('/logout')
def logout():
	flask_login.logout_user()
	return render_template('hello.html', message='Logged out')

@login_manager.unauthorized_handler
def unauthorized_handler():
	return render_template('unauth.html')

#you can specify specific methods (GET/POST) in function header instead of inside the functions as seen earlier
@app.route("/register", methods=['GET'])
def register():
	return render_template('register.html', supress=True)

@app.route("/register", methods=['GET','POST'])
def register_user():
	try:
		email=request.form.get('email')
		password=request.form.get('password')
		first_name=request.form.get('first_name')
		last_name=request.form.get('last_name')
		hometown=request.form.get('hometown')
		gender=request.form.get('gender')
		date_of_birth=request.form.get('date_of_birth')
	except:
		print("couldn't find all tokens") #this prints to shell, end users will not see this (all print statements go to shell)
		return flask.redirect(flask.url_for('register'))
	cursor = conn.cursor()
	test =  isEmailUnique(email)
	if test:
		print(cursor.execute("INSERT INTO Users (email, first_name, last_name, password, date_of_birth, hometown, gender) VALUES ('{0}', '{1}','{2}', '{3}','{4}', '{5}','{6}')".format(email, first_name, last_name, password, date_of_birth, hometown, gender)))
		conn.commit()
		#log user in
		user = User()
		user.id = email
		flask_login.login_user(user)
		return render_template('hello.html', name=email, message='Account Created!')
	else:
		print("couldn't find all tokens")
		flash('That email is already taken.')
		return flask.redirect(flask.url_for('register'))

def getUsersPhotos(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT imgdata, picture_id, caption FROM Pictures WHERE user_id = '{0}'".format(uid))
	return cursor.fetchall() #NOTE list of tuples, [(imgdata, pid), ...]

def getUserIdFromEmail(email):
	cursor = conn.cursor()
	cursor.execute("SELECT user_id  FROM Users WHERE email = '{0}'".format(email))
	return cursor.fetchone()[0]

def isEmailUnique(email):
	#use this to check if a email has already been registered
	cursor = conn.cursor()
	if cursor.execute("SELECT email  FROM Users WHERE email = '{0}'".format(email)):
		#this means there are greater than zero entries with that email
		return False
	else:
		return True
#end login code

def isAlbumUnique(album):
	if cursor.execute("SELECT name FROM Albums WHERE name = '{0}'".format(album)):
		return False
	else:
		return True

@app.route('/profile')
@flask_login.login_required
def protected():
	return render_template('hello.html', name=flask_login.current_user.id, message="Here's your profile", albums=getUsersAlbums(getUserIdFromEmail(flask_login.current_user.id)))

#begin photo uploading code
# photos uploaded using base64 encoding so they can be directly embeded in HTML
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['GET', 'POST'])
@flask_login.login_required
def upload_file():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	if request.method == 'POST':
		album_id = request.form.get("album");
		imgfile = request.files['photo']
		caption = request.form.get('caption')
		photo_data =imgfile.read()
		cursor = conn.cursor()
		cursor.execute('INSERT INTO Pictures (imgdata, user_id, caption, album_id) VALUES (%s, %s, %s, %s)' ,(photo_data,uid, caption, album_id))
		cursor.execute("UPDATE Users SET contributions = contributions + 1 WHERE user_id = '{0}'".format(uid))
		conn.commit()
		return render_template('hello.html', name=flask_login.current_user.id, message='Photo uploaded to album!')
	#The method is GET so we return a  HTML form to upload the a photo.
	else:
		return render_template('upload.html', albums=getUsersAlbums(uid))
#end photo uploading code

@app.route('/browsePhotos', methods=['GET'])
@flask_login.login_required
def browse_photos():
		uid = getUserIdFromEmail(flask_login.current_user.id)
		return render_template('hello.html', name=flask_login.current_user.id, photos=getUsersPhotos(uid),base64=base64)

def getAllPhotos():
	cursor = conn.cursor()
	cursor.execute("SELECT imgdata, picture_id, caption FROM Pictures")
	return cursor.fetchall() #NOTE list of tuples, [(imgdata, pid), ...]

@app.route('/browsePublic', methods=['GET'])
def browse_public():
		return render_template('hello.html', photos=getAllPhotos(),base64=base64)

 
@app.route('/createAlbum', methods=['GET', 'POST'])
@flask_login.login_required
def create_album():
	if request.method == 'POST':
		uid = getUserIdFromEmail(flask_login.current_user.id)
		name = request.form.get('name')
		cursor = conn.cursor()
		test =  isAlbumUnique(name)
		if (test):
			cursor.execute('INSERT INTO Albums (user_id, name, date_of_creation) VALUES (%s, %s, NOW())' ,(uid,name))
			conn.commit()
			return render_template('hello.html', name=flask_login.current_user.id, message='Album Created!', albums=getUsersAlbums(uid))
		else:
			return flask.redirect(flask.url_for('create_album'))
	else:
		return render_template('/create.html')

@app.route('/deleteAlbum', methods=['GET', 'POST'])
@flask_login.login_required
def delete_album():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	if request.method == 'POST':
		album_id = request.form.get('album')
		cursor = conn.cursor()
		cursor.execute("DELETE FROM Albums WHERE album_id = '{0}'".format(album_id))
		conn.commit()
		return render_template('hello.html', name=flask_login.current_user.id, message='Album deleted!', albums=getUsersAlbums(uid))
	else:
		return render_template('/delete.html', albums=getUsersAlbums(uid))

def getPhotoAlbum(album_id):
	cursor = conn.cursor()
	cursor.execute("SELECT imgdata, picture_id, caption FROM Pictures WHERE album_id = '{0}'".format(album_id))
	return cursor.fetchall()

def getAlbumName(album_id):
	cursor = conn.cursor()
	cursor.execute("SELECT name FROM Albums WHERE album_id = '{0}'".format(album_id))
	return cursor.fetchall()

@app.route('/browseAlbum', methods=['GET', 'POST'])
@flask_login.login_required
def browse_Album():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	if request.method == 'POST':
		album_id = request.form.get('album')
		return render_template('/albumImages.html', name=flask_login.current_user.id, album=getAlbumName(album_id)[0][0], photos=getPhotoAlbum(album_id), base64=base64)
	else:
		return render_template('/browse.html', albums=getUsersAlbums(uid))

def getUsersAlbums(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT name, date_of_creation, album_id FROM Albums WHERE user_id = '{0}'".format(uid))
	return cursor.fetchall() #NOTE list of tuples, [(imgdata, pid), ...]


# Gets the top 10 user contributions in descending order so we can display them
def getUserContributions():
	cursor = conn.cursor()
	cursor.execute("SELECT first_name, last_name, contributions FROM Users ORDER BY contributions DESC")
	return cursor.fetchmany(size=10)


# Begin Search+Add Friends Code
def getEmailFromId( id ):
	print( "IN getEmailFromId function" )
	cursor = conn.cursor()
	query = "SELECT email FROM Users WHERE user_id={0};".format( id )
	try:
		cursor.execute( query )
	except (MySQLdb.Error, MySQLdb.Warning) as e:
		print( e )
		return None
	vals = cursor.fetchall()
	conn.commit()
	return vals[0][0]

def convertTuplesToEmails( tups, userid ):
	result = []
	for i in tups:
		user1 = i[0]
		user2 = i[1]
		email = user1 if user1 != userid else user2
		result.append( getEmailFromId( email ) )
	
	return result

def getFriendsList( user_id ):
	print( "IN getFriendsList FUNCTION" )
	print(user_id)
	cursor = conn.cursor()
	query = "SELECT * FROM has_friends WHERE user1={0} OR user2={1}".format(user_id, user_id)
	try:
		cursor.execute(query)
	except (MySQLdb.Error, MySQLdb.Warning) as e:
		print( e )
		return None

	vals = cursor.fetchall()
	conn.commit()
	result = []
	for i in range( 0, len(vals) ):
		result.append( vals[i] )
	result = convertTuplesToEmails( result, user_id )

	return result

def checkFriendExists( u1, u2 ):
	cursor = conn.cursor()
	print( "Checking that friends '{0}' and '{1}' exist:".format( u1, u2 ) )
	try:
		cursor.execute( "SELECT * FROM has_friends WHERE user1='{0}' AND user2='{1}'".format( u1, u2 ) )
	except (MySQLdb.Error, MySQLdb.Warning) as e:
		print( e )
		return None

	if not cursor.fetchall():
		return 0	
	return 1

#Get list of all users on the site except for the currently logged in user
def getUserList_notself( user_id ):
	print( "IN getUserList_notself FUNCTION" )
	cursor = conn.cursor()
	query = "SELECT email FROM Users WHERE user_id != {0}".format(user_id)
	try:
		cursor.execute(query)
	except (MySQLdb.Error, MySQLdb.Warning) as e:
		print( e )
		return None
	vals = cursor.fetchall()
	conn.commit()
	result = []
	for i in range(0,len(vals)):
		x = vals[ i ][0]
		result.append(x)

	return result

#Add friend to user's account
@app.route("/profile", methods=['POST'])
def add_friend():
	print( "IN add_friend FUNCTION" )
	try:
		email_fr = request.form.get('add-friend-button')
	except:
		print("couldn't find all tokens") #this prints to shell, end users will not see this (all print statements go to shell)
		return flask.redirect(flask.url_for('profile'))

	print( "email_fr: " + email_fr )
	cursor = conn.cursor()
	user = User()
	userid = getUserIdFromEmail(flask_login.current_user.id)
	friendid = getUserIdFromEmail(email_fr)
	msg = ''
	if not checkFriendExists( userid, friendid ):
		print(cursor.execute("INSERT INTO has_friends (user1, user2) VALUES ('{0}', '{1}')".format(userid, friendid)))
		msg = 'You have added ' + email_fr + ' to your list of friends!'
	else:
		msg = 'You already have ' + email_fr +' in your list of friends.'

	conn.commit()
	
	return render_template( 'friends.html', 
	users=getUserList_notself( userid ),
	friends=getFriendsList( getUserIdFromEmail(flask_login.current_user.id) ),
	message=msg 
	)
	
#Need to add checking for when user is already your friend

@app.route("/friends", methods=['GET'])
def friends():
	return render_template('friends.html', 
	users=getUserList_notself(getUserIdFromEmail(flask_login.current_user.id)),
	friends=getFriendsList( getUserIdFromEmail(flask_login.current_user.id) )
	)

# END Search+Add Friends Code

# BEGIN Tags Code

def getDBQuery( query ):
	print( "IN getDBQuery FUNCTION" )
	cursor = conn.cursor()
	try:
		cursor.execute( query )
	except (MySQLdb.Error, MySQLdb.Warning) as e:
		print( e )
		return None
	result = cursor.fetchall()
	conn.commit()
	return result


def getUserTags( user_id ):
	print( "IN getUserTags FUNCTION" )
	# First get list of user's photo's ids
	photo_ids = getDBQuery( "SELECT picture_id FROM Pictures WHERE user_id={0}".format( user_id) )
	print( photo_ids )
	# Second get list of tags from has_tags where photo_id is in photo's ids
	result = []
	#for i in photo_ids:
	return ['test_user_tag']


def getAllTags():
	vals = getDBQuery( "SELECT * FROM Tags;" )
	tags = []
	for i in vals:
		tags.append( i[0] ) 
	print( tags )
	return tags

@app.route("/browsetags", methods=['GET'])
def browsetags():
	user_id = getUserIdFromEmail(flask_login.current_user.id)
	return render_template( 'browsetags.html', user_tags=getUserTags(user_id), all_tags=getAllTags() )

def getPhotoData( user_id ):
	print( "IN getPhotoData FUNCTION" )
	return getDBQuery( "SELECT picture_id, caption FROM Pictures WHERE user_id={0}".format(user_id) )

def tagExists( taglabel ):
	result = getDBQuery( "SELECT * FROM Tags WHERE tag_label='{0}'".format(taglabel) )
	if not result:
		return False
	return True

def createTag( taglabel ):
	getDBQuery( "INSERT INTO Tags ( tag_label ) VALUES ('{0}')".format(taglabel) )

def photoHasTag( photo_id, taglabel ):
	if not getDBQuery( "SELECT * FROM has_tag WHERE picture_id={0} AND tag_label='{1}'".format( photo_id, taglabel ) ):
		return False
	return True

def addTagToPhoto( photo_id, taglabel ):
	getDBQuery( "INSERT INTO has_tag ( picture_id, tag_label ) VALUES ( {0}, '{1}' )".format( photo_id, taglabel ) )

@app.route("/addtags", methods=['GET','POST'])
def addtags():
	print( "Hello!" )
	user_id = getUserIdFromEmail(flask_login.current_user.id)
	if request.method == 'POST':
		photo_id = request.form.get('photo')
		taglabel = request.form.get('taglabel')
		print( photo_id )
		print( taglabel )
		#Check if tag exists
		if not tagExists( taglabel ): # if not, create it
			print( "Tag does not exist." )
			#Create tag!
			createTag( taglabel )
		
		#Check if photo already has tag
		if photoHasTag( photo_id, taglabel ):
			print( "Photo already has tag!" )
			return render_template( 'tags.html', 
			photos=getPhotoData( user_id ),
			message="This photo already has that tag!" )
		else:
			print( "Photo does not have this tag yet!" )
			addTagToPhoto( photo_id, taglabel )
			return render_template( 'tags.html', 
			photos=getPhotoData( user_id ),
			message="Tag successfully added!" )
		# If yes, send message to user saying photo already has this tag
		# If not, add tag to photo and send success message to user
		

	return render_template( 'tags.html', photos=getPhotoData( user_id ) )

# End Tags Code


#default page
@app.route("/", methods=['GET'])
def hello():
	return render_template('hello.html', message='Welecome to Photoshare', contributions=getUserContributions())

if __name__ == "__main__":
	#this is invoked when in the shell  you run
	#$ python app.py
	app.run(port=5000, debug=True)
