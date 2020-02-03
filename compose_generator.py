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
		for sub in file['External Servers'][server]["subdomains"]:
			hostfile.append(sub)
	master_stack = dict()
	for server in file['External Servers']:
		sublist = list()
		for sub in file['External Servers'][server]['subdomains']:
			sub = f"{sub}.{defaults['Domain']}"
			sublist.append(sub)
		file['External Servers'][server]['subdomains'] = sublist
	gen_setup_servers_toml(defaults, file['External Servers'])
	for stack in file['Stack Group Name']:
		composeFile = ComposeFile(file['Defaults']['Domain'],
		                          file["Defaults"]["VPN Container"],
		                          stack,
		                          file["Defaults"]["Email Authentication File"],
		                          file["Defaults"]["Email"],
		                          file['Stack Group Name'][stack],
		                          file['Defaults'],
		                          file['External Servers'],
		                          file['Globals'])
		configs = set_config_directory(stack)
		services = set_services(file, stack)
		gen_globals_env_file(configs, defaults)
		networks = dict()
		for app in services:
			hosts = list()
			master_stack[get_index(stack)] = get_stack_file(stack)
			parse_hostfile(services[app], hostfile, hosts, defaults)
			gen_setup_shell_script(stack, app, defaults, g, configs)
			gen_app_specific_env_file(configs, app, set_environment(services[app]))
			services[app]['HOSTS'] = ",".join(hosts)
			gen_docker_yaml(configs, file['Stack Group Name'][stack], defaults, cleanup_name(stack), composeFile)
	gen_hostfile(file['Stack Group Name'][stack], defaults, hostfile)
	gen_master_stack_file(master_stack)
