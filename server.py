from flask import Flask, render_template, request, redirect, session, flash
from mysqlconnection import connectToMySQL
from flask_bcrypt import Bcrypt
import re
import datetime
app = Flask(__name__)
app.secret_key = 'keep it secret, keep it safe'
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')
bcrypt = Bcrypt(app)
# Register and login page
@app.route('/')
def reg_sign():
    return render_template("reg_sign.html")

# Register
@app.route("/register", methods=["POST"])
def add_new_user():
    is_valid = True
    # first_name
    if len(request.form['fname']) < 2:
        is_valid = False
        flash("First name must contain at least two letters and contain only letters", 'fnError1')
    # last_name
    if len(request.form['lname']) < 2:
        is_valid = False
        flash("Last name must contain at least two letters and contain only letters", 'lnError1')
    # email
    if not EMAIL_REGEX.match(request.form['email']):
        is_valid = False
        flash("Invalid Email Address", 'emailError1')
    # password
    if len(request.form['password']) < 1:
        is_valid = False
        flash("Password must contain a number, a capital letter, and be between 8-15 characters", 'passwordError1')
    # confirm password
    if len(request.form['cofirmPassword']) < 1:
        is_valid = False
        flash("This field is required!", 'coPasswordError1')
    elif request.form['password'] != request.form['cofirmPassword'] :
        is_valid = False
        flash("Password must match", 'coPasswordError1')
    if not is_valid:
        return redirect('/')
    else:
        # session['name] using for custmize html and tracking user
        session['name']=request.form['fname']
        flash("You've been succesfully registered!")
        pw_hash = bcrypt.generate_password_hash(request.form['password']) 
        mysql = connectToMySQL('jobs')
        query = "INSERT INTO users(first_name, last_name, email, password, created_at, updated_at) VALUES (%(fn)s, %(ln)s, %(ema)s, %(ps)s, NOW(), NOW());"
        data = {
            'fn':request.form['fname'],
            'ln':request.form['lname'],
            'ema':request.form['email'],
            "ps":pw_hash
        }
        new_user_id = mysql.query_db(query,data)
        session['id'] = new_user_id
        return redirect("/dashboard") 
# login
@app.route("/login", methods=['POST'])
def login():
    mysql = connectToMySQL('jobs')
    query="SELECT * from users WHERE email= %(email)s;"
    data = { "email" : request.form["email"] }
    users=mysql.query_db(query, data)
    if len(users) > 0:
        if bcrypt.check_password_hash(users[0]['password'], request.form['password']):
            session['id'] = users[0]['id']
            session['name'] = users[0]['first_name']
            return redirect('/dashboard')
    flash("You could not be logged in", "must_log_in")
    return redirect("/")
# Dashboard
@app.route("/dashboard")
def show_dash():
    mysql = connectToMySQL('jobs')
    query="SELECT * FROM jobs.all_jobs WHERE user_id = %(id)s;"
    data={ "id" : session['id'] }
    my_jobs=mysql.query_db(query,data)

    mysql = connectToMySQL('jobs')
    query="SELECT * FROM jobs.all_jobs WHERE user_id != %(id)s;"
    data={ "id" : session['id'] }
    others_jobs=mysql.query_db(query,data)

    return render_template("dashboard.html", my_jobs_on=my_jobs, others_jobs_on=others_jobs)



# jobs/3
@app.route("/jobs/<id>")
def show_job(id):
    mysql = connectToMySQL('jobs')
    # try tommorrow!
    query="SELECT * FROM jobs.all_jobs JOIN jobs.users ON users.id = user_id WHERE all_jobs.id = %(id)s;"
    data={ "id" : id }
    result=mysql.query_db(query,data)[0]
    print(result)
    return render_template("viewjob.html", result_on=result)



# jobs/edit/3
@app.route("/jobs/edit/<id>")
def show_edit(id):
    session["edit_id"]=id
    print(session["edit_id"])
    return render_template("edit.html")

#update
@app.route("/editjob", methods=["POST"])
def edit_job():
    is_valid = True
    # title
    if len(request.form['title']) < 3:
        is_valid = False
        flash("Title must contain at least 3 characters", 'titleError')
    if len(request.form['description']) < 3:
        is_valid = False
        flash("Description must contain at least 3 characters", 'desError')
    if len(request.form['location']) < 3:
        is_valid = False
        flash("Location must contain at least 3 characters", 'locError')
    if not is_valid:
        return redirect('/jobs/edit/<id>')
    else:
        query="UPDATE jobs.all_jobs SET title=%(tit)s, description=%(des)s, location=%(loc)s WHERE jobs.all_jobs.id = %(id)s;"
        data={
            "tit" : request.form['title'],
            "des" : request.form['description'],
            "loc" : request.form['location'],
            "id" : session["edit_id"]
        }
        mysql = connectToMySQL('jobs')
        mysql.query_db(query, data)
        return redirect("/dashboard")
# remove
@app.route("/remove/<id>")
def remove(id):
    query="DELETE FROM all_jobs WHERE all_jobs.id =%(id)s;"
    data = {
        "id": id
    }
    mysql = connectToMySQL('jobs')
    mysql.query_db(query, data)
    return redirect("/dashboard")
# show page
@app.route("/jobs/new")
def show_creat():
    return render_template("newjobs.html")

# add job
@app.route("/addjob", methods=["POST"])
def add_new_job():
    is_valid = True
    # title
    if len(request.form['title']) < 3:
        is_valid = False
        flash("Title must contain at least 3 characters", 'titleError')
    if len(request.form['description']) < 3:
        is_valid = False
        flash("Description must contain at least 3 characters", 'desError')
    if len(request.form['location']) < 3:
        is_valid = False
        flash("Location must contain at least 3 characters", 'locError')
    if not is_valid:
        return redirect('/jobs/new')
    else:
        query = "INSERT INTO all_jobs (user_id, title, description, location, created_at, updated_at) VALUES (%(id)s, %(tit)s, %(des)s, %(loc)s, NOW(), NOW());"
        data = {
            'id':session['id'],
            'tit':request.form['title'],
            'des':request.form['description'],
            'loc': request.form['location'],
        }
        mysql = connectToMySQL('jobs')
        new_job_id = mysql.query_db(query,data)
        return redirect("/dashboard") 

#logout
@app.route("/logout")
def logout():
    # need to clear the session to logout
    session.clear()
    flash("You have been logged out!", 'logged_out')
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)