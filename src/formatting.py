#!/usr/bin/env python3.7
def formatString(payload):
	payload = str(payload).lower()
	payload = payload.replace(" ", "-")
	payload = payload.replace("_", "-")
	return payload
