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


@app.route('/agregar-compra', methods=['POST'])
def agregar_compra():
    nombre = request.form['nombre']
    email = request.form['email']
    direccion = request.form['direccion']
    producto = request.form['producto']
    cantidad = request.form['cantidad']
    precio = request.form['precio']

    conn = sqlite3.connect('database/mi_base_de_datos.db')
    cursor = conn.cursor()
    
    # Insertar cliente
    cursor.execute("INSERT INTO cliente (nombre, email, direccion, empresa) VALUES (?, ?, ?, ?)", 
                   (nombre, email, direccion, ""))
    # Insertar orden de compra
    cursor.execute("INSERT INTO ordencompra (producto, cantidad, precio) VALUES (?, ?, ?)",
                   (producto, cantidad, precio))
    conn.commit()
    conn.close()
    
    mensaje = "¡Compra agregada correctamente!"
    return render_template('formulario.html', mensaje=mensaje)

def crear_base_datos():
    """Función para crear las tablas de la base de datos"""
    conn = sqlite3.connect('database/mi_base_de_datos.db')
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS ordencompra (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        producto TEXT NOT NULL,
        cantidad TEXT NOT NULL,
        precio INTEGER,
        fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        nombre TEXT NOT NULL,
        contraseña TEXT NOT NULL
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS cliente (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        nombre TEXT NOT NULL,
        email TEXT NOT NULL,
        direccion TEXT,
        empresa TEXT
    )
    ''')
    
    conn.commit()
    conn.close()

if __name__ == '__main__':
    # Crear base de datos y tablas al iniciar la aplicación
    crear_base_datos()
    app.run(debug=True)