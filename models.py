from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Cliente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True)
    telefono = db.Column(db.String(20))
    empresa = db.Column(db.String(120))
    notas = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    facturas = db.relationship('Factura', backref='cliente', lazy=True)

class Producto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False)
    descripcion = db.Column(db.Text)
    precio = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, default=0)
    categoria = db.Column(db.String(80))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Factura(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.String(20), unique=True, nullable=False)
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=False)
    concepto = db.Column(db.Text, nullable=False)
    base = db.Column(db.Float, default=0.0)
    iva = db.Column(db.Float, default=21.0)
    total = db.Column(db.Float, default=0.0)
    estado = db.Column(db.String(20), default='pendiente')  # pendiente, pagada, cancelada
    fecha = db.Column(db.DateTime, default=datetime.utcnow)

class MensajeChat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    rol = db.Column(db.String(10))  # user / assistant
    contenido = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
