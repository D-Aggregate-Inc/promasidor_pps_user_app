# Use a Python 3.10 slim base image for a smaller footprint
FROM python:3.10-slim

# Update and install security patches to reduce vulnerabilities
RUN apt-get update && apt-get upgrade -y && apt-get clean && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Install dependencies, including Streamlit, from requirements.txt
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application's source code
COPY . .

# Expose Streamlit's default port
EXPOSE 8501

# Command to run the Streamlit app
# --server.port: Ensures the app runs on the correct port inside the container
# --server.address: Binds to all network interfaces, making it accessible from outside
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
