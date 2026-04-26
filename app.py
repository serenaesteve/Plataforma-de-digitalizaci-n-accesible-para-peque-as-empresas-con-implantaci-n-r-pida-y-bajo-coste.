import os
import requests
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, session
from dotenv import load_dotenv
from models import db, Usuario, Cliente, Producto, Factura, MensajeChat

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bizcore.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

OLLAMA_URL = os.getenv('OLLAMA_URL', 'http://localhost:11434')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'llama3')

db.init_app(app)

with app.app_context():
    db.create_all()

# ─── AUTH ─────────────────────────────────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        password = request.form['password']
        user = Usuario.query.filter_by(email=email).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['user_nombre'] = user.nombre
            return redirect(url_for('dashboard'))
        flash('Email o contraseña incorrectos.', 'warn')
    return render_template('login.html')

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        nombre = request.form['nombre'].strip()
        email = request.form['email'].strip().lower()
        password = request.form['password']
        confirm = request.form['confirm']
        if password != confirm:
            flash('Las contraseñas no coinciden.', 'warn')
            return render_template('registro.html')
        if Usuario.query.filter_by(email=email).first():
            flash('Ya existe una cuenta con ese email.', 'warn')
            return render_template('registro.html')
        u = Usuario(nombre=nombre, email=email)
        u.set_password(password)
        db.session.add(u)
        db.session.commit()
        session['user_id'] = u.id
        session['user_nombre'] = u.nombre
        flash('Cuenta creada. ¡Bienvenido/a!', 'ok')
        return redirect(url_for('dashboard'))
    return render_template('registro.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ─── DASHBOARD ────────────────────────────────────────────────────────────────

@app.route('/')
@login_required
def dashboard():
    total_clientes = Cliente.query.count()
    total_productos = Producto.query.count()
    total_facturas = Factura.query.count()
    ingresos = db.session.query(db.func.sum(Factura.total)).filter_by(estado='pagada').scalar() or 0
    pendiente = db.session.query(db.func.sum(Factura.total)).filter_by(estado='pendiente').scalar() or 0
    ultimas_facturas = Factura.query.order_by(Factura.fecha.desc()).limit(5).all()
    ultimos_clientes = Cliente.query.order_by(Cliente.created_at.desc()).limit(5).all()
    return render_template('dashboard.html',
        total_clientes=total_clientes,
        total_productos=total_productos,
        total_facturas=total_facturas,
        ingresos=ingresos,
        pendiente=pendiente,
        ultimas_facturas=ultimas_facturas,
        ultimos_clientes=ultimos_clientes
    )

# ─── CLIENTES ─────────────────────────────────────────────────────────────────

@app.route('/clientes')
@login_required
def clientes():
    q = request.args.get('q', '')
    if q:
        lista = Cliente.query.filter(
            Cliente.nombre.ilike(f'%{q}%') | Cliente.email.ilike(f'%{q}%')
        ).all()
    else:
        lista = Cliente.query.order_by(Cliente.created_at.desc()).all()
    return render_template('clientes.html', clientes=lista, q=q)

@app.route('/clientes/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo_cliente():
    if request.method == 'POST':
        c = Cliente(
            nombre=request.form['nombre'],
            email=request.form.get('email'),
            telefono=request.form.get('telefono'),
            empresa=request.form.get('empresa'),
            notas=request.form.get('notas')
        )
        db.session.add(c)
        db.session.commit()
        flash('Cliente añadido.', 'ok')
        return redirect(url_for('clientes'))
    return render_template('cliente_form.html', cliente=None)

@app.route('/clientes/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar_cliente(id):
    c = Cliente.query.get_or_404(id)
    if request.method == 'POST':
        c.nombre = request.form['nombre']
        c.email = request.form.get('email')
        c.telefono = request.form.get('telefono')
        c.empresa = request.form.get('empresa')
        c.notas = request.form.get('notas')
        db.session.commit()
        flash('Cliente actualizado.', 'ok')
        return redirect(url_for('clientes'))
    return render_template('cliente_form.html', cliente=c)

@app.route('/clientes/<int:id>/eliminar', methods=['POST'])
@login_required
def eliminar_cliente(id):
    c = Cliente.query.get_or_404(id)
    db.session.delete(c)
    db.session.commit()
    flash('Cliente eliminado.', 'warn')
    return redirect(url_for('clientes'))

# ─── PRODUCTOS ────────────────────────────────────────────────────────────────

@app.route('/productos')
@login_required
def productos():
    q = request.args.get('q', '')
    cat = request.args.get('cat', '')
    query = Producto.query
    if q:
        query = query.filter(Producto.nombre.ilike(f'%{q}%'))
    if cat:
        query = query.filter_by(categoria=cat)
    lista = query.order_by(Producto.created_at.desc()).all()
    categorias = db.session.query(Producto.categoria).distinct().all()
    categorias = [c[0] for c in categorias if c[0]]
    return render_template('productos.html', productos=lista, categorias=categorias, q=q, cat=cat)

@app.route('/productos/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo_producto():
    if request.method == 'POST':
        p = Producto(
            nombre=request.form['nombre'],
            descripcion=request.form.get('descripcion'),
            precio=float(request.form['precio']),
            stock=int(request.form.get('stock', 0)),
            categoria=request.form.get('categoria')
        )
        db.session.add(p)
        db.session.commit()
        flash('Producto añadido.', 'ok')
        return redirect(url_for('productos'))
    return render_template('producto_form.html', producto=None)

@app.route('/productos/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar_producto(id):
    p = Producto.query.get_or_404(id)
    if request.method == 'POST':
        p.nombre = request.form['nombre']
        p.descripcion = request.form.get('descripcion')
        p.precio = float(request.form['precio'])
        p.stock = int(request.form.get('stock', 0))
        p.categoria = request.form.get('categoria')
        db.session.commit()
        flash('Producto actualizado.', 'ok')
        return redirect(url_for('productos'))
    return render_template('producto_form.html', producto=p)

@app.route('/productos/<int:id>/eliminar', methods=['POST'])
@login_required
def eliminar_producto(id):
    p = Producto.query.get_or_404(id)
    db.session.delete(p)
    db.session.commit()
    flash('Producto eliminado.', 'warn')
    return redirect(url_for('productos'))

# ─── FACTURAS ─────────────────────────────────────────────────────────────────

@app.route('/facturas')
@login_required
def facturas():
    estado = request.args.get('estado', '')
    query = Factura.query
    if estado:
        query = query.filter_by(estado=estado)
    lista = query.order_by(Factura.fecha.desc()).all()
    return render_template('facturas.html', facturas=lista, estado=estado)

@app.route('/facturas/nueva', methods=['GET', 'POST'])
@login_required
def nueva_factura():
    clientes_list = Cliente.query.order_by(Cliente.nombre).all()
    if request.method == 'POST':
        base = float(request.form['base'])
        iva = float(request.form.get('iva', 21))
        total = base * (1 + iva / 100)
        count = Factura.query.count() + 1
        numero = f"FAC-{datetime.now().year}-{count:04d}"
        f = Factura(
            numero=numero,
            cliente_id=int(request.form['cliente_id']),
            concepto=request.form['concepto'],
            base=base,
            iva=iva,
            total=total,
            estado=request.form.get('estado', 'pendiente')
        )
        db.session.add(f)
        db.session.commit()
        flash(f'Factura {numero} creada.', 'ok')
        return redirect(url_for('facturas'))
    return render_template('factura_form.html', factura=None, clientes=clientes_list)

@app.route('/facturas/<int:id>/estado', methods=['POST'])
@login_required
def cambiar_estado_factura(id):
    f = Factura.query.get_or_404(id)
    f.estado = request.form['estado']
    db.session.commit()
    return redirect(url_for('facturas'))

@app.route('/facturas/<int:id>/eliminar', methods=['POST'])
@login_required
def eliminar_factura(id):
    f = Factura.query.get_or_404(id)
    db.session.delete(f)
    db.session.commit()
    flash('Factura eliminada.', 'warn')
    return redirect(url_for('facturas'))

# ─── CHATBOT ──────────────────────────────────────────────────────────────────

@app.route('/chat')
@login_required
def chat():
    historial = MensajeChat.query.order_by(MensajeChat.created_at).all()
    return render_template('chat.html', historial=historial)

@app.route('/chat/enviar', methods=['POST'])
@login_required
def chat_enviar():
    data = request.get_json()
    mensaje = data.get('mensaje', '').strip()
    if not mensaje:
        return jsonify({'error': 'Mensaje vacío'}), 400

    db.session.add(MensajeChat(rol='user', contenido=mensaje))
    db.session.commit()

    clientes_count = Cliente.query.count()
    productos_count = Producto.query.count()
    ingresos = db.session.query(db.func.sum(Factura.total)).filter_by(estado='pagada').scalar() or 0

    system_prompt = f"""Eres el asistente de atención al cliente de BizCore, una plataforma de gestión para pequeñas empresas.
Datos actuales del negocio: {clientes_count} clientes registrados, {productos_count} productos, {ingresos:.2f}€ en ingresos.
Responde de forma profesional, concisa y útil. Si te preguntan por funcionalidades, explica las secciones: Clientes, Productos, Facturas y este Chat.
Responde siempre en español."""

    historial = MensajeChat.query.order_by(MensajeChat.created_at).all()
    messages = [{"role": m.rol, "content": m.contenido} for m in historial]

    try:
        resp = requests.post(f"{OLLAMA_URL}/api/chat", json={
            "model": OLLAMA_MODEL,
            "messages": [{"role": "system", "content": system_prompt}] + messages,
            "stream": False
        }, timeout=30)
        resp.raise_for_status()
        respuesta = resp.json()['message']['content']
    except Exception as e:
        respuesta = f"Error al conectar con el modelo IA: {str(e)}"

    db.session.add(MensajeChat(rol='assistant', contenido=respuesta))
    db.session.commit()
    return jsonify({'respuesta': respuesta})

@app.route('/chat/limpiar', methods=['POST'])
@login_required
def chat_limpiar():
    MensajeChat.query.delete()
    db.session.commit()
    return redirect(url_for('chat'))

if __name__ == '__main__':
    app.run(debug=True)
