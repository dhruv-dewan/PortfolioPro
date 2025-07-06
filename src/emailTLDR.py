from user import User
from snaptrade_client import SnapTrade
import os
from dotenv import load_dotenv
from pprint import pprint
from localInsights import localInsights, _format_snapshot_for_llm

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

small_snapshot_formatted = test_user.small_holdings_snapshot("Robinhood Individual")

print(_format_snapshot_for_llm(small_snapshot_formatted))