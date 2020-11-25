from adacolegios import app
from flask import render_template, request, flash, session, redirect, url_for
from passlib.handlers.sha2_crypt import sha256_crypt
from adacolegios.main_functions import verificar_no_loggeado, verificar_loggeado
import pyodbc

#Verificador no logeado
from functools import wraps

# Conexión a la base de datos SQL Server

conx_string = ('DRIVER={ODBC Driver 17 for SQL Server};SERVER='+app.config["DB_SERVER"]+';DATABASE='+app.config["DB_NAME"]+';UID='+app.config["DB_USERNAME"]+';PWD='+app.config["DB_PASSWORD"]+'')

@app.route('/index')
@app.route('/', methods=['GET', 'POST'])
def index():
	return render_template('auth/index.html')

@app.route('/inicio_sesion', methods=['GET', 'POST'])
@verificar_no_loggeado
def inicio_sesion():
	#Ver si hace falta esto o era para Windows
	#app_name = os.getenv("APP_NAME")
	if request.method == 'POST':
		email_formulario = request.form['email']
		contraseña = request.form['contraseña']
		if email_formulario == "" or contraseña == "":
			flash('Debe completar todos los campos.', 'danger')
		else:
			try: 
				with pyodbc.connect(conx_string) as conx:
					cursor = conx.cursor()
					cursor.execute('EXEC SP_BuscaDatosUsuario_InicioSesion @ema = ?', email_formulario)
					datos_usuario = cursor.fetchone()
				email_base_datos = datos_usuario[0]
				# ver si hace falta el str aca abajo
				tipo_de_usuario = str(datos_usuario[2])
				dni = datos_usuario[3]
				if email_base_datos == email_formulario:
					contraseña_base_datos = datos_usuario[1]
					# Comparo las contraseñas
					if sha256_crypt.verify(contraseña, contraseña_base_datos):
						session['loggeado'] = True
						session['email'] = email_base_datos
						session['dni'] = dni
						# Parametrizar para que sea con cualquier tipo de usuario
						if tipo_de_usuario == 'Profesor':
							session['tipo_de_usuario'] = 'profesor'
						elif tipo_de_usuario == 'Alumno':
							session['tipo_de_usuario'] = 'alumno'
						return redirect(url_for('index'))
					else:
						flash('La contraseña ingresada es incorrecta.', 'danger')
			except TypeError:
				flash('El email ingresado no es correcto o no existe. Por favor, revisalo e intenta nuevamente.', 'danger')
	return render_template('auth/inicio_sesion.html')

@app.route('/cerrar_sesion')
@verificar_loggeado
def cerrar_sesion():
	session.clear()
	flash('Has cerrado sesión.', 'success')
	return redirect(url_for('index'))

@app.route('/recuperar_contraseña', methods=['GET', 'POST'])
@verificar_no_loggeado
def recuperar_contraseña():
	return render_template('auth/recuperar_contraseña.html')

@app.route('/recuperar_contraseña/<token>')
@verificar_no_loggeado
def recuperar_contraseña_token(token):
	return render_template('auth/restablecer_contraseña_token.html')