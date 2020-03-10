{%- for provider in defaults %}
{{ "provider" + provider|lower + "{" }}
{{ "alias"|indent(2) + alias | default(provider|lower) }}
{%- for k, v in defaults["providers"][provider].items() %}
{{ k|indent(2) + " = " + v }}
{%- endfor %}
{{ "}" }}

{%- endfor %}
