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
		cursor.execute('INSERT INTO Albums (user_id, name, date_of_creation) VALUES (%s, %s, NOW())' ,(uid,name))
		conn.commit()
		return render_template('hello.html', name=flask_login.current_user.id, message='Album Created!', albums=getUsersAlbums(uid))
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
		return render_template('/browse.html', albums=getUsersAlbums(uid),action="/browseAlbum")

@app.route('/browsePublicAlbums', methods=['GET', 'POST'])
def browsePublicAlbum():
	if request.method == 'POST':
		album_id = request.form.get('album')
		return render_template('/albumImages.html', album=getAlbumName(album_id)[0][0], photos=getPhotoAlbum(album_id), base64=base64)
	else:
		return render_template('/browse.html', albums=getAlbums(), action="/browsePublicAlbums")

def getUsersAlbums(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT name, date_of_creation, album_id FROM Albums WHERE user_id = '{0}'".format(uid))
	return cursor.fetchall() #NOTE list of tuples, [(imgdata, pid), ...]

def getAlbums():
	cursor = conn.cursor()
	cursor.execute("SELECT name, date_of_creation, album_id FROM Albums")
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
	cursor.execute( query )
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
	cursor.execute(query)
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
	cursor.execute( "SELECT * FROM has_friends WHERE user1='{0}' AND user2='{1}'".format( u1, u2 ) )

	if not cursor.fetchall():
		return 0	
	return 1

#Get list of all users on the site except for the currently logged in user
def getUserList_notself( user_id ):
	print( "IN getUserList_notself FUNCTION" )
	cursor = conn.cursor()
	query = "SELECT email FROM Users WHERE user_id != {0}".format(user_id)
	cursor.execute(query)
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
	#print( "IN getDBQuery FUNCTION" )
	cursor = conn.cursor()
	cursor.execute( query )
	result = cursor.fetchall()
	conn.commit()
	return result


def getUserTags( user_id ):
	print( "IN getUserTags FUNCTION" )
	# First get list of user's photo's ids
	query = "SELECT DISTINCT T.tag_label FROM Pictures P INNER JOIN has_tag T ON P.picture_id = T.picture_id INNER JOIN Users U ON P.user_id = U.user_id WHERE U.user_id = \"{0}\"".format( user_id )
	vals = getDBQuery( query )
	tags = []
	for i in vals:
		tags.append( i[0] )
	print( tags )
	return tags


def getAllTags():
	vals = getDBQuery( "SELECT * FROM Tags;" )
	tags = []
	for i in vals:
		tags.append( i[0] ) 
	print( tags )
	return tags

@app.route("/browsetags", methods=['GET'])
@flask_login.login_required
def browsetags():
	user_id = getUserIdFromEmail(flask_login.current_user.id)
	return render_template( 'browsetags.html', user_tags=getUserTags(user_id), all_tags=getAllTags() )

def getPhotoData( user_id ):
	#print( "IN getPhotoData FUNCTION" )
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
@flask_login.login_required
def addtags():
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


## Get the picture data -> returns a tuple of the form ( tag, list of picture data that has tag )
def getPhotosWithTag( tag ):	
	return ( tag, getDBQuery( "SELECT P.imgdata, P.picture_id, P.caption, T.tag_label FROM Pictures P INNER JOIN has_tag T ON P.picture_id = T.picture_id AND T.tag_label = \"{0}\"".format( tag ) ) )

# Renders showTagPhotos.html with all the photos that 
# 	have the associated tag specified in the url by 
# 	the 'tag' variable
@app.route("/<prevpage>/showtagphotos/<tag>", methods=['GET'] )
def showTagPhotos( prevpage, tag ):
	return render_template( 'showTagPhotos.html', prev_page=prevpage, photo_list=getPhotosWithTag( tag ), base64=base64 )

def getMostPopularTags():
    #Generate list of the most popular tags ( make list of 10 tags ) on the website
    cursor = conn.cursor()
    cursor.execute("SELECT tag_label, COUNT(*) AS tagCount FROM has_tag GROUP BY tag_label ORDER BY tagCount DESC")
    return cursor.fetchmany(size=10)

def getMostPopularTags1():
	#Generate list of the most popular tags ( make list of 10 tags ) on the website
	cursor = conn.cursor()
	cursor.execute("SELECT tag_label, COUNT(*) AS tagCount FROM has_tag GROUP BY tag_label ORDER BY tagCount DESC")
	return cursor.fetchmany(size=10)

# End Tags Code

# Search Photos by Tag code
@app.route( "/browsePhotosByTag", methods=['GET', 'POST'] )
def browsePhotosByTags():
	print( "Now in browsePhotosByTags() function!" )
	if request.method == 'POST':	# If post, get the tags from form, Query DB for all photos
		tags = request.form.get('tags')
		print( tags )
		tags = (tags.strip()).split( " " )	# Get all tags by using delimiters
		
		# Run query to get all images associated with all tags
		# Construct query to contain all the tags retrieved from the form.
		query = "SELECT DISTINCT P.imgdata, P.picture_id, P.caption FROM Pictures P INNER JOIN has_tag ON P.picture_id = has_tag.picture_id WHERE"
		for i in range( 0, len(tags) ):
			query = query + " has_tag.tag_label=\"{0}\"".format( tags[i] )
			if i != len(tags)-1:
				query = query + " OR "
		
		photo_list = getDBQuery( query )
		return render_template( 'browsePhotosByTags.html', photo_list=photo_list, base64=base64 )

	return render_template( 'browsePhotosByTags.html' )

def getFriendsOfFriendsList( user_id ):
	query = '''SELECT DISTINCT
					Users.email, Users.first_name, Users.last_name
					FROM 
						Users, has_friends, (SELECT U2.user_id FROM Users U2, (SELECT * FROM has_friends WHERE user1=2 OR user2={0}) AS frnds WHERE (U2.user_id=frnds.user1 AND frnds.user2 = {0}) or (U2.user_id=frnds.user2 AND frnds.user1 = {0})) AS frnds
					WHERE 
						( has_friends.user1 = frnds.user_id ) 
						or 
						( has_friends.user2 = Users.user_id )'''.format( user_id )
	frndOfFrnds = getDBQuery( query )

	frnds = getDBQuery( ''' 
							SELECT 
								Users.email, Users.first_name, Users.last_name 
								FROM 
									Users, (SELECT * FROM has_friends WHERE user1={0} OR user2=8) AS frnds 
								WHERE 
									(Users.user_id=frnds.user1 AND frnds.user2 = {0} ) 
									or 
									(Users.user_id=frnds.user2 AND frnds.user1 = {0} )'''.format( user_id ) )
	
	result = []
	for i in frndOfFrnds:
		result.append( i )
		for j in frnds:
			if i[0] == j[0]:
				result.remove( i )
	return result


def getPhoto(picture_id):
	cursor = conn.cursor()
	cursor.execute("SELECT imgdata, picture_id, caption, user_id, likes FROM Pictures WHERE picture_id = '{0}'".format(picture_id))
	return cursor.fetchone() #NOTE list of tuples, [(imgdata, pid), ...]

@app.route('/photo/<int:num>', methods=['GET', 'POST'])
def photo(num):
	if (flask_login.current_user.is_authenticated):
		uid = getUserIdFromEmail(flask_login.current_user.id)
	picture_id = num
	if request.method == 'POST':
		if (request.form['submit'] == 'Like'):
			cursor = conn.cursor()
			cursor.execute('INSERT INTO has_likes (picture_id, user_id) VALUES (%s, %s)' ,(picture_id, uid))
			cursor.execute("UPDATE Pictures SET likes = likes + 1 WHERE picture_id = '{0}'".format(picture_id))
			conn.commit()
			return flask.redirect(request.path)
		elif (request.form['submit'] == 'Unlike'):
			cursor = conn.cursor()
			cursor.execute("DELETE FROM has_likes WHERE user_id = '{0}' AND picture_id = '{1}'".format(uid, picture_id))
			cursor.execute("UPDATE Pictures SET likes = likes - 1 WHERE picture_id = '{0}'".format(picture_id))
			conn.commit()
			return flask.redirect(request.path)
		elif (request.form['submit'] == 'Comment'):
			comment = request.form.get('comment')
			cursor = conn.cursor()
			if (flask_login.current_user.is_authenticated):
				cursor.execute("INSERT INTO Comments (comment, user_id, picture_id, date) VALUES (%s, %s, %s, NOW())", (comment, uid, picture_id))
				cursor.execute("UPDATE Users SET contributions = contributions + 1 WHERE user_id = '{0}'".format(uid))
				conn.commit()
				return flask.redirect(request.path)
			else:
				cursor.execute("INSERT INTO Comments (comment, user_id, picture_id, date) VALUES (%s, NULL, %s, NOW())", (comment, picture_id))
				conn.commit()
				return flask.redirect(request.path)

	else:
		if (flask_login.current_user.is_authenticated):
			return render_template('/photo.html', photo=getPhoto(picture_id), base64=base64, uid=uid, liked=getLikedUsers(picture_id), button=didUserLike(uid, picture_id), comments=getComments(picture_id))
		else:
			return render_template('/photo.html', photo=getPhoto(picture_id), base64=base64, liked=getLikedUsers(picture_id),comments=getComments(picture_id))

def getComments(picture_id):
	cursor = conn.cursor()
	cursor.execute("SELECT comment, date, user_id FROM Comments WHERE picture_id = '{0}' ORDER BY date ASC".format(picture_id))
	return cursor.fetchall()

def didUserLike(user_id, picture_id):
	cursor = conn.cursor()
	cursor.execute("SELECT hl.user_id FROM has_likes hl WHERE hl.user_id = '{1}' AND hl.picture_id = '{0}'".format(picture_id, user_id))
	length = len(cursor.fetchall()) #NOTE list of tuples, [(imgdata, pid), ...]
	if (length == 1):
		return False
	else:
		return True

def getLikedUsers(picture_id):
	cursor = conn.cursor()
	cursor.execute("SELECT u.user_id, u.first_name, u.last_name FROM Users u, has_likes hl WHERE hl.user_id = u.user_id AND hl.picture_id = '{0}'".format(picture_id))
	return cursor.fetchall() #NOTE list of tuples, [(imgdata, pid), ...]

#default page
@app.route("/", methods=['GET', 'POST'])
def hello():
	if request.method == 'POST':
		query = request.form.get('cSearch')
		return render_template('comments.html', comments=getCSearch(query), text=query)
	else:	
		if (flask_login.current_user.is_authenticated):
			uid = getUserIdFromEmail(flask_login.current_user.id)
			return render_template('hello.html', message='Welcome to Photoshare', contributions=getUserContributions(), popular_tags=getMostPopularTags(), uid=uid, likeRecommendation=likeRecommendation(uid), friend_recommendations=getFriendsOfFriendsList(uid))
		else:
			return render_template('hello.html', message='Welcome to Photoshare', contributions=getUserContributions(), popular_tags=getMostPopularTags())

def getCSearch(text):
	cursor = conn.cursor()
	cursor.execute("select u.first_name, u.last_name, count(*), u.user_id from Users u, Comments c where c.comment = '{0}' and c.user_id = u.user_id GROUP BY user_id ORDER BY count(*) DESC".format(text))
	return cursor.fetchall()

def likeRecommendation(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT temp.picture_id, temp.user_id, count(temp.picture_id) from (SELECT * from Pictures WHERE user_id != '{0}') temp, has_tag h WHERE h.picture_id = temp.picture_id AND h.tag_label IN (select t.tag_label from (SELECT t.tag_label FROM Users u, Pictures p, has_tag t WHERE u.user_id = p.user_id and p.picture_id = t.picture_id and p.user_id = '{0}' GROUP by t.tag_label ORDER BY Count(t.tag_label) DESC  LIMIT 5) t) GROUP BY temp.picture_id ORDER BY count(temp.picture_id) DESC ".format(uid))
	return cursor.fetchall()

if __name__ == "__main__":
	#this is invoked when in the shell  you run
	#$ python app.py
	app.run(port=5000, debug=True)
