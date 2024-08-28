"""
title: Email Sending Tool
author: Karol S. Danisz
author_url: https://github.com/k-mktr/llm-tool-calling-examples
buy_me_a_coffee: https://mktr.sbs/coffee
version: 0.1.0
license: MIT
description: A tool for preparing and sending emails using SMTP, with user confirmation and HTML support.
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Any, Callable
from pydantic import BaseModel, Field
from datetime import datetime

class Tools:
    class Valves(BaseModel):
        FROM_EMAIL: str = Field(
            default="someone@example.com",
            description="The email address to use for sending emails",
        )
        PASSWORD: str = Field(
            default=None,
            description="The password for the provided email address",
        )
        SMTP_SERVER: str = Field(
            default="smtp.gmail.com",
            description="The SMTP server to use for sending emails",
        )
        SMTP_PORT: int = Field(
            default=465,
            description="The port to use for the SMTP server",
        )
        EMAIL_SIGNATURE: str = Field(
            default="",
            description="The signature to append to all emails",
        )

    def __init__(self):
        self.valves = self.Valves()
        self.prepared_email = None

    def get_user_name_and_email_and_id(self, __user__: dict = {}) -> str:
        """
        Get the user name, Email and ID from the user object.
        """
        result = ""
        if "name" in __user__:
            result += f"User: {__user__['name']}"
        if "id" in __user__:
            result += f" (ID: {__user__['id']})"
        if "email" in __user__:
            result += f" (Email: {__user__['email']})"
        return result if result else "User: Unknown"

    async def prepare_email(self, subject: str, body: str, recipients: str, 
                            __event_emitter__: Callable[[dict], Any] = None) -> str:
        """
        Prepare an email for sending.
        
        :param subject: The subject of the email.
        :param body: The body content of the email (can include HTML).
        :param recipients: The recipient(s) of the email (comma-separated if multiple).
        :param __event_emitter__: An optional callback function to emit status events.
        :return: A message indicating the email has been prepared and asking for confirmation.
        """
        def status_object(description="Unknown State", status="in_progress", done=False):
            return {
                "type": "status",
                "data": {
                    "status": status,
                    "description": description,
                    "done": done,
                },
            }

        if __event_emitter__:
            await __event_emitter__(status_object("Preparing Email"))

        recipients = recipients.strip("[]").replace("'", "").replace('"', '')
        
        # Add signature to the body
        body_with_signature = f"{body}<br><br>{self.valves.EMAIL_SIGNATURE}"
        
        self.prepared_email = {
            "subject": subject,
            "body": body_with_signature,
            "recipients": recipients,
        }

        if __event_emitter__:
            await __event_emitter__(status_object("Email Prepared", status="complete", done=True))

        return f"""
Email prepared for sending:
TO: {recipients}
SUBJECT: {subject}
BODY: {body}

Signature will be automatically appended.

Present prepared email to the user requesting to review its details and confirm if the user wants to send it to the recipients.
To send the email, use the 'send_prepared_email' function.
To discard this email and start over, use the 'discard_prepared_email' function.
"""

    async def send_prepared_email(self, __event_emitter__: Callable[[dict], Any] = None) -> str:
        """
        Send the previously prepared email.
        
        :param __event_emitter__: An optional callback function to emit status events.
        :return: A message indicating the result of the email sending attempt.
        """
        def status_object(description="Unknown State", status="in_progress", done=False):
            return {
                "type": "status",
                "data": {
                    "status": status,
                    "description": description,
                    "done": done,
                },
            }

        if not self.prepared_email:
            if __event_emitter__:
                await __event_emitter__(status_object("Error: No email prepared", status="error", done=True))
            return "No email has been prepared. Please use the 'prepare_email' function first."

        if not self.valves.PASSWORD:
            if __event_emitter__:
                await __event_emitter__(status_object("Error: Email password is not set", status="error", done=True))
            return "Email password is not set. Please set it in your environment variables."

        try:
            if __event_emitter__:
                await __event_emitter__(status_object("Connecting to SMTP server"))

            msg = MIMEMultipart('alternative')
            msg['Subject'] = self.prepared_email["subject"]
            msg['From'] = self.valves.FROM_EMAIL
            msg['To'] = self.prepared_email["recipients"]

            # Create both plain text and HTML versions of the message
            text_part = MIMEText(self.prepared_email["body"].replace('<br>', '\n'), 'plain')
            html_part = MIMEText(self.prepared_email["body"], 'html')

            msg.attach(text_part)
            msg.attach(html_part)

            with smtplib.SMTP_SSL(self.valves.SMTP_SERVER, self.valves.SMTP_PORT) as server:
                server.login(self.valves.FROM_EMAIL, self.valves.PASSWORD)
                
                if __event_emitter__:
                    await __event_emitter__(status_object("Sending email"))
                
                server.sendmail(self.valves.FROM_EMAIL, [self.prepared_email["recipients"]], msg.as_string())
            
            current_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
            
            if __event_emitter__:
                await __event_emitter__(status_object(f"Email sent successfully at {current_time}", status="complete", done=True))
            
            self.prepared_email = None  # Clear the prepared email after sending
            return f"Message sent successfully at {current_time}."
        except Exception as e:
            if __event_emitter__:
                await __event_emitter__(status_object(f"Error: {str(e)}", status="error", done=True))
            return str({"status": "error", "message": f"{str(e)}"})

    async def discard_prepared_email(self, __event_emitter__: Callable[[dict], Any] = None) -> str:
        """
        Discard the previously prepared email.
        
        :param __event_emitter__: An optional callback function to emit status events.
        :return: A message indicating the email has been discarded.
        """
        if __event_emitter__:
            await __event_emitter__({"type": "status", "data": {"status": "in_progress", "description": "Discarding prepared email", "done": False}})

        self.prepared_email = None

        if __event_emitter__:
            await __event_emitter__({"type": "status", "data": {"status": "complete", "description": "Prepared email discarded", "done": True}})

        return "The prepared email has been discarded. You can prepare a new email using the 'prepare_email' function."