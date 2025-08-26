import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

load_dotenv()

# Configure email info
smtp_host = os.getenv("SMTP_HOST")
smtp_port = os.getenv("SMTP_PORT")
smtp_user = os.getenv("SMTP_USER")
smtp_pass = os.getenv("SMTP_PASS")

sender_email = "insights@dhruvdewan.com"
receiver_email = "dhruvrdewan@gmail.com"

message = MIMEText("Hey, this is a test email.")

message["Subject"] = "Portfolio Update"
message["From"] = sender_email
message["To"] = receiver_email

try:
    server = smtplib.SMTP_SSL(smtp_host, smtp_port)
    server.login(smtp_user, smtp_pass)
    server.send_message(message)
    server.quit()
    print("Email sent successfully!")

except Exception as e:
    print(f"Error sending email: {e}")
