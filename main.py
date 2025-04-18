import os
import requests
import zipfile
from datetime import datetime
from io import BytesIO

# Load from environment variables
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
TENANT_ID = os.getenv("TENANT_ID")
USER_EMAIL = os.getenv("USER_EMAIL")
DOWNLOAD_PATH = os.getenv("DOWNLOAD_PATH", "/tmp")

# Authenticate to Graph API
def get_access_token():
    url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "client_credentials",
        "scope": "https://graph.microsoft.com/.default"
    }
    response = requests.post(url, data=data)
    return response.json().get("access_token")

def download_and_extract_zip_from_email():
    token = get_access_token()
    headers = {"Authorization": f"Bearer {token}"}

    # Get today's date in yyyy-mm-dd
    today = datetime.utcnow().date().isoformat()

    # Filter today's received messages
    url = f"https://graph.microsoft.com/v1.0/users/{USER_EMAIL}/messages?$filter=receivedDateTime ge {today}T00:00:00Z&$top=10"
    response = requests.get(url, headers=headers)
    messages = response.json().get("value", [])

    for message in messages:
        subject = message.get("subject", "")
        if subject.startswith("Correction Report | Date:") and "ENV: http://20.150.143.33" in subject:
            message_id = message["id"]

            # Get attachments
            attach_url = f"https://graph.microsoft.com/v1.0/users/{USER_EMAIL}/messages/{message_id}/attachments"
            attach_resp = requests.get(attach_url, headers=headers)
            attachments = attach_resp.json().get("value", [])

            for att in attachments:
                if att["name"].endswith(".zip"):
                    print(f"✅ Found zip attachment: {att['name']}")
                    zip_data = BytesIO()
                    zip_data.write(bytes(att["contentBytes"], encoding="utf-8"))
                    zip_data.seek(0)

                    # Extract to dated folder
                    extract_folder = os.path.join(DOWNLOAD_PATH, today)
                    os.makedirs(extract_folder, exist_ok=True)

                    with zipfile.ZipFile(zip_data) as zip_ref:
                        zip_ref.extractall(extract_folder)

                    print(f"📁 Extracted to: {extract_folder}")
                    return

    print("⚠️ No matching email or zip attachment found.")

if __name__ == "__main__":
    download_and_extract_zip_from_email()
