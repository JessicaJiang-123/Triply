# Use the official Dev Containers Python image for 3.13
FROM mcr.microsoft.com/devcontainers/python:3.13-bullseye

# Install Node.js (for React + TypeScript frontend)
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && npm install -g npm@latest

# Working directory inside the container
WORKDIR /workspace

CMD ["bash"]