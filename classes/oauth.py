#!/usr/bin/env python3.7
import src.formatting
import src.gets
from pathlib import Path


class OauthProxy(object):
	def __init__(self,
	             service,
	             compose,
	             external = False,
	             emailDomain = 'gmail', cookieRefreshInerval = 1, cookieExpiration = 672):
		self.service = str(service)
		self.container_name = str(f"{service}-proxy")
		self.environment = dict()
		if not external:
			self.depends_on = [service]
			self.env_file = compose.envFile["env_file"]
			self.environment = compose.environment
		else:
			self.depends_on = list()
			self.env_file = ["globals.env", f"{self.service}.env"]
			self.environment.update(compose.externalServers[self.service]["Environment"])
			path = src.gets.set_config_directory(compose.stackTitle)
			src.generators.gen_app_specific_env_file(path, self.service, self.environment)
		self.schema = "http" if (
				str(compose.parsePort(service)) != str(443) or (self.service == "nextcloud")) else "https"
		self.upstream = self.parseUpstream(compose)
		self.provider = "github"
		self.commands = listCleanup([
				f"--authenticated-emails-file={compose.authenticatedEmailsContainerPath}",
				f"--cookie-domain={compose.domain}",
				f"--cookie-expire={cookieExpiration}h",
				f"--cookie-httponly=true",
				f"--cookie-refresh={cookieRefreshInerval}h",
				f"--cookie-secure=true",
				f"--email-domain={emailDomain}",
				f"--http-address=http://0.0.0.0:{compose.oauth_port}",
				f"--provider={self.provider}",
				f"--redirect-url=https://{compose.traefikLabels.parsePrimarySubdomain()}",
				f"--request-logging=false",
				f"--upstream={self.upstream}",
				])
		self.dns = compose.dns
		self.dns_search = compose.traefikLabels.subdomains
		self.image_name = "quay.io/pusher/oauth2_proxy"
		self.image_tag = "latest"
		self.image = ":".join([self.image_name, self.image_tag])
		initSubdomains = listCleanup(compose.traefikLabels.subdomains)
		subdomains = str(",".join(initSubdomains))
		self.labels = listCleanup([
				f"traefik.enable=true",
				f"traefik.backend={self.container_name}",
				f"traefik.frontend.rule=Host:{subdomains}",
				f"traefik.docker.network={'frontend'}",
				f"traefik.port={4180}",
				f"traefik.frontend.headers.browserXSSFilter={str(bool(True)).lower()}",
				f"traefik.frontend.headers.contentTypeNosniff={str(bool(True)).lower()}",
				f"traefik.frontend.headers.customResponseHeaders={compose.traefikLabels.customResponseHeadersValue}",
				f"traefik.frontend.headers.forceSTSHeader={str(bool(True)).lower()}",
				f"traefik.frontend.headers.frameDeny={str(bool(True)).lower()}",
				f"traefik.frontend.headers.SSLForceHost={str(bool(True)).lower()}",
				f"traefik.frontend.headers.SSLRedirect={str(bool(True)).lower()}",
				f"traefik.frontend.headers.STSIncludeSubdomains={str(bool(True)).lower()}",
				f"traefik.frontend.headers.STSPreload={str(bool(True)).lower()}",
				f"traefik.frontend.headers.STSSeconds=315360000",
				f"traefik.frontend.passHostHeader={str(bool(True)).lower()}",
				f"traefik.protocol={self.schema}",
				f"traefik.frontend.headers.customFrameOptionsValue={compose.traefikLabels.customFrameOptionsValue}",
				f"traefik.frontend.headers.SSLHost={compose.traefikLabels.parsePrimarySubdomain()}",
				f"traefik.frontend.rule=Host:{subdomains}",
				])
		self.networks = listCleanup([
				"frontend",
				"backend",
				])
		self.secrets = listCleanup([
				str(f"{self.service}_proxy_client_id").replace("-", "_"),
				str(f"{self.service}_proxy_client_secret").replace("-", "_"),
				str(f"{self.service}_proxy_cookie_secret").replace("-", "_"),
				])
		self.client_id = { "file":  f"${{SECRETS}}/{self.service}/OAUTH2_PROXY_CLIENT_ID.secret" }
		self.client_id_body = f"/secrets/{self.service}/OAUTH2_PROXY_CLIENT_ID.secret"
		self.client_secret = { "file": f"${{SECRETS}}/{self.service}/OAUTH2_PROXY_CLIENT_SECRET.secret" }
		self.client_secret_body = f"/secrets/{self.service}/OAUTH2_PROXY_CLIENT_SECRET.secret"
		self.cookie_secret = { "file":  f"${{SECRETS}}/{self.service}/OAUTH2_PROXY_COOKIE_SECRET.secret" }
		self.cookie_secret_body = f"/secrets/{self.service}/OAUTH2_PROXY_COOKIE_SECRET.secret"
		self.authenticatedEmails = f"{compose.authenticatedEmailsFile}:{compose.authenticatedEmailsContainerPath}"
		for secret in self.secrets:
			secret = str(secret).replace("-", "_")
			Path(f"/secrets/{self.service}").mkdir(parents = True, exist_ok = True)
			open(self.client_id_body, "w+").write(self.environment["OAUTH2_PROXY_CLIENT_ID"])
			open(self.client_secret_body, "w+").write(self.environment["OAUTH2_PROXY_CLIENT_SECRET"])
			open(self.cookie_secret_body, "w+").write(self.environment["OAUTH2_PROXY_COOKIE_SECRET"])
			compose.secrets.update({ secret: self.client_id })
			compose.secrets.update({ secret: self.client_secret })
			compose.secrets.update({ secret: self.cookie_secret })
		self.containerVolumes = listCleanup([self.authenticatedEmails])
		self.obj = {
				str(self.container_name): {
						"image":          self.image,
						"secrets":        self.secrets,
						"container_name": self.container_name,
						"hostname":       self.container_name,
						"env_file":       compose.envFile["env_file"],
						"networks":       self.networks,
						"labels":         self.labels,
						"volumes":        self.containerVolumes,
						"command":        self.commands
						}
				}
	
	def parseUpstream(self, compose):
		if compose.conditionals["vpn"] and compose.conditionals["ports"]:
			payload = f"{self.schema}://{'-'.join([compose.stackTitle.lower(), 'pia-openvpn'])}:" \
			          f"{compose.parsePort(self.service)}"
		elif compose.conditionals["ports"]:
			payload = f"{self.schema}://{self.service}:{compose.parsePort(self.service)}"
		else:
			payload = f"{self.schema}://{self.service}:80"
		return payload


def listCleanup(x):
	return list(dict.fromkeys(x))
