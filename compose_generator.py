#!/usr/bin/env python3.7
import yaml
from classes.composeParameters import ComposeFile
from src.generators import *
from src.gets import get_index, get_stack_file, set_config_directory
from src.parser import parse_hostfile
from src.sets import set_environment, set_services
from src.helpers import *

if __name__ == "__main__":
	parameters = open(Path(str("/parameters.yaml")))
	file = yaml.load(parameters, Loader = yaml.FullLoader)
	g = file['Globals']
	defaults = file['Defaults']
	hostfile = list()
	for server in file['External Servers']:
		hostfile = [sub for sub in file['External Servers'][server]["subdomains"]]
	master_stack = dict()
	for server in file['External Servers']:
		sublist = [f"{sub}.{defaults['Domain']}" for sub in file['External Servers'][server]['subdomains']]
		file['External Servers'][server]['subdomains'] = sublist
	gen_setup_servers_toml(defaults, file['External Servers'])
	for stack in file['Stack Group Name']:
		composeFile = ComposeFile(file['Defaults']['Domain'],
		                          stack,
		                          file["Defaults"]["Email Authentication File"],
		                          file["Defaults"]["Email"],
		                          file['Stack Group Name'][stack],
		                          file['Defaults'],
		                          file['External Servers'],
		                          file['Globals'])
		configs = set_config_directory(stack)
		yaml.dump(composeFile.globals, open(f"{configs}/docker-compose.yaml", "w+"),
		          indent = 4,
		          width = 85,
		          default_flow_style = False)
		#gen_docker_yaml(configs, file['Stack Group Name'][stack], defaults, cleanup_name(stack), composeFile)
		# this is probably redundant
		services = set_services(file, stack)
		gen_globals_env_file(configs, defaults)
		networks = dict()
                # env files seem to not generate correctly
		for app in composeFile.services:
			hosts = list()
			#gen_app_specific_env_file(configs, app, set_environment(composeFile.services[app]))
			master_stack[get_index(stack)] = get_stack_file(stack)
			parse_hostfile(composeFile.services[app], hostfile, hosts, defaults)
			gen_setup_shell_script(stack, app, defaults, g, configs)
			composeFile.services[app]['HOSTS'] = ",".join(hosts)
		gen_hostfile(file['Stack Group Name'][stack], defaults, hostfile)
	gen_master_stack_file(master_stack)
