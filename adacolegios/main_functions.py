from functools import wraps
from flask import session, flash, redirect, url_for

# Verifica que el usuario haya iniciado sesion
def verificar_loggeado(f):
	@wraps(f)
	def wrap(*args, **kwargs):
		if 'loggeado' in session:
			return f(*args, **kwargs)
		else:
			flash('Si desea dirigirse a esa página primero debe iniciar sesión.', 'danger')
			return redirect(url_for('inicio_sesion'))
	return wrap

# Verifica que el usuario haya cerrado sesión
def verificar_no_loggeado(l):
	@wraps(l)
	def wrap(*args, **kwargs):
		if not 'loggeado' in session:
			return l(*args, **kwargs)
		# Chequear por qué cuando entro después de prender la pc me sale este cartel de abajo
		else:
			flash('Si desea dirigirse a esa página primero debe cerrar sesión.', 'danger')
			return redirect(url_for('index'))
	return wrap

# Verifica que el usuario sea profesor
# Parametrizarlo para que verifique el tipo de usuario necesario
def es_profesor(g):
	@wraps(g)
	def wrap(*args, **kwargs):
		if session['tipo_de_usuario'] == 'profesor':
			return g(*args, **kwargs)
		else:
			flash('Acceso no autorizado para su tipo de usuario.', 'danger')
			return redirect(url_for('index'))
	return wrap