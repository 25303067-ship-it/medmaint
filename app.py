from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)

# ==============================
# CONFIGURACIÓN SEGURA
# ==============================

app.secret_key = os.environ.get("SECRET_KEY", "super_secret_key")

DATABASE_URL = os.environ.get("DATABASE_URL")

if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# ==============================
# MODELO DE BASE DE DATOS
# ==============================

class Orden(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    equipo = db.Column(db.String(100), nullable=False)
    tecnico = db.Column(db.String(100), nullable=False)
    estado = db.Column(db.String(50), nullable=False, default="Pendiente")
    fecha = db.Column(db.DateTime, default=datetime.utcnow)

# Crear tablas automáticamente
with app.app_context():
    db.create_all()

# ==============================
# LOGIN
# ==============================

USUARIO = os.environ.get("ADMIN_USER", "admin")
CLAVE = os.environ.get("ADMIN_PASS", "1234")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form["usuario"] == USUARIO and request.form["clave"] == CLAVE:
            session["user"] = request.form["usuario"]
            return redirect(url_for("index"))
        else:
            flash("Credenciales incorrectas")

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ==============================
# RUTA PRINCIPAL
# ==============================

@app.route("/")
def index():
    if "user" not in session:
        return redirect(url_for("login"))

    ordenes = Orden.query.order_by(Orden.fecha.desc()).all()
    return render_template("index.html", ordenes=ordenes)

# ==============================
# CREAR ORDEN
# ==============================

@app.route("/crear", methods=["POST"])
def crear():
    if "user" not in session:
        return redirect(url_for("login"))

    nueva = Orden(
        equipo=request.form["equipo"],
        tecnico=request.form["tecnico"]
    )

    db.session.add(nueva)
    db.session.commit()

    return redirect(url_for("index"))

# ==============================
# CAMBIAR ESTADO
# ==============================

@app.route("/cambiar/<int:id>")
def cambiar(id):
    if "user" not in session:
        return redirect(url_for("login"))

    orden = Orden.query.get(id)
    if orden:
        estados = ["Pendiente", "En proceso", "Finalizado"]
        orden.estado = estados[(estados.index(orden.estado) + 1) % len(estados)]
        db.session.commit()

    return redirect(url_for("index"))

# ==============================
# BORRAR ORDEN
# ==============================

@app.route("/borrar/<int:id>")
def borrar(id):
    if "user" not in session:
        return redirect(url_for("login"))

    orden = Orden.query.get(id)
    if orden:
        db.session.delete(orden)
        db.session.commit()

    return redirect(url_for("index"))

# ==============================
# ARRANQUE PARA RENDER
# ==============================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)