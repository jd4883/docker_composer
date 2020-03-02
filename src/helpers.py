#!/usr/bin/env python3.7
import os
from pathlib import Path
import jinja2


def load_template(environ):
	template = Path(str(os.environ[environ]))
	jinja2_template = jinja2.Template(open(template).read())
	return jinja2_template


def mkdir(service_configs):
	try:
		os.makedirs(service_configs)
	except FileExistsError:
		# directory already exists
		pass
