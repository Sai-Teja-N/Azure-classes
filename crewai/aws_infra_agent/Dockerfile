FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install build dependencies required by some python packages (e.g. PyYAML, if needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Ensure terraform_output directory exists
RUN mkdir -p terraform_output

# Run the agent
CMD ["python", "main.py"]
