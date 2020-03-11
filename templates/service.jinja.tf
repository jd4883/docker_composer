module {{ svc }} {
  source = "{{ helm_module }}"
  providers = {
{%- for provider in service.kubernetes.providers %}
    {{ provider }} = {{ provider }}.{{ provider }}
{%- endfor %}
  }
  helm_chart = {{ service.kubernetes.helm_chart }}
  name = {{ svc }}
  namespace = {{ service.kubernetes.namespace }}
  spec = {
    max_replicas = {{ service.kubernetes.spec.max_replicas||default(defaults.kubernetes.spec.max_replicas) }}
    min_replicas = {{ service.kubernetes.spec.min_replicas|default(defaults.kubernetes.spec.min_replicas) }}
    cpu_usage = {{ service.kubernetes.spec.cpu_usage|default(defaults.kubernetes.spec.cpu_usage) }}
    api_version = "{{ service.kubernetes.spec.api_version|default(defaults.kubernetes.spec.api_verseion) }}"
    kind = "{{ service.kubernetes.spec.kind|default(defaults.kubernetes.spec.kind) }}"
  }
  domain = "{{ defaults.domain|default(example.com) }}"
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
