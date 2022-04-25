
from flask import Flask,render_template,flash,redirect, render_template_string,url_for,session,logging,request
from flask_mysqldb import MySQL
from wtforms import Form,StringField,TextAreaField,PasswordField,validators
from passlib.hash import sha256_crypt
from functools import wraps

# user login decorator

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session :
            return f(*args, **kwargs)
        else:
            flash("login for this page","danger")
            return redirect(url_for("login"))
    return decorated_function



# user Register form
class RegisterForm(Form):
    name = StringField("Name Surname",validators=[validators.Length(min = 4,max = 25)])
    username = StringField("Username",validators=[validators.Length(min = 5,max = 35)])
    email = StringField("Email ",validators=[validators.Email(message = "Please enter a correct email...")])
    password = PasswordField("Password:",validators=[
        validators.DataRequired(message = "Creat password"),
        validators.EqualTo(fieldname = "confirm",message="invalid password ...")
    ])
    confirm = PasswordField("Success Password")

#Login form
class LoginForm(Form):
    username = StringField("Username")
    password = PasswordField("Password")

app = Flask(__name__)
#important! KEY
app.secret_key= "project"
 # mysql 
app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "project"
app.config["MYSQL_CURSORCLASS"] = "DictCursor"

mysql = MySQL(app)
#apps to do
@app.route("/")
def index():
   return render_template("index.html")

#about
@app.route("/about")
def about():
    return render_template("about.html")


# Article PAge
@app.route("/articles")
def articles():
        
    cursor = mysql.connection.cursor()

    qry = "Select * From articles"

    result = cursor.execute(qry)
    if result > 0:
        articles = cursor.fetchall()
        return render_template("articles.html",articles = articles)
    else:
        return render_template("articles.html")


#Dashboard
@app.route("/dashboard")
@login_required
def dashboard():
    cursor = mysql.connection.cursor()

    qry = "Select * From articles where author = %s"

    result = cursor.execute(qry,(session["username"],))

    if result > 0:
        articles = cursor.fetchall()
        return render_template("dashboard.html",articles = articles)
    else:
        return render_template("dashboard.html")


# register 
@app.route("/register",methods = ["GET","POST"])
def register():
    form = RegisterForm(request.form)

    if request.method == "POST" and form.validate():
        name = form.name.data
        username = form.username.data
        email = form.email.data
        password = sha256_crypt.encrypt(form.password.data)

        cursor = mysql.connection.cursor()

        qry = "Insert into users(name,email,username,password) VALUES(%s,%s,%s,%s)"

        cursor.execute(qry,(name,email,username,password))
        mysql.connection.commit()

        cursor.close()
        flash( "Registered...","success")
        return redirect(url_for("login"))
    else:
        return render_template("register.html",form = form)

#Login

@app.route("/login", methods = ["GET","POST"])
def login():
    form = LoginForm(request.form)
    if request.method=="POST":
        username = form.username.data
        password_entered = form.password.data

        cursor = mysql.connection.cursor()

        qry = "Select * From users where username = %s"

        result =  cursor.execute(qry,(username,))

        if result > 0:
            data = cursor.fetchone()
            real_password = data["password"]
            if sha256_crypt.verify(password_entered,real_password):
                    flash("success enter","success")

                    session["logged_in"] =True
                    session["username"] = username
                    
                    

                    return redirect(url_for("index"))
            else:
                    flash("invalid password...", "danger")
                    return redirect(url_for("login")) 
        else:
            flash(" has no users....","danger")
            return redirect(url_for("login"))    

    return render_template("login.html",form=form)

#page details

@app.route("/article/<string:id>")
def article(id):
    cursor = mysql.connection.cursor()
    

    qry = "Select * from articles where id = %s"
    result = cursor.execute(qry,(id,))

    if result>0 :
        article=  cursor.fetchone()
        return render_template("article.html", article=article)
    else:
        return render_template("article.html")


#log out

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


#add article

@app.route("/addarticle",methods = ["GET","POST"])
def addarticle ():
    form = ArticleForm(request.form)

    if request.method== "POST" and form.validate():
        title = form.title.data
        content = form.content.data
        
        cursor = mysql.connection.cursor()

        cursor = mysql.connection.cursor()

        sorgu = "Insert into articles(title,author,content) VALUES(%s,%s,%s)"

        cursor.execute(sorgu,(title,session["username"],content))

        mysql.connection.commit()

        cursor.close()
        flash("Update is success","success")

        return redirect(url_for("dashboard"))
    return render_template("addarticle.html",form=form)

#article delete

@app.route("/delete/<string:id>")
@login_required
def delete(id):

    cursor = mysql.connection.cursor()
    qry = "Select *from articles where author = %s and id = %s "

    result = cursor.execute(qry,(session["username"],id))
    if result>0 :
        qry2 = "delete from articles where id = %s"
        cursor.execute(qry2,(id,))

        mysql.connection.commit()
        return redirect(url_for("dashboard")
        )
    else:
        flash("you are unauthorized","danger")
        return redirect(url_for("index"))

#article update

@app.route("/edit/<string:id>", methods = ["GET","POST"])
@login_required
def update(id):
    if request.method == "GET":
        cursor = mysql.connection.cursor()
        qry = "Select * from articles where id = %s and author = %s "
       
        result = cursor.execute(qry,(id,session["username"]))
        if result ==0 :
            flash(" dont find article", "danger")
            return redirect(url_for("index"))
        else:
            article = cursor.fetchone()
            form = ArticleForm()
            form.title.data = article["title"]
            form.content.data =article["content"]
            return render_template("update.html",form =form)

    else: 
        #post request 

        form = ArticleForm(request.form)

        newTitle = form.title.data
        newContent = form.content.data

        qry2 = "Update articles Set title = %s,content = %s where id =%s"
        
        cursor = mysql.connection.cursor()
       
        cursor.execute(qry2,(newTitle,newContent,id))
      
        mysql.connection.commit()

        flash("success update","success")
    return redirect(url_for("dashboard"))
    pass
        
# article form
class ArticleForm(Form):
    title = StringField("article title",validators=[validators.Length(min= 5,max = 100)])
    content = TextAreaField("article content ",validators=[validators.Length(min= 10)])

#Search URL

@app.route("/search", methods = ["GET", "POST"])
def search():
    if request.method == "GET":
        return redirect(url_for("index"))

    else:
        keyword =  request.form.get("keyword")

        cursor = mysql.connection.cursor()

        qry = " Select * from  articles where title like '" + keyword+"%' "
        result =cursor.execute(qry)

        if result == 0 :
            flash("not found the keyword.....")
            return redirect(url_for("articles"))
        else:
            articles= cursor.fetchall()
            return render_template("articles.html",articles=articles)

if __name__ == "__main__":
    app.run(debug=True)
