#!/usr/bin/env python3.7
import os
import jinja2
import yaml
from pathlib import Path

def mkdir(service_configs):
	try:
		os.makedirs(service_configs)
	except FileExistsError:
		# directory already exists
		pass
with open(f"{os.environ['CONFIGS']}/templates/compose_generator_parameters.yaml") as f:
	config = yaml.load(f, Loader = yaml.FullLoader)
globals = config['Globals']
defaults = config['Defaults']
with open(f'{os.path.dirname(os.path.realpath(__file__))}/templates/shell_script.jinja.sh') as f:
	shell_script = jinja2.Template(f.read())
with open(f'{os.path.dirname(os.path.realpath(__file__))}/templates/globals.jinja.env') as f:
	global_env = jinja2.Template(f.read())
with open(f'{os.path.dirname(os.path.realpath(__file__))}/templates/service.jinja.env') as f:
	service_env = jinja2.Template(f.read())
with open(f'{os.path.dirname(os.path.realpath(__file__))}/templates/docker-compose.jinja.yaml') as f:
	compose_yaml = jinja2.Template(f.read())
for path in globals['Paths']:
	print(path, globals['Paths'][path])
exports = []
for i in globals['Exports']:
	try:
		os.makedirs(globals['Exports'][i])
	except FileExistsError:
		# directory already exists
		pass
	exports.append(f"{i}={globals['Exports'][i]}")
for stack in config['Stack Group Name']:
	services = config['Stack Group Name'][stack]['Services']
	configs = f"{globals['Exports']['CONFIGS']}/{str(stack).lower()}".replace(" ", "_")
	mkdir(configs)
	print(f"Creating stack configuration: {configs}")
	with open(f"{configs}/globals.env", "w+") as f:
		f.write(global_env.render(defaults = defaults))
	for app in services:
		with open(f"{configs}/setup.sh", "w+") as f:
			f.write(shell_script.render(stack_group = str(stack).lower().replace(" ", "_"),
										service = app,
										defaults = defaults,
										globals = globals,
										global_exports = exports))
		print(f"Creating stack configuration: {configs}/setup.sh")
		with open(f"{configs}/{app.lower()}.env", "w+") as f:
			f.write(service_env.render(environment = (services[app]['Environment'])))
		print(f"Creating stack configuration: {configs}/{app.lower()}.env")
		with open(f"{configs}/docker-compose.yaml", "w+") as f:
			f.write(compose_yaml.render(stack = (config['Stack Group Name'][stack]), defaults = defaults))
		print(f"Creating stack configuration: {configs}/docker-compose.yaml")
