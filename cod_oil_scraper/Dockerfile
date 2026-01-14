ARG BUILD_FROM
FROM $BUILD_FROM

# Install system dependencies
RUN apk add --no-cache \
    python3 \
    py3-pip \
    bash \
    jq \
    dcron

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install Python packages
RUN pip3 install --break-system-packages --no-cache-dir -r requirements.txt

# Copy application files
COPY oil_scraper.py .
COPY run.sh .

# Make run script executable
RUN chmod a+x /app/run.sh

# Set entrypoint
CMD ["/app/run.sh"]
