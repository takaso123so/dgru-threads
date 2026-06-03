"""
Threads 長期アクセストークンを更新して GitHub Secrets に書き戻すスクリプト。
毎月1回 GitHub Actions で実行する。
必要な環境変数:
  GH_PAT                  - secrets 書き込み権限付き GitHub PAT
  {BREED}_ACCESS_TOKEN    - 各犬種の現在のトークン
"""
import base64
import os
import sys

import requests

REPO = "takaso123so/dgru-threads"
BREEDS = ["shiba", "schnauzer", "cavalier", "toypoodle", "chihuahua", "dachshund"]


def refresh_token(access_token: str) -> str | None:
    res = requests.get(
        "https://graph.threads.net/refresh_access_token",
        params={"grant_type": "th_refresh_token", "access_token": access_token},
    )
    if res.status_code == 200:
        return res.json().get("access_token")
    print(f"[ERROR] トークン更新失敗: {res.status_code} {res.text}")
    return None


def get_repo_public_key(gh_token: str) -> tuple[str, str]:
    headers = {"Authorization": f"token {gh_token}", "Accept": "application/vnd.github+json"}
    res = requests.get(
        f"https://api.github.com/repos/{REPO}/actions/secrets/public-key",
        headers=headers,
    )
    res.raise_for_status()
    data = res.json()
    return data["key_id"], data["key"]


def encrypt_secret(public_key_b64: str, secret_value: str) -> str:
    from nacl import encoding, public
    pk = public.PublicKey(public_key_b64.encode(), encoding.Base64Encoder())
    encrypted = public.SealedBox(pk).encrypt(secret_value.encode())
    return base64.b64encode(encrypted).decode()


def update_secret(gh_token: str, secret_name: str, secret_value: str, key_id: str, public_key: str):
    headers = {"Authorization": f"token {gh_token}", "Accept": "application/vnd.github+json"}
    payload = {"encrypted_value": encrypt_secret(public_key, secret_value), "key_id": key_id}
    res = requests.put(
        f"https://api.github.com/repos/{REPO}/actions/secrets/{secret_name}",
        headers=headers,
        json=payload,
    )
    if res.status_code in (201, 204):
        print(f"[OK] {secret_name} 更新成功")
    else:
        print(f"[ERROR] {secret_name} 更新失敗: {res.status_code} {res.text}")


if __name__ == "__main__":
    gh_token = os.environ.get("GH_PAT", "")
    if not gh_token:
        print("[ERROR] GH_PAT が未設定")
        sys.exit(1)

    key_id, public_key = get_repo_public_key(gh_token)
    failed = []

    for breed in BREEDS:
        secret_name = f"{breed.upper()}_ACCESS_TOKEN"
        current_token = os.environ.get(secret_name, "")
        if not current_token:
            print(f"[SKIP] {secret_name} が未設定")
            continue
        new_token = refresh_token(current_token)
        if new_token:
            update_secret(gh_token, secret_name, new_token, key_id, public_key)
        else:
            failed.append(breed)

    if failed:
        print(f"[WARN] 更新失敗した犬種: {', '.join(failed)}")
        sys.exit(1)
