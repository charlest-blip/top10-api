from flask import Flask, jsonify, render_template_string
import csv
import os

app = Flask(__name__)

# Path to CSV (same folder as this file)
CSV_PATH = os.path.join(os.path.dirname(__file__), "top10.csv")

def load_top10():
    rows = []
    try:
        with open(CSV_PATH, newline="") as f:
            reader = csv.DictReader(f)
            for r in reader:
                rows.append(r)
    except FileNotFoundError:
        # No data file yet – return empty list
        pass
    return rows

def clean_money(value):
    """Turn '355.22' or '$355.22' or '1,017.78' into a float."""
    if value is None:
        return 0.0
    s = str(value).replace("$", "").replace(",", "").strip()
    try:
        return float(s)
    except ValueError:
        return 0.0

def format_ytd(value):
    """
    Handle YTD% values like:
    - '53.22%'  -> 53.22%
    - '53.22'   -> 53.22%
    - '0.5322'  -> 53.22%
    """
    if value is None:
        return "0.00%"
    s = str(value).replace("%", "").strip()
    try:
        num = float(s)
    except ValueError:
        return "0.00%"

    # If it's a fraction (0.53), convert to percentage
    if num <= 1:
        num = num * 100
    return f"{num:.2f}%"

@app.route("/top10")
def top10_json():
    """Return data as JSON"""
    rows = load_top10()
    return jsonify(rows)

@app.route("/widget")
def top10_widget():
    """Return a simple HTML table for embedding"""
    rows = load_top10()

    table_rows = ""
    for r in rows:
        ticker = r.get("Ticker", "")
        last_price = clean_money(r.get("Last Price"))
        prev_close = clean_money(r.get("Prev Year Close"))
        ytd_display = format_ytd(r.get("YTD %"))

        table_rows += f"""
        <tr>
          <td>{ticker}</td>
          <td>${last_price:.2f}</td>
          <td>${prev_close:.2f}</td>
          <td>{ytd_display}</td>
        </tr>
        """

    if not table_rows:
        table_rows = """
        <tr>
          <td colspan="4">No data available. Check top10.csv on the server.</td>
        </tr>
        """

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8" />
      <title>Top 10 by YTD Performance</title>
      <style>
        body {{
          font-family: Arial, sans-serif;
          margin: 0;
          padding: 10px;
        }}
        h3 {{
          margin-top: 0;
        }}
        table {{
          border-collapse: collapse;
          width: 100%;
        }}
        th, td {{
          border: 1px solid #ddd;
          padding: 8px;
          font-size: 14px;
        }}
        th {{
          background-color: #002b5c;
          color: white;
          text-align: left;
        }}
        tr:nth-child(even) {{ background-color: #f9f9f9; }}
      </style>
    </head>
    <body>
      <h3>Top 10 by YTD Performance</h3>
      <table>
        <thead>
          <tr>
            <th>Ticker</th>
            <th>Last Price</th>
            <th>Prev Year Close</th>
            <th>YTD %</th>
          </tr>
        </thead>
        <tbody>
          {table_rows}
        </tbody>
      </table>
    </body>
    </html>
    """
    return render_template_string(html)

# For local testing; Azure uses gunicorn entry point
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
