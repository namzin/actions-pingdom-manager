FROM python:3.7

COPY pingdom.py /opt/pingdom/pingdom.py
COPY requirements.txt /opt/pingdom/requirements.txt

COPY entrypoint.sh /bin
ENTRYPOINT ["/bin/entrypoint.sh"]