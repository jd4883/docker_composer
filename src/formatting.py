#!/usr/bin/env python3
def formatString(self, payload):
	payload = str(payload).lower()
	payload = payload.replace(" ", "-")
	payload = payload.replace("_", "-")
	return payload
