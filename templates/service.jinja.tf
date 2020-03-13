module {{ svc + " {" }}
  source = {{ helm_module|string }}
  providers = {
{%- for provider in service.kubernetes.providers %}
{{ provider|indent(4, true) + " = " + provider + "." + provider }}
{%- endfor %}
  }
  helm_chart = stable/consul
  name = {{ svc }}
  namespace = storage
  spec = {
    max_replicas = {{ service.kubernetes.spec.max_replicas||default(defaults.kubernetes.spec.max_replicas) }}
    min_replicas = {{ service.kubernetes.spec.min_replicas|default(defaults.kubernetes.spec.min_replicas) }}
    cpu_usage = {{ service.kubernetes.spec.cpu_usage|default(defaults.kubernetes.spec.cpu_usage) }}
    api_version = {{ service.kubernetes.spec.api_version|default(defaults.kubernetes.spec.api_verseion)|string }}
    kind = {{ service.kubernetes.spec.kind|default(defaults.kubernetes.spec.kind)|string }}
  }
  domain = {{ defaults.domain|default(example.com)|string }}
  subdomains = [
{%- if service.subdomains is defined %}
{%- for i in service.subdomains %}
    - "{{ i }}"
{%- endfor %}
{%- else %}
  ]
{%- endif %}
  sets = [
{%- for k,v in service.kubernetes.values.items() %}
    {
      name = "{{ k }}",
      value = "{{ v }}"
    }
{%- endfor %}
  ]
}
