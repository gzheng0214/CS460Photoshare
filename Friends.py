from flask import Blueprint, render_template

friendapp = Blueprint( 'Friends', __name__ )

def getUserIdFromEmail(email):
	cursor = conn.cursor()
	cursor.execute("SELECT user_id  FROM Users WHERE email = '{0}'".format(email))
	return cursor.fetchone()[0]

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
	result = []
	for i in range(0,len(vals)):
		x = vals[ i ][0]
		result.append(x)

	return result

#Add friend to user's account
@friendapp.route("/profile", methods=['POST'])
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

@friendapp.route("/friends", methods=['GET'])
def friends():
	return render_template('friends.html', 
	users=getUserList_notself(getUserIdFromEmail(flask_login.current_user.id)),
	friends=getFriendsList( getUserIdFromEmail(flask_login.current_user.id) )
	)

# END Search+Add Friends Code