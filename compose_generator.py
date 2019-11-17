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
with open(Path(str("/parameters.yaml"))) as f:
	config = yaml.load(f, Loader = yaml.FullLoader)
globals = config['Globals']
defaults = config['Defaults']
with open(Path(str(os.environ['SHELL_SCRIPT']))) as f:
	shell_script = jinja2.Template(f.read())
with open(Path(os.environ['GLOBALS_ENV'])) as f:
	global_env = jinja2.Template(f.read())
with open(Path(str(os.environ['SERVICE_ENV']))) as f:
	service_env = jinja2.Template(f.read())
with open(Path(str(os.environ['COMPOSE_YAML']))) as f:
	compose_yaml = jinja2.Template(f.read())
for stack in config['Stack Group Name']:
	services = config['Stack Group Name'][stack]['Services']
	configs = f"{os.environ['CONFIG']}/{str(stack).lower()}".replace(" ", "_")
	mkdir(configs)
	print(f"Creating stack configuration: {configs}")
	with open(Path(str(f"{configs}/globals.env")), "w+") as f:
		f.write(global_env.render(defaults = defaults))
	for app in services:
		with open(Path(str(f"{configs}/setup.sh")), "w+") as f:
			f.write(shell_script.render(stack_group = str(stack).lower().replace(" ", "_"),
										service = app,
										defaults = defaults,
										globals = globals))
		print(f"Creating stack configuration: {configs}/setup.sh")
		environment = services[app]['Environment'] if 'Environment' in services[app] else str()
		with open(Path(f"{configs}/{app.lower()}.env"), "w+") as f:
			f.write(service_env.render(environment = environment))
			
		print(f"Creating stack configuration: {configs}/{app.lower()}.env")
		with open(Path(f"{configs}/docker-compose.yaml"), "w+") as f:
			f.write(compose_yaml.render(stack = (config['Stack Group Name'][stack]), defaults = defaults))
		print(f"Creating stack configuration: {configs}/docker-compose.yaml")
