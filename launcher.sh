#!/bin/bash
docker volume prune -f
rebuild-symlinks
docker image prune -f
python3.7 /var/lib/docker/config/docker_composer/compose_generator.py
rebuild-docker-stacks
rebuild-symlinks
docker volume list
