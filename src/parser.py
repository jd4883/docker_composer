#!/usr/bin/env python3
def parse_hostfile(app, hostfile, hosts, defaults):
	if 'subdomains' in app and app['subdomains']:
		for sub in app['subdomains']:
			hostfile.append(sub)
			hosts.append(f"{sub}.{defaults['Domain']}")