#!/usr/bin/env python3
def set_environment(app):
	in_app = 'Environment' in app and app['Environment']
	return app['Environment'] if in_app else str()


def set_services(config, stack):
	return config['Stack Group Name'][stack]['Services']


def setItems(self,
             environ,
             parentDict = dict(),
             payload = list(),
             index = None):
	# CONDITIONALS
	createParentDictionary = not parentDict
	subdictionary = environ in parentDict and not index
	sublist = environ in parentDict and str(index).isdigit() and 'list' in type(parentDict[environ])
	# TODO: adjust to a master conditional map
	if createParentDictionary:
		parentDict = self.defaults
	if subdictionary:
		payload = parentDict[environ]
	elif sublist:
		payload = parentDict[environ][index]
	return payload
