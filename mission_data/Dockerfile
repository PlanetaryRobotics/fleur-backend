FROM influxdb:2.0

# Copy your entry point script to the container
COPY entrypoint.sh /entrypoint.sh

# Make the script executable
RUN chmod +x /entrypoint.sh

# Define the entry point
CMD ["./entrypoint.sh"]