module {{ svc + " {" }}
  source = {{ helm_module|string }}
  providers = {
{%- for provider in service.kubernetes.providers %}
    {{ provider }} = {{ provider }}.{{ provider }}
{%- endfor %}
  }
  helm_chart = {{ service.kubernetes.helm_chart|string }}
}
