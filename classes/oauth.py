#!/usr/bin/self python3.7
from pathlib import Path

import src.formatting
import src.gets


class OauthProxy(object):
	def __init__(self,
	             service,
	             compose,
	             external = False,
	             cookieRefreshInerval = 1,
	             cookieExpiration = 672,
	             network = 'frontend'):
		self.service = str(service)
		self.container_name = str(f"{service}-proxy")
		self.environment = dict()
		self.env = compose.environment
		# self.env_file = ["globals.env", f"{service}.env"]
		if not external:
			self.depends_on = [service]
			self.environment = compose.environment.environs
		else:
			self.depends_on = list()
			self.environment.update(compose.externalServers[self.service]["Environment"])
			path = src.gets.set_config_directory(compose.stackTitle)
			self.env.gen_app_specific_env_file(path, self.service, self.environment)
		self.dns = compose.dns
		self.dns_search = compose.traefik.subdomains
		self.image_name = "quay.io/pusher/oauth2_proxy"
		self.image_tag = "v5.0.0"
		# v5.0.0 is needed due to a cookie reading bug with pusher's OAUTH in the latest build
		#self.image_tag = "latest"
		self.image = ":".join([self.image_name, self.image_tag])
		subdomains = str(",".join(list(dict.fromkeys(compose.traefik.subdomains))))
		self.schema = "http" if (
				str(compose.parsePort(service, compose)) != str(443) or (self.service == "nextcloud")) else "https"
		self.labels = dict([
				("traefik.backend", self.container_name),
				compose.traefik.enable,
				("traefik.docker.network", network),
				("traefik.frontend.headers.customFrameOptionsValue", compose.traefik.customFrameOptionsValue),
				("traefik.frontend.headers.customResponseHeaders", compose.traefik.customResponseHeadersValue),
				compose.traefik.forceStsHeader,
				compose.traefik.frameDeny,
				compose.traefik.sslForceHost,
				compose.traefik.sslRedirect,
				compose.traefik.stsIncludeSubdomains,
				compose.traefik.stsPreload,
				compose.traefik.stsSeconds,
				compose.traefik.passHostHeader,
				("traefik.frontend.headers.SSLHost", compose.traefik.parsePrimarySubdomain()),
				("traefik.frontend.rule", f"Host:{subdomains}"),
				("traefik.port", compose.traefik.oauthPort),
				("traefik.protocol", self.schema),
				])
		self.networks = list(dict.fromkeys([
				"frontend",
				"backend",
				]))
		self.secrets = list(dict.fromkeys([
				str(f"{self.service}_proxy_client_id").replace("-", "_"),
				str(f"{self.service}_proxy_client_secret").replace("-", "_"),
				str(f"{self.service}_proxy_cookie_secret").replace("-", "_"),
				]))
		self.cookieSecretEnviron = self.environment["OAUTH2_PROXY_COOKIE_SECRET"]
		self.clientIdEnviron = self.environment["OAUTH2_PROXY_CLIENT_ID"]
		self.clientSecretEnviron = self.environment["OAUTH2_PROXY_CLIENT_SECRET"]
		self.client_id = { "file": f"${{SECRETS}}/{self.service}/OAUTH2_PROXY_CLIENT_ID.secret" }
		self.client_secret = { "file": f"${{SECRETS}}/{self.service}/OAUTH2_PROXY_CLIENT_SECRET.secret" }
		self.cookie_secret = { "file": f"${{SECRETS}}/{self.service}/OAUTH2_PROXY_COOKIE_SECRET.secret" }
		
		self.clientSecretBody = f"/secrets/{self.service}/OAUTH2_PROXY_CLIENT_SECRET.secret"
		self.clientIdFile = f"/secrets/{self.service}/OAUTH2_PROXY_CLIENT_ID.secret"
		self.cookieSecretFile = f"/secrets/{self.service}/OAUTH2_PROXY_COOKIE_SECRET.secret"
		for secret in self.secrets:
			secret = str(secret).replace("-", "_")
			Path(f"/secrets/{self.service}").mkdir(parents = True, exist_ok = True)
			open(self.clientIdFile, "w+").write(self.clientIdEnviron)
			open(self.clientSecretBody, "w+").write(self.clientSecretEnviron)
			open(self.cookieSecretFile, "w+").write(self.cookieSecretEnviron)
			compose.secrets.update({ secret: self.client_id })
			compose.secrets.update({ secret: self.client_secret })
			compose.secrets.update({ secret: self.cookie_secret })
		self.authenticatedEmails = f"{compose.authenticatedEmailsFile}:/authenticated-emails.txt"
		self.upstream = self.parseUpstream(compose)
		self.provider = "github"
		open("/authenticated-emails.txt", "w+").write('\n'.join(compose.defaults['Authenticated Emails File']))
		
		self.commands = list(dict.fromkeys([
				f"--authenticated-emails-file=/authenticated-emails.txt",
				f"--client-id={self.clientIdEnviron}",
				f"--client-secret-file=/run/secrets/{self.secrets[1]}",
				# f"--cookie-domain={compose.domain}",
				f"--cookie-expire={cookieExpiration}h",
				f"--cookie-httponly=false",
				f"--cookie-refresh={cookieRefreshInerval}h",
				f"--http-address=http://0.0.0.0:{compose.traefik.oauthPort}",
				f"--provider={self.provider}",
				f"--redirect-url=https://{compose.traefik.parsePrimarySubdomain()}",
				f"--request-logging=false",
				f"--ssl-upstream-insecure-skip-verify=true",
				f"--upstream={self.upstream}",
				]))
		
		self.containerVolumes = list(dict.fromkeys([self.authenticatedEmails]))
		self.obj = {
				str(self.container_name): {
						"image":                self.image,
						"secrets":              self.secrets,
						str(self.env.fileName): self.env.files,
						"networks":             self.networks,
						"labels":               self.labels,
						"volumes":              self.containerVolumes,
						"command":              self.commands,
						"restart":              "on-failure",
						}
				} if not (compose.conditionals["vpn"] and compose.conditionals["ports"]) \
			else {
				str(self.container_name): {
						"image":                self.image,
						"secrets":              self.secrets,
						str(self.env.fileName): self.env.files,
						"network_mode":         f"service:{compose.vpnContainerName}",
						"labels":               self.labels,
						"volumes":              self.containerVolumes,
						"command":              self.commands,
						"restart":              "on-failure",
						}
				}
	
	def parseUpstream(self, compose):
		if compose.conditionals["vpn"] and compose.conditionals["ports"]:
			payload = f"{self.schema}://{'-'.join([compose.stackTitle.lower(), 'pia-openvpn'])}:" \
			          f"{compose.parsePort(self.service, compose)}"
		elif compose.conditionals["ports"]:
			payload = f"{self.schema}://{self.service}:{compose.parsePort(self.service, compose)}"
		else:
			payload = f"{self.schema}://{self.service}:80"
		return payload
