FROM mcr.microsoft.com/playwright/python:v1.42.0-jammy

WORKDIR /app

# Install Python dependencies
COPY pyproject.toml ./
RUN pip install --no-cache-dir -e .

# Copy runner code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 runner && chown -R runner:runner /app
USER runner

CMD ["pytest", "--help"]
