#!/usr/bin/env python3.7
import json
import os
import shutil
from pathlib import Path

from src.helpers import load_template


def gen_docker_yaml(configs, stack, defaults, stack_name, composeFile):
	old = f"{configs}/docker-compose.yaml.old"
	current = f"{configs}/docker-compose.yaml"
	print(f"Creating stack configuration: {current}")
	if os.path.isfile(current) and not (os.stat(current).st_size == 0):
		shutil.copyfile(current, old)
	backup = open(old, "w+")
	# f_new = open(new, "w+")
	# f_current = open(current, "w+")
	t = load_template('COMPOSE_YAML')
	render = t.render(stack = stack, defaults = defaults, stack_name = stack_name, compose = composeFile)
	backup.write(render)
	# if f_new.write(render):
	# 	f_current.write(render)


def gen_app_specific_env_file(configs, app, environment):
	print(f"Creating stack configuration: {configs}/{app}.env")
	f = open(Path(f"{configs}/{app}.env"), "w+")
	t = load_template('SERVICE_ENV')
	render = t.render(environment = environment)
	f.write(render)


def gen_globals_env_file(configs, defaults):
	config_file = open(Path(str(f"{configs}/globals.env")), "w+")
	config_file.write(load_template('GLOBALS_ENV').render(defaults = defaults))


def gen_hostfile(stack, defaults, hostfile):
	f = open(Path(f"{os.environ['HOSTFILE']}"), "w+")
	t = load_template('HOSTFILE_TEMPLATE')
	render = t.render(stack = stack, defaults = defaults, hosts = hostfile)
	f.write(render)


def gen_master_stack_file(payload):
	print(f"Writing JSON file of stacks for a stack rebuild script\n{payload}")
	f = open(f"{os.environ['STACKS_JSON']}", 'w+', encoding = 'utf-8')
	json.dump(payload, f, ensure_ascii = False, indent = 4)


def gen_setup_shell_script(stack, app, defaults, globals, configs):
	stack_group = str(stack).lower().replace(" ", "_")
	p = f"{configs}/setup.sh"
	t = load_template('SHELL_SCRIPT')
	f = open(Path(p), "w+")
	print(f"Creating stack configuration: {p}")
	render = t.render(stack_group = stack_group, service = app, defaults = defaults, globals = globals)
	f.write(render)


def gen_setup_servers_toml(defaults, servers):
	p = f"{os.environ['SERVERS_TOML']}"
	f = open(Path(p), "w+")
	t = load_template('SERVERS_TOML_TEMPLATE')
	print(f"Creating stack configuration: {p}")
	render = t.render(defaults = defaults, servers = servers)
	f.write(render)
