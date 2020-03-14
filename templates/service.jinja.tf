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
  domain = "{{ defaults.domain|default("example.com")|string }}"
  subdomains = [
{%- if service.subdomains is defined %}{{ service.subdomains }}
    "{{ i }}",
{%- endfor %}]
{%- else %}
{%- endif %}
  sets = [
{%- for k,v in values %}
    {
      name = "{{ k }}",
      value = "{{ v }}"
    }
{%- endfor %}
  ]
}
