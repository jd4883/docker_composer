import re

import classes.traefik
from classes.environment import Environs
from classes.oauth import OauthProxy
from src.formatting import formatString
from src.gets import getServiceHostname
from src.parser import parseImage
from src.sets import setItems


class IP(object):
	def __init__(self,
	             defaults = dict(),
	             globalStackItems = dict(),
	             stackDict = dict(),
	             octet1 = int(10),
	             octet2 = int(23),
	             networkIP = int(0),
	             externalNetworkBool = bool(True),
	             defaultNetworkDriver = "bridge"):
		self.subnetMask = str(int(setItems(self, "subnetMask",
		                                   globalStackItems)))
		self.octet1 = str(int(setItems(self, "octet1", defaults, octet1)))
		self.octet2 = str(int(setItems(self, "octet2", defaults, octet2)))
		self.octet3 = str(int(setItems(self, "octets", stackDict)[0]))
		self.networkIP = str(networkIP)
		# 4th octet is dynamically calculated for each app
		self.octetsList = [
				str(self.octet1),
				str(self.octet2),
				str(self.octet3)
				]
		self.address = formatString(".".join(self.octetsList))
		self.backendSubnet = self.parseBackendSubnet()
		self.networks = { "networks": dict() }
		self.networks["networks"].update({ "frontend": { "external": externalNetworkBool } })
		self.networks["networks"].update({ "backend": dict() })
		self.networks["networks"]["backend"].update({ "driver": defaultNetworkDriver })
		self.networks["networks"]["backend"].update({ "ipam": dict() })
		self.networks["networks"]["backend"]["ipam"].update({ "config": list() })
		self.networks["networks"]["backend"]["ipam"]["config"].append({ "subnet": self.backendSubnet })
	
	def parseBackendSubnet(self, networkIP = 0):
		networkIP = networkIP
		subnetMaskComponents = [(str(self.address) + "." + str(networkIP)), str(self.subnetMask)]
		payload = formatString("/".join(subnetMaskComponents))
		return payload


def combineLocalSecrets(v):
	items = ([x for x in v["Secrets"]] if "Secrets" in v else []) + ['puid', 'pgid']
	payload = list(dict.fromkeys(items))
	return payload


def parseLabels(v):
	return { x for x in v["labels"] } if "labels" in v else dict()


