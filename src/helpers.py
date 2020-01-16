#!/usr/bin/env python3
import os
from pathlib import Path
import jinja2


def load_template(environ):
	template = Path(str(os.environ[environ]))
	return jinja2.Template(open(template).read())


def mkdir(service_configs):
	try:
		os.makedirs(service_configs)
	except FileExistsError:
		# directory already exists
		pass
