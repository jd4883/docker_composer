#!/usr/bin/env python3.7
import yaml

from classes.composeParameters import ComposeFile
from src.generators import *
from src.gets import get_index, get_stack_file, set_config_directory
from src.helpers import *
from src.parser import parse_hostfile
from src.sets import set_services

def gen_terraform_code(stack,  defaults, g, configs):
	stack_group = str(stack).lower().replace(" ", "_")
	# add in conditionals about generating more than just providers
	# limit what providers are added
	p = f"{configs}/providers.tf"
	t = load_template("TF_PROVIDERS_TEMPLATE")
	f = open(Path(p), "w+")
	print(f"Creating terraform providers configuration: {p}")
	render = t.render(defaults = defaults["kubernetes"]["providers"])
	f.write(render)

def gen_terraform_service_code(app, app_dict, defaults, configs):
	p = f"{configs}/{app}.tf"
	t = load_template("TF_SERVICE_TEMPLATE")
	f = open(Path(p), "w+")
	print(f"Creating terraform service file for {app}: {p}")
	render = t.render(svc = app,
	                  defaults = defaults,
	                  helm_module = str(os.environ["TF_MODULE_HELM"]),
	                  service = app_dict)
	f.write(render)

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
		                          file["Defaults"]["Authenticated Emails File"],
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
		services = set_services(file, stack)
		gen_globals_env_file(configs, defaults)
		networks = dict()
		gen_terraform_code(stack, defaults, g, configs)
		for app in composeFile.services:
			hosts = list()
			master_stack[get_index(stack)] = get_stack_file(stack)
			parse_hostfile(composeFile.services[app], hostfile, hosts, defaults)
			gen_setup_shell_script(stack, app, defaults, g, configs)
			composeFile.services[app]['HOSTS'] = ",".join(hosts)
			try:
				if "kubernetes" in stack[app] or app == "consul":
					gen_terraform_service_code(app, stack[app], defaults, configs)
			except KeyError:
				pass
		gen_hostfile(file['Stack Group Name'][stack], defaults, hostfile)
	gen_master_stack_file(master_stack)
