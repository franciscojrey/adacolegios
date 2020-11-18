from adacolegios import app
from flask import request, render_template, flash, redirect, url_for
from wtforms import Form, StringField
from datetime import date
from passlib.handlers.sha2_crypt import sha256_crypt
import pyodbc
import re

# Conexión a la base de datos SQL Server
conx_string = ('DRIVER={ODBC Driver 17 for SQL Server};SERVER='+app.config["DB_SERVER"]+';DATABASE='+app.config["DB_NAME"]+';UID='+app.config["DB_USERNAME"]+';PWD='+app.config["DB_PASSWORD"]+'')

class PerfilFormulario(Form):
	codigo_formulario = StringField('Código')
	nombre = StringField('Nombre')
	nombre_completo = StringField('Nombre completo')

@app.route('/registro', methods=['GET', 'POST'])
#@verificar_no_loggeado
def registro():
	with pyodbc.connect(conx_string) as conx:
		cursor = conx.cursor()
		cursor.execute('EXEC SP_PerfilesRegistro')
		perfiles = cursor.fetchall()
	if request.method == 'POST':
		try:
			email = request.form['email']
			contraseña = request.form['contraseña']
			contraseña_repetida = request.form['contraseña_repetida']
			tipo_de_usuario = request.form['tipo_de_usuario']
			dni_formulario = request.form['dni']
			today = date.today()
			fecha_de_alta = today.strftime("%d/%m/%Y")
			# Chequeo del campo DNI
			dni_solo_numeros = True
			dni_formulario_ingresado = True
			campo_tipo_de_usuario_incorrecto = False
			dni_largo_correcto = True
			try:
				dni = int(dni_formulario)
				dni_formulario_fue_utilizado = False
				with pyodbc.connect(conx_string) as conx:
					cursor = conx.cursor()
					cursor.execute('EXEC SP_BuscaDniFormulario_Registro @dni = ?', dni)
					resultado_busca_dni = cursor.fetchone()
					if resultado_busca_dni:
						dni_formulario_fue_utilizado = True
				dni_formulario_existe = False
				# Hay que hacer stored procedures con los otros tipos de usuario
				try:
					cursor = conx.cursor()
					if tipo_de_usuario == "Alumno":
						cursor.execute('EXEC SP_BuscaDniAlumno_Registro @dni = ?', dni)
					elif tipo_de_usuario == "Profesor":
						cursor.execute('EXEC SP_BuscaDniDocente_Registro @dni = ?', dni)
					elif tipo_de_usuario == "Preceptor":
						cursor.execute('EXEC SP_BuscaDniDocente_Registro @dni = ?', dni)
					elif tipo_de_usuario == "Administrador":
						cursor.execute('EXEC SP_BuscaDniDocente_Registro @dni = ?', dni)
					resultado_busca_dni = cursor.fetchone()
					if resultado_busca_dni[0] == dni:
						dni_formulario_existe = True		
				except TypeError:
					dni_formulario_existe = False	
				except pyodbc.ProgrammingError:
					campo_tipo_de_usuario_incorrecto = True
				
			except ValueError:
				if len(dni_formulario) == 0:
					dni_formulario_ingresado = False
				# Chequear que solo deje poner números con esto de abajo, no se si elimina todas las posibilidades
				else:
					dni_solo_numeros = False
			except OverflowError:
				dni_largo_correcto = False
			except pyodbc.ProgrammingError:
				dni_largo_correcto = False

			espacios_en_contraseña = 0
			for i in contraseña:
				if(i.isspace()):
					espacios_en_contraseña=espacios_en_contraseña+1
			
			espacios_en_email = 0
			for i in email:
				if(i.isspace()):
					espacios_en_email=espacios_en_email+1

			numeros_en_contraseña = 0
			for i in contraseña:
				if(i.isdigit()):
					numeros_en_contraseña=numeros_en_contraseña+1

			if email == "":
				flash('Debe ingresar una dirección de correo electrónico.', 'danger')
			elif email.count('@')!=1 or email.rfind('@')==(len(email)-1) or email.find('@')==0 or email.count('.')!=1 or email.rfind('.')==(len(email)-1) or email.find('.')==0 or espacios_en_email>0:
				flash('La dirección de correo ingresada no es correcta.', 'danger')
			elif len(email)<8 or len(email)>80:
				flash('La dirección de correo debe tener un mínimo de 8 carácteres y un máximo de 80.', 'danger')
			elif contraseña == "":
				flash('Debe ingresar una contraseña.', 'danger')
			elif len(contraseña)<8 or len(contraseña)>20:
				flash('La contraseña debe tener un mínimo de 8 carácteres y un máximo de 20.', 'danger')
			elif contraseña != contraseña_repetida:
				flash('Las contraseñas ingresadas no coinciden.', 'danger')
			elif len(re.findall(r'[A-Z]', contraseña))<1:
				flash('La contraseña debe tener como mínimo una letra mayúscula.', 'danger')
			elif len(re.findall(r'[a-z]', contraseña))<1:
				flash('La contraseña debe tener como mínimo una letra minúscula.', 'danger')
			elif espacios_en_contraseña>0:
				flash('La contraseña no puede contener espacios en blanco.', 'danger')
			elif numeros_en_contraseña<2:
				flash('La contraseña debe tener 2 o más números.', 'danger')
			# Ver si estos 2 de abajo no son repetitivos
			elif campo_tipo_de_usuario_incorrecto == True:
				flash('Debe especificar el tipo de usuario.', 'danger')
			elif tipo_de_usuario!="Profesor" and tipo_de_usuario!="Administrativo" and tipo_de_usuario!="Preceptor" and tipo_de_usuario!="Alumno":
				flash('El tipo de usuario ingresado no es válido.', 'danger')
			elif dni_formulario_ingresado == False:
				flash('Debe ingresar un DNI.', 'danger')
			elif dni_solo_numeros == False:
				flash('El DNI ingresado no es válido.', 'danger')
			elif dni_formulario_fue_utilizado == True:
				flash('Ya existe un usuario con el DNI ingresado.', 'danger')
			elif len(str(dni))<=6 or len(str(dni))>=9 or dni_largo_correcto == False:
				flash('El DNI debe tener entre 7 y 9 caracteres.', 'danger')
			# Hay que hacer que busque el dni de administrativos y preceptores también
			elif dni_formulario_existe == False:
				flash('El DNI ingresado no coincide con ningún registro de la base de datos.', 'danger')
			else:
				with pyodbc.connect(conx_string) as conx:
					contraseña = sha256_crypt.encrypt(str(contraseña)) 
					cursor = conx.cursor()
					cursor.execute('EXEC SP_RegistrarUsuario_Registro @email = ?, @contraseña = ?, @fecha_de_alta = ?, @tipo_de_usuario = ?, @dni = ?', (email, contraseña, fecha_de_alta, tipo_de_usuario, dni))
					flash('Su cuenta se ha registrado con éxito.', 'success')
		except pyodbc.IntegrityError:
			flash('Ya existe una cuenta con el email ingresado.', 'danger')
	return render_template('perfiles/registro.html', perfiles = perfiles)

