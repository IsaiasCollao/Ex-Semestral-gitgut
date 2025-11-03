import sqlite3
from flask import Flask, request, render_template, redirect, url_for, session, flash
from login import login_bp  # Importar el Blueprint de login

app = Flask(__name__)
app.secret_key = 'tu_clave_secreta_aqui'  # Necesario para manejar sesiones

# Registrar el Blueprint de login
app.register_blueprint(login_bp)


productos = [
    {'id': 1, 'nombre': 'Lingote de Oro', 'precio': 500, 'imagen': 'oro.png'},
    {'id': 2, 'nombre': 'Lingote de Diamante', 'precio': 1000, 'imagen': 'diamante.png'},
    {'id': 3, 'nombre': 'Lingote de Hierro', 'precio': 200, 'imagen': 'hierro.png'},
]


@app.route('/agregar/<int:id>')
def agregar(id):
    producto = next((item for item in productos if item["id"] == id), None)
    if producto:
        if 'carrito' not in session:
            session['carrito'] = []
        session['carrito'].append(producto)
        flash(f'Producto {producto["nombre"]} agregado al carrito.')
    return redirect(url_for('catalogo'))

@app.route('/carrito')
def ver_carrito():
    carrito = session.get('carrito', [])
    total = sum(item['precio'] for item in carrito)
    return render_template('carrito.html', titulo="Carrito de Compras", productos=carrito, total=total)

@app.route('/vaciar-carrito')
def vaciar_carrito():
    session.pop('carrito', None)
    return redirect(url_for('ver_carrito'))


@app.route('/catalogo')
def catalogo():
    return render_template('catalogo.html', titulo="Catálogo de Lingotes", productos=productos)

@app.route('/')
def inicio():
    return render_template('principal.html', titulo="Página Principal", productos=productos)


@app.route('/formulario')
def formulario():
    return render_template('formulario.html', titulo="Formulario de Compra", productos=productos)


@app.route('/generar_factura')
def generar_factura():
    carrito_session = session.get('carrito', [])
    carrito_para_factura = []
    for item in carrito_session:
        if isinstance(item, dict):
            nombre = item.get('nombre') or item.get('name') or str(item)
            precio = item.get('precio') or item.get('price') or 0
            carrito_para_factura.append((None, nombre, None, precio))
        else:
            carrito_para_factura.append(item)



    total = sum(float(it[3]) for it in carrito_para_factura)
    iva = round(total * 0.16, 2)
    total_con_iva = round(total + iva, 2)

    return render_template('factura.html',
                           carrito=carrito_para_factura,
                           total=total,
                           iva=iva,
                           total_con_iva=total_con_iva)


@app.route('/factura/<int:factura_id>')
def ver_factura(factura_id):
    # Mostrar la factura guardada en la base de datos
    conn = sqlite3.connect('database/mi_base_de_datos.db')
    cursor = conn.cursor()

    cursor.execute('SELECT orden_id, total, iva, total_con_iva, fecha_registro FROM factura WHERE id = ?', (factura_id,))
    f = cursor.fetchone()
    if not f:
        conn.close()
        flash('Factura no encontrada', 'error')
        return redirect(url_for('inicio'))

    orden_id, total, iva, total_con_iva, fecha = f

    # Obtener items de la orden
    cursor.execute('SELECT producto, cantidad, precio FROM orden_item WHERE orden_id = ?', (orden_id,))
    items = cursor.fetchall()

    # Construir estructura compatible con factura.html (item[1]=nombre, item[3]=precio)
    carrito_para_factura = []
    for it in items:
        nombre, cantidad, precio = it
        # usamos la tupla (None, nombre, cantidad, precio) para mantener compatibilidad
        carrito_para_factura.append((None, nombre, cantidad, precio))

    # Obtener datos del cliente
    cursor.execute('SELECT c.nombre, c.email, c.direccion FROM cliente c JOIN orden o ON o.cliente_id = c.id WHERE o.id = ?', (orden_id,))
    cliente = cursor.fetchone()

    conn.close()

    return render_template('factura.html', carrito=carrito_para_factura, total=total, iva=iva, total_con_iva=total_con_iva, cliente=cliente)




