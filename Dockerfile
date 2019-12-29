FROM python:alpine3.7
MAINTAINER 'Jacob Dresdale'
LABEL name=docker_composer
USER root

VOLUME /config /configs
WORKDIR /config

COPY requirements.txt /config/
RUN pip install --upgrade pip; pip install -r requirements.txt
COPY . /config/

ENV HOSTFILE /configs/hostfile.txt
ENV CONFIG /configs
ENV HOSTFILE_TEMPLATE /config/templates/hostfile.jinja.txt
ENV HOSTFILE /config/hostfile.txt
ENV SHELL_SCRIPT /config/templates/shell_script.jinja.sh
ENV GLOBALS_ENV /config/templates/globals.jinja.env
ENV SERVICE_ENV /config/templates/service.jinja.env
ENV COMPOSE_YAML /config/templates/docker-compose.jinja.yaml
ENV STACKS_JSON /stacks.json

RUN echo '*/1 *  *  *  * python /config/compose_generator.py' > /etc/crontabs/root; cat /etc/crontabs/root

RUN ["chmod", "+x", "/config/compose_generator.py", "/config/launcher.sh"]
CMD ["/usr/sbin/crond", "-f", "-d", "8"]