@app.route('/administrar_perfiles', methods=['GET', 'POST'])
def administrar_perfiles():
	try:
		with pyodbc.connect(conx_string) as conx:
			cursor = conx.cursor()
			cursor.execute('EXEC SP_VerPerfiles')
			perfiles = cursor.fetchall()
			return render_template('perfiles/administrar_perfiles.html', perfiles=perfiles)
	except TypeError:
		flash('No se encontraron perfiles.', 'warning')
		return render_template('perfiles/administrar_perfiles.html')
	
@app.route('/agregar_perfil', methods=['GET', 'POST'])
def agregar_perfil():
	if request.method == 'POST':
		codigo_perfil = request.form['codigo_perfil']
		nombre_perfil = request.form['nombre_perfil']
		with pyodbc.connect(conx_string) as conx:
			cursor = conx.cursor()
			cursor.execute('EXEC SP_AgregarPerfil @codigo = ?, @nombre = ?', (codigo_perfil, nombre_perfil))
		flash('Tarea creada correctamente.', 'success')
		return redirect(url_for('administrar_perfiles'))
	return render_template('perfiles/agregar_perfil.html')

@app.route('/editar_perfil/<codigo>', methods=['GET', 'POST'])
def editar_perfil(codigo):
	with pyodbc.connect(conx_string) as conx:
		cursor = conx.cursor()
		cursor.execute('EXEC SP_VerPerfilAEditar @codigo = ?', codigo)
		perfil = cursor.fetchone()
	form = PerfilFormulario(request.form)
	form.codigo_formulario.data = perfil[0]
	form.nombre.data = perfil[1]
	if request.method == 'POST':
		codigo_formulario = request.form['codigo_formulario']
		nombre = request.form['nombre']
		with pyodbc.connect(conx_string) as conx:
			cursor = conx.cursor()
			cursor.execute('EXEC SP_EditarPerfil @codigo_formulario = ?, @nombre = ?, @codigo=?', (codigo_formulario, nombre, codigo))
		flash('Perfil editado correctamente.', 'success')
		return redirect(url_for('administrar_perfiles'))
		# Agregar esto cuando agregue las validaciones y haya errores, para que no se borren los cambios ingresados
		#form.codigo.data = codigo
		#form.nombre.data = nombre
	return render_template('perfiles/editar_perfil.html', form=form)

@app.route('/eliminar_perfil/<string:codigo>', methods=['POST'])
def eliminar_perfil(codigo):
	with pyodbc.connect(conx_string) as conx:
		cursor = conx.cursor()
		cursor.execute('EXEC SP_EliminarPerfil @codigo = ?', codigo)
	flash('Perfil eliminado correctamente.', 'success')
	return redirect(url_for('administrar_perfiles'))