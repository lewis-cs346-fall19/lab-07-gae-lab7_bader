import webapp2
import MySQLdb
import passwords
import random
import string
import logging
database = "gaeTest"


# pre: assumes the database and passwords.py exist
# post: connects to the database
def connectToDatabase():
    return MySQLdb.connect(unix_socket = passwords.SQL_UNIX_SOCKET, user = passwords.SQL_USER, passwd = passwords.SQL_PASSWD, db = database, charset = "utf8")

# pre: an open connection and an open cursor
# post: commits and closes the connection
def close(cursor, connection):
    cursor.close()
    connection.commit()
    connection.close()

class MainPage(webapp2.RequestHandler):
    # pre: nothing
    # post: loads the main page of the project
    def get(self):
        cookie = self.getCookie()
        name, count, NoNullsFoundInTables = self.getUserFromCookie(cookie)
        if(NoNullsFoundInTables):
            self.response.write("""<!--This is mainInc.html--><!DOCTYPE html><html lang="en"><head>
                                <meta charset="UTF-8"><title>Increment Page</title></head>
                                    <body><div><h2>This is where you can increment a user's count</h2></div>
                                    <div><p>Why hello there {}, how are you today? Your count is {}, isn't that great?</p></div>
                                    <div><br><p> You can go <a href="/userForm">to this form</a> to change the user. You can go <a href="/listUsers"> here to see a list of all users</a> or <a href="/">back to main page</a>, which will  redirect you back to this page....hmm.. By the way your cookie is {}</p></div><br><p>Anyway, here is the form to increment count:</p><br>
                                    <form method="post" action="/incrementHandler"><div><label for="count">Count to increment (or decrement!) by: </label><input id="count" name="count" type="number" required="true" step="1"></div>
                                    <div><input type="submit" id="submit" name="submit" value="Add the specified count to this user!"></div>
                            </form></body></html>""".format(name, count, cookie))

        else:
            self.redirect("/noUser", False)

    # pre: nothing
    # post: gets the cookie in the browser. If cookie does not exist, generates a new cookie and adds it to sessions. Then returns cookie
    def getCookie(self):
        cookie = self.request.cookies.get("sessionID")
        connection = connectToDatabase()
        cursor = connection.cursor()
        if(cookie is None):
            newCookie = "%032x" % random.getrandbits(128)
            self.response.set_cookie("sessionID", newCookie, max_age=20000)
            cookie = newCookie
            cursor.execute("INSERT INTO sessions (id) VALUES (%s)", (cookie,))
        else:
            cursor.execute("INSERT IGNORE INTO sessions (id) VALUES (%s)", (cookie,))
        close(cursor, connection)
        return cookie

    # pre: a cookie
    # post: checks if the cookie exists and if the user associated with cookie exists in table SESSIONS.
        # If the user associated doesn't exist, return ("blank", False)
        # Otherwise check if the user exists and if the name exists in table USERS.
        # If the user does not exist or the name does not exit, return ("blank", False)
        # Otherwise, return (name, True)
    def getName(self, cookie):
        connection = connectToDatabase()
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM sessions WHERE id=%s", (cookie,))
        session = cursor.fetchall()

        if((not (session)) or (not (session[0][1]))):
            close(cursor, connection)
            return ("blank", 0, False)

        userID = session[0][1] # can be sure it exists at this point
        cursor.close()
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM users WHERE id=%s", (userID,))
        user = cursor.fetchall()
        close(cursor, connection)
        if((not (user)) or (not (user[0][1]))):
            return ("blank", 0, False)
        name = user[0][1]  # not needed but for clarity and debugging puposes for now; Also, this definetly exists at this point
        count = user[0][2]
        return (name, count, True)

    # pre: a cookie and maybe a count
    # post: if cookie exists and nothing important is NULL, then maybe update count, then return name, count, and True.
            # Otherwise return ("blank", 0, False)
    def getUserFromCookie(self, cookie, count=0):
        connection = connectToDatabase()
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM sessions WHERE id=%s", (cookie,))
        session = cursor.fetchall()

        if(not session):
            self.response.write("The cookie does not exist in the database")
            close(cursor, connection)
            return ("blank", 0, False)
        if(not session[0][1]):
            self.response.write("The cookie exists but points to NULL")
            close(cursor, connection)
            return ("blank", 0, False)
        userID = session[0][1]
        cursor.execute("SELECT * FROM users WHERE id=%s", (userID,))
        user = cursor.fetchall()

        if(not user):
            self.response.write("The user does not exist in the database users")
            close(cursor, connection)
            return ("blank", 0, False)
        if((not user[0][1])):
            logging.info("The name or count is null")
            close(cursor, connection)
            return ("blank", 0, False)

        if(count != 0):
            cursor.execute("UPDATE users SET count=count + %s WHERE id=%s", (count,userID))
            cursor.execute("SELECT * FROM users WHERE id=%s", (userID,))
            user = cursor.fetchall()

        name = user[0][1]
        count = user[0][2]
        close(cursor, connection)
        return(name, count, True)

class NoUser(webapp2.RequestHandler):
    # pre: nothing
    # post: loads the noUser page of the project
    def get(self):
        cookie = self.getCookie()
        self.response.write("""<!--This is NoUser.html--><!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">
                                <title>There is no user</title></head><body><div><h2>
                                Looks like there is no user in the database</h2></div><div><br><p> You can go
                                <a href="/userForm">to this form</a> or <a href="/">back to main page</a>, which will logically redirect you back to this page....hmm....tough decisions...<br>You can view all users <a href="/listUsers">here</a><br>By the way your cookie is {}</p></div></body></html>""".format(cookie))

    # pre: nothing
    # post: gets the cookie in the browser. If cookie does not exist, generates a new cookie and adds it to sessions. Then returns cookie
    def getCookie(self):
        cookie = self.request.cookies.get("sessionID")
        connection = connectToDatabase()
        cursor = connection.cursor()
        if(cookie is None):
            newCookie = "%032x" % random.getrandbits(128)
            self.response.set_cookie("sessionID", newCookie, max_age=20000)
            cookie = newCookie
            cursor.execute("INSERT INTO sessions (id) VALUES (%s)", (cookie,))
        else:
            cursor.execute("INSERT IGNORE INTO sessions (id) VALUES (%s)", (cookie,))
        close(cursor, connection)
        return cookie

class UserForm(webapp2.RequestHandler):
    # pre: nothing
    # post: loads the create user form
    def get(self):
        self.response.write("""<!--This is UserForm.html--><!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">
                               <title>Form to create a new user or change to another user</title>
                               </head><body><h1>Form to post Course into SQL Database:</h1><br><br><form method="post" action="/changeHandler">
                                <div><label for="name">User name: </label><input id="name" name="name" type="text" required="true"></div>
                                <div><input type="submit" id="submit" name="submit" value="Change to this user, (add if it does not exist)"></div>
                                </form><div><br><p><a href="/">Back to main page</a> or <a href="/listUsers">see all users here.</a></p></div></body></html>""")

class IncrementHandler(webapp2.RequestHandler):
    # pre: a user exists with a cookie
    # post: increments its count
    def post(self):
        if(not (self.request.get("count")) or (not (isinstance(self.request.get("count"), (int, long))))):
            self.response.write("""<!--This is notEnough.html--><!DOCTYPE html><html lang="en">
                                <head><meta charset="UTF-8"><title>Not enough parameters</title></head><body><div><h2>
                                Looks like you didn't give the correct parameters</h2></div><div><br><p> You can go
                                <a href="/">back to the previous form</a> or <a href="/">back to main page</a>
                                </p></div></body></html>""")
        cookie = self.getCookie()
        count = str(self.request.get("count"))
        name, count, NoNullsFoundInTables = self.getUserFromCookie(cookie, count)
        self.redirect("/", False)

    # pre: nothing
    # post: gets the cookie in the browser. If cookie does not exist, generates a new cookie and adds it to sessions. Then returns cookie
    def getCookie(self):
        cookie = self.request.cookies.get("sessionID")
        connection = connectToDatabase()
        cursor = connection.cursor()
        if(cookie is None):
            newCookie = "%032x" % random.getrandbits(128)
            self.response.set_cookie("sessionID", newCookie, max_age=20000)
            cookie = newCookie
            cursor.execute("INSERT INTO sessions (id) VALUES (%s)", (cookie,))
        else:
            cursor.execute("INSERT IGNORE INTO sessions (id) VALUES (%s)", (cookie,))
        close(cursor, connection)
        return cookie

    # pre: a cookie and maybe a count
    # post: if cookie exists and nothing important is NULL, then maybe update count, then return name, count, and True.
            # Otherwise return ("blank", 0, False)
    def getUserFromCookie(self, cookie, count=0):
        connection = connectToDatabase()
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM sessions WHERE id=%s", (cookie,))
        session = cursor.fetchall()

        if(not session):
            self.response.write("The cookie does not exist in the database")
            close(cursor, connection)
            return ("blank", 0, False)
        if(not session[0][1]):
            self.response.write("The cookie exists but points to NULL")
            close(cursor, connection)
            return ("blank", 0, False)
        userID = session[0][1]
        cursor.execute("SELECT * FROM users WHERE id=%s", (userID,))
        user = cursor.fetchall()

        if(not user):
            self.response.write("The user does not exist in the database users")
            close(cursor, connection)
            return ("blank", 0, False)
        if((not user[0][1])):
            logging.info("The name or count is null")
            close(cursor, connection)
            return ("blank", 0, False)

        if(count != 0):
            cursor.execute("UPDATE users SET count=count + %s WHERE id=%s", (count,userID))
            cursor.execute("SELECT * FROM users WHERE id=%s", (userID,))
            user = cursor.fetchall()

        name = user[0][1]
        count = user[0][2]
        close(cursor, connection)
        return(name, count, True)
