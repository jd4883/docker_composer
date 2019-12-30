#!/usr/bin/env python3
import os

from src.helpers import mkdir


def get_index(stack):
	return str(stack.replace(" ", "_")).lower()


def get_stack_file(stack):
	return f"{os.environ['CONFIG']}/{str(stack.replace(' ', '_')).lower()}/docker-compose.yaml"


def set_config_directory(stack):
	configs = f"{os.environ['CONFIG']}/{str(stack.replace(' ', '_')).lower()}"
	mkdir(configs)
	print(f"Creating stack configuration: {configs}")
	return configs
