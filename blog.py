from flask import Flask,render_template,flash,request,redirect,url_for,session,logging
from flask_mysqldb import MySQL
from wtforms import Form,StringField,TextAreaField,PasswordField,validators
from passlib.hash import sha256_crypt
from functools import wraps
#kullanıcı giriş decerator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            flash("Bu sayfayı görüntülemek için giriş yapın","danger")
            return redirect(url_for("login"))
    return decorated_function
#kullanıcı kayıt formu
class RegisterForm(Form):
    name=StringField("İsim Soyisim",validators=[validators.length(min=4,max=25)])
    username=StringField("Kullanıcı adı",validators=[validators.length(min=5,max=25)])
    email=StringField("Email adresi",validators=[validators.Email(message="Lütfen geçerli bir email adresi giriniz.")])
    password=PasswordField("Parola:",validators=[
        validators.DataRequired(message="Lütfen bir parola belirleyin"),
        validators.EqualTo(fieldname="confirm",message="Parolanız uyuşmuyor...")
    ])
    confirm=PasswordField("Parola doğrula")

class LoginForm(Form):
    username=StringField("Kullanıcı Adı")
    password=PasswordField("Parola")

    




app=Flask(__name__)
app.secret_key="özerblog"
app.config["MYSQL_HOST"]="localhost"
app.config["MYSQL_USER"]="root"
app.config["MYSQL_PASSWORD"]=""
app.config["MYSQL_DB"]="özerblog"
app.config["MYSQL_CURSORCLASS"]="DictCursor"
mysql=MySQL(app)



@app.route("/")
def index():
    return render_template("index.html")

@app.route("/about")
def about():
    return render_template("about.html")


    

#kayıt olma
@app.route("/register",methods=["GET","POST"])
def register():
    form=RegisterForm(request.form)
    if request.method =="POST" and form.validate():
        name=form.name.data
        username=form.username.data
        email=form.email.data
        password=sha256_crypt.encrypt(form.password.data)

        cursor=mysql.connection.cursor()
        sorgu=("INSERT INTO users(name,email,username,password) VALUES(%s,%s,%s,%s)")
        cursor.execute(sorgu,(name,email,username,password))
        mysql.connection.commit()
        cursor.close()
        flash("Başarıyla kayıt oldunuz..","success")

        return redirect(url_for("login"))
    
    else:
        return render_template("register.html",form=form)
#LOGİN İŞLEMİ
@app.route("/login",methods=["GET","POST"])
def login():
    form=LoginForm(request.form)
    if request.method=="POST":
        username=form.username.data
        Password_entered=form.password.data
        cursor=mysql.connection.cursor()
        sorgu="Select * from users where username = %s"
        result= cursor.execute(sorgu,(username,))
        if result > 0:
            data=cursor.fetchone()
            realpassword=data["password"]
            if sha256_crypt.verify(Password_entered,realpassword):
                flash("Başarıyla giriş yaptınız..","success")
                session["logged_in"]=True
                session["username"]=username
                return redirect(url_for("index"))
            else:
                flash("Parolanızı yanlış girdiniz..","danger")
                return redirect(url_for("login"))
            

        else:
            flash("Böyle bir kullanıcı bulunmuyor","danger")
            return redirect(url_for("login"))
    
    
    return render_template("login.html",form=form)

@app.route("/articles")
def articles():
    cursor=mysql.connection.cursor()
    sorgu="Select * from article"
    result=cursor.execute(sorgu)

    if result >0:
        articles=cursor.fetchall()

        return render_template("articles.html",articles=articles)
    
    

    else:
        return render_template("articles.html")
    

@app.route("/dashboard")
@login_required
def dashboard():
    cursor=mysql.connection.cursor()
    sorgu="Select * from article where author=%s"
    result=cursor.execute(sorgu,(session["username"],))
    if result >0:
        articles=cursor.fetchall()
        return render_template("dashboard.html",articles=articles)
    else:

        return render_template("dashboard.html")
    
#detay sayfası
@app.route("/article/<string:id>")
def article(id):
    cursor=mysql.connection.cursor()
    sorgu="Select * from article where id=%s"
    result =cursor.execute(sorgu,(id,))
    if result >0:
        article=cursor.fetchone()
        return render_template("article.html",article=article)
    
    else:
        return render_template("article.html")
    

#logout işlemi
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/addarticle",methods=["GET","POST"])
def addarticle():
    form=ArticleForm(request.form)
    if request.method=="POST" and form.validate():
        title=form.title.data
        content=form.content.data
        cursor=mysql.connection.cursor()

        sorgu="INSERT INTO article (title,author,content) VALUES(%s,%s,%s)"
        cursor.execute(sorgu,(title,session["username"],content))
        mysql.connection.commit()
        cursor.close()
        flash("Makale başarıyla eklendi !","success")
        return redirect(url_for("dashboard"))
    
    return render_template("addarticle.html",form=form)
#makale silme
@app.route("/delete/<string:id>")
@login_required
def delete(id):
    cursor=mysql.connection.cursor()
    sorgu= "Select * from article where author=%s and id=%s"

    result =cursor.execute(sorgu,(session["username"],id))

    if result >0:
        sorgu2="Delete from article where id=%s"
        cursor.execute(sorgu2,(id,))
        mysql.connection.commit()
        return redirect(url_for("dashboard"))
    
    else:
        flash("Böyle bir makale yok veya bu işleme yetkiniz yok","danger")
        return redirect(url_for("index"))
    


#makale form
class ArticleForm(Form):
    title=StringField("Makale başlığı",validators=[validators.length(min=5,max=100)])
    content=TextAreaField("Makale içeriği",validators=[validators.length(min=9)])

#arama url
@app.route("/search",methods=["GET","POST"])
def search():
    if request.method=="GET":
        return redirect(url_for("index"))
    else:
        keyword=request.form.get("keyword")
        cursor=mysql.connection.cursor()
        sorgu="Select * from article where title like '%" + keyword +"%'"
        result=cursor.execute(sorgu)

        if result ==0:  
            flash("Aranan kelimeye uygun makale bulunamadı:(","warning")
            return redirect(url_for("articles"))
        else:
            articles=cursor.fetchall()
            return render_template("articles.html",articles=articles)
    
    




if __name__=="__main__":
    app.run(debug=True)
 

