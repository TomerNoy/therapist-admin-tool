"""
Fetches therapist form responses directly from Google Sheets.
"""

import pandas as pd
import gspread

from config import SPREADSHEET_ID, SHEET_GID, SHEETS_CREDENTIALS_PATH


def fetch_spreadsheet_as_dataframe():
    """
    Fetch the Google Form response sheet and return it as a pandas DataFrame.

    Returns:
        pandas DataFrame with all form responses
    """
    client = gspread.service_account(filename=SHEETS_CREDENTIALS_PATH)

    spreadsheet = client.open_by_key(SPREADSHEET_ID)
    worksheet = spreadsheet.get_worksheet_by_id(SHEET_GID)

    rows = worksheet.get_all_values()
    if not rows:
        return pd.DataFrame()

    headers = rows[0]
    data = rows[1:]
    df = pd.DataFrame(data, columns=headers)

    # Drop columns with empty headers (trailing empty columns from Google Forms)
    df = df.loc[:, df.columns != '']

    print(f"Fetched {len(df)} rows from Google Sheets (worksheet gid={SHEET_GID})")
    return df
