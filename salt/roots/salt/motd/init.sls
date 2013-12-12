/etc/motd:
  file.managed:
    - source: salt://motd/message.txt
