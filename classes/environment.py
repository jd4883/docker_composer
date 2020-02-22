#!/usr/bin/self python3
from pathlib import Path

from src.gets import set_config_directory
from src.helpers import load_template


class Environs(object):
	def __init__(self,
	             service,
	             value,
	             compose):
		self.fileName = str("env_file")
		self.globalFile = str("globals.env")
		self.serviceFile = str(f"{service}.env")
		self.files = list(dict.fromkeys([self.globalFile, self.serviceFile]))
		self.obj = dict({self.fileName: self.files})
		self.stackPath = set_config_directory(compose.stackTitle)
		self.environs = value["Environment"] if "Environment" in value else dict()
		self.generateServiceEnvFile(service)
	
	def generateServiceEnvFile(self, service):
		print(f"Creating stack configuration: {self.stackPath}/{service}.env")
		f = open(Path(f"{self.stackPath}/{service}.env"), "w+")
		t = load_template('SERVICE_ENV')
		render = t.render(environment = self.environs)
		f.write(render)

