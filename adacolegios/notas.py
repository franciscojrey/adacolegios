from adacolegios import app
from flask import session, render_template, request, flash, redirect, url_for
from adacolegios.main_functions import verificar_loggeado, es_profesor
import datetime
import pyodbc
import itertools

# Conexión a la base de datos SQL Server

conx_string = ('DRIVER={ODBC Driver 17 for SQL Server};SERVER='+app.config["DB_SERVER"]+';DATABASE='+app.config["DB_NAME"]+';UID='+app.config["DB_USERNAME"]+';PWD='+app.config["DB_PASSWORD"]+'')

@app.route('/cargar_notas', methods=['POST', 'GET'])
@verificar_loggeado
@es_profesor
def cargar_notas():
	# Chequear que esto esté bien hecho después de haber hecho todo en un solo stored procedure
	with pyodbc.connect(conx_string) as conx:
		anio = datetime.datetime.now().year #Cuando esté todo listo hay que poner la variable '@anio' en vez de 2019 en SP_PlanillaAlumnosNotas. Ahora queda así porque no hay notas en el 2020
		cursor = conx.cursor()
		cursor.execute('EXEC SP_BuscaMateriaDocente @dni = ?', session['dni'])
		materias = cursor.fetchall()
		if request.method == 'POST':
			try: 
				cursor = conx.cursor()	
				materia_anr = request.form['materia']
				cursor.execute('SP_PlanillaAlumnosNotas @anr = ?', materia_anr)
				planilla_alumnos_notas = cursor.fetchall()
				return render_template('notas/cargar_notas.html', materias = materias, planilla_alumnos_notas = planilla_alumnos_notas)
			except KeyError:
				flash('Debe seleccionar una materia.','danger')
	return render_template('notas/cargar_notas.html', materias = materias)

@app.route('/ver_notas')
def ver_notas():
	if session['tipo_de_usuario'] == 'alumno':
		#Este import está mal acá creo
		import datetime
		anio = datetime.datetime.now().year #Cuando esté todo listo hay que poner la variable '@anio' en vez de 2019 en SP_BuscaNotasAlumno. Ahora queda así porque no hay notas en el 2020
		with pyodbc.connect(conx_string) as conx:
			cursor = conx.cursor()
			cursor.execute('EXEC SP_BuscaNotasAlumno @dni = ?', session['dni'])
			notas_materias = cursor.fetchall()
		return render_template('notas/ver_notas.html', notas_materias = notas_materias)

@app.route('/actualizar_notas', methods=['POST'])
@verificar_loggeado
@es_profesor
def actualizar_notas():
	if request.method == 'POST':
		nota1 = request.form.getlist('NOTA1')
		nota2 = request.form.getlist('NOTA2')
		nota3 = request.form.getlist('NOTA3')
		alumno = request.form.getlist('ALU')
		materia = request.form.getlist('materia')
	notas_ingresadas_validas = True
	campo_notas_vacio = False
	caracter_invalido = False
	# Une las listas 
	for x in itertools.chain(nota1, nota2, nota3):
		try:
			float(x)
			if x == "":
				campo_notas_vacio = True
			# Chequea que las notas estén entre 1 y 10
			elif float(x)<1 or float(x)>10:
				notas_ingresadas_validas = False
		except ValueError:
			caracter_invalido = True

	if campo_notas_vacio:
		flash('No puede haber campos vacíos.','danger')
	elif caracter_invalido:
		flash('Solamente pueden ingresarse números enteros o decimales.','danger')
	elif notas_ingresadas_validas == False:
		flash('Los valores ingresados en uno o más campos son incorrectos. La nota ingresada no puede ser menor a 1 o mayor a 10.','danger')
	else:
		# Intercala las listas
		notas_lista = list(itertools.chain.from_iterable(zip(nota1, nota2, nota3, alumno, materia)))
		try:
			[float(i) for i in notas_lista]
			# Separa en bloques de 5 los elementos de las listas
			lista_notas = [notas_lista[i:i + 5] for i in range (0, len(notas_lista), 5)]
			if not lista_notas:
				flash('Debe elegir una materia.', 'danger')
			else:
				with pyodbc.connect(conx_string) as conx:
					cursor = conx.cursor()
					act_notas = """ UPDATE [CURXALUM] 
									SET [CURXALUM].[NOTA1] = ?, [CURXALUM].[NOTA2] = ?, [CURXALUM].[NOTA3] = ? 
									WHERE [CURXALUM].[ALU] = ? AND [CURXALUM].[MAT] = ?"""
					# Ver cómo hacer un Stored Procedure para que ejecute una lista
					#cursor.execute('EXEC SP_ActualizarNotas_ActualizarNotas @nota1 = ?, @nota2 = ?, @nota3 = ?, @alu = ?', (lista_notas))
					cursor.executemany(act_notas, lista_notas)  
				flash('Notas actualizadas correctamente.', 'success')   
		except ValueError:
			flash('Carácter no válido en uno de los campos. Revise las notas ingresadas e intente nuevamente.', 'danger')   
	return redirect(url_for('cargar_notas'))  