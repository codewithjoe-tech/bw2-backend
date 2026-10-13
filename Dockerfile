FROM python:3.11-slim

# Set environment variables to avoid writing bytecode and ensure output is unbuffered
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install required packages including ffmpeg from Debian repositories
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements.txt file into the container
COPY requirements.txt .

# Install Python dependencies using pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Expose port 8000 for the application
EXPOSE 8000

# Define the default command to run the application using uvicorn
CMD ["uvicorn", "mysite.asgi:application", "--host", "0.0.0.0", "--port", "8000", "--reload"]
