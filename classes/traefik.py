#!/usr/bin/env python3.7
from random import randrange as rand

from src.formatting import formatString
from src.sets import setItems


class Traefik(object):
	def __init__(self,
	             compose,
	             ports,
	             globalValues = dict(),
	             service = str(),  # k
	             serviceItems = dict(),  # v
	             frontendNetwork = "frontend",
	             backendNetwork = "backend",
	             organizrSubdomain = "home",
	             customResponseHeaders = dict()
	             ):
		self.oauthPort = self.generateRandomUniquePort(compose)
		self.passHostHeader = ("traefik.frontend.passHostHeader", True)
		self.stsSeconds = ("traefik.frontend.headers.STSSeconds", 315360000)
		self.stsPreload = ("traefik.frontend.headers.STSPreload", True)
		self.stsIncludeSubdomains = ("traefik.frontend.headers.STSIncludeSubdomains", True)
		self.sslRedirect = ("traefik.frontend.headers.SSLRedirect", True)
		self.trustForwardHeader = ("traefik.frontend.auth.forward.trustForwardHeader", True)
		self.sslForceHost = ("traefik.frontend.headers.SSLForceHost", True)
		self.frameDeny = ("traefik.frontend.headers.frameDeny", bool())
		self.forceStsHeader = ("traefik.frontend.headers.forceSTSHeader", True)
		self.enable = ("traefik.enable", True)
		self.compose = compose
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
		self.organizrURL = f"{organizrSubdomain}.{compose.domain}"
		self.labels = dict()
		self.service = str(service)
		self.oauthService = f"{service}-proxy"
		self.backendLabel = self.service if not (self.compose.conditionals["oauth"] or self.compose.conditionals[
			"proxy_secrets"]) else f"{self.oauthService}"
		self.serviceItems = serviceItems
		self.subdomains = self.setSubdomains()
		self.ports = str(80) if not ports else ports
		self.protocol = "http" if (str(self.ports) != str(443)) or (self.service != "nextcloud") else "https"
		self.customResponseHeaders = setCustomResponseHeader(customResponseHeaders)
		self.customResponseHeadersValue = self.parseCustomResponseHeader()
		self.customFrameOptionsValue = self.parseCustomFrameOptionsValue()
		self.backend = ("traefik.backend", self.backendLabel)
		self.network = ("traefik.docker.network", "frontend")
		self.set(compose)
	
	def generateRandomUniquePort(self, compose):
		while True:
			payload = rand(23700, 23900)
			if payload not in compose.activePorts:
				payload = rand(23700, 23900)
				compose.activePorts = list(dict.fromkeys(compose.activePorts + [int(payload)]))
				break
		return payload
	
	def setSubdomains(self):
		subdomains = list()
		if "subdomains" in self.serviceItems and self.serviceItems["subdomains"]:
			subdomains = [".".join([sub, self.compose.domain]) for sub in self.combineSubdomains()]
		payload = list(dict.fromkeys(subdomains))
		return payload
	
	def combineSubdomains(self):
		payload = self.serviceItems["subdomains"] + [self.service]
		return payload
	
	def set(self, compose):
		subdomains = str(",".join(list(dict.fromkeys(self.subdomains))))
		port = self.compose.parsePort(self.service, compose)
		if self.compose.conditionals["oauth"] or self.compose.conditionals["proxy_secrets"]:
			port = self.oauthPort
		self.labels = dict([self.backend,
		                    self.network,
		                    self.enable,
		                    ("traefik.frontend.headers.customFrameOptionsValue", self.customFrameOptionsValue),
		                    ("traefik.frontend.headers.customResponseHeaders", self.customResponseHeadersValue),
		                    self.forceStsHeader,
		                    self.frameDeny,
		                    self.sslForceHost,
		                    ("traefik.frontend.headers.SSLHost", self.parsePrimarySubdomain()),
		                    self.sslRedirect,
		                    self.stsIncludeSubdomains,
		                    self.stsPreload,
		                    self.stsSeconds,
		                    self.passHostHeader,
		                    ("traefik.frontend.rule", f"Host:{subdomains}"),
		                    ("traefik.port", port),
		                    ("traefik.protocol", self.protocol)])
		# bandage fix should be a better way
		if self.service == "nextcloud":
			self.labels["traefik.protocol"] = "https"
			self.labels["traefik.frontend.redirect.regex"] = "https://(.*)/.well-known/(card|cal)dav"
			self.labels["traefik.frontend.redirect.replacement"] = "https://$$1/remote.php/dav/"
		if self.service == "traefik":
			# need to adjust to do the following:
			# htpasswd -Bbn ${USERNAME} ${PASSWORD} | sed -e 's/\$/\$\$/g'
			# suspect a popen calling a bash script that feeds in username and passwords the way to go
			# may need to add dependencies
			self.labels["traefik.frontend.auth.basic.users"] = "${USERNAME}:${PASSWORD}"
	
	def parseCustomFrameOptionsValue(self):
		urls = ["SAMEORIGIN", f"https://{self.organizrURL}"]
		payload = f"allow-from {str(','.join(list(dict.fromkeys(urls))))}"
		return payload
	
	def parsePort(self, service, compose, port = 80):
		if service == "plex":
			port = 32400
		elif self.ports:
			port = str(self.ports[0]).split(":")[1]
		compose.activePorts = list(dict.fromkeys(compose.activePorts + [port]))
		return int(port)
	
	def parseCustomResponseHeader(self):
		payload = ",".join(list(dict.fromkeys([f"{k}:{','.join(v)}" for k, v in self.customResponseHeaders.items()])))
		return payload
	
	def parsePrimarySubdomain(self):
		try:
			payload = self.subdomains[0]
		except IndexError:
			payload = ".".join([str(self.service), str(self.compose.domain)])
		return payload


def setCustomResponseHeader(customResponseHeaders):
	payload = {
			"X-Robots-Tag": ["noindex", "nofollow", "nosnippet", "noarchive", "notranslate", "noimageindex", "none"]
			}
	
	customResponseHeaders.update(payload)
	return customResponseHeaders
