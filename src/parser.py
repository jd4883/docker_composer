#!/usr/bin/env python3.7
def parse_hostfile(app, hostfile, hosts, defaults):
	subdomains = 'subdomains' in app and app['subdomains']
	if subdomains:
		for sub in app['subdomains']:
			hostfile.append(sub)
			fqdn = f"{sub}.{defaults['Domain']}"
			hosts.append(fqdn)


def parseImage(v):
	tag = "latest"
	if "tags" in v:
		tag = str(v["tags"])
	payload = { "image": f"{v['Image']}:{tag}" }
	return payload
