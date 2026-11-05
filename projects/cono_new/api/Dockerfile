FROM docker.1ms.run/library/python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y --no-install-recommends gcc default-libmysqlclient-dev pkg-config && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --retries 5 --timeout 120 --index-url https://mirrors.aliyun.com/pypi/simple/ -r requirements.txt
COPY . .
EXPOSE 8001
CMD ["gunicorn", "cono_api.wsgi:application", "--bind", "0.0.0.0:8001", "--workers", "2", "--timeout", "120"]
