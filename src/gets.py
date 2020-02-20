#!/usr/bin/env python3.7
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
	compose_file_absolute_path = f"{os.environ['HOST_CONFIGS']}/{stack}/docker-compose.yaml"
	return compose_file_absolute_path


def set_config_directory(stack):
	stack = stack.replace(' ', '-')
	stack = stack.replace('_', "-")
	stack = stack.lower()
	configs = f"{os.environ['CONFIG']}/{stack}"
	mkdir(configs)
	print(f"Creating stack configuration: {configs}")
	return configs


def getServiceHostname(k):
	payload = { "hostname": k }
	return payload
