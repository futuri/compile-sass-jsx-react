import re
import sys
import os
from os import path
from subprocess import Popen, PIPE
from sublime_plugin import TextCommand
from sublime_plugin import WindowCommand
import sublime_plugin
import sublime
import functools
import locale
import tempfile

import hashlib
import json
from pprint import pprint

#ruta para laravel (si tiene otra ruta para otro framework cambiela aqui o dejelo vacio para que compile en la misma carpeta)
ruta = '../../../public/'


class BuildonSave(sublime_plugin.EventListener):

	def on_post_save(self, view):
		resultado = {"okay": False}
		archivo = view.file_name()
		nom, ext = os.path.splitext(archivo)

		#PARA COMPILACION DE ARCHIVOS JSX CON REACTJS
		if ext == ".jsx":
			name = manifest(archivo,'js')

			if name[1]:
				resultado = run("babel", args=[
					"--minified",
					#"--plugins", "/usr/lib/node_modules/babel-plugin-transform-es2015-modules-amd,/usr/lib/node_modules/babel-plugin-transform-react-jsx",
					"--presets", "es2015,react",
					archivo,
					"-o", name[0]
				])

				estado(resultado,ext)

		#PARA SASS
		if ext == ".sass":
			#sass --style compressed --sourcemap=none estilo.sass estilo.css
			name = manifest(archivo,'css')

			if name[1]:
				resultado = run("sass", args=[
					"--style=compressed",
					"--sourcemap=none",
					archivo,
					name[0]
				])

				estado(resultado,ext)
			

def nombre(archivo):
	return hashlib.sha1(open(archivo, 'rb').read()).hexdigest()

def manifest(archivo,extension):
	base_url = os.path.dirname(archivo)
	base_name = os.path.basename(archivo)
	nom, ext = os.path.splitext(base_name)
	hash = hashlib.sha1(open(archivo, 'rb').read()).hexdigest()

	ruta = base_url+'/'+base_name+"."+extension

	#verifico si el archivo existe
	if os.path.exists(base_url+"/../"+extension+"/"+nom+"."+hash+"."+extension):
		#print("archivo existe")
		ruta = base_url+"/../"+extension+"/"+nom+"."+hash+"."+extension;
		#ruta = base_url+"../"+extension+"/"+nom+"."+hash+"."+extension+"";
		return [ruta,False]
	else:
		#print("archivo NO existe")
		if os.path.exists(base_url+'/../mix-manifest.json'):
			#print("existe MANIFEST")
			data = {}

			try:
				with open(base_url+'/../mix-manifest.json', "r") as data_file:    
					data = json.load(data_file)
			except Exception as e:
				print("ERROR LECTURA")


			try:
				if os.path.exists(base_url+'/..'+data["/"+extension+"/"+nom+"."+extension+""]):
					os.remove(base_url+'/..'+data["/"+extension+"/"+nom+"."+extension+""])
			except Exception as e:
				print("KEY NO EXISTIA")

			data["/"+extension+"/"+nom+"."+extension+""] = "/"+extension+"/"+nom+"."+hash+"."+extension+""

			with open(base_url+'/../mix-manifest.json', "w") as jsonFile:
				json.dump(data, jsonFile,indent=4)

			ruta = base_url+"/../"+extension+"/"+nom+"."+hash+"."+extension;
		else:
			#print("NO existe MANIFEST")
			ruta = base_url+'/'+nom+"."+extension

		return [ruta,True]


def estado(resultado,ext):
	if resultado['okay'] is True:
		status = 'Archivo '+ext+' compilado'
	else:
		lines = resultado['err'].splitlines()
		if len(lines) >= 3:
			line = lines[2]
			if re.search("throw err;$", line):
				# Remove useless lines
				lines = lines[4:]
				index = 0
				linenb = 0
				for line in lines:
					if re.search("^	at ", line):
						linenb = index
						break
					index += 1
				if linenb > 0:
					# remove useless lines
					lines = lines[:linenb - 1]

		status = 'Archivo '+ext+' no pudo ser compilado:\n' + lines[0]
		sublime.error_message("\n".join(lines))

	later = lambda: sublime.status_message(status)
	sublime.set_timeout(later, 300)

def run(cmd, args=[], source="", cwd=None, env=None, callback=None):
	if callback:
		threading.Thread(target=lambda cb: cb(_run(cmd, args=args, source=source, cwd=cwd, env=env)), args=(callback,)).start()
	else:
		res = _run(cmd, args=args, source=source, cwd=cwd, env=env)
		return res


def _run(cmd, args=[], source="", cwd=None, env=None):
	if not type(args) is list:
		args = [args]

	if source == "":
		command = [cmd] + args
	else:
		command = [cmd] + args + [source]

	proc = Popen(command, cwd=cwd, stdout=PIPE, stderr=PIPE)
	stat = proc.communicate()
	okay = proc.returncode == 0

	return {"okay": okay, "out": stat[0].decode('utf-8'), "err": stat[1].decode('utf-8')}
