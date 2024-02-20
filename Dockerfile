# Use an official Python runtime as a parent image
FROM python:3.12 AS base

# Set the working directory in the container to /app
WORKDIR /app

# Add the current directory contents into the container at /app
ADD . /app

# Install Poetry
RUN pip install --no-cache-dir poetry

# Use Poetry to install dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi

# Make port 8000 available to the world outside this container
EXPOSE 8000

FROM base AS development

# Use Poetry to install dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --with=dev --no-interaction --no-ansi

FROM base AS main
# Not meant for production.
# Run app.py when the container launches
CMD ["poetry", "run", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]