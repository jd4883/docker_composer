#!/usr/bin/env python3
def set_environment(app):
	return app['Environment'] if 'Environment' in app else str()


def set_services(config, stack):
	return config['Stack Group Name'][stack]['Services']
