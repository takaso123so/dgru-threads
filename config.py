import json
import os

CLAUDE_API_KEY = os.environ["CLAUDE_API_KEY"]
DATA_SOURCE = "csv"
REPOST_INTERVAL_DAYS = 7

with open(os.path.join(os.path.dirname(__file__), "breeds.json"), encoding="utf-8") as _f:
    _breeds_json = json.load(_f)

# breeds.json + 環境変数から全犬種情報を構築
# 新しい犬種は breeds.json に追加 + GitHub Secretsに {KEY.upper()}_ACCOUNT_ID / ACCESS_TOKEN を追加するだけ
BREEDS: dict[str, dict] = {}
THREADS_ACCOUNTS: dict[str, dict] = {}

for _key, _info in _breeds_json.items():
    _account_id = os.environ.get(f"{_key.upper()}_ACCOUNT_ID", "")
    _access_token = os.environ.get(f"{_key.upper()}_ACCESS_TOKEN", "")
    BREEDS[_key] = {
        **_info,
        "account_id": _account_id,
        "access_token": _access_token,
    }
    THREADS_ACCOUNTS[_key] = {
        "account_id": _account_id,
        "access_token": _access_token,
    }
