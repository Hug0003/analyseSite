FROM mcr.microsoft.com/playwright/python:v1.41.0-jammy

WORKDIR /app

# Install system dependencies (curl for healthcheck)
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers (if not included in base, but they usually are. 
# We run this just in case specifically for the browsers we need or if the base image is bare)
RUN playwright install chromium
RUN playwright install-deps

COPY . .

EXPOSE 8000

CMD ["python", "run.py"]
