{%- for provider in defaults %}
provider "{{ provider|lower }}" {
  alias = "{{ alias | default(provider|lower) }}"
{%- for k, v in defaults[provider].items()|sort %}
{%- if v|lower == "true") %}
  {{ k }} = true
{%- elif v|lower == "false" %}
  {{ k }} = false
{%- else %}
  {{ k }} = "{{ v }}"
{%- endif %}
{%- endfor %}
}
{% endfor %}