class ComposeFile(object):
	def __init__(self,
	             domain = "example.com",
	             stackTitle = str(),
	             authenticatedEmailsFile = str(),
	             emailAddress = "email@mydomain.com",
	             stackDict = dict(),
	             defaults = dict(),
	             externalServers = dict(),
	             globalValues = dict(),
	             authenticatedEmailsContainerPath = "/config/authenticated-emails.txt",
	             organizrSubdomain = "home",
	             secretsPath = "${SECRETS}",
	             puid = str(1001),
	             pgid = str(1001),
	             version = 3.7,
	             frontendIP = "192.168.80",
	             openVpnName = "openvpn",
	             subnetStart = 225):
		self.oauthService = None
		# master list of all active ports in a given stack
		self.defaults = defaults
		self.activePorts = list()
		self.networks = dict()
		self.stackDict = stackDict
		self.local_volumes = list()
		self.conditionals = dict()
		self.combinedConditionals = dict()
		self.externalServers = externalServers
		self.globalValues = globalValues
		self.secretsPath = str(secretsPath)
		self.domain = str(setItems(self, "Domain",
		                           self.defaults,
		                           domain))
		self.email = str(setItems(self, "Email",
		                          self.defaults,
		                          emailAddress))
		self.secrets = setItems(self, "Secrets", self.stackDict, dict())
		self.conditionals.update({ "oauth": bool() })
		self.conditionals.update({ "proxy_secrets": bool() })
		self.ports = list()
		self.proxy_networks = dict()
		self.authenticatedEmailsFile = str(self.defaults["Authenticated Emails File"])
		self.services = dict()
		self.secrets.update({ 'puid': { "file": f"{self.secretsPath}/{'PUID'.upper()}.secret" } })
		self.secrets.update({ 'pgid': { "file": f"{self.secretsPath}/{'PGID'.upper()}.secret" } })
		self.conditionals.update({ "Volumes": bool("Volumes" in self.stackDict and self.stackDict["Volumes"]) })
		self.globals = dict()
		self.globals.update({ "version": str(version) })
		self.globals.update({ "networks": IP(self.defaults, self.globalValues, self.stackDict).networks })
		self.globals.update({ "secrets": self.secrets })
		self.globals.update({ "volumes": dict() })
		self.globals["volumes"].update({ vol: { "external": bool(True) } \
		                                 for vol in self.stackDict["Volumes"] } \
			                               if self.conditionals["Volumes"] \
			                               else dict())
		self.globals.update(IP(self.defaults, self.globalValues, self.stackDict).networks)
		self.ip = str(IP(self.defaults, self.globalValues, self.stackDict).address)
		self.frontendIP = frontendIP
		self.organizrSubdomain = formatString(organizrSubdomain)
		self.organizrURL = self.parseOrganizrFQDN()
		self.authenticatedEmailsFile = str(authenticatedEmailsFile)
		self.authenticatedEmailsContainerPath = str(authenticatedEmailsContainerPath)
		self.backend_subnet = str(IP(self.defaults, self.globalValues, self.stackDict).backendSubnet)
		# i = int()
		for index, (k, v) in enumerate(setItems(self, "Services", self.stackDict, dict()).items()):
			self.local_volumes = list()
			# add logic to loop the octet backwards when hitting 0 along with knowing what numbers are network /
			# broadcast addresses
			self.fourthOctet = subnetStart - index
			self.stackTitle = formatString(stackTitle)
			k = formatString(k)
			self.vpnContainerName = formatString('-'.join([self.stackTitle, "pia-openvpn"]).lower())
			# bandage fix make dynamic
			if openVpnName in k:
				k = self.vpnContainerName
			self.services.update({ k: dict() })
			self.globals.update({ "services": self.services })
			self.networks = {
					"networks": {
							"backend":  { "ipv4_address": f"{self.ip}.{self.fourthOctet}" },
							"frontend": dict(),  # { "ipv4_address": f"{self.frontendIP}.{self.fourthOctet}" }
							}
					}
			self.services.update({ k: { "volumes": list() } })
			self.setConditionals(v)
			self.setLocalVolumes(k, v)
			self.ports = list()
			self.environment = Environs(k, v, self)
			self.services[k].update(self.environment.obj)
			self.dns = ["8.8.8.8", "8.8.4.4"]
			self.local_secrets = combineLocalSecrets(v)
			self.puid = str(int(setItems(self, "PUID", self.defaults, puid)))
			self.pgid = str(int(setItems(self, "PGID", self.defaults, pgid)))
			self.services[k].update({ "container_name": k })
			self.services[k].update(self.parseLocalSecrets(v))
			v["secrets"] = self.services[k]['secrets']
			self.setPrivs(k)
			self.labels = parseLabels(v)
			if self.conditionals["Entrypoint"]:
				self.services[k].update({ "entrypoint": v["Entrypoint"] })
				[self.parseList(k, v, x) for x in ["cap_add", "cap_drop", "sysctls", "depends_on"]]
			self.setNetworking(k, v)
			self.traefik = classes.traefik.Traefik(self,
			                                       self.ports,
			                                       self.globalValues, k, v)
			self.setCommands(k, v)
			# expand this out into a much better more robust version of build
			# likely this approach will work for almost every resource type as a cleaner way to do this
			# TODO: add logic to put image here and not in its other location
			# really fragile right now as context must also be defined
			if ("build" in v and v["build"]) and ("args" in v["build"] and v["build"]["args"]):
				self.services[k].update({ "build": { "args": v["build"]["args"] } })
				self.services[k]["build"].update({ "context": v["build"]["context"] })
			self.services[k].update(parseImage(v))
			if (not (not (not self.traefik.subdomains)
			         and not (self.conditionals["proxy_secrets"] or self.conditionals["oauth"]))) \
					and not re.match('(?i)plex.linker', k) \
					and not re.match(f'(?i){self.vpnContainerName}', k):
				try:
					del self.networks["networks"]["frontend"]
				except (KeyError, TypeError):
					pass
			## SETS DNS
			if "vpn" not in v or self.vpnContainerName == k:
				if self.conditionals["DNS"]:
					self.dns = [v["DNS"]]
				self.services[k].update({ "domainname": self.domain })
				try:
					self.services[k].update({ "dns_search": list(dict.fromkeys(self.traefik.subdomains)) })
					self.services[k].update({ "dns": list(dict.fromkeys(self.dns)) })
					if not self.services[k]["dns_search"]:
						del self.services[k]["dns_search"]
				except (KeyError, TypeError):
					pass
			if self.combinedConditionals["frontend_no_oauth"]:
				self.labels.update(self.traefik.labels)
			if self.conditionals["oauth"] or self.conditionals["proxy_secrets"]:
				self.services.update(OauthProxy(k, self).obj)
			else:
				try:
					self.services[k].update({ "labels": self.labels })
				except (KeyError, TypeError):
					pass
			self.services[k]["restart"] = "on-failure"
			if "network_mode" in self.services[k] and "vpn" not in k:
				if not "depends_on" in self.services[k]:
					self.services[k].update({ "depends_on": list() })
				self.services[k]["depends_on"].append(self.vpnContainerName)
				if "vpn" not in k:
					for i in ["dns", "dns_search", "domainname"]:
						try:
							del self.services[k][i]
						except (KeyError, TypeError):
							pass
			if k.lower() == "depends_on" and k in self.services[k]["depends_on"]:
				self.services[k]["depends_on"].remove(k)
			try:
				self.dictCleanup(k)
			except (KeyError, TypeError):
				pass
			if "vpn" in k or k is self.vpnContainerName:
				self.services[k].update({ "dns": ["8.8.8.8", "8.8.4.4"] })
	
	def dictCleanup(self, k):
		self.removeEmptyDict(k, "labels")
		self.removeEmptyDict(k, "volumes")
		if "volumes" in self.globals and not self.globals["volumes"]:
			del self.globals["volumes"]
		self.local_secrets = list()
	
	def setCommands(self, k, v):
		if self.conditionals["Commands"]:
			payload = v["Commands"]
			self.services[k].update({ "command": list(dict.fromkeys(payload)) })
	
	def setNetworking(self, k, v):
		if self.conditionals["ports"]:
			self.ports = v["ports"]
		if self.conditionals["vpn"]:
			self.services[k].update({ "network_mode": ":".join(["service", self.vpnContainerName]) })
		else:
			self.services[k].update(getServiceHostname(k))
			if not self.conditionals["mask_ports"]:
				if self.ports.__len__() > 0:
					self.services[k].update({ "ports": self.ports })
			self.services[k].update(self.networks)
	
	def setLocalVolumes(self, k, v):
		self.local_volumes = [vol for vol in v["Volumes"]] if ("Volumes" in v and v["Volumes"]) else []
		self.services[k].update({ "volumes": list(dict.fromkeys(self.local_volumes)) })
	
	def setPrivs(self, k):
		if self.conditionals["privileged"]:
			self.services[k].update({ "privileged": bool(True) })
		else:
			self.services[k].update({ "user": f"{self.puid}:{self.pgid}" })
	
	def setHealthcheck(self, k):
		if self.conditionals["healthcheck"]:
			healthcheck = {
					"healthcheck": {
							{ "test": ["CMD", "curl", "-f", "http://localhost"] },
							{ "interval": "1m30s" },
							{ "timeout": "10s" },
							{ "retries": 3 },
							{ "start_period": "40s" } }
					}
			self.services[k].update(healthcheck)
	
	def setLogging(self, k):
		if self.conditionals["logging"]:
			logging = dict().update({ "driver": str("json-file") })
			logging.update({ "options": dict() })
			logging["options"].update({ "max-size": str("200k") })
			logging["options"].update({ "max-file": str(10) })
			self.services[k].update({ "logging": logging })
	
	def removeEmptyDict(self, k, environ):
		if environ in self.services[k] and not self.services[k][environ]:
			del self.services[k][environ]
	
	def setConditionals(self, v):
		self.conditionals.update({ "entrypoint": bool("entrypoint" in v and v["entrypoint"]) })
		self.conditionals.update({ "Entrypoint": bool("Entrypoint" in v and v["Entrypoint"]) })
		self.conditionals.update({ "oauth": bool("OAUTH_PROXY" in v and v["OAUTH_PROXY"]) })
		self.conditionals.update({ "ports": bool("ports" in v and v["ports"]) })
		self.conditionals.update({ "privileged": bool("privileged" in v and v["privileged"]) })
		self.conditionals.update({ "proxy_secrets": bool("proxy_secrets" in v and v["proxy_secrets"]) })
		self.conditionals.update({ "subdomains": bool("subdomains" in v and v["subdomains"]) })
		self.conditionals.update({ "Volumes": ("Volumes" in v and v["Volumes"]) })
		self.conditionals.update({ "volumes": ("volumes" in v and v["volumes"]) })
		self.conditionals.update(
				{ "vpn": (("networks" in v) and ("vpn" in v["networks"]) and (v["networks"]["vpn"]) or "vpn" in v) })
		self.conditionals.update({ "mask_ports": ("mask_ports" in v and v["mask_ports"]) })
		self.conditionals.update({ "DNS": ("DNS" in v and v["DNS"]) })
		self.conditionals.update({ "Commands": ("Commands" in v and v["Commands"]) })
		self.combinedConditionals.update({
				"frontend_no_oauth": (not self.conditionals["oauth"] \
				                      and self.conditionals["ports"] \
				                      and self.conditionals["subdomains"])
				})
	
	def parseList(self, name, container, environ):
		if environ in container and container[environ]:
			payload = [str(x) for x in container[environ]]
			self.services[name].update({ str(environ): payload })
	
	def parseLocalSecrets(self, v):
		if "secrets" in v:
			self.local_secrets = [secret for secret in v["secrets"]] if "secrets" in v else [self.secrets.keys()]
		# add conditional change to not be in place if network mode is toggled
		payload = { "secrets": list(dict.fromkeys(self.local_secrets)) }
		return payload
	
	def parseOrganizrFQDN(self):
		domainComponentList = [self.organizrSubdomain, self.domain]
		payload = formatString(".".join(domainComponentList))
		formatString(payload)
		return payload
	
	def parsePort(self, service, compose, port = 80):
		if service == "plex":
			port = 32400
		elif self.ports:
			port = str(self.ports[0]).split(":")[1]
		compose.activePorts = list(dict.fromkeys(compose.activePorts + [port]))
		return int(port)
