/envs/docs:
  virtualenv.managed:
    - user: vagrant
    - group: vagrant
    - system_site_packages: False
    - requirements: /vagrant/requirements.txt
    - python: /usr/bin/python

jig-develop-egg:
  pip.installed:
    - editable:
      - /vagrant
    - env: /envs/docs

/envs/docs/bin/httpdocs.py:
  file.managed:
    - user: vagrant
    - group: vagrant
    - source: salt://docs/httpdocs.py
    - mode: 755

/etc/supervisor/conf.d/docs.conf:
  file:
    - managed
    - source: salt://docs/supervisor.conf
    - watch_in:
      - service: supervisor

docs:
  supervisord:
    - running
    - restart: False
    - require:
      - service: supervisor

{% set jigops_rst = "/tmp/jigops.rst" %}

{{ jigops_rst }}:
  file.managed:
    - source: salt://docs/jigops.rst

docutils:
  pip.installed:
    - env: /envs/docs

make-man-page-from-docs:
  cmd:
    - run
    - name: /envs/docs/bin/rst2man.py {{ jigops_rst }} /usr/share/man/man7/jigops.7
