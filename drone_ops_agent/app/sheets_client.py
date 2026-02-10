from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
import pandas as pd

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

class SheetsClient:
    def __init__(self, spreadsheet_id, creds_file="service_account.json"):
        creds = Credentials.from_service_account_file(creds_file, scopes=SCOPES)
        self.service = build("sheets", "v4", credentials=creds)
        self.spreadsheet_id = spreadsheet_id

    def read_sheet(self, range_name):
        result = self.service.spreadsheets().values().get(
            spreadsheetId=self.spreadsheet_id,
            range=range_name
        ).execute()
        values = result.get("values", [])
        return pd.DataFrame(values[1:], columns=values[0])

    def update_cell(self, range_name, value):
        body = {"values": [[value]]}
        self.service.spreadsheets().values().update(
            spreadsheetId=self.spreadsheet_id,
            range=range_name,
            valueInputOption="RAW",
            body=body
        ).execute()
