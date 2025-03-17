# Ask AI Slack Bot 🤖

This is a Flask-based Slack bot that integrates with OpenAI's GPT-4 to provide AI-generated responses to Slack thread discussions. Users can invoke the bot through a message shortcut, enter a query, and receive AI-powered insights based on the thread's context.

---

## 🚀 Features
- Secure Slack request verification to prevent unauthorized access.
- Interactive Slack modal to capture user queries.
- Fetches and processes Slack thread messages for better AI context.
- Uses OpenAI's GPT-4 to generate AI responses.
- Posts ephemeral responses in the Slack thread for privacy.
- Asynchronous AI processing to prevent timeout issues.
- Error handling and user notifications in case of failures.

---

## 🛠️ Setup & Installation

### 1️⃣ Prerequisites
- Python 3.10+
- A Slack App with permissions:
  - `chat:write`
  - `chat:write.public`
  - `conversations.history`
  - `conversations.replies`
  - `commands`
- OpenAI API Key

### 2️⃣ Clone the Repository
```bash
git clone https://github.com/tonythomas01/slack-ai-bot.git
cd ask-ai-slack-bot
```

### 3️⃣ Install Dependencies
```bash
pip install -r requirements.txt
```

### 4️⃣ Set Up Environment Variables
Create a `.env` file and add the following:
```
SLACK_SIGNING_SECRET=your_slack_signing_secret
SLACK_BOT_TOKEN=your_slack_bot_token
OPENAI_API_KEY=your_openai_api_key
```
Or export them in your terminal:
```bash
export SLACK_SIGNING_SECRET=your_slack_signing_secret
export SLACK_BOT_TOKEN=your_slack_bot_token
export OPENAI_API_KEY=your_openai_api_key
```

### 5️⃣ Run the Bot
```bash
python app.py
```

---

## 🛠️ Deploying to Production

For production, you can deploy this bot using **Google Cloud Run**, **AWS Lambda**, or **Docker**.

### Deploy with Docker
1. Build the Docker image:
   ```bash
   docker build -t ask-ai-slack-bot .
   ```
2. Run the container:
   ```bash
   docker run -p 8080:8080 --env-file .env ask-ai-slack-bot
   ```

---

## 📝 How It Works
1. A user invokes the Slack bot using a **message shortcut**.
2. The bot opens a modal where the user enters a query.
3. The bot fetches the **entire Slack thread** where the shortcut was used.
4. The thread's context is sent to **OpenAI's GPT-4**.
5. The AI generates a response based on the conversation.
6. The bot posts an **ephemeral** AI response in the same thread.

---

## ⚠️ Error Handling
- If the bot is not invited to a channel, users receive a prompt to invite it.
- If OpenAI API fails, users receive a message to retry later.
- If Slack API calls fail, errors are logged, and users are notified.

---

## 🔗 Slack Permissions & API Configuration
Ensure your Slack app has the following::
- **OAuth Scopes**:
   - `chat:write`
   - `chat:write.public`
   - `channels:history`
   - `im:history`
   - `mpim:history`
   - `groups:history`
   - `groups:read`
---

## 🛠️ Contributing
1. Fork the repo.
2. Create a new branch: `git checkout -b feature-new-feature`.
3. Commit changes: `git commit -m "Added new feature"`.
4. Push to the branch: `git push origin feature-new-feature`.
5. Submit a pull request.


---

## ✨ Credits
Developed with ❤️ using **Flask**, **Slack SDK**, and **OpenAI API**.

---

## 📩 Questions or Issues?
Open an issue on [GitHub Issues](https://github.com/tonythomas01/slack-ai-bot/issues) or reach out via Slack!
