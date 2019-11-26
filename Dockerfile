FROM python:3.7

COPY entrypoint.sh /bin
ENTRYPOINT ["/bin/entrypoint.sh"]