FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements-dev.txt ./
# Dev image: includes the test tools (a slimmer production image comes later)
RUN pip install --no-cache-dir -r requirements-dev.txt

# Copy project
COPY . .

# Copy entrypoint and make executable
COPY entrypoint.sh ./entrypoint.sh
RUN chmod +x ./entrypoint.sh

# Expose port
EXPOSE 8000

# Entrypoint will wait for DB, run migrations and then start the server
ENTRYPOINT ["./entrypoint.sh"]
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
