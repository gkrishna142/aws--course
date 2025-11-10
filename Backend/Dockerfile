FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /code

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    netcat-traditional \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY dist/requirements.txt /code/requirements.txt
RUN pip install --upgrade pip
RUN pip install -r /code/requirements.txt

# Copy backend project (dist folder)
COPY dist/ /code/

# Create media + static folders
RUN mkdir -p /code/media /code/static
RUN chmod -R 777 /code/media /code/static

# Replace 'projectname' with your actual Django project folder name
CMD ["gunicorn", "edustream.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
