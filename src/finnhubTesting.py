import finnhub
import os
from dotenv import load_dotenv

load_dotenv()

finnhub_client = finnhub.Client(api_key=os.getenv("CLIENT_API_KEY"))

print(finnhub_client.company_profile2(symbol='VOO'))