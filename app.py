import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)

# ==============================
# CONFIGURACIÓN
# ==============================
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "medmaint_secret_key")

# Cookies seguras para Render (HTTPS)
app.config["SESSION_COOKIE_SECURE"] = True
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

database_url = os.environ.get("DATABASE_URL")

if database_url:
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
else:
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# ==============================
# MODELOS
# ==============================
class Usuario(db.Model):
    __tablename__ = "usuario"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    rol = db.Column(db.String(20), default="usuario")  # usuario o admin

class Equipo(db.Model):
    __tablename__ = "equipo"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    marca = db.Column(db.String(100))
    modelo = db.Column(db.String(100))
    numero_serie = db.Column(db.String(100))
    ubicacion = db.Column(db.String(100))
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)

class Orden(db.Model):
    __tablename__ = "orden"

    id = db.Column(db.Integer, primary_key=True)
    descripcion = db.Column(db.Text, nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)

    equipo_id = db.Column(db.Integer, db.ForeignKey("equipo.id"))
    equipo = db.relationship("Equipo", backref=db.backref("ordenes", lazy=True))

# Crear tablas automáticamente
with app.app_context():
    db.create_all()

# ==============================
# RUTAS
# ==============================

@app.route("/")
def index():
    if "user_id" not in session:
        return redirect(url_for("login"))

    ordenes = Orden.query.order_by(Orden.fecha.desc()).all()
    equipos = Equipo.query.all()

    return render_template("index.html", ordenes=ordenes, equipos=equipos)

# ==============================
# LOGIN
# ==============================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        if not email or not password:
            flash("Todos los campos son obligatorios")
            return redirect(url_for("login"))

        usuario = Usuario.query.filter_by(email=email).first()

        if usuario and check_password_hash(usuario.password, password):
            session["user_id"] = usuario.id
            session["user_name"] = usuario.nombre
            session["rol"] = usuario.rol
            return redirect(url_for("index"))
        else:
            flash("Credenciales incorrectas")

    return render_template("login.html")

# ==============================
# REGISTRO
# ==============================
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        nombre = request.form.get("nombre")
        email = request.form.get("email")
        password_raw = request.form.get("password")

        if not nombre or not email or not password_raw:
            flash("Todos los campos son obligatorios")
            return redirect(url_for("register"))

        if Usuario.query.filter_by(email=email).first():
            flash("El usuario ya existe")
            return redirect(url_for("register"))

        password_hash = generate_password_hash(password_raw)

        nuevo_usuario = Usuario(
            nombre=nombre,
            email=email,
            password=password_hash,
            rol="usuario"
        )

        db.session.add(nuevo_usuario)
        db.session.commit()

        flash("Usuario creado correctamente")
        return redirect(url_for("login"))

    return render_template("register.html")

# ==============================
# LOGOUT
# ==============================
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ==============================
# GESTIÓN DE EQUIPOS
# ==============================
@app.route("/equipos")
def mostrar_equipos():
    if "user_id" not in session:
        return redirect(url_for("login"))

    equipos = Equipo.query.all()
    return render_template("equipos.html", equipos=equipos)

@app.route("/equipos/crear", methods=["POST"])
def crear_equipo():
    if "user_id" not in session:
        return redirect(url_for("login"))

    nombre = request.form.get("nombre")
    marca = request.form.get("marca")
    serie = request.form.get("serie")
    ubicacion = request.form.get("ubicacion")

    if not nombre:
        flash("El nombre es obligatorio")
        return redirect(url_for("mostrar_equipos"))

    nuevo_equipo = Equipo(
        nombre=nombre,
        marca=marca,
        numero_serie=serie,
        ubicacion=ubicacion
    )

    db.session.add(nuevo_equipo)
    db.session.commit()

    flash("Equipo agregado correctamente")
    return redirect(url_for("mostrar_equipos"))

@app.route("/equipos/<int:equipo_id>")
def detalle_equipo(equipo_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    equipo = Equipo.query.get_or_404(equipo_id)
    return render_template("detalles_equipo.html", equipo=equipo)

@app.route("/equipos/borrar/<int:equipo_id>")
def borrar_equipo(equipo_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("rol") != "admin":
        flash("No tienes permisos para borrar equipos")
        return redirect(url_for("mostrar_equipos"))

    equipo = Equipo.query.get_or_404(equipo_id)
    db.session.delete(equipo)
    db.session.commit()
    flash("Equipo borrado correctamente")
    return redirect(url_for("mostrar_equipos"))

# ==============================
# AGREGAR ORDEN
# ==============================
@app.route("/agregar_orden", methods=["POST"])
def agregar_orden():
    if "user_id" not in session:
        return redirect(url_for("login"))

    descripcion = request.form.get("descripcion")
    equipo_id = request.form.get("equipo_id")

    if not descripcion or not equipo_id:
        flash("Datos incompletos")
        return redirect(url_for("index"))

    nueva_orden = Orden(
        descripcion=descripcion,
        equipo_id=equipo_id
    )

    db.session.add(nueva_orden)
    db.session.commit()

    return redirect(url_for("index"))

# ==============================
# PRODUCCIÓN
# ==============================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)