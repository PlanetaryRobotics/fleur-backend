# Use an official Python runtime as a parent image
FROM python:3.8

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install influxdb_client

# Install pydantic
RUN pip install pydantic

# Make port 8070 available to the world outside this container
EXPOSE 8070

# Run app.py when the container launches
CMD ["sh", "-c", "sleep 60 && python -u app.py"]
