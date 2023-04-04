# Use the official Python image as the base image
FROM python:3.11

# Set the working directory in the container
WORKDIR /Sim

# Copy the application files into the working directory
COPY . /Sim

# Install the application dependencies
RUN pip install -r requirements.txt


# Define the entry point for the container
CMD ["flask", "run", "--host=0.0.0.0", "--port=8000"]