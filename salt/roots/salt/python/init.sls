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
      - python2.6-dev
      - python3.1-dev
      - python3.2-dev
      - python3.3-dev
      - python3.4-dev

virtualenv:
  pip.installed
