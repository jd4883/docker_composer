#!/bin/bash
ssh-add /home/batman/.ssh/personal_git_rsa &wait
docker config rm $({{ stack_group }} config list | grep -i {{ stack_group }} | awk '{print $1}')
{%- for pair in global_exports|sort  %}
export {{ pair }}
{%- endfor %}
source {{ globals['Paths']['Profile'] }}
rebuild-symlinks &wait
{%- if service['OAUTH_PROXY'] %}
touch ${SECRETS}/{{ service }}/OAUTH2_PROXY_CLIENT_ID.secret
touch ${SECRETS}/{{ service }}/OAUTH2_PROXY_CLIENT_SECRET.secret
touch ${SECRETS}/{{ service }}/OAUTH2_PROXY_COOKIE_SECRET.secret
{%- endif %}
chmod 600 ${SECRETS}/*/*.secret
chown -R  {{ defaults['PUID'] }}:{{ defaults['PGID'] }} ${SECRETS} ${CONFIGS}/{{ service }}/*
cd ${CONFIGS}/{{ service[0]|lower }}{{ service[1:] }}
{%- for file in global_path_cleanup|sort %}
rm -rf {{ file }}
{%- endfor %}
git add .
git commit -m "{{ service[0]|upper }}{{ service[1:] }} Current version - ${date}"
git push &wait
cd -
{%- for script in globals['Paths']['Scripts'] %}
{{ script }} &wait
{%- endfor %}
# these will get revised to match all paths from config_files and from the list
touch ${LOGS}/ ${CONFIGS}/traefik/acme.json
echo "baseline data" > ${LOGS}/traefik.log
