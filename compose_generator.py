#!/usr/bin/env python3.7

import yaml

from classes.composeParameters import ComposeFile
from src.generators import *
from src.gets import get_index, get_stack_file, set_config_directory
from src.helpers import *
from src.parser import parse_hostfile
from src.sets import set_services


def gen_terraform_code(payload, conf):
	p = f"{conf}/providers.tf"
	t = load_template("TF_PROVIDERS_TEMPLATE")
	f = open(Path(p), "w+")
	print(f"Creating terraform providers configuration: {p}")
	render = t.render(defaults = payload["kubernetes"]["providers"])
	f.write(render)


def gen_terraform_service_code(service, app_dict, base, conf, stack):
	app_dict["kubernetes"]["name"] = service
	p = f"{conf}/{service}.tf"
	y = f"{conf}/{service}.yaml"
	t = load_template("TF_SERVICE_TEMPLATE")
	f = open(Path(p), "w+")
	print(f"Creating terraform service file for {service}: {p}")
	yaml.dump(app_dict['kubernetes']['values'], open(y, "w+"))
	render = t.render(defaults = base,
	                  helm_module = str(os.environ["TF_MODULE_HELM"]),
	                  service = app_dict,
	                  stack = conf,
	                  host_port = str(app_dict['ports'][0]).split(":")[0],
	                  container_port = str(app_dict['ports'][0]).split(":")[1],
	                  port_name = f"{service}-webui",
	                  namespace = stack)
	f.write(render)


def set_subdomains(yml, server):
	yml['External Servers'][server]['subdomains'] = \
		[[f"{sub}.{defaults['Domain']}" for sub in yml['External Servers'][server]['subdomains']] \
		 for server in yml['External Servers']]


if __name__ == "__main__":
	parameters = open(Path(str("/parameters.yaml")))
	file = yaml.load(parameters, Loader = yaml.FullLoader)
	g = file['Globals']
	defaults = file['Defaults']
	hostfile = [[sub for sub in file['External Servers'][server]["subdomains"]] for server in file['External Servers']]
	master_stack = dict()
	[set_subdomains(file, server) for server in file['External Servers']]
	# TODO: update to also include base config
	gen_setup_servers_toml(defaults, file['External Servers'])
	stack_dict = file['Stack Group Name']
	for stack in stack_dict:
		# add handling per service for if docker disabled
		composeFile = ComposeFile(file['Defaults']['Domain'],
		                          stack,
		                          file["Defaults"]["Authenticated Emails File"],
		                          file["Defaults"]["Email"],
		                          stack_dict[stack],
		                          file['Defaults'],
		                          file['External Servers'],
		                          file['Globals'])
		configs = set_config_directory(stack)
		yaml.dump(composeFile.globals, open(f"{configs}/docker-compose.yaml", "w+"),
		          indent = 4,
		          width = 85,
		          default_flow_style = False)
		services = set_services(file, stack)
		gen_globals_env_file(configs, defaults)
		networks = dict()
		gen_terraform_code(defaults, configs)
		for app in composeFile.services:
			hosts = list()
			master_stack[get_index(stack)] = get_stack_file(stack)
			parse_hostfile(composeFile.services[app], hostfile, hosts, defaults)
			gen_setup_shell_script(stack, app, defaults, g, configs)
			composeFile.services[app]['HOSTS'] = ",".join(hosts)
			if app in stack_dict[stack]["Services"] and "kubernetes" in stack_dict[stack]["Services"][app]:
				gen_terraform_service_code(app,
				                           stack_dict[stack]['Services'][app],
				                           defaults,
				                           configs,
				                           stack)
		gen_hostfile(stack_dict[stack], defaults, hostfile)
	gen_master_stack_file(master_stack)
