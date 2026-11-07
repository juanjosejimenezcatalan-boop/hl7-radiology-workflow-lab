FROM python:3.12-alpine
WORKDIR /app
COPY src ./src
EXPOSE 2575
CMD ["python", "-m", "src.hl7_server", "--host", "0.0.0.0", "--port", "2575", "--log", "/app/logs/receiver.log"]

