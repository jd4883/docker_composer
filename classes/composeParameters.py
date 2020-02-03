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
	             frontendNetwork = "frontend",
	             backendNetwork = "backend",
	             authenticatedEmailsContainerPath = "/config/authenticated-emails.txt",
	             traefikProtocol = "http",
	             organizrSubdomain = "home",
	             secretsPath = "${SECRETS}",
	             oauth_port = str(4180),
	             puid = str(1001),
	             pgid = str(1001),
	             version = 3.8):
		self.stackDict = stackDict
		self.defaults = defaults
		self.externalServers = externalServers
		self.globalValues = globalValues
		self.secrets = setItems(self, "Secrets",
		                        self.stackDict)
		self.volumes = setItems(self, "Volumes",
		                        self.stackDict)
		self.services = setItems(self, "Services",
		                         self.stackDict)
		self.domain = str(setItems(self, "Domain",
		                           self.defaults,
		                           domain))
		self.email = str(setItems(self, "Email",
		                          self.defaults,
		                          emailAddress))
		self.frontendNetwork = formatString(self, setItems(self, "Networks",
		                                                   self.globalValues,
		                                                   frontendNetwork,
		                                                   0))
		self.backendNetwork = formatString(self, setItems(self, "Networks",
		                                                  self.globalValues,
		                                                  backendNetwork,
		                                                  1))
		self.traefikProtocol = traefikProtocol
		self.globals = {
				"networks": dict(),
				"secrets":  dict(),
				"volumes":  dict(),
				"version":  f'"{version}"'
				}
		self.oauth_port = oauth_port
		self.puid = str(int(setItems(self, "PUID", self.defaults, puid)))
		self.pgid = str(int(setItems(self, "PGID", self.defaults, pgid)))
		self.secretsPath = str(secretsPath)
		self.authenticatedEmailsFile = str(authenticatedEmailsFile)
		self.authenticatedEmailsContainerPath = str(authenticatedEmailsContainerPath)
		self.stackTitle = formatString(self, stackTitle)
		self.vpnContainerName = formatString(self, vpnContainerName)
		self.vpnHostName = self.setVPNHostname()
		self.organizrSubdomain = formatString(self, organizrSubdomain)
		self.labels = labels
		self.customResponseHeaders = self.setCustomResponseHeader(customResponseHeaders)
		self.ip = str(IP(self.defaults, self.globalValues, self.stackDict).address)
		self.backend_subnet = str(IP(self.defaults, self.globalValues, self.stackDict).backendSubnet)
		self.globals.update(IP(self.defaults, self.globalValues, self.stackDict).networks)
		self.organizrURL = self.parseOrganizrFQDN()
		self.customResponseHeadersValue = self.parseCustomResponseHeader()
		self.customFrameOptionsValue = self.parseCustomFrameOptionsValue()
		self.traefikLabels = self.setTraefikLabels()
		self.appendLabelsForTraefik()
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
		           { "traefik.docker.network": self.frontendNetwork },
		           { "traefik.frontend.headers.SSLRedirect": bool(True) },
		           { "traefik.frontend.headers.SSLForceHost": bool(True) },
		           { "traefik.frontend.headers.browserXSSFilter": bool(True) },
		           { "traefik.frontend.headers.STSSeconds": 315360000 },
		           { "traefik.frontend.headers.contentTypeNosniff": bool(True) },
		           { "traefik.frontend.headers.forceSTSHeader": bool(True) },
		           { "traefik.frontend.headers.customResponseHeaders": self.customResponseHeadersValue },
		           { "traefik.frontend.headers.STSIncludeSubdomains": bool(True) }]
		return payload
	
	def parseCustomFrameOptionsValue(self, items = ["sameorigin"]):
		items.append(f"allow-from https://{self.organizrURL}")
		payload = ",".join(items)
		return payload
	
	def parseCustomResponseHeader(self):
		headerList = list()
		for k, v in self.customResponseHeaders.items():
			value = ','.join(v)
			headerList.append(f"{k}: {value}")
		payload = formatString(self, ",".join(headerList))
		return payload


def formatString(self, payload):
	payload = str(payload).lower()
	payload = payload.replace(" ", "-")
	payload = payload.replace("_", "-")
	return payload


def setItems(self,
             environ,
             parentDict = dict(),
             payload = list(),
             index = None):
	# CONDITIONALS
	createParentDictionary = not parentDict
	subdictionary = environ in parentDict and not index
	sublist = environ in parentDict and str(index).isdigit() and 'list' in type(parentDict[environ])
	# TODO: adjust to a master conditional map
	if createParentDictionary:
		parentDict = self.defaults
	if subdictionary:
		payload = parentDict[environ]
	elif sublist:
		payload = parentDict[environ][index]
	return payload
