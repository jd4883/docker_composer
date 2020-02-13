from src.formatting import formatString
from src.gets import getServiceHostname
from src.parser import parseImage
from src.sets import setItems


class Traefik(object):
	def __init__(self,
	             globalValues = dict(),
	             domain = "example.com",
	             emailAddress = "email@mydomain.com",
	             frontendNetwork = "frontend",
	             backendNetwork = "backend"):
		self.frontendNetwork = formatString(setItems(self,
		                                             "Networks",
		                                             globalValues,
		                                             frontendNetwork,
		                                             0))
		self.backendNetwork = formatString(setItems(self,
		                                            "Networks",
		                                            globalValues,
		                                            backendNetwork,
		                                            1))


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


def setCustomResponseHeader(customResponseHeaders):
	payload = {
			"X-Robots-Tag": ["noindex", "nofollow", "nosnippet", "noarchive", "notranslate", "noimageindex", "none"]
			}
	customResponseHeaders.update(payload)
	return customResponseHeaders


def combineLocalSecrets(v):
	items = ([x for x in v["Secrets"]] if "Secrets" in v else []) + ['puid', 'pgid']
	payload = listCleanup(items)
	return payload


class ComposeFile(object):
	def __init__(self,
	             domain = "example.com",
	             vpnContainerName = "vpn",
	             stackTitle = str(),
	             authenticatedEmailsFile = str(),
	             emailAddress = "email@mydomain.com",
	             stackDict = dict(),
	             defaults = dict(),
	             externalServers = dict(),
	             globalValues = dict(),
	             customResponseHeaders = dict(),
	             authenticatedEmailsContainerPath = "/config/authenticated-emails.txt",
	             traefikProtocol = "http",
	             organizrSubdomain = "home",
	             secretsPath = "${SECRETS}",
	             oauth_port = str(4180),
	             puid = str(1001),
	             pgid = str(1001),
	             version = 3.7,
	             frontendIP = "192.168.80"):
		self.stackDict = stackDict
		self.defaults = defaults
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
		self.traefikProtocol = traefikProtocol
		self.oauth_port = oauth_port
		self.authenticatedEmailsFile = str(authenticatedEmailsFile)
		self.services = dict()
		self.secrets.update({ 'puid': { "file": f"{self.secretsPath}/{'PUID'.upper()}.secret" } })
		self.secrets.update({ 'pgid': { "file": f"{self.secretsPath}/{'PGID'.upper()}.secret" } })
		self.conditionals.update({ "Volumes": bool("Volumes" in self.stackDict and self.stackDict["Volumes"]) })
		self.globals = dict()
		self.globals.update({ "version": str(version) })
		self.globals.update({ "networks": IP(self.defaults, self.globalValues, self.stackDict).networks })
		self.globals.update({ "secrets": self.secrets })
		self.globals.update({ "volumes": dict() })
		self.globals["volumes"].update(
				{ vol: { "external": bool(True) } for vol in self.stackDict["Volumes"] } if self.conditionals[
					"Volumes"] else dict())
		self.globals.update(IP(self.defaults, self.globalValues, self.stackDict).networks)
		self.cap_add = list()
		self.cap_drop = list()
		self.sysctls = list()
		self.ip = str(IP(self.defaults, self.globalValues, self.stackDict).address)
		self.frontendIP = frontendIP
		self.organizrSubdomain = formatString(organizrSubdomain)
		self.organizrURL = self.parseOrganizrFQDN()
		self.authenticatedEmailsFile = str(authenticatedEmailsFile)
		self.authenticatedEmailsContainerPath = str(authenticatedEmailsContainerPath)
		self.backend_subnet = str(IP(self.defaults, self.globalValues, self.stackDict).backendSubnet)
		i = int()
		for k, v in setItems(self, "Services", self.stackDict, dict()).items():
			i += 1
			self.fourthOctet = 255 - i
			self.stackTitle = formatString(stackTitle)
			self.services.update({ k: dict() })
			## INIT SERVICE DICT
			k = formatString(k)
			self.local_secrets = combineLocalSecrets(v)
			self.labels = listCleanup([x for x in v["labels"]]) if "labels" in v else list()
			self.ports = list()
			self.stackTitle = formatString(stackTitle)
			self.vpnContainerName = formatString(vpnContainerName)
			self.vpnHostName = self.setVPNHostname()
			self.puid = str(int(setItems(self, "PUID", self.defaults, puid)))
			self.pgid = str(int(setItems(self, "PGID", self.defaults, pgid)))
			self.oauth_image = "a5huynh/oauth2_proxy:latest"
			self.service_proxy = f"{k}_proxy"
			self.subdomains = list()
			self.setConditionals(v)
			self.dns = ["8.8.8.8", "8.8.4.4"]
			## END SERVICE INIT
			self.services.update({ k: { "volumes": list() } })
			self.local_volumes = list()
			self.services[k].update({ "container_name": k })
			self.services[k].update(parseImage(v))
			self.services[k].update(self.parseLocalSecrets(v))
			v["secrets"] = self.services[k]['secrets']
			self.services[k].update({ "env_file": listCleanup(["globals.env", f"{k}.env"]) })
			self.setPrivs(k)
			self.setNetworking(k, v, vpnContainerName)
			self.globals.update({ "services": self.services })
			self.traefikLabels = Traefik(self.globalValues, self.domain, self.email)
			self.customResponseHeaders = setCustomResponseHeader(customResponseHeaders)
			self.customResponseHeadersValue = self.parseCustomResponseHeader()
			self.customFrameOptionsValue = self.parseCustomFrameOptionsValue()
			traefik_labels = self.setTraefikLabels(k, v)
			if self.conditionals["Entrypoint"]:
				self.services[k].update({ "entrypoint": v["Entrypoint"] })
			self.setLocalVolumes(k, v)
			self.setHealthcheck(k)
			self.setLogging(k)
			self.parseList(k, v, "cap_add")
			self.parseList(k, v, "cap_drop")
			self.parseList(k, v, "sysctls")
			if "depends_on" in v and v["depends_on"]:
				payload = v["depends_on"]
				self.services[k].update({ str("depends_on"): [str(x1) for x1 in payload] })
			self.setCommands(k, v)
			
			# plan is to use labels as a reference point instead of recalculating
			
			# this is really stupid and should get removed just not sure where I have a logic error yet
			
			## SETS DNS
			if self.conditionals["DNS"] and "vpn" not in v:
				self.dns = [v["DNS"]]
				## SETS DOMAIN NAME
				self.services[k].update({ "domainname": self.domain })
			if self.combinedConditionals["frontend_no_oauth"]:
				for label in traefik_labels:
					if label not in self.labels:
						self.labels.append(label)
				self.services[k].update({ "dns_search": listCleanup(self.subdomains) })
				self.services[k].update({ "dns": listCleanup(self.dns) })
			elif self.conditionals["oauth"] or self.conditionals["proxy_secrets"]:
				if self.service_proxy not in self.services:
					self.services.update({ str(self.service_proxy): dict() })
				if "labels" not in self.services[self.service_proxy]:
					self.services[self.service_proxy].update({ "labels": list() })
				self.buildOauthObject(k, traefik_labels)
			# elif "networks" in self.services[k] and "frontend" in self.services[k]["networks"]:
			# 	del self.services[k]["networks"]["frontend"]
			
			self.services[k].update({ "labels": listCleanup(self.labels) })
			
			# TODO: clean up replace statement in a better way
			
			# conditionals - move to a separate class down the line
			self.dictCleanup(k)
	
	def dictCleanup(self, k):
		self.removeEmptyDict(k, "labels")
		self.removeEmptyDict(k, "volumes")
		if "volumes" in self.globals and not self.globals["volumes"]:
			del self.globals["volumes"]
		# resets value may be depricatable
		self.local_secrets = list()
	
	def setCommands(self, k, v):
		if self.conditionals["Commands"]:
			payload = v["Commands"]
			self.services[k].update({ str("command"): listCleanup(payload) })
	
	def setNetworking(self, k, v, vpnContainerName):
		if self.conditionals["ports"]:
			self.ports = v["ports"]
		if self.conditionals["vpn"]:
			self.services.update({ "network_mode": f"service:{vpnContainerName}" })
		else:
			self.services[k].update(getServiceHostname(k))
			if not self.conditionals["mask_ports"]:
				if self.ports.__len__() > 0:
					self.services[k].update({ "ports": self.ports })
			self.networks = { "networks": ["backend", "frontend"] }
			# self.networks = {
			# 		"networks": {
			# 				"backend": { "ipv4_address": f"{self.ip}.{self.fourthOctet}" },
			# 				"frontend": dict()  # { "ipv4_address": f"{self.frontendIP}.{self.fourthOctet}" }
			# 				}
			# 		}
			self.services[k].update(self.networks)
	
	def setLocalVolumes(self, k, v):
		if "Volumes" in v and v["Volumes"]:
			for vol in v["Volumes"]:
				self.local_volumes.append(vol)
			self.services[k].update({ "volumes": listCleanup(self.local_volumes) })
	
	def setPrivs(self, k):
		if self.conditionals["privileged"]:
			self.services[k].update({ "privileged": bool(True))
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
	
	def buildOauthObject(self, k, traefik_labels):
		# TODO: - logic can be improved here to remove the oauth secrets completely from the base
		# TODO: make all oauth file reads rather or come from vault
		authenticatedEmails = f"{self.authenticatedEmailsFile}:{self.authenticatedEmailsContainerPath}:ro"
		# self.labels.append(f"{k}.oauth.backend={k}")
		# self.labels.append(f"{k}.oauth.frontend={self.service_proxy}")
		# self.services[self.service_proxy]["labels"].append(f"{k}.oauth.backend={k}")
		# self.services[self.service_proxy]["labels"].append(f"{k}.oauth.frontend={self.service_proxy}")
		# TODO: add handling to prevent oauth port here
		
		parsedPort = self.parsePort(k)
		schema = "http" if str(parsedPort) != str(443) else "https"
		upstream = f"{schema}://{k}:80"
		if self.conditionals["vpn"] and self.conditionals["ports"]:
			upstream = f"{schema}://{self.vpnContainerName}:{parsedPort}"
		elif self.conditionals["ports"]:
			upstream = f"{schema}://{k}:{parsedPort}"
		provider = "github"
		oauthCommands = listCleanup([
				f"cookie-secure=false",
				f"authenticated-emails-file={self.authenticatedEmailsContainerPath}",
				f"email-domain=gmail",
				f"upstream={upstream}",
				f"http-address=http://0.0.0.0:{self.oauth_port}",
				f"provider={provider}",
				f"redirect-url=https://{self.subdomains[0]}",
				])
		## APPEND SERVICE OAUTH LABEL
		self.oauth = self.setOauthProxyFlags(k)
		for x in traefik_labels:
			if x not in self.services[self.service_proxy]["labels"]:
				self.services[self.service_proxy]["labels"].append(x)
		self.services[self.service_proxy].update(
				{ "labels": listCleanup(self.services[self.service_proxy]["labels"]) })
		self.services[self.service_proxy].update({ "container_name": self.service_proxy })
		#self.services[self.service_proxy].update({ "hostname": self.service_proxy })
		self.services[self.service_proxy].update({ "image": self.oauth_image })
		self.services[self.service_proxy].update({ "secrets": listCleanup(self.local_secrets) })
		self.services[self.service_proxy].update({ "env_file": listCleanup(["globals.env", f"{k}.env"]) })
		self.services[self.service_proxy].update({ "volumes": [authenticatedEmails] })
		self.services[self.service_proxy].update({ "user": f"{self.puid}:{self.pgid}" })
		self.services[self.service_proxy].update({ "networks": listCleanup(["frontend", "backend"]) })
		self.services[self.service_proxy].update({ "dns_search": listCleanup(self.subdomains) })
		self.services[self.service_proxy].update({ "dns": listCleanup(self.dns) })
		self.services[self.service_proxy].update({ "depends_on": [k] })
		self.services[self.service_proxy].update({ "restart": "always" })
		self.services[self.service_proxy].update({ "command": listCleanup(oauthCommands) })
	
	def globalVolumes(self):
		payload = dict()
		if "Volumes" in self.stackDict and self.stackDict["Volumes"]:
			payload = listCleanup(self.stackDict["Volumes"])
		return payload
	
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
		self.conditionals.update({ "healthcheck": ("healthcheck" in v and v["healthcheck"]) })
		self.conditionals.update({ "logging": ("logging" in v and v["logging"]) })
		self.conditionals.update({ "Commands": ("Commands" in v and v["Commands"]) })
		self.combinedConditionals.update(
				{
						"frontend_no_oauth":
							(
									not self.conditionals["oauth"] and
									self.conditionals["ports"] and
									self.conditionals["subdomains"])
						}
				)
	
	def parseList(self, name, container, environ):
		if environ in container and container[environ]:
			payload = [container[environ]]
			self.services[name].update({ str(environ): [str(x) for x in payload] })
	
	def parseLocalSecrets(self, v):
		if "secrets" in v:
			self.local_secrets = [secret for secret in v["secrets"]] if "secrets" in v else [self.secrets.keys()]
		# add conditional change to not be in place if network mode is toggled
		payload = { "secrets": listCleanup(self.local_secrets) }
		return payload
	
	def setOauthProxyFlags(self, name):
		payload = bool()
		if self.conditionals["oauth"] or self.conditionals["proxy_secrets"]:
			payload = str(bool(True)).lower()
			base = f"{self.secretsPath}/{name}/OAUTH2_PROXY_"
			# adds to global secrets
			self.secrets.update({ f"{name}_proxy_client_id": { "file": f"{base}CLIENT_ID.secret" } })
			self.secrets.update({ f"{name}_proxy_client_secret": { "file": f"{base}CLIENT_SECRET.secret" } })
			self.secrets.update({ f"{name}_proxy_cookie_secret": { "file": f"{base}COOKIE_SECRET.secret" } })
			# secrets per service
			self.local_secrets += [
					f"{name}_proxy_client_id",
					f"{name}_proxy_client_secret",
					f"{name}_proxy_cookie_secret",
					]
		return payload
	
	def setVPNHostname(self):
		payload = "-".join([self.stackTitle, self.vpnContainerName])
		return payload
	
	def parseOrganizrFQDN(self):
		domainComponentList = [self.organizrSubdomain, self.domain]
		payload = formatString(".".join(domainComponentList))
		formatString(payload)
		return payload
	
	def setTraefikLabels(self, service, items):
		subdomains = ".".join([service, self.domain])
		self.subdomains = list()
		if "subdomains" in items and items["subdomains"]:
			for sub in items["subdomains"]:
				if not str(sub).startswith("http"):
					self.subdomains.append(".".join([sub, self.domain]))
			if subdomains not in items["subdomains"]:
				self.subdomains.append(subdomains)
		subdomains = str(",".join(listCleanup(self.subdomains))).replace(f"https://{self.organizrURL}.{self.domain}, ", "")
		port = self.parsePort(service)
		traefik_port = self.oauth_port if self.conditionals["oauth"] or self.conditionals["proxy_secrets"] else port
		payload = listCleanup([
				f"traefik.backend={self.getServiceName(service)}",
				f"traefik.{service}.frontend.rule='Host:{subdomains}'",
				f"traefik.docker.network={self.traefikLabels.frontendNetwork}",
				f"traefik.frontend.headers.browserXSSFilter={str(bool(True)).lower()}",
				f"traefik.frontend.headers.contentTypeNosniff={str(bool(True)).lower()}",
				f"traefik.frontend.headers.customFrameOptionsValue={self.customFrameOptionsValue}",
				f"traefik.frontend.headers.customResponseHeaders={self.customResponseHeadersValue}",
				f"traefik.frontend.headers.forceSTSHeader={str(bool(True)).lower()}",
				f"traefik.frontend.headers.frameDeny={str(bool(True)).lower()}",
				f"traefik.frontend.headers.SSLForceHost={str(bool(True)).lower()}",
				f"traefik.frontend.headers.SSLHost={self.subdomains[0]}",
				f"traefik.frontend.headers.SSLRedirect={str(bool(True)).lower()}",
				f"traefik.frontend.headers.STSIncludeSubdomains={str(bool(True)).lower()}",
				f"traefik.frontend.headers.STSPreload={str(bool(True)).lower()}",
				f"traefik.frontend.headers.STSSeconds={315360000}",
				f"traefik.frontend.passHostHeader={str(bool(True)).lower()}",
				f"traefik.port={traefik_port}",
				f"traefik.protocol={self.traefikProtocol}",
				])
		# change all to traefik.service for constency and multi port mapping
		return payload
	
	def getServiceName(self, service):
		payload = str(service)
		if self.conditionals["oauth"] or self.conditionals["proxy_secrets"]:
			payload += "_proxy"
		return payload
	
	def parsePort(self, service, port = 80):
		if service == "plex":
			port = 32400
		# elif self.conditionals["oauth"]:
		# 	port = str(self.oauth_port)
		elif self.ports:
			port = str(self.ports[0]).split(":")[1]
		return int(port)
	
	def parseCustomFrameOptionsValue(self):
		urls = self.subdomains
		urls.append(f"'https://{self.organizrURL}'")
		allowFrom = f"'allow-from {str(','.join(listCleanup(urls)))}'"
		payload = ",".join(["'SAMEORIGIN'", allowFrom])
		return payload
	
	def parseCustomResponseHeader(self):
		headerList = list()
		for k, v in self.customResponseHeaders.items():
			value = ','.join(v)
			headerList.append(f"{k}: {value}")
		payload = formatString(",".join(listCleanup(headerList)))
		return payload


def listCleanup(x):
	return list(dict.fromkeys(x))


def listToDict(x):
	y = iter(x)
	res_dct = dict(zip(y, y))
	return res_dct
