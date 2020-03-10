{{ "module " + svc + "{" }}
{{ "source = \""|indent(2, true) helm_module + "\"" }}
{{ "providers = {"|indent(2, true) }}
{%- for provider in service.kubernetes.providers %}
{{ provider|indent(4, true) + " = " + provider + "." + provider }}
{%- endfor %}
{{ "}"|indent(2, true) }}
{{ "helm_chart = "|indent(2, true) + service.kubernetes.helm_chart + "\"" }}
{{ "name = "|indent(2, true) + svc }}
{{ "namespace = "|indent(2, true) + service.kubernetes.namespace + "\"" }}
{{ "spec = {"|indent(2, true) }}
{{ "max_replicas = "|indent(4, true) + service.kubernetes.spec.max_replicas||default(defaults.kubernetes.spec.max_replicas) }}
{{ "min_replicas = "|indent(4, true) + service.kubernetes.spec.min_replicas|default(defaults.kubernetes.spec.min_replicas) }}
{{ "cpu_usage = "|indent(4, true) + service.kubernetes.spec.cpu_usage|default(defaults.kubernetes.spec.cpu_usage) }}
{{ "api_version = "|indent(4, true) + service.kubernetes.spec.api_version|default(defaults.kubernetes.spec.api_verseion) }}
{{ "kind = "|indent(4, true) + service.kubernetes.spec.kind|default(defaults.kubernetes.spec.kind) }}
{{ "}"|indent(2, true) }}
{{ "domain = "|indent(2, true) + defaults.domain|default("example.com") + "\"" }}
{{ "subdomains = [" |indent(2, true) }}
{%- if service.subdomains is defined %}
{{ "]"}
{%- for i in service.subdomains %}
{{ "\""|indent(4, true) + i + "\"" }}
{%- endfor %}
{%- else %}
{{- "]" }}
{%- endif %}
{{ "sets = ["|indent(2, true) }}
{%- for k,v in service.kubernetes.values.items() %}
{{ "{"|indent(4, true) }}
{{ "name = "|indent(6, true) + k + "\"," }}
{{ "value = "|indent(6, true) + v + "\"" }}
{{ "},"|indent(4, true) }}
{%- endfor %}
{{ "]"|indent(2, true) }}
{{ "}" }}
