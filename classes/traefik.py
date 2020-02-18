#!/usr/bin/env python3
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
	             customResponseHeaders = dict(),
	             traefikProtocol = "http"
	             ):
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
		self.labels = list()
		self.service = str(service)
		self.oauthService = f"{service}-proxy"
		self.backendLabel = self.service if not (self.compose.conditionals["oauth"] or self.compose.conditionals[
			"proxy_secrets"]) else f"{self.oauthService}"
		self.serviceItems = serviceItems
		self.subdomains = self.setSubdomains()
		self.ports = str(80) if not ports else ports
		self.protocol = traefikProtocol
		self.customResponseHeaders = setCustomResponseHeader(customResponseHeaders)
		self.customResponseHeadersValue = self.parseCustomResponseHeader()
		self.customFrameOptionsValue = self.parseCustomFrameOptionsValue()
		self.set()
	
	def setSubdomains(self):
		subdomains = list()
		if "subdomains" in self.serviceItems and self.serviceItems["subdomains"]:
			subdomains = [".".join([sub, self.compose.domain]) for sub in self.combineSubdomains()]
		payload = listCleanup(subdomains)
		return payload
	
	def combineSubdomains(self):
		payload = self.serviceItems["subdomains"] + [self.service]
		return payload
	
	def set(self):
		initSubdomains = listCleanup(self.subdomains)
		subdomains = str(",".join(initSubdomains))
		port = self.compose.parsePort(self.service)
		if self.compose.conditionals["oauth"] or self.compose.conditionals["proxy_secrets"]:
			port = self.compose.oauth_port
		self.labels = self.setLabels(port, subdomains)
	
	def setLabels(self, port, subdomains):
		payload = [
				f"traefik.backend={self.backendLabel}",
				f"traefik.docker.network=frontend",
				f"traefik.enable={str(bool(True)).lower()}",
				f"traefik.frontend.headers.browserXSSFilter={str(bool(True)).lower()}",
				f"traefik.frontend.headers.contentTypeNosniff={str(bool(True)).lower()}",
				f"traefik.frontend.headers.customResponseHeaders={self.customResponseHeadersValue}",
				f"traefik.frontend.headers.forceSTSHeader={str(bool(True)).lower()}",
				f"traefik.frontend.headers.frameDeny={str(bool(True)).lower()}",
				f"traefik.frontend.headers.SSLForceHost={str(bool(True)).lower()}",
				f"traefik.frontend.headers.SSLRedirect={str(bool(True)).lower()}",
				f"traefik.frontend.headers.STSIncludeSubdomains={str(bool(True)).lower()}",
				f"traefik.frontend.headers.STSPreload={str(bool(True)).lower()}",
				f"traefik.frontend.headers.STSSeconds=315360000",
				f"traefik.frontend.passHostHeader={str(bool(True)).lower()}",
				f"traefik.protocol={self.protocol}",
				f"traefik.{self.service}.frontend.headers.customFrameOptionsValue={self.customFrameOptionsValue}",
				f"traefik.{self.service}.frontend.headers.SSLHost={self.parsePrimarySubdomain()}",
				f"traefik.{self.service}.frontend.rule=Host:{subdomains}",
				f"traefik.{self.service}.port={port}",
				# f"traefik.frontend.headers.customFrameOptionsValue={self.customFrameOptionsValue}",
				# f"traefik.frontend.headers.SSLHost={self.parsePrimarySubdomain()}",
				# f"traefik.frontend.rule=Host:{subdomains}",
				# f"traefik.port={port}",
				]
		return listCleanup(payload)
	
	def parseCustomFrameOptionsValue(self):
		urls = [f"https://{url}" for url in self.subdomains]
		urls.append(f"https://{self.organizrURL}")
		allowFrom = f"'allow-from {str(','.join(listCleanup(urls)))}'"
		payload = ",".join(["SAMEORIGIN", allowFrom])
		return payload
	
	def parsePort(self, service, port = 80):
		if service == "plex":
			port = 32400
		elif self.ports:
			port = str(self.ports[0]).split(":")[1]
		if port == (443 or str(443)):
			self.protocol = "https"
		return int(port)
	
	def parseCustomResponseHeader(self):
		payload = ",".join(listCleanup([(f"{k}:{','.join(v)}") for k, v in self.customResponseHeaders.items()]))
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


def listCleanup(x):
	return list(dict.fromkeys(x))
