# Use official Python runtime
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy project files
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Ollama (Note: For cloud deployment, you usually use an external LLM API 
# because running Ollama inside Docker requires GPU or huge CPU resources.
# For this Dockerfile, we assume external Ollama or just Python logic.)

# Expose port (if you build a Flask UI later)
EXPOSE 8080

# Command to run the app
CMD ["python", "main.py"]