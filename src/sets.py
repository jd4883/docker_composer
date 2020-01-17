#!/usr/bin/env python3
def set_environment(app):
	in_app = 'Environment' in app and app['Environment']
	return app['Environment'] if in_app else str()


def set_services(config, stack):
	return config['Stack Group Name'][stack]['Services']
