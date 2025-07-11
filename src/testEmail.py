import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv
from user import User
from snaptrade_client import SnapTrade
from localInsights import localInsights

load_dotenv()

# Configure email info
smtp_host = os.getenv("SMTP_HOST")
smtp_port = os.getenv("SMTP_PORT")
smtp_user = os.getenv("SMTP_USER")
smtp_pass = os.getenv("SMTP_PASS")

sender_email = "insights@dhruvdewan.com"
receiver_email = "dhruvrdewan@gmail.com"


snaptrade_client = SnapTrade(
    client_id=os.getenv("CLIENT_ID"),
    consumer_key=os.getenv("CONSUMER_KEY"),
)

test_user = User(
    userId=os.getenv("USER_ID"),
    userSecret=os.getenv("USER_SECRET"),
)

test_user.pull_connected_brokerage_accounts(snaptrade_client)

test_user.pull_account_holdings(snaptrade_client, "Robinhood Individual")

portfolio_snapshot = test_user.format_portfolio_summary("Robinhood Individual")
snapshot_LLM = test_user.small_holdings_snapshot("Robinhood Individual")
local_insights = localInsights(snapshot_LLM)

email_body = portfolio_snapshot + "\n\n" + local_insights

message = MIMEText(email_body)

message["Subject"] = "Test Email"
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
