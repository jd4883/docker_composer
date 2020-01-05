#!/usr/bin/env python3
import os

from src.helpers import mkdir


def get_index(stack):
	stack = str(stack.replace(' ', '-')).lower()
	return stack.replace('_', '-')


def get_stack_file(stack):
	return f"{os.environ['HOST_CONFIGS']}/{str(stack.replace(' ', '_')).lower()}/docker-compose.yaml"


def set_config_directory(stack):
	stack = str(stack.replace(' ', '-')
	stack = str(stack).replace('_', "-")
	configs = f"{os.environ['CONFIG']}/{stack).lower()}"
	mkdir(configs)
	print(f"Creating stack configuration: {configs}")
	return configs
