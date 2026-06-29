# Use Python 3.10 slim as the base image (lightweight and secure)
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file and install dependencies (if any)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the source code files
COPY candidate_parser.py .
COPY ranker.py .
COPY rank.py .

# Define the entrypoint to run the ranking pipeline
ENTRYPOINT ["python", "rank.py"]
