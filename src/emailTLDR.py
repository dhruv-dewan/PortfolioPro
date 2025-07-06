from user import User
from snaptrade_client import SnapTrade
import os
from dotenv import load_dotenv
from pprint import pprint

load_dotenv()

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

small_snapshot_formatted = test_user.format_portfolio_summary("Robinhood Individual")

print(small_snapshot_formatted)