from flask import Blueprint, request, render_template, redirect, url_for, session, flash

# Crear el Blueprint para login
login_bp = Blueprint('login', __name__)

# Usuarios simulados (normalmente usarías una base de datos)
usuarios = {
    'usuario1': 'password1',
    'usuario2': 'password2'
}


@login_bp.route('/logout')
def logout():
    session.pop('usuario', None)
    flash('Has cerrado sesión', 'info')
    return redirect(url_for('login.login'))


@login_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form['usuario']
        password = request.form['password']

        if usuario in usuarios and usuarios[usuario] == password:
            session['usuario'] = usuario
            flash('¡Has iniciado sesión correctamente!', 'success')
            return redirect(url_for('inicio'))
        else:
            flash('Usuario o contraseña incorrectos', 'error')
    
    return render_template('login.html')

@login_bp.route('/protected')
def protected():
    if 'usuario' not in session:
        flash('Debes iniciar sesión para acceder a esta página', 'error')
        return redirect(url_for('login.login'))
    
    return f"¡Bienvenido a la página protegida, {session['usuario']}!"