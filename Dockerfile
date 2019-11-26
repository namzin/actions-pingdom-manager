FROM python:3.7

COPY pingdom.py /opt/pingdom
COPY requirements.txt /opt/pingdom

COPY entrypoint.sh /bin
ENTRYPOINT ["/bin/entrypoint.sh"]