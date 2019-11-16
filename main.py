import webapp2
import MySQLdb
import passwords
import random
database = "gaeTest"
class MainPage(webapp2.RequestHandler):
        # pre: nothing
        # post: loads the main page of the project
        def get(self):
            cookie = self.request.cookies.get("sessionID")
            if(cookie is None):
                self.response.write("New cookie generated")
                self.response.set_cookie("sessionID", "%032x" % random.getrandbits(128), max_age=20000)

                # self.redirect("/NoCookie", True) # the parameter is a boolean indicating permanence
            cookie = self.request.cookies.get("sessionID")
            self.response.write("You have a cookie! The cookie is: {}<br>".format(cookie))
            results = self.getResults(cookie)

            if(not (results)):
                #self.response.write("The user ID associated with cookie {} is null<br>".format(cookie))
                self.redirect("/noUser", False)
            else:
                self.response.write("The user ID associated with cookie {} is {}<br>".format(cookie, results[0][1]))


        # pre: assumes the database and passwords.py exist
        # post: connects to the database
        def connectToDatabase(self):
            return MySQLdb.connect(unix_socket = passwords.SQL_UNIX_SOCKET, user = passwords.SQL_USER, passwd = passwords.SQL_PASSWD, db = database, charset = "utf8")

        # pre: an open connection
        # post: commits and closes the connection
        def close(self, connection):
            connection.commit()
            connection.close()

        # pre: a cookie's value
        # post: returns the cookies from the database with that value
        def getResults(self, cookie):
            connection = self.connectToDatabase()
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM sessions WHERE id=%s", (cookie,))
            results = cursor.fetchall()
            cursor.close()
            self.close(connection)
            return results


        # def get(self):
        #     connection = MySQLdb.connect(unix_socket = passwords.SQL_UNIX_SOCKET, user = passwords.SQL_USER, passwd = passwords.SQL_PASSWD, db = database, charset = "utf8")
        #     cursor = connection.cursor()
        #     cursor.execute("SELECT * FROM l7")
        #     results = cursor.fetchall()
        #     cursor.close()
        #     connection.commit()
        #     connection.close()
        #
        #     self.response.headers["Content-Type"] = "text/html"
        #     self.response.set_cookie("sessionID", "%032x" % random.getrandbits(128), max_age=20000)
        #     self.response.write("Hello world")
        #     self.response.write(results)
class NoUser(webapp2.RequestHandler):
    # pre: nothing
    # post: loads the noUser page of the project
    def get(self):
        self.response.write("""<!--This is NoUser.html--><!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">
                                <title>There is no user</title></head><body><div><h2>
                                Looks there is no user in the database</h2></div><div><br><p> You can go
                                <a href="/userForm">to this form</a> or <a href="/">back to main page</a>, which will logically redirect you back to this page....hmm....tough decision</p></div></body></html>""")
app = webapp2.WSGIApplication([ ("/", MainPage), ("/noUser", NoUser),], debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
