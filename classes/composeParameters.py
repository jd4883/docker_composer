from src.formatting import formatString
from src.sets import setItems


class Traefik(object):
	def __init__(self,
	             globalValues = dict(),
	             domain = "example.com",
	             emailAddress = "email@mydomain.com",
	             frontendNetwork = "frontend",
	             backendNetwork = "backend"):
		self.frontendNetwork = formatString(self, setItems(self,
		                                                   "Networks",
		                                                   globalValues,
		                                                   frontendNetwork,
		                                                   0))
		self.backendNetwork = formatString(self, setItems(self,
		                                                  "Networks",
		                                                  globalValues,
		                                                  backendNetwork,
		                                                  1))


class IP(object):
	def __init__(self,
	             defaults = dict(),
	             globals = dict(),
	             stackDict = dict(),
	             octet1 = int(10),
	             octet2 = int(23),
	             networkIP = int(0),
	             externalNetworkBool = bool(True),
	             defaultNetworkDriver = "bridge"):
		self.subnetMask = str(int(setItems(self, "subnetMask",
		                                   globals)))
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
		self.address = formatString(self, ".".join(self.octetsList))
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
		payload = formatString(self, "/".join(subnetMaskComponents))
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
	             labels = list(),
	             customResponseHeaders = dict(),
	             authenticatedEmailsContainerPath = "/config/authenticated-emails.txt",
	             traefikProtocol = "http",
	             organizrSubdomain = "home",
	             secretsPath = "${SECRETS}",
	             oauth_port = str(4180),
	             puid = str(1001),
	             pgid = str(1001),
	             version = 3.7):
		self.stackDict = stackDict
		self.services = setItems(self, "Services", self.stackDict, dict())
		self.defaults = defaults
		self.externalServers = externalServers
		self.globalValues = globalValues
		self.secretsPath = str(secretsPath)
		self.secrets = setItems(self, "Secrets", self.stackDict, dict())
		for service in self.services:
			# TODO:
			# will add in support for dynamic secret reading from globals, need to have path support though
			# also this area would be a lot better if it auto generates the files or integrates with vault
			
			# if self.secrets:
			# 	for secret in self.secrets:
			# 		if str(service).lower() in str(secret).lower():
			# 			parsedPath = f"{self.secretsPath}/{service}/{secret.upper()}.secret"
			# 			self.secrets[secret].update({ "file": parsedPath })
			self.oauth_enabled = "OAUTH_PROXY" in self.services[service] and self.services[service]["OAUTH_PROXY"]
			self.proxy_secrets_enabled = "proxy_secrets" in self.services[service] and self.services[service]["proxy_secrets"]
			service = formatString(self, service)
			if self.oauth_enabled or self.proxy_secrets_enabled:
				base = f"{self.secretsPath}/{service}"
				proxy_client_id_file = f"{base}/OAUTH2_PROXY_CLIENT_ID.secret"
				self.secrets.update({f"{service.replace('-','_')}_proxy_client_id":{"file": proxy_client_id_file}})
				proxy_client_secret_file = f"{base}/OAUTH2_PROXY_CLIENT_ID.secret"
				self.secrets.update({f"{service.replace('-','_')}_proxy_client_secret":{"file": proxy_client_secret_file}})
				proxy_cookie_secret_file = f"{base}/OAUTH2_PROXY_CLIENT_ID.secret"
				self.secrets.update({f"{service.replace('-','_')}_proxy_cookie_secret":{"file": proxy_cookie_secret_file}})
		parsedPath = f"{self.secretsPath}/{'PUID'.upper()}.secret"
		self.secrets.update({'puid':{ "file": parsedPath }})
		parsedPath = f"{self.secretsPath}/{'PGID'.upper()}.secret"
		self.secrets.update({'pgid':{ "file": parsedPath }})
		
		
		self.ip = str(IP(self.defaults, self.globalValues, self.stackDict).address)
		self.globals = {
				"networks": IP(self.defaults, self.globalValues, self.stackDict).networks,
				"secrets":  self.secrets,
				"volumes":  setItems(self, "Volumes", self.stackDict),
				"version":  f'"{version}"',
				"services": dict()
				}
		self.globals.update(IP(self.defaults, self.globalValues, self.stackDict).networks)
		
		self.domain = str(setItems(self, "Domain",
		                           self.defaults,
		                           domain))
		self.email = str(setItems(self, "Email",
		                          self.defaults,
		                          emailAddress))
		self.traefikLabels = Traefik(self.globalValues, self.domain, self.email)
		# traefik
		self.traefikProtocol = traefikProtocol
		self.oauth_port = oauth_port
		self.authenticatedEmailsFile = str(authenticatedEmailsFile)
		self.stackTitle = formatString(self, stackTitle)
		
		self.organizrSubdomain = formatString(self, organizrSubdomain)
		self.labels = labels
		self.customResponseHeaders = self.setCustomResponseHeader(customResponseHeaders)
		self.backend_subnet = str(IP(self.defaults, self.globalValues, self.stackDict).backendSubnet)
		self.organizrURL = self.parseOrganizrFQDN()
		self.customResponseHeadersValue = self.parseCustomResponseHeader()
		self.customFrameOptionsValue = self.parseCustomFrameOptionsValue()
		self.traefikLabels = self.setTraefikLabels()
		self.appendLabelsForTraefik()
		
		self.puid = str(int(setItems(self, "PUID", self.defaults, puid)))
		self.pgid = str(int(setItems(self, "PGID", self.defaults, pgid)))
		self.authenticatedEmailsFile = str(authenticatedEmailsFile)
		self.authenticatedEmailsContainerPath = str(authenticatedEmailsContainerPath)
		self.stackTitle = formatString(self, stackTitle)
		self.vpnContainerName = formatString(self, vpnContainerName)
		self.vpnHostName = self.setVPNHostname()
		# conditionals - move to a separate class down the line
		self.conditionals = list()
	
	def setVPNHostname(self):
		return "-".join([self.stackTitle, self.vpnContainerName])
	
	def parseOrganizrFQDN(self):
		domainComponentList = [self.organizrSubdomain, self.domain]
		payload = formatString(self, ".".join(domainComponentList))
		formatString(self, payload)
		return payload
	
	def setCustomResponseHeader(self, customResponseHeaders):
		customResponseHeaders.update({
				"X-Robots-Tag": ["noindex",
				                 "nofollow",
				                 "nosnippet",
				                 "noarchive",
				                 "notranslate",
				                 "noimageindex",
				                 "none"]
				})
		return customResponseHeaders
	
	def appendLabelsForTraefik(self):
		for label in self.traefikLabels:
			self.labels.append(label)
	
	def setTraefikLabels(self):
		payload = [{ "traefik.frontend.headers.customFrameOptionsValue": self.customFrameOptionsValue },
		           { "traefik.frontend.passHostHeader": bool(True) },
		           { "traefik.frontend.headers.STSPreload": bool(True) },
		           { "traefik.protocol": self.traefikProtocol },
		           { "traefik.frontend.headers.frameDeny": bool(True) },
		           { "traefik.docker.network": self.traefikLabels.frontendNetwork },
		           { "traefik.frontend.headers.SSLRedirect": bool(True) },
		           { "traefik.frontend.headers.SSLForceHost": bool(True) },
		           { "traefik.frontend.headers.browserXSSFilter": bool(True) },
		           { "traefik.frontend.headers.STSSeconds": 315360000 },
		           { "traefik.frontend.headers.contentTypeNosniff": bool(True) },
		           { "traefik.frontend.headers.forceSTSHeader": bool(True) },
		           { "traefik.frontend.headers.customResponseHeaders": self.customResponseHeadersValue },
		           { "traefik.frontend.headers.STSIncludeSubdomains": bool(True) }]
		return payload
	
	def parseCustomFrameOptionsValue(self, items = ["SAMEORIGIN"]):
		# urls = list()
		# urls.append(f"https://{self.organizrURL}")
		urls = f"https://{self.organizrURL}"
		# urls.append(f"https://{self.organizrURL}")
		# allowFrom = f"'allow-from {str(','.join(urls))}'"
		payload = f"'SAMEORIGIN','allow-from https://{self.organizrURL}'"
		# items.append(f"{allowFrom}")
		# payload = ",".join(items)
		return payload
	
	def parseCustomResponseHeader(self):
		headerList = list()
		for k, v in self.customResponseHeaders.items():
			value = ','.join(v)
			headerList.append(f"{k}: {value}")
		payload = formatString(self, ",".join(headerList))
		return payload
