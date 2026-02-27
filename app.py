from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "super_secret_key")

DATABASE_URL = os.environ.get("DATABASE_URL")

if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# ======================
# MODELOS
# ======================

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    rol = db.Column(db.String(50), nullable=False, default="tecnico")

class Orden(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    equipo = db.Column(db.String(100), nullable=False)
    tecnico = db.Column(db.String(100), nullable=False)
    estado = db.Column(db.String(50), nullable=False, default="Pendiente")
    fecha = db.Column(db.DateTime, default=datetime.utcnow)

with app.app_context():
    db.create_all()

# ======================
# REGISTRO
# ======================

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["usuario"]
        password = generate_password_hash(request.form["clave"])
        rol = request.form["rol"]

        if Usuario.query.filter_by(username=username).first():
            flash("El usuario ya existe")
            return redirect(url_for("register"))

        nuevo = Usuario(username=username, password=password, rol=rol)
        db.session.add(nuevo)
        db.session.commit()

        flash("Usuario creado correctamente")
        return redirect(url_for("login"))

    return render_template("register.html")

# ======================
# LOGIN
# ======================

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = Usuario.query.filter_by(username=request.form["usuario"]).first()

        if user and check_password_hash(user.password, request.form["clave"]):
            session["user"] = user.username
            session["rol"] = user.rol
            return redirect(url_for("index"))
        else:
            flash("Credenciales incorrectas")

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ======================
# PANEL PRINCIPAL
# ======================

@app.route("/")
def index():
    if "user" not in session:
        return redirect(url_for("login"))

    busqueda = request.args.get("buscar", "")
    estado_filtro = request.args.get("estado", "")

    query = Orden.query

    if busqueda:
        query = query.filter(
            Orden.equipo.ilike(f"%{busqueda}%")
        )

    if estado_filtro:
        query = query.filter_by(estado=estado_filtro)

    ordenes = query.order_by(Orden.fecha.desc()).all()

    total = Orden.query.count()
    pendientes = Orden.query.filter_by(estado="Pendiente").count()
    proceso = Orden.query.filter_by(estado="En proceso").count()
    finalizadas = Orden.query.filter_by(estado="Finalizado").count()

    return render_template(
        "index.html",
        ordenes=ordenes,
        total=total,
        pendientes=pendientes,
        proceso=proceso,
        finalizadas=finalizadas
    )

@app.route("/crear", methods=["POST"])
def crear():
    if "user" not in session:
        return redirect(url_for("login"))

    nueva = Orden(
        equipo=request.form["equipo"],
        tecnico=session["user"]
    )

    db.session.add(nueva)
    db.session.commit()

    return redirect(url_for("index"))

@app.route("/cambiar/<int:id>")
def cambiar(id):
    if "user" not in session:
        return redirect(url_for("login"))

    orden = Orden.query.get(id)
    estados = ["Pendiente", "En proceso", "Finalizado"]
    orden.estado = estados[(estados.index(orden.estado) + 1) % len(estados)]
    db.session.commit()

    return redirect(url_for("index"))

@app.route("/borrar/<int:id>")
def borrar(id):
    if "user" not in session:
        return redirect(url_for("login"))

    if session["rol"] != "admin":
        flash("No tienes permisos")
        return redirect(url_for("index"))

    orden = Orden.query.get(id)
    db.session.delete(orden)
    db.session.commit()

    return redirect(url_for("index"))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)