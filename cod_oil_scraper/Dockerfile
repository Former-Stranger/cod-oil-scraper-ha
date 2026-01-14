ARG BUILD_FROM
FROM $BUILD_FROM

# Install system dependencies
RUN apk add --no-cache \
    python3 \
    py3-pip \
    chromium \
    chromium-chromedriver \
    bash \
    jq \
    dcron

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python packages
RUN pip3 install --no-cache-dir -r requirements.txt

# Install Playwright and Chromium
RUN playwright install-deps && \
    playwright install chromium

# Copy application files
COPY oil_scraper.py .
COPY run.sh .

# Make run script executable
RUN chmod +x /app/run.sh

# Set entrypoint
CMD ["/app/run.sh"]
