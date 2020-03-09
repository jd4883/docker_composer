#!/usr/bin/self python3.7
import json
import os
from pathlib import Path

from src.helpers import load_template


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

def gen_setup_shell_script(stack, app, defaults, g, configs):
	stack_group = str(stack).lower().replace(" ", "_")
	p = f"{configs}/setup.sh"
	t = load_template('SHELL_SCRIPT')
	f = open(Path(p), "w+")
	print(f"Creating stack configuration: {p}")
	render = t.render(stack_group = stack_group, service = app, defaults = defaults, globals = g)
	f.write(render)


def gen_setup_servers_toml(defaults, servers):
	p = f"{os.environ['SERVERS_TOML']}"
	f = open(Path(p), "w+")
	t = load_template('SERVERS_TOML_TEMPLATE')
	print(f"Creating stack configuration: {p}")
	render = t.render(defaults = defaults, servers = servers)
	f.write(render)
