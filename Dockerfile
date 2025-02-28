# Use an official lightweight Python image
FROM python:3.10

WORKDIR /app

# Copy files and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Install Google Cloud SDK for fetching secrets
RUN apt-get update && apt-get install -y curl && \
    curl -sSL https://sdk.cloud.google.com | bash -s -- --install-dir=/root && \
    echo 'source /root/google-cloud-sdk/path.bash.inc' >> /root/.bashrc && \
    apt-get clean

# Ensure the correct shell is used
SHELL ["/bin/bash", "-c"]

# Expose the Flask port
ENV PORT=8080

# Fetch secrets dynamically from Google Secret Manager and start the app
CMD source /root/.bashrc && \
    export SLACK_SIGNING_SECRET=$(gcloud secrets versions access latest --secret=slack-signing-secret) && \
    export SLACK_BOT_TOKEN=$(gcloud secrets versions access latest --secret=slack-bot-token) && \
    export OPENAI_API_KEY=$(gcloud secrets versions access latest --secret=openai-api-key) && \
    python app.py
