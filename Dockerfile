FROM python:3.12

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=AadhityaaBackend.settings
ENV DEBUG=False

# Set work directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Create empty .env file to prevent errors
RUN touch .env

# Create and set static files directory
RUN mkdir -p staticfiles
ENV STATIC_ROOT=/app/staticfiles

# Collect static files with default environment
RUN python manage.py collectstatic --noinput

# Run migrations
RUN python manage.py migrate

# Expose port
EXPOSE 8000

# Start Gunicorn
CMD ["gunicorn", "AadhityaaBackend.wsgi:application", "--bind", "0.0.0.0:8000"]
