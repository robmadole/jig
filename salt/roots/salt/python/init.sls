python-tools:
  pkg.installed:
    - pkgs:
      - python-software-properties
      - python-dev
      - python-pip

old-python-versions:
  pkgrepo.managed:
    - ppa: fkrull/deadsnakes
  pkg.latest:
    - pkgs:
      - python2.6
      - python2.6-dev
      - python3.1
      - python3.1-dev
      - python3.2
      - python3.2-dev

virtualenv:
  pip.installed
