#!/usr/bin/env python3.7
import yaml

from src.generators import *
from src.gets import get_index, get_stack_file, set_config_directory
from src.parser import parse_hostfile
from src.sets import set_environment, set_services
from src.helpers import *

def cleanup_name(name):
	name = name.replace("_", "-")
	name = name.replace(" ", "-")
	name = name.lower()
	return name

if __name__ == "__main__":
	config = yaml.load(open(Path(str("/parameters.yaml"))), Loader = yaml.FullLoader)
	globals = config['Globals']
	defaults = config['Defaults']
	hostfile = list()
	master_stack = dict()
	for stack in config['Stack Group Name']:
		configs = set_config_directory(stack)
		services = set_services(config, stack)
		gen_globals_env_file(configs, defaults)
		for app in services:
			hosts = list()
			master_stack[get_index(stack)] = get_stack_file(stack)
			parse_hostfile(services[app], hostfile, hosts, defaults)
			gen_setup_shell_script(stack, app, defaults, globals, configs)
			gen_app_specific_env_file(configs, app, set_environment(services[app]))
			services[app]['HOSTS'] = ",".join(hosts)
			gen_docker_yaml(configs, config['Stack Group Name'][stack], defaults, cleanup_name(stack))
	gen_hostfile(config['Stack Group Name'][stack], defaults, hostfile)
	gen_master_stack_file(master_stack)
