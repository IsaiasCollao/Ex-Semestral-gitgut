from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import random

app = Flask(__name__)

# Configuración de la base de datos
DATABASE = 'database.db'

# Crear la base de datos y agregar los productos si no existen
def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Crear la tabla de productos
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS productos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        descripcion TEXT NOT NULL,
        precio REAL NOT NULL
    )
    ''')

    # Insertar productos si la tabla está vacía
    cursor.execute('SELECT COUNT(*) FROM productos')
    if cursor.fetchone()[0] == 0:
        productos = [
            ('Producto 1', 'Descripción del Producto 1', 100),
            ('Producto 2', 'Descripción del Producto 2', 150),
            ('Producto 3', 'Descripción del Producto 3', 200)
        ]
        cursor.executemany('INSERT INTO productos (nombre, descripcion, precio) VALUES (?, ?, ?)', productos)

    conn.commit()
    conn.close()

init_db()


@app.route('/')
def index():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM productos')
    productos = cursor.fetchall()
    conn.close()
    return render_template('index.html', productos=productos)

# Lista de productos en el carrito
carrito = []

@app.route('/agregar_al_carrito/<int:producto_id>')
def agregar_al_carrito(producto_id):
    # Buscar el producto en la base de datos
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM productos WHERE id = ?', (producto_id,))
    producto = cursor.fetchone()
    conn.close()

    if producto:
        # Verificar si el producto ya está en el carrito
        for item in carrito:
            if item['producto'][0] == producto[0]:  # Compara el ID del producto
                item['cantidad'] += 1  # Incrementa la cantidad
                break
        else:
            # Si el producto no está en el carrito, agregarlo con cantidad 1
            carrito.append({'producto': producto, 'cantidad': 1})

    return redirect(url_for('index'))


@app.route('/carrito')
def carrito_view():
    total = 0
    for item in carrito:
        producto = item.get('producto', {})
        cantidad = item.get('cantidad', 1)

        # If producto is a dict with 'precio'
        if isinstance(producto, dict):
            precio = producto.get('precio', 0)
        # If producto is a list or tuple, assume price is at index 3
        elif isinstance(producto, (list, tuple)) and len(producto) > 3:
            precio = producto[3]
        else:
            precio = 0

        total += precio * cantidad

    iva = total * 0.16
    total_con_iva = total + iva
    return render_template(
        'carrito.html',
        carrito=carrito,
        total=total,
        iva=iva,
        total_con_iva=total_con_iva
    )



@app.route('/pagar')
def pagar():
    total = sum(item['producto'][3] * item['cantidad'] for item in carrito)
    iva = total * 0.16
    total_con_iva = total + iva

    return render_template('factura.html', carrito=carrito, total=total, iva=iva, total_con_iva=total_con_iva)



if __name__ == '__main__':
    app.run(debug=True)
