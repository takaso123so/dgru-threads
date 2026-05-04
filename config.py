import os

CLAUDE_API_KEY = os.environ["CLAUDE_API_KEY"]

THREADS_ACCOUNTS = {
    "shiba": {
        "account_id": os.environ["SHIBA_ACCOUNT_ID"],
        "access_token": os.environ["SHIBA_ACCESS_TOKEN"],
    },
    "schnauzer": {
        "account_id": os.environ["SCHNAUZER_ACCOUNT_ID"],
        "access_token": os.environ["SCHNAUZER_ACCESS_TOKEN"],
    },
}

DATA_SOURCE = "csv"
REPOST_INTERVAL_DAYS = 7
