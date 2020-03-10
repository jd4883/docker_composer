{%- for provider in defaults %}
{{ "provider " + provider|lower + " {" }}
{{ "alias = "|indent(2, true) + alias | default(provider|lower) }}
{%- for k, v in defaults[provider].items() %}
{%- if v|lower is ("true" or "false") %}
{{ k|indent(2, true) + " = " + v|string|lower }}
{%- else %}
{{ k|indent(2, true) + " = \"" + v|string + "\"" }}
{%- endif %
{%- endfor %}
{{ "}" }}

{%- endfor %}
