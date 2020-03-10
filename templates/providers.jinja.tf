{%- for provider in defaults %}
{{ "provider " + provider|lower + " {" }}
{{ "alias = "|indent(2, true) + alias | default(provider|lower) }}
{%- for k, v in defaults[provider].items() %}
{{ k|indent(2, true) + " = " + v|string }}
{%- endfor %}
{{ "}" }}

{%- endfor %}
