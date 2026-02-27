from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)

app.secret_key = os.environ.get("SECRET_KEY", "clave_super_segura")

# =========================================
# CONFIGURACIÓN POSTGRESQL
# =========================================

DATABASE_URL = os.environ.get("DATABASE_URL")

if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# =========================================
# MODELO
# =========================================

class Orden(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    equipo = db.Column(db.String(100), nullable=False)
    tecnico = db.Column(db.String(100), nullable=False)
    estado = db.Column(db.String(50), nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)

# Crear tablas si no existen
with app.app_context():
    db.create_all()

# =========================================
# LOGIN
# =========================================

USUARIO = os.environ.get("ADMIN_USER", "admin")
CLAVE = os.environ.get("ADMIN_PASS", "1234")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario = request.form.get("usuario")
        clave = request.form.get("clave")

        if usuario == USUARIO and clave == CLAVE:
            session["user"] = usuario
            return redirect(url_for("index"))
        else:
            flash("Credenciales incorrectas")

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/")
def index():
    if "user" not in session:
        return redirect(url_for("login"))

    ordenes = Orden.query.order_by(Orden.fecha.desc()).all()
    return render_template("index.html", ordenes=ordenes)

@app.route("/crear", methods=["POST"])
def crear():
    if "user" not in session:
        return redirect(url_for("login"))

    equipo = request.form.get("equipo")
    tecnico = request.form.get("tecnico")

    nueva_orden = Orden(
        equipo=equipo,
        tecnico=tecnico,
        estado="Pendiente"
    )

    db.session.add(nueva_orden)
    db.session.commit()

    return redirect(url_for("index"))

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

@app.route("/borrar/<int:id>")
def borrar(id):
    if "user" not in session:
        return redirect(url_for("login"))

    orden = Orden.query.get(id)
    if orden:
        db.session.delete(orden)
        db.session.commit()

    return redirect(url_for("index"))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)