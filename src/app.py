import sqlite3
from flask import Flask, request, render_template



app = Flask(__name__)

@app.route('/')
def inicio():
    return render_template('principal.html')

@app.route('/formulario')
def formulario():
    return render_template('formulario.html')

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

if __name__ == '__main__':
    app.run(debug=True)



# Conectar (si no existe, se crea la base de datos)
conn = sqlite3.connect('database/mi_base_de_datos.db')


# Crear un cursor para ejecutar comandos SQL
cursor = conn.cursor()


# Crear una tabla (si no existe)
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
    direccion,
    empresa TEXT NOT NULL
)
''')


# Confirmar los cambios
conn.commit()

# Cerrar la conexión a la base de datos
conn.close()



# Crear usuario
def crear_usuario(nombre, email):
    conn = sqlite3.connect('mi_base_de_datos.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute("INSERT INTO usuarios (nombre, email) VALUES (?, ?)", (nombre, email))
        conn.commit()
        print("Usuario creado correctamente.")
    except sqlite3.IntegrityError:
        print("El email ya está registrado.")
    finally:
        conn.close()

# Leer todos los usuarios
def obtener_usuarios():
    conn = sqlite3.connect('mi_base_de_datos.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM usuarios")
    usuarios = cursor.fetchall()
    
    conn.close()
    
    return usuarios

# Actualizar usuario
def actualizar_usuario(id_usuario, nuevo_nombre, nuevo_email):
    conn = sqlite3.connect('mi_base_de_datos.db')
    cursor = conn.cursor()
    
    cursor.execute("UPDATE usuarios SET nombre = ?, email = ? WHERE id = ?", 
                   (nuevo_nombre, nuevo_email, id_usuario))
    conn.commit()
    
    conn.close()
    print("Usuario actualizado correctamente.")

# Eliminar usuario
def eliminar_usuario(id_usuario):
    conn = sqlite3.connect('mi_base_de_datos.db')
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM usuarios WHERE id = ?", (id_usuario,))
    conn.commit()
    
    conn.close()
    print("Usuario eliminado correctamente.")
