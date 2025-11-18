import os
import csv
import io
import datetime
import requests
from urllib.parse import quote

from flask import Flask, Response

app = Flask(__name__)


# ---------- Graph helpers ----------

def get_graph_token() -> str:
    tenant_id = os.environ["GRAPH_TENANT_ID"]
    client_id = os.environ["GRAPH_CLIENT_ID"]
    client_secret = os.environ["GRAPH_CLIENT_SECRET"]

    token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "client_credentials",
        "scope": "https://graph.microsoft.com/.default",
    }

    resp = requests.post(token_url, data=data)
    resp.raise_for_status()
    return resp.json()["access_token"]


def fetch_csv_from_graph() -> str:
    site_id = os.environ["GRAPH_SITE_ID"]
    drive_id = os.environ["GRAPH_DRIVE_ID"]
    csv_path = os.environ.get(
        "GRAPH_CSV_PATH",
        "Ivory Share/Kevin/GPT projects/top10.csv",
    )

    token = get_graph_token()
    encoded_path = quote(csv_path)

    url = (
        f"https://graph.microsoft.com/v1.0"
        f"/sites/{site_id}/drives/{drive_id}/root:/{encoded_path}:/content"
    )

    resp = requests.get(url, headers={"Authorization": f"Bearer {token}"})
    resp.raise_for_status()
    return resp.text


# ---------- HTML rendering ----------

def build_html_table() -> str:
    csv_text = fetch_csv_from_graph()
    reader = csv.reader(io.StringIO(csv_text))

    rows = list(reader)
    if not rows:
        return "<p>No data</p>"

    header = rows[0]
    data_rows = rows[1:]

    # Basic styling similar to what you already had
    html = []
    html.append(
        """
        <html>
        <head>
        <meta charset="utf-8" />
        <style>
            body {
                font-family: Arial, sans-serif;
                font-size: 14px;
            }
            table {
                border-collapse: collapse;
                width: 100%;
            }
            thead tr {
                background-color: #001f4d;
                color: white;
            }
            th, td {
                border: 1px solid #ddd;
                padding: 6px 8px;
                text-align: left;
            }
            tr:nth-child(even) {
                background-color: #f9f9f9;
            }
            tr:hover {
                background-color: #f1f1f1;
            }
        </style>
        </head>
        <body>
        <h3>Top 10 by YTD Performance</h3>
        <table>
        <thead><tr>
        """
    )

    for col in header:
        html.append(f"<th>{col}</th>")
    html.append("</tr></thead><tbody>")

    for row in data_rows:
        if not any(row):
            continue  # skip blank rows
        html.append("<tr>")
        for cell in row:
            html.append(f"<td>{cell}</td>")
        html.append("</tr>")

    html.append("</tbody></table>")

    # just to be safe, add a timestamp
    html.append(
        f"<p style='margin-top:8px;font-size:12px;color:#666;'>"
        f"Last updated (server time): {datetime.datetime.utcnow().isoformat()}Z"
        f"</p>"
    )

    html.append("</body></html>")
    return "".join(html)


# ---------- Routes ----------

@app.route("/")
def index():
    # simple redirect to widget for now
    return build_html_table()


@app.route("/widget")
def widget():
    html = build_html_table()
    return Response(html, mimetype="text/html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
