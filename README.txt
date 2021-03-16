To get the skeleton running, open a terminal and do the following:
	1. enter the skeleton folder 'cd path/to/skeleton'
	2. install all necessary packages 'pip install -r requirements.txt' (or use pip3)
	3. export flask (Mac, Linux)'export FLASK_APP=app.py', (Windows)'set FLASK_APP=app.py'

	4. run schema.sql using MySQL Workbench
	5. open app.py using your favorite editor, change #PASSWORD in 'app.config['MYSQL_DATABASE_PASSWORD'] = '#PASSWORD'' to your MySQL root password

	6. back to the terminal, run the app 'python -m flask run' (or use python3)
	7. open your browser, and open the local website 'localhost:5000'
	
NOTE: For the #PASSWORD to the mysql database, we create a 'password.txt' file that the app.py accesses to get 
        the password for the database. That way, we could use different passwords on our machines as specified by the 
        password.txt and not have to share our passwords between eachother.

For graders, please create a password.txt file in the same directory as the app.py file that has your database's 
        password and nothing else in it ( ideally, no new lines, spaces, or anything like that ). If this does
        not work, you can email us ( Michael: mra88@bu.edu ), or you can always just change the #PASSWORD in app.py manually.