class AllPeople(webapp2.RequestHandler):
    # pre: a database of users
    # post: shows a table of all users
    def get(self):
        connection = connectToDatabase()
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM users")
        users = cursor.fetchall()
        close(cursor,connection)
        table = """<table><tr><th>ID</th><th>Name</th><th>Count</th></tr>"""
        for user in users:
            table += """<tr><td>{}</td><td>{}</td><td>{}</td></tr>""".format(user[0], user[1], user[2])
        table += """</table>"""
        self.response.write("""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><title>Printing people</title></head><body>{} <br><br> <a href="/" method="get">Back to main page.</a></body></html>""".format(table))

class ChangeHandler(webapp2.RequestHandler):
    # pre: a name as a cgi variable
    # post: creates a user, or changes to it if the name already exists, and redirects to main page.
    def post(self):
        if(not (self.request.get("name"))):
            self.request.write("""<!--This is notEnough.html--><!DOCTYPE html><html lang="en">
                                <head><meta charset="UTF-8"><title>Not enough parameters</title></head><body><div><h2>
                                Looks like you didn't give enough parameters</h2></div><div><br><p> You can go
                                <a href="/userForm">back to the previous form</a> or <a href="/">back to main page</a>
                                </p></div></body></html>""")
            return
        cookie = self.getCookie()
        name = string.capwords(str(self.request.get("name")).lower(), sep = None)
        connection = connectToDatabase()
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM users WHERE name=%s", (name,))
        results = cursor.fetchall()
        cursor.close()
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM sessions WHERE id=%s", (cookie,))
        session = cursor.fetchall()

        if(session and results):
            cursor.execute("UPDATE sessions SET user=%s WHERE id=%s", (results[0][0],cookie)) # userID, cookie
        elif(session and (not results)):
            cursor.execute("INSERT INTO users (name) VALUES (%s)", (name,))
            newID = cursor.lastrowid
            cursor.execute("UPDATE sessions SET user=%s WHERE id=%s", (newID,cookie))
        elif((not session) and results):
            cursor.execute("INSERT INTO sessions (id, user) VALUES (%s,%s)", (cookie,results[0][0]))
        else:
            cursor.execute("INSERT INTO users (name) VALUES (%s)", (name,))
            newID = cursor.lastrowid
            cursor.execute("INSERT INTO sessions (id, user) VALUES (%s,%s)", (cookie, newID))


        # cursor.execute("INSERT IGNORE INTO users (name) VALUES (%s)", (name,))
        # cursor.execute("SELECT * FROM users WHERE name=%s",())
        # cursor.execute("INSERT IGNORE ")
        close(cursor, connection)
        self.redirect("/", False)

    # This is a duplicate because I can't make getCookie static nor can I call MainPage's, so ask about this later
    # pre: nothing
    # post: gets the cookie in the browser. If cookie does not exist, generates a new cookie and adds it to sessions. Then returns cookie
    def getCookie(self):
        cookie = self.request.cookies.get("sessionID")
        connection = connectToDatabase()
        cursor = connection.cursor()
        if(cookie is None):
            newCookie = "%032x" % random.getrandbits(128)
            self.response.set_cookie("sessionID", newCookie, max_age=20000)
            cookie = newCookie
            cursor.execute("INSERT INTO sessions (id) VALUES (%s)", (cookie,))
        else:
            cursor.execute("INSERT IGNORE INTO sessions (id) VALUES (%s)", (cookie,))
        close(cursor, connection)
        return cookie

app = webapp2.WSGIApplication([ ("/", MainPage), ("/noUser", NoUser), ("/userForm", UserForm), ("/changeHandler",ChangeHandler), ("/incrementHandler", IncrementHandler), ("/listUsers",AllPeople),], debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
