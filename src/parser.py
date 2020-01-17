#!/usr/bin/env python3
def parse_hostfile(app, hostfile, hosts, defaults):
	subdomains = 'subdomains' in app and app['subdomains']
	if subdomains:
		for sub in app['subdomains']:
			hostfile.append(sub)
			fqdn = f"{sub}.{defaults['Domain']}"
			hosts.append(fqdn)
