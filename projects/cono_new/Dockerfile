FROM docker.1ms.run/python:latest

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc default-libmysqlclient-dev pkg-config \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements-linux.txt .
RUN pip install --no-cache-dir --retries 10 --timeout 60 --index-url https://pypi.org/simple -r requirements-linux.txt

COPY . .

EXPOSE 8000

CMD ["gunicorn", "cono_new.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2", "--timeout", "120"]