@app.route('/procesar_formulario', methods=['POST'])
def procesar_formulario():
    # Validación básica de campos requeridos
    nombre = request.form.get('nombre', '').strip()
    email = request.form.get('email', '').strip()
    direccion = request.form.get('direccion', '').strip()

    if not nombre or not email or not direccion:
        flash('Por favor complete los campos obligatorios: nombre, email y dirección', 'error')
        return redirect(url_for('formulario'))

    # Obtener carrito de la sesión
    carrito = session.get('carrito', [])
    if not carrito:
        flash('El carrito está vacío. Agrega productos antes de finalizar la compra.', 'error')
        return redirect(url_for('catalogo'))

    # Guardar cliente y órdenes en la base de datos
    conn = sqlite3.connect('database/mi_base_de_datos.db')
    cursor = conn.cursor()

    # Insertar cliente y obtener su id
    cursor.execute("INSERT INTO cliente (nombre, email, direccion, empresa) VALUES (?, ?, ?, ?)",
                   (nombre, email, direccion, ""))
    cliente_id = cursor.lastrowid

    # Crear encabezado de orden
    cursor.execute('INSERT INTO orden (cliente_id) VALUES (?)', (cliente_id,))
    orden_id = cursor.lastrowid

    # Insertar items de la orden
    for item in carrito:
        if isinstance(item, dict):
            producto = item.get('nombre') or item.get('name') or str(item)
            precio = item.get('precio') or item.get('price') or 0
            cantidad = item.get('cantidad', 1)
        else:
            producto = item[1] if len(item) > 1 else str(item)
            precio = item[3] if len(item) > 3 else 0
            cantidad = 1

        cursor.execute('SELECT id FROM productos WHERE nombre = ?', (producto,))
        prod_row = cursor.fetchone()
        prod_id = prod_row[0] if prod_row else None

        cursor.execute("INSERT INTO orden_item (orden_id, producto_id, producto, cantidad, precio) VALUES (?, ?, ?, ?, ?)",
                       (orden_id, prod_id, producto, cantidad, precio))

    # Calcular totales para la factura
    cursor.execute('SELECT SUM(cantidad * precio) FROM orden_item WHERE orden_id = ?', (orden_id,))
    total_row = cursor.fetchone()
    total = float(total_row[0]) if total_row and total_row[0] is not None else 0.0
    iva = round(total * 0.16, 2)
    total_con_iva = round(total + iva, 2)

    # Insertar factura
    cursor.execute('INSERT INTO factura (orden_id, total, iva, total_con_iva) VALUES (?, ?, ?, ?)',
                   (orden_id, total, iva, total_con_iva))
    factura_id = cursor.lastrowid

    conn.commit()
    conn.close()

    # Limpiar carrito y redirigir a la vista de la factura recién creada
    session.pop('carrito', None)
    flash('Compra finalizada correctamente. Mostrando factura.', 'success')
    return redirect(url_for('ver_factura', factura_id=factura_id))

def crear_base_datos():
    """Función para crear las tablas de la base de datos"""
    conn = sqlite3.connect('database/mi_base_de_datos.db')
    cursor = conn.cursor()
    # Tabla de clientes
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS cliente (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        email TEXT NOT NULL,
        direccion TEXT,
        empresa TEXT
    )
    ''')

    # Tabla de productos (catálogo)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS productos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL UNIQUE,
        precio REAL NOT NULL,
        imagen TEXT
    )
    ''')

    # Tabla de órdenes (encabezado)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS orden (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cliente_id INTEGER NOT NULL,
        fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(cliente_id) REFERENCES cliente(id)
    )
    ''')

    # Tabla de items de orden (detalles)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS orden_item (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        orden_id INTEGER NOT NULL,
        producto_id INTEGER,
        producto TEXT NOT NULL,
        cantidad INTEGER NOT NULL,
        precio REAL,
        FOREIGN KEY(orden_id) REFERENCES orden(id),
        FOREIGN KEY(producto_id) REFERENCES productos(id)
    )
    ''')

    # Tabla de facturas
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS factura (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        orden_id INTEGER NOT NULL,
        total REAL,
        iva REAL,
        total_con_iva REAL,
        fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(orden_id) REFERENCES orden(id)
    )
    ''')

    # Tabla de usuarios (para login simple, se mantiene)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        contraseña TEXT NOT NULL
    )
    ''')

    # Poblamos la tabla de productos con los items iniciales si no existen
    for p in productos:
        cursor.execute('SELECT id FROM productos WHERE nombre = ?', (p['nombre'],))
        if cursor.fetchone() is None:
            cursor.execute('INSERT INTO productos (nombre, precio, imagen) VALUES (?, ?, ?)',
                           (p['nombre'], p['precio'], p.get('imagen')))

    conn.commit()
    conn.close()

if __name__ == '__main__':
    # Crear base de datos y tablas al iniciar la aplicación
    crear_base_datos()
    app.run(debug=True)