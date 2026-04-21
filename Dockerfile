FROM python:3.14-bookworm

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY app /app/app
COPY migrations /app/migrations
COPY start.sh /app/start.sh

RUN chmod +x /app/start.sh

EXPOSE 8000

CMD ["sh", "/app/start.sh"]