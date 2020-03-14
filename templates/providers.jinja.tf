{%- for provider in defaults %}
provider "{{ provider|lower }}" {
  alias = "{{ alias | default(provider|lower) }}"
{%- for k, v in defaults[provider].items()|sort %}
  {{ k }} = "{{ v }}"
{%- endfor %}
},
{% endfor %}
