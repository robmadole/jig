/envs:
  file.directory:
    - user: vagrant
    - group: vagrant

{% for python in pillar['pythons'] %}
/envs/{{ python }}:
  virtualenv.managed:
    - user: vagrant
    - group: vagrant
    - system_site_packages: False
    - requirements: /vagrant/requirements.txt
    - python: /usr/bin/{{ python }}
{% endfor %}
