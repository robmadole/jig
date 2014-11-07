{% for python in pillar['pythons'] %}
/envs/{{ python }}/bin/pip install -e /jig:
  cmd.run:
    - unless: /envs/{{ python }}/bin/pip freeze | grep jig
    - user: vagrant
    - group: vagrant
{% endfor %}
