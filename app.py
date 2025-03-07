from http.server import DEFAULT_ERROR_MESSAGE

from flask import Flask, request, jsonify
import os
import openai
import json
import hmac
import hashlib
import time
import logging
import threading

from openai import OpenAI
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# Configure logging
logging.basicConfig(level=logging.ERROR)  # Log only errors
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Load secrets securely
SLACK_SIGNING_SECRET = os.getenv("SLACK_SIGNING_SECRET")
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not SLACK_SIGNING_SECRET or not SLACK_BOT_TOKEN or not OPENAI_API_KEY:
    logger.error("Missing required environment variables. Ensure secrets are loaded correctly.")
    raise ValueError("Missing required environment variables. Ensure secrets are loaded correctly.")

slack_client = WebClient(token=SLACK_BOT_TOKEN)

DEFAULT_ERROR_MESSAGE = ("⚠️ There was an error processing your request. Please make sure that @Ask AI bot"
                         " is invited in this channel before trying again. "
                         "You can easily invite the bot by writing `/invite @Ask AI` in this channel.")

def verify_slack_request(req):
    """Verifies that the request comes from Slack."""
    timestamp = req.headers.get("X-Slack-Request-Timestamp")
    slack_signature = req.headers.get("X-Slack-Signature")

    if not timestamp or not slack_signature:
        return False

    # Prevent replay attacks (requests older than 5 mins are rejected)
    if abs(time.time() - int(timestamp)) > 300:
        return False

    # Create the Slack signature
    sig_basestring = f"v0:{timestamp}:{req.get_data(as_text=True)}"
    my_signature = "v0=" + hmac.new(
        SLACK_SIGNING_SECRET.encode(),
        sig_basestring.encode(),
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(my_signature, slack_signature)


def notify_user_on_thread_on_error(channel_id, message_ts, user_id, error_text=DEFAULT_ERROR_MESSAGE):
    """Posts an error message in the thread."""
    try:
        slack_client.chat_postEphemeral(
            channel=channel_id,
            text=error_text,
            user=user_id,
            thread_ts=message_ts
        )
    except SlackApiError as e:
        logger.error(f"Failed to post error message: {e.response['error']}")


def process_ai_request(channel_id, message_ts, user_question, user_id):
    """Runs AI processing in a separate thread."""
    try:
        response = slack_client.conversations_replies(channel=channel_id, ts=message_ts)
        thread_messages = "\n".join([msg["text"] for msg in response["messages"]])
    except SlackApiError as e:
        logger.error(f"Failed to fetch thread messages: {e.response['error']}")
        notify_user_on_thread_on_error(channel_id, message_ts, user_id=user_id)
        return

    # Generate AI response
    prompt = f"Here's a Slack thread:\n{thread_messages}\n\nUser question: {user_question}\n\nProvide a helpful answer based on the context."
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        ai_response = response.choices[0].message.content
    except Exception as e:
        logger.error(f"OpenAI API call failed: {str(e)}")
        notify_user_on_thread_on_error(channel_id, message_ts, user_id=user_id, error_text="⚠️ We could not talk to ChatGPT. Please try again later.")
        ai_response = "There was an error generating the response. Please try again later."

    # Post AI response as an ephemeral message inside the thread
    try:
        slack_client.chat_postEphemeral(
            channel=channel_id,
            text=f"🤖 <@{user_id}>, here's your AI response:\n{ai_response}",
            user=user_id,
            thread_ts=message_ts
        )
    except SlackApiError as e:
        notify_user_on_thread_on_error(channel_id, message_ts, user_id=user_id)
        logger.error(f"Failed to post AI response: {e.response['error']}")


@app.route("/slack/actions", methods=["POST"])
def handle_slack_action():
    """Handles Slack message shortcut and interactive modals securely."""
    if not verify_slack_request(request):
        return jsonify({"error": "Unauthorized"}), 403

    try:
        payload = json.loads(request.form["payload"])

        # Case 1: User selects the message shortcut
        if payload["type"] == "message_action":
            trigger_id = payload["trigger_id"]
            message_ts = payload["message"]["ts"]
            channel_id = payload["channel"]["id"]

            # Open a modal for user input
            slack_client.views_open(
                trigger_id=trigger_id,
                view={
                    "type": "modal",
                    "callback_id": "ask_ai_modal",
                    "title": {"type": "plain_text", "text": "Ask AI about this thread"},
                    "blocks": [
                        {
                            "type": "input",
                            "block_id": "user_question",
                            "element": {"type": "plain_text_input", "action_id": "question_input", "initial_value": "Summarize this thread"},
                            "label": {"type": "plain_text", "text": "What do you want to ask?"}
                        }
                    ],
                    "submit": {"type": "plain_text", "text": "Ask AI"},
                    "private_metadata": json.dumps({"channel_id": channel_id, "message_ts": message_ts})
                }
            )

        # Case 2: User submits the modal
        elif payload["type"] == "view_submission":
            view_data = payload["view"]
            private_metadata = json.loads(view_data["private_metadata"])
            channel_id = private_metadata["channel_id"]
            message_ts = private_metadata["message_ts"]
            user_question = view_data["state"]["values"]["user_question"]["question_input"]["value"]
            user_id = payload["user"]["id"]

            # Send an immediate response to avoid Slack timeout
            slack_client.chat_postEphemeral(
                channel=channel_id,
                text="✅ We received your question! AI is thinking... You'll get a response soon.",
                user=user_id,
                thread_ts=message_ts
            )
            # Run the AI processing in a separate thread
            threading.Thread(target=process_ai_request, args=(channel_id, message_ts, user_question, user_id)).start()
            return jsonify({"response_action": "clear"}), 200

    except SlackApiError as e:
        logger.error(f"Slack API error occurred: {e.response['error']}")
        return jsonify({
            "response_action": "errors",
            "errors": {
                "user_question": "⚠️ The app may not be in this channel. Please invite it before using this feature."
            }
        }), 200
    except Exception as e:
        logger.error("Unexpected error occurred", exc_info=True)
        return jsonify({"error": "Internal Server Error"}), 500

    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
