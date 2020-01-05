#!/usr/bin/env python3
import json
import os
from pathlib import Path
from src.helpers import load_template


def gen_docker_yaml(configs, stack, defaults, stack_name):
	open(Path(f"{configs}/docker-compose.yaml"), "w+").write(load_template('COMPOSE_YAML').render(stack = stack,
	                                                                                              defaults = defaults,
																								  stack_name = stack_name))
	print(f"Creating stack configuration: {configs}/docker-compose.yaml")

def gen_app_specific_env_file(configs, app, environment):
	app = app.replace("_", "-")
	app = app.replace(" ", "-")
	app = app.lower()
	print(f"Creating stack configuration: {configs}/{app}.env")
	open(Path(f"{configs}/{app}.env"), "w+").write(load_template('SERVICE_ENV').render(environment = environment))

 #| lower | replace(" ", "-") | replace("_", "-")

def gen_globals_env_file(configs, defaults):
	open(Path(str(f"{configs}/globals.env")), "w+").write(load_template('GLOBALS_ENV').render(defaults = defaults))

def gen_hostfile(stack, defaults, hostfile):
	open(Path(f"{os.environ['HOSTFILE']}"), "w+").write(
		load_template('HOSTFILE_TEMPLATE').render(stack = stack,
		                                          defaults = defaults,
		                                          hosts = hostfile))

def gen_master_stack_file(stack_json):
	print(f"Writing JSON file of stacks for a stack rebuild script\n{stack_json}")
	json.dump(stack_json,
	          open(f"{os.environ['STACKS_JSON']}", 'w+', encoding = 'utf-8'),
	          ensure_ascii = False,
	          indent = 4)

def gen_setup_shell_script(stack, app, defaults, globals, configs):
	shell_script = f"{configs}/setup.sh"
	print(f"Creating stack configuration: {shell_script}")
	open(Path(shell_script), "w+").write(load_template('SHELL_SCRIPT').render(stack_group = str(stack).lower().replace(" ", "_"),
	                                                                          service = app,
	                                                                          defaults = defaults,
	                                                                          globals = globals))
