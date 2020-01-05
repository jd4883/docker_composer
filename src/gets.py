#!/usr/bin/env python3
import os

from src.helpers import mkdir


def get_index(stack):
	stack = stack.replace(' ', '-')
	stack = stack.replace('_', "-")
	stack = stack.lower()
	return stack


def get_stack_file(stack):
	stack = stack.replace(' ', '-')
	stack = stack.replace('_', "-")
	stack = stack.lower()
	return f"{os.environ['HOST_CONFIGS']}/{stack}/docker-compose.yaml"


def set_config_directory(stack):
	stack = stack.replace(' ', '-')
	stack = stack.replace('_', "-")
	stack = stack.lower()
	configs = f"{os.environ['CONFIG']}/{stack}"
	mkdir(configs)
	print(f"Creating stack configuration: {configs}")
	return configs
