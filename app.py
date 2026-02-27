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

# =========================
# MODELOS
# =========================

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    rol = db.Column(db.String(50), nullable=False, default="tecnico")

class Equipo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    marca = db.Column(db.String(100))
    serie = db.Column(db.String(100))
    ubicacion = db.Column(db.String(100))
    ordenes = db.relationship("Orden", backref="equipo_rel", lazy=True)

class Orden(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    equipo_id = db.Column(db.Integer, db.ForeignKey("equipo.id"), nullable=False)
    tecnico = db.Column(db.String(100), nullable=False)
    estado = db.Column(db.String(50), nullable=False, default="Pendiente")
    fecha = db.Column(db.DateTime, default=datetime.utcnow)

with app.app_context():
    db.create_all()

# =========================
# LOGIN / REGISTER
# =========================

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
        return redirect(url_for("login"))

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = Usuario.query.filter_by(username=request.form["usuario"]).first()

        if user and check_password_hash(user.password, request.form["clave"]):
            session["user"] = user.username
            session["rol"] = user.rol
            return redirect(url_for("index"))

        flash("Credenciales incorrectas")

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# =========================
# PANEL PRINCIPAL
# =========================

@app.route("/")
def index():
    if "user" not in session:
        return redirect(url_for("login"))

    ordenes = Orden.query.order_by(Orden.fecha.desc()).all()
    equipos = Equipo.query.all()

    total = Orden.query.count()
    pendientes = Orden.query.filter_by(estado="Pendiente").count()
    proceso = Orden.query.filter_by(estado="En proceso").count()
    finalizadas = Orden.query.filter_by(estado="Finalizado").count()

    return render_template(
        "index.html",
        ordenes=ordenes,
        equipos=equipos,
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
        equipo_id=request.form["equipo_id"],
        tecnico=session["user"]
    )

    db.session.add(nueva)
    db.session.commit()
    return redirect(url_for("index"))

@app.route("/cambiar/<int:id>")
def cambiar(id):
    orden = Orden.query.get_or_404(id)
    estados = ["Pendiente", "En proceso", "Finalizado"]
    orden.estado = estados[(estados.index(orden.estado) + 1) % len(estados)]
    db.session.commit()
    return redirect(url_for("index"))

@app.route("/borrar/<int:id>")
def borrar(id):
    if session.get("rol") != "admin":
        return redirect(url_for("index"))

    orden = Orden.query.get_or_404(id)
    db.session.delete(orden)
    db.session.commit()
    return redirect(url_for("index"))

# =========================
# EQUIPOS
# =========================

@app.route("/equipos")
def equipos():
    if "user" not in session:
        return redirect(url_for("login"))

    lista = Equipo.query.all()
    return render_template("equipos.html", equipos=lista)

@app.route("/equipos/crear", methods=["POST"])
def crear_equipo():
    nuevo = Equipo(
        nombre=request.form["nombre"],
        marca=request.form["marca"],
        serie=request.form["serie"],
        ubicacion=request.form["ubicacion"]
    )
    db.session.add(nuevo)
    db.session.commit()
    return redirect(url_for("equipos"))

@app.route("/equipos/<int:id>")
def detalle_equipo(id):
    if "user" not in session:
        return redirect(url_for("login"))

    equipo = Equipo.query.get_or_404(id)
    return render_template("detalle_equipo.html", equipo=equipo)

@app.route("/equipos/borrar/<int:id>")
def borrar_equipo(id):
    if session.get("rol") != "admin":
        return redirect(url_for("equipos"))

    equipo = Equipo.query.get_or_404(id)

    if equipo.ordenes:
        flash("No se puede eliminar el equipo porque tiene órdenes registradas.")
        return redirect(url_for("equipos"))

    db.session.delete(equipo)
    db.session.commit()
    return redirect(url_for("equipos"))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)