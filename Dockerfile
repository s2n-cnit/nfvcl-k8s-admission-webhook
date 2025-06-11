FROM python:3.12-slim
RUN pip install flask kubernetes
COPY webhook.py /webhook.py
RUN mkdir -p /certs
CMD ["python", "/webhook.py"]
