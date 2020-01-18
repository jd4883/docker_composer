class ComposeFile(object):
	def __init__(self,
	             domain = "example.com",
	             vpnContainerName = "vpn",
	             stackTitle = str(),
	             secrets = list(),
	             volumes = list(),
	             services = list(),
	             ports = list(),
	             labels = list(),
	             customResponseHeaders = dict(),
	             octet1 = str(172),
	             octet2 = str(20),
	             octet3 = str(30),
	             subnetMask = str(24),
	             frontendNetwork = "frontend",
	             backendNetwork = "backend",
	             sharedBackendNetwork = "shared-backend",
	             traefikProtocol = "http",
	             organizrSubdomain = "home",
	             oauth_port = str(4180),
	             puid = str(1001),
	             pgid = str(1001)):
		self.octet1 = octet1
		self.octet2 = octet2
		self.octet3 = octet3
		# 4th octet is dynamically calculated for each app
		self.subnet_mask = subnetMask
		self.frontendNetwork = frontendNetwork
		self.backendNetwork = backendNetwork
		self.sharedBackend = sharedBackendNetwork
		self.traefikProtocol = traefikProtocol
		self.oauth_port = oauth_port
		self.puid = puid
		self.pgid = pgid
		self.secrets = secrets
		self.volumes = volumes
		self.services = services
		self.ports = ports
		self.domain = domain
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
	
	def parseBackendSubnet(self, networkIP = ".0"):
		networkIP = networkIP
		subnetMaskComponents = [self.formatString(self.ip) + networkIP, self.formatString(self.subnet_mask)]
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
