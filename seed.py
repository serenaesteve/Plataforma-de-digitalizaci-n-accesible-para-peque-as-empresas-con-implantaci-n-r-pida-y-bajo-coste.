"""
seed.py — Datos de prueba para BizCore
Ejecutar: python seed.py
"""
from app import app
from models import db, Cliente, Producto, Factura
from datetime import datetime, timedelta
import random

with app.app_context():
    db.create_all()

    # Clientes
    clientes = [
        Cliente(nombre="María García", email="maria@empresa.com", telefono="612345678", empresa="García & Asociados", notas="Cliente desde 2023"),
        Cliente(nombre="Carlos López", email="carlos@techsol.es", telefono="698765432", empresa="TechSol SL"),
        Cliente(nombre="Ana Martínez", email="ana@creativos.es", empresa="Creativos Studio"),
        Cliente(nombre="Pedro Sánchez", email="pedro@pyme.com", telefono="655111222", empresa="Pyme Solutions"),
        Cliente(nombre="Laura Fernández", email="laura@lf.es"),
    ]
    db.session.add_all(clientes)
    db.session.commit()

    # Productos
    productos = [
        Producto(nombre="Consultoría básica", descripcion="1 hora de consultoría estratégica", precio=90.0, stock=999, categoria="Consultoría"),
        Producto(nombre="Pack mantenimiento web", descripcion="Mantenimiento mensual de sitio web", precio=149.0, stock=999, categoria="Web"),
        Producto(nombre="Diseño de logotipo", descripcion="Logotipo profesional + manual de marca", precio=350.0, stock=50, categoria="Diseño"),
        Producto(nombre="Setup CRM", descripcion="Implantación y formación BizCore", precio=499.0, stock=20, categoria="Software"),
        Producto(nombre="Licencia anual Pro", descripcion="Acceso completo durante 12 meses", precio=199.0, stock=999, categoria="Software"),
    ]
    db.session.add_all(productos)
    db.session.commit()

    # Facturas
    estados = ['pagada', 'pagada', 'pendiente', 'pendiente', 'cancelada']
    conceptos = [
        "Consultoría estratégica — 3 sesiones",
        "Mantenimiento web — Enero 2025",
        "Diseño logotipo corporativo",
        "Licencia anual Pro + onboarding",
        "Pack diseño web completo",
    ]
    bases = [270.0, 149.0, 350.0, 499.0, 800.0]

    for i, c in enumerate(clientes):
        base = bases[i]
        iva = 21.0
        total = base * 1.21
        f = Factura(
            numero=f"FAC-2025-{i+1:04d}",
            cliente_id=c.id,
            concepto=conceptos[i],
            base=base,
            iva=iva,
            total=total,
            estado=estados[i],
            fecha=datetime.utcnow() - timedelta(days=random.randint(1, 60))
        )
        db.session.add(f)

    db.session.commit()
    print("✓ Base de datos poblada con datos de prueba.")
    print(f"  {len(clientes)} clientes · {len(productos)} productos · 5 facturas")
