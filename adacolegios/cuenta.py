from adacolegios import app
from flask import render_template, flash

@app.route('/perfil', methods=['GET', 'POST'])
def perfil():
	return render_template('cuenta/perfil.html')

@app.route('/cambiar_contraseña', methods=['GET', 'POST'])
def cambiar_contraseña():
	return render_template('cuenta/cambiar_contraseña.html')