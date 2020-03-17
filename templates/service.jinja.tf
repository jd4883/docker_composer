module {{ "consul" + " {" }}
  source = "{{ helm_module|string }}"
  providers = {
{%- for provider in service.kubernetes.providers %}
{{ provider|indent(4, true) + " = " + provider + "." + provider }}
{%- endfor %}
  }
  helm_chart = "{{ service.kubernetes.helm_chart }}"
  name = "{{ service.kubernetes.name }}"
  namespace = "{{ service.kubernetes.namespace }}"
  spec = {
    max_replicas = {{ service.kubernetes.spec.max_replicas|default(defaults.kubernetes.spec.max_replicas) }}
    min_replicas = {{ service.kubernetes.spec.min_replicas|default(defaults.kubernetes.spec.min_replicas) }}
    cpu_usage = {{ service.kubernetes.spec.cpu_usage|default(defaults.kubernetes.spec.cpu_usage) }}
    api_version = "{{ service.kubernetes.spec.api_version|default(defaults.kubernetes.spec.api_version)|string }}"
    kind = "{{ service.kubernetes.spec.kind|default(defaults.kubernetes.spec.kind)|string }}"
  }
  domain = "{{ defaults.Domain|default("example.com")|string }}"
  helm_value = {{ '["${file("' + service.kubernetes.name  + '.yaml")}"]' }}
  ports = {
   name = {{ port_name }}
   host_port = {{ host_port }}
   container_port = {{ container_port }}
  }

  subdomains = [{% if service.subdomains is defined %}{% for i in service.subdomains %}
    "{{ i }}",
{%- endfor %}
{%- endif %}
  ]
}
