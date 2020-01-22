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
	             octet1 = str(10),
	             octet2 = str(23),
	             subnetMask = str(24),
	             frontendNetwork = "frontend",
	             backendNetwork = "backend",
	             sharedBackendNetwork = "shared-backend",
	             authenticatedEmailsContainerPath = "/config/authenticated-emails.txt",
	             traefikProtocol = "http",
	             organizrSubdomain = "home",
	             secretsPath = "${SECRETS}",
	             oauth_port = str(4180),
	             puid = str(1001),
	             pgid = str(1001)):
		self.stackDict = stackDict
		self.defaults = defaults
		self.externalServers = externalServers
		self.globalValues = globalValues
		self.subnetMask = str(int(self.setItems("subnetMask",
		                                        self.globalValues,
		                                        subnetMask)))
		self.secrets = self.setItems("Secrets",
		                             self.stackDict)
		self.volumes = self.setItems("Volumes",
		                             self.stackDict)
		self.services = self.setItems("Services",
		                              self.stackDict)
		self.domain = str(self.setItems("Domain",
		                                self.defaults,
		                                domain))
		self.email = str(self.setItems("Email",
		                               self.defaults,
		                               emailAddress))
		self.octet1 = str(int(self.setItems("octet1",
		                                    self.defaults,
		                                    octet1)))
		self.octet2 = str(int(self.setItems("octet2",
		                                    self.defaults,
		                                    octet2)))
		self.octet3 = str(int(self.setItems("octets",
		                                    self.stackDict)[0]))
		# 4th octet is dynamically calculated for each app
		self.frontendNetwork = self.formatString(self.setItems("Networks",
		                                                       self.globalValues,
		                                                       frontendNetwork,
		                                                       0))
		self.backendNetwork = self.formatString(self.setItems("Networks",
		                                                      self.globalValues,
		                                                      backendNetwork,
		                                                      1))
		self.sharedBackend = self.formatString(self.setItems("Networks",
		                                                     self.globalValues,
		                                                     sharedBackendNetwork,
		                                                     2))
		self.traefikProtocol = traefikProtocol
		self.oauth_port = oauth_port
		self.puid = str(int(self.setItems("PUID", self.defaults, puid)))
		self.pgid = str(int(self.setItems("PGID", self.defaults, pgid)))
		self.secretsPath = str(secretsPath)
		self.authenticatedEmailsFile = str(authenticatedEmailsFile)
		self.authenticatedEmailsContainerPath = str(authenticatedEmailsContainerPath)
		self.stackTitle = self.formatString(stackTitle)
		self.vpnContainerName = self.formatString(vpnContainerName)
		self.vpnHostName = self.setVPNHostname()
		self.organizrSubdomain = self.formatString(organizrSubdomain)
		self.labels = labels
		self.customResponseHeaders = self.setCustomResponseHeader(customResponseHeaders)
		self.ip = self.parseIP()
		self.backend_subnet = self.parseBackendSubnet()
		self.organizrURL = self.parseOrganizrFQDN()
		self.customResponseHeadersValue = self.parseCustomResponseHeader()
		self.customFrameOptionsValue = self.parseCustomFrameOptionsValue()
		self.traefikLabels = self.setTraefikLabels()
		self.appendLabelsForTraefik()
		# conditionals - move to a separate class down the line
		self.conditionals = list()
	
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
	
	def setVPNHostname(self):
		return "-".join([self.stackTitle, self.vpnContainerName])
	
	def parseIP(self):
		octetsList = [
				str(self.octet1),
				str(self.octet2),
				str(self.octet3)
				]
		payload = self.formatString(".".join(octetsList))
		return payload
	
	def parseOrganizrFQDN(self):
		domainComponentList = [self.organizrSubdomain, self.domain]
		payload = self.formatString(".".join(domainComponentList))
		self.formatString(payload)
		return payload
	
	def formatString(self, payload):
		payload = str(payload).lower()
		payload = payload.replace(" ", "-")
		payload = payload.replace("_", "-")
		return payload
	
	def parseBackendSubnet(self, networkIP = 0):
		networkIP = networkIP
		subnetMaskComponents = [(str(self.ip) + "." + str(networkIP)), str(self.subnetMask)]
		payload = self.formatString("/".join(subnetMaskComponents))
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
		payload = self.formatString(",".join(headerList))
		return payload
