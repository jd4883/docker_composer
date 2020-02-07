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


def parseImage(v):
	tag = "latest"
	if "tags" in v:
		tag = str(v["tags"])
	image = { "image": f"{v['Image']}:{tag}" }
	return image


def getServiceHostname(k):
	payload = { "hostname": k }
	return payload


def setCustomResponseHeader(customResponseHeaders):
	payload = {
			"X-Robots-Tag": ["noindex",
			                 "nofollow",
			                 "nosnippet",
			                 "noarchive",
			                 "notranslate",
			                 "noimageindex",
			                 "none"]
			}
	customResponseHeaders.update(payload)
	return customResponseHeaders


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
		self.defaults = defaults
		self.externalServers = externalServers
		self.globalValues = globalValues
		self.secretsPath = str(secretsPath)
		self.secrets = setItems(self, "Secrets", self.stackDict, dict())
		self.oauth_enabled = bool()
		self.proxy_secrets_enabled = bool()
		self.services = dict()
		self.generateDefaultSecrets()
		self.globals = {
				"version":  f'"{version}"',
				"networks": IP(self.defaults, self.globalValues, self.stackDict).networks,
				"secrets":  self.secrets,
				"volumes":  setItems(self, "Volumes", self.stackDict)
				}
		self.globals.update(IP(self.defaults, self.globalValues, self.stackDict).networks)
		
		self.domain = str(setItems(self, "Domain",
		                           self.defaults,
		                           domain))
		self.email = str(setItems(self, "Email",
		                          self.defaults,
		                          emailAddress))
		self.ip = str(IP(self.defaults, self.globalValues, self.stackDict).address)
		i = int()
		for k, v in setItems(self, "Services", self.stackDict, dict()).items():
			i += 1
			self.fourthOctet = 255 - i
			## INIT SERVICE DICT
			k = formatString(self, k)
			self.local_secrets = list(self.secrets.keys())
			self.oauth = bool()
			self.local_volumes = list()
			self.services.update({ k: dict() })
			self.services.update({ k: { "volumes": list() } })
			self.stackTitle = formatString(self, stackTitle)
			self.vpnContainerName = formatString(self, vpnContainerName)
			self.vpnHostName = self.setVPNHostname()
			## END SERVICE INIT
			
			## APPEND SERVICE OAUTH LABEL
			self.oauth = self.setOauthProxyFlags(k, v)
			self.services[k].update(self.setOauthLabel(k))
			## INIT SERVICE CONTAINER NAME
			self.services[k].update({ "container_name": k })
			print(f"CONTAINER NAME: {self.services[k]['container_name']}")
			## SERVICE IMAGE AND TAG
			self.services[k].update(parseImage(v))
			print(f"IMAGE: {self.services[k]['image']}")
			## SETS SERVICE LOCAL SECRETS
			self.services[k].update(self.parseLocalSecrets(v))
			v["secrets"] = self.services[k]['secrets']
			print(f"SECRETS: {self.services[k]['secrets']}")
			## SET EXTERNAL ENVIRON REFERENCES
			self.env_file = { "env_file": ["globals.env", f"{k}.env"] }
			self.services[k].update(self.env_file)
			print(f"ENV FILE: {self.services[k]['env_file']}")
			## SET SERVICE VOLUMES
			if "Volumes" in v.keys():
				self.services[k].update({ "volumes": list(v["Volumes"]) })
			print(f"VOLUMES: {self.services[k]['volumes']}")
			
			# update logic to cut the frontend when not needed
			if (("networks" in k) and ("vpn" in k["networks"]) and (k["networks"]["vpn"])):
				## SETS NETWORK MODE TO THE VPN CONTAINER
				self.services.update({ "network_mode": str(vpnContainerName) })
				print(f"NETWORK MODE SET FOR VPN CONTAINER: {self.services[k]['network_mode']}")
			else:
				## SETS LOCAL HOSTNAME
				self.services[k].update(getServiceHostname(k))
				print(f"HOSTNAME: {self.services[k]['hostname']}")
				## SETS LOCAL NETWORKS
				self.networks = {
						"networks": { "backend": { "ipv4_address": f"{self.ip}.{self.fourthOctet}" }, "frontend": { } }
						}
				self.services[k].update(self.networks)
				print(f"ENV FILE: {self.services[k]['networks']}")
		
		# plan is to use labels as a reference point instead of recalculating
		# oauth.frontend will be for the oauth container which will be a class object
		
		self.globals.update({ "services": self.services })
		
		self.traefikLabels = Traefik(self.globalValues, self.domain, self.email)
		
		# traefik
		self.traefikProtocol = traefikProtocol
		self.oauth_port = oauth_port
		self.authenticatedEmailsFile = str(authenticatedEmailsFile)
		self.stackTitle = formatString(self, stackTitle)
		
		self.organizrSubdomain = formatString(self, organizrSubdomain)
		self.labels = labels
		self.customResponseHeaders = setCustomResponseHeader(customResponseHeaders)
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
		# conditionals - move to a separate class down the line
		self.conditionals = list()
	
	def generateDefaultSecrets(self):
		parsedPath = f"{self.secretsPath}/{'PUID'.upper()}.secret"
		self.secrets.update({ 'puid': { "file": parsedPath } })
		parsedPath = f"{self.secretsPath}/{'PGID'.upper()}.secret"
		self.secrets.update({ 'pgid': { "file": parsedPath } })
	
	def setOauthLabel(self, k):
		return { "labels": list().append(f"{k}.oauth.backend={self.oauth}") }
	
	def parseLocalSecrets(self, v):
		if "secrets" in v:
			for secret in v["secrets"]:
				self.local_secrets.append(secret)
		# add conditional change to not be in place if network mode is toggled
		secrets_ = { "secrets": self.local_secrets }
		return secrets_
	
	def setOauthProxyFlags(self, name, service):
		oauth_enabled = "OAUTH_PROXY" in service and service["OAUTH_PROXY"]
		proxy_secrets_enabled = "proxy_secrets" in service and service["proxy_secrets"]
		if oauth_enabled or proxy_secrets_enabled:
			base = f"{self.secretsPath}/{name}/OAUTH2_PROXY_"
			# adds to global secrets
			self.secrets.update({ f"{name}_proxy_client_id": { "file": f"{base}CLIENT_ID.secret" } })
			self.secrets.update({ f"{name}_proxy_client_secret": { "file": f"{base}CLIENT_SECRET.secret" } })
			self.secrets.update({ f"{name}_proxy_cookie_secret": { "file": f"{base}COOKIE_SECRET.secret" } })
			# secrets per service
			self.local_secrets.append(f"{name}_proxy_client_id")
			self.local_secrets.append(f"{name}_proxy_client_secret")
			self.local_secrets.append(f"{name}_proxy_cookie_secret")
			return bool(True)
		return bool()
	
	def setVPNHostname(self):
		payload = "-".join([self.stackTitle, self.vpnContainerName])
		return payload
	
	def parseOrganizrFQDN(self):
		domainComponentList = [self.organizrSubdomain, self.domain]
		payload = formatString(self, ".".join(domainComponentList))
		formatString(self, payload)
		return payload
	
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
