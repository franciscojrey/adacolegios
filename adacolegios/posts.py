from adacolegios import app
from flask import render_template, request, flash, session, redirect, url_for
from wtforms import Form, StringField, TextAreaField
from datetime import date
from adacolegios.main_functions import verificar_loggeado, es_profesor
import pyodbc
import itertools
import math

# Conexión a la base de datos SQL Server
conx_string = ('DRIVER={ODBC Driver 17 for SQL Server};SERVER='+app.config["DB_SERVER"]+';DATABASE='+app.config["DB_NAME"]+';UID='+app.config["DB_USERNAME"]+';PWD='+app.config["DB_PASSWORD"]+'')

@app.route('/posts')
@verificar_loggeado
def posts():
	with pyodbc.connect(conx_string) as conx:
		cursor = conx.cursor()
		# Hacer stored procedure
		if session['tipo_de_usuario'] == 'alumno':
			cursor.execute("SELECT [ALUMNOS].[NIV], [ALUMNOS].[CUR], [ALUMNOS].[DIV] FROM [ALUMNOS] WHERE [ALUMNOS].[DNI] = ?", session['dni'])
			datos_alumno = cursor.fetchone()
			cursor.execute("SELECT COUNT(*) FROM WEBPOSTS WHERE NIV = ? AND CUR = ? AND DIV = ?", datos_alumno[0], datos_alumno[1], datos_alumno[2])
		elif session['tipo_de_usuario'] == 'profesor':
			cursor.execute("SELECT COUNT(*) FROM WEBPOSTS WHERE AUTOR = ?", session['email'])
		cantidad_posts = cursor.fetchone()[0]
		resultados_por_pagina = 5
		paginas = cantidad_posts/resultados_por_pagina
		# Redondeo para arriba la división
		cantidad_paginas = (math.ceil(paginas))+1
		try:
			numero_de_pagina = int(request.args.get('pagina', 1))
			offset = (numero_de_pagina-1) * resultados_por_pagina
			with pyodbc.connect(conx_string) as conx:
				cursor = conx.cursor()
				if session['tipo_de_usuario'] == 'alumno':
					cursor.execute('EXEC SP_VerPosts_Alumnos @niv = ?, @cur = ?, @div = ?, @offset = ?, @resultados_por_pagina = ?', datos_alumno[0], datos_alumno[1], datos_alumno[2], offset, resultados_por_pagina)
				elif session ['tipo_de_usuario'] == 'profesor':
					cursor.execute('EXEC SP_VerPosts_Posts @email = ?, @offset = ?, @resultados_por_pagina = ?', session['email'], offset, resultados_por_pagina)
				posts = cursor.fetchall()
				if not posts:
					flash('Por el momento no hay publicaciones para mostrar.','warning')
				return render_template('posts/posts.html', posts=posts, cantidad_paginas=cantidad_paginas)
		except TypeError:
			flash('No se encontraron publicaciones', 'warning')
			return render_template('posts/posts.html')

@app.route('/post/<string:id>/')
def post(id):
	with pyodbc.connect(conx_string) as conx:
		cursor = conx.cursor()
		cursor.execute('EXEC SP_BuscaPost_VerPost @id = ?', id)
		post = cursor.fetchone()
		if session['tipo_de_usuario'] == 'alumno':
			cursor.execute('EXEC SP_VerDatosAlumno_Post @dni = ?', session['dni'])
			datos_alumno = cursor.fetchone()
			if post[4]!=datos_alumno[0] or post[5]!=datos_alumno[1] or post[6]!=datos_alumno[2]:
				flash('Acceso no autorizado.', 'danger')
				return redirect(url_for('posts'))
		elif session['tipo_de_usuario'] == 'profesor':
			cursor.execute('EXEC SP_BuscaMateriaDocente @dni= ?', session['dni'])
			materias_profesor = cursor.fetchall()
			acceso_permitido = False
			numero_materia = 0
			while numero_materia < len(materias_profesor) and acceso_permitido == False:
				for materia in materias_profesor:
					if post[4]==materia[0] and post[5]==materia[1] and post[6]==materia[2]:
						acceso_permitido = True
					numero_materia = numero_materia+1
			if acceso_permitido == False:
				flash('Acceso no autorizado.', 'danger')
				return redirect(url_for('posts'))
		return render_template('posts/ver_post.html', post=post)

@app.route('/administrar_posts')
@verificar_loggeado 
@es_profesor
def administrar_posts():
	with pyodbc.connect(conx_string) as conx:
		cursor = conx.cursor()
		cursor.execute("EXEC SP_ContarPostsPanelAdministracion @autor = ?", session['email'])
		cantidad_posts = cursor.fetchone()[0]
		resultados_por_pagina = 10
		paginas = cantidad_posts/resultados_por_pagina
		# Redondeo para arriba la división
		cantidad_paginas = (math.ceil(paginas))+1
		try:
			numero_de_pagina = int(request.args.get('pagina', 1))
			offset = (numero_de_pagina-1) * resultados_por_pagina
			with pyodbc.connect(conx_string) as conx:
				cursor = conx.cursor()
				cursor.execute('EXEC SP_VerPosts_AdministrarPosts @email = ?, @offset = ?, @resultados_por_pagina = ?', session['email'], offset, resultados_por_pagina)
				posts = cursor.fetchall()
				return render_template('posts/administrar_posts.html', posts=posts, cantidad_paginas=cantidad_paginas)
		except TypeError:
			flash('No se encontraron tareas.', 'warning')
			return render_template('posts/administrar_posts.html')

class ArticleForm(Form):
	titulo = StringField('Título')
	texto = TextAreaField('Texto')

def largoCaracteres(variable, nombreVariable, minimo, maximo):
	if len(variable)<minimo or len(variable)>maximo:
		return flash('El campo ' + nombreVariable + ' debe tener entre ' + str(minimo) + ' y ' + str(maximo) + ' caracteres','danger')

@app.route('/agregar_post', methods=['GET', 'POST'])
@verificar_loggeado
@es_profesor
def agregar_post():
	with pyodbc.connect(conx_string) as conx:
		cursor = conx.cursor()
		cursor.execute('EXEC SP_BuscaMateriaDocente @dni = ?', session['dni'])
		materias_checkbox = cursor.fetchall()
	if request.method == 'POST':
		titulo = request.form['titulo']
		texto = request.form['texto']
		materias_elegidas = request.form.getlist('materia')
		if texto == "" or titulo == "" or not materias_elegidas:
			flash('Debe completar todos los campos.', 'danger')	
		#elif len(titulo)<1 or len(titulo)>60:
		#	flash('El titulo debe tener entre 5 y 60 caracteres.', 'danger')		
		#elif len(texto)<1 or len(texto)>500:
		#	flash('El texto debe tener entre 30 y 500 caracteres.', 'danger')
		else:
			for materia in materias_elegidas:
				autor = session['email']
				today = date.today()
				fecha_post = today.strftime("%d/%m/%Y")
				with pyodbc.connect(conx_string) as conx:
					cursor = conx.cursor()
					cursor.execute('EXEC SP_InfoMateriaPorANR @anr = ?', materia)
					materia_informacion = cursor.fetchone()
				nivel = materia_informacion[0]
				curso = materia_informacion[1]
				division = materia_informacion[2]
				#posts_lista = list(itertools.chain.from_iterable(zip(titulo, autor, texto, fecha_post, nivel, curso, division, materia)))
				#lista_posts = [posts_lista[i:i + 8] for i in range (0, len(posts_lista), 8)]
				with pyodbc.connect(conx_string) as conx:
					cursor = conx.cursor()
					cursor.execute('EXEC SP_AgregarPost_AgregarPost @titulo = ?, @autor = ?, @texto = ?, @fecha_post = ?, @nivel = ?, @curso = ?, @division = ?, @codigo_materia = ?', (titulo,autor,texto,fecha_post, nivel, curso, division, materia))
					#agregar_post = """ INSERT INTO [WEBPOSTS](TITULO, AUTOR, TEXTO, FECHA, NIV, CUR, DIV, COD) 
										#VALUES(?,?,?,?,?,?,?,?) """
					#cursor.executemany(agregar_post, lista_posts)
			flash('Tarea creada.', 'success')
			return redirect(url_for('administrar_posts'))
	return render_template('posts/agregar_post.html', materias_checkbox = materias_checkbox)

@app.route('/editar_post/<id>', methods=['GET', 'POST'])
@verificar_loggeado
@es_profesor
def edit(id):
	with pyodbc.connect(conx_string) as conx:
		cursor = conx.cursor()
		cursor.execute('EXEC SP_BuscarPost_EditarPost @id = ?', id)
		post = cursor.fetchone()
	if session['tipo_de_usuario'] == 'profesor':
		cursor.execute('EXEC SP_BuscaMateriaDocente @dni= ?', session['dni'])
		materias_profesor = cursor.fetchall()
		acceso_permitido = False
		numero_materia = 0
		while numero_materia < len(materias_profesor) and acceso_permitido == False:
			for materia in materias_profesor:
				if post[2]==materia[0] and post[3]==materia[1] and post[4]==materia[2]:
					acceso_permitido = True
				numero_materia = numero_materia+1
		if acceso_permitido == False:
			flash('Acceso no autorizado.', 'danger')
			return redirect(url_for('administrar_posts'))
	form = ArticleForm(request.form)
	form.titulo.data = post[0]
	form.texto.data = post[1]
	if request.method == 'POST':
		titulo = request.form['titulo']
		texto = request.form['texto']
		if texto == "" or titulo == "":
			flash('No puede haber campos vacíos.', 'danger')
		#elif len(titulo)<5 or len(titulo)>60:
		#	flash('El titulo debe tener entre 5 y 60 caracteres.', 'danger')		
		#elif len(texto)<30 or len(texto)>500:
		#	flash('El texto debe tener entre 30 y 500 caracteres.', 'danger')
		else:
			with pyodbc.connect(conx_string) as conx:
				cursor = conx.cursor()
				cursor.execute('EXEC SP_EditarPost_EditarPost @titulo = ?, @texto = ?, @id = ?', (titulo,texto,id))
			flash('Tarea editada correctamente.', 'success')
			return redirect(url_for('administrar_posts'))
		form.titulo.data = titulo
		form.texto.data = texto
	return render_template('posts/editar_post.html', form=form)

@app.route('/eliminar_post/<string:id>', methods=['POST'])
@verificar_loggeado
@es_profesor
def eliminar_post(id):
	with pyodbc.connect(conx_string) as conx:
		cursor = conx.cursor()
		cursor.execute('EXEC SP_EliminarPost_EliminarPost @id = ?', id)
	flash('Tarea eliminada correctamente.', 'success')
	return redirect(url_for('administrar_posts'))