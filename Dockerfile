FROM python:alpine3.7
MAINTAINER 'Jacob Dresdale'
LABEL name=docker_composer
USER root

VOLUME /config /configs
WORKDIR /config

COPY requirements.txt /config/
RUN pip install --upgrade pip; pip install -r requirements.txt
COPY . /config/

ENV COMPOSE_YAML /config/templates/docker-compose.jinja.yaml
ENV CONFIG /configs
ENV GLOBALS_ENV /config/templates/globals.jinja.env
ENV HOST_CONFIGS /var/data/configs
ENV HOSTFILE /config/hostfile.txt
ENV HOSTFILE_TEMPLATE /config/templates/hostfile.jinja.txt
ENV SERVERS_TOML /config/servers.toml
ENV SERVERS_TOML_TEMPLATE /config/templates/servers.jinja.toml
ENV SERVICE_ENV /config/templates/service.jinja.env
ENV SHELL_SCRIPT /config/templates/shell_script.jinja.sh
ENV STACKS_JSON /stacks.json
ENV TF_MAIN_TEMPLATE /config/templates/main.jinja.tf
ENV TF_MODULE_HELM ../terraform/kubernetes/modules/helm/
ENV TF_OUTPUT_TEMPLATE /config/templates/outputs.jinja.tf
ENV TF_PROVIDERS_TEMPLATE /config/templates/providers.jinja.tf
ENV TF_SERVICE_TEMPLATE /config/templates/service.jinja.tf
ENV TF_VARS_TEMPLATE /config/templates/variables.jinja.tf

# adjust timer to be an argument
RUN echo '*/1 *  *  *  * python /config/compose_generator.py' > /etc/crontabs/root; cat /etc/crontabs/root

RUN ["chmod", "+x", "/config/compose_generator.py", "/config/launcher.sh"]
CMD ["/usr/sbin/crond", "-f", "-d", "8"]
