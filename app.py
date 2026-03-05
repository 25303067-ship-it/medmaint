from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)

app.secret_key = "medmaint_secret"

# Base de datos (Render o local)
database_url = os.environ.get("DATABASE_URL")

if database_url:
    database_url = database_url.replace("postgres://", "postgresql://")

app.config["SQLALCHEMY_DATABASE_URI"] = database_url or "sqlite:///medmaint.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# ==========================
# MODELOS
# ==========================

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100))
    email = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(200))


class Equipo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100))
    area = db.Column(db.String(100))
    estado = db.Column(db.String(50))


# ==========================
# RUTAS
# ==========================

@app.route("/")
def index():

    if "usuario_id" not in session:
        return redirect(url_for("login"))

    equipos = Equipo.query.all()

    return render_template("index.html", equipos=equipos)


# ==========================
# LOGIN
# ==========================

@app.route("/login", methods=["GET","POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        usuario = Usuario.query.filter_by(email=email).first()

        if usuario and check_password_hash(usuario.password, password):

            session["usuario_id"] = usuario.id
            return redirect(url_for("index"))

        else:
            flash("Correo o contraseña incorrectos")

    return render_template("login.html")


# ==========================
# REGISTRO
# ==========================

@app.route("/register", methods=["GET","POST"])
def register():

    if request.method == "POST":

        nombre = request.form["nombre"]
        email = request.form["email"]
        password = request.form["password"]

        password_hash = generate_password_hash(password)

        nuevo_usuario = Usuario(
            nombre=nombre,
            email=email,
            password=password_hash
        )

        db.session.add(nuevo_usuario)
        db.session.commit()

        flash("Usuario registrado correctamente")

        return redirect(url_for("login"))

    return render_template("register.html")


# ==========================
# EQUIPOS
# ==========================

@app.route("/equipos", methods=["GET","POST"])
def equipos():

    if "usuario_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":

        nombre = request.form["nombre"]
        area = request.form["area"]
        estado = request.form["estado"]

        nuevo = Equipo(
            nombre=nombre,
            area=area,
            estado=estado
        )

        db.session.add(nuevo)
        db.session.commit()

        return redirect(url_for("equipos"))

    lista = Equipo.query.all()

    return render_template("equipos.html", equipos=lista)


# ==========================
# LOGOUT
# ==========================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login"))


# ==========================
# CREAR BASE DE DATOS
# ==========================

with app.app_context():
    db.create_all()


# ==========================
# RUN LOCAL
# ==========================

if __name__ == "__main__":
    app.run(debug=True)