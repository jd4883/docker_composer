#!/usr/bin/env python3.7
import os
import jinja2
import yaml
from pathlib import Path

# may be worth adding more dynamic config changes such as traefik.traefik_toml
# TODO: look into making secrets automatically referenced in config files > text

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
for stack in config['Stack Group Name']:
	services = config['Stack Group Name'][stack]['Services']
	config_files = f"{os.environ['CONFIGS']}/{stack.lower().replace(' ', '_')}"
	print(f"Creating stack configuration: {config_files}")
	with open(f"{config_files}/globals.env", "w+") as f:
		f.write(global_env.render(defaults = defaults))
	for app in services:
		with open(f"{config_files}/setup.sh", "w+") as f:
			f.write(shell_script.render(stack_group = str(stack).lower().replace(" ", "_"),
										service = app,
										defaults = defaults,
										globals = globals))
		print(f"Creating stack configuration: {config_files}/setup.sh")
		with open(f"{config_files}/{app.lower()}.env", "w+") as f:
			f.write(service_env.render(environment = services[app]['Environment'] if 'Environment' in services[app] else
			str()))
		print(f"Creating stack configuration: {config_files}/{app.lower()}.env")
		with open(f"{config_files}/docker-compose.yaml", "w+") as f:
			f.write(compose_yaml.render(stack = (config['Stack Group Name'][stack]), defaults = defaults))
		print(f"Creating stack configuration: {config_files}/docker-compose.yaml")
