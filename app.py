from flask import Flask, jsonify, render_template_string, request, abort
import csv
import os

app = Flask(__name__)

# Path to CSV (same folder as this file)
CSV_PATH = os.path.join(os.path.dirname(__file__), "top10.csv")

# Secret key for update endpoint (set in Azure Configuration)
UPDATE_KEY = os.environ.get("UPDATE_KEY", "")


def load_top10():
    """
    Read top10.csv.

    Handles two formats:
    1) Clean table: header row starts with 'Ticker'
    2) Your current export: title row, 'Last refreshed' columns, etc.
       -> we scan until we find a row whose first cell is 'Ticker'
    """
    rows = []
    if not os.path.exists(CSV_PATH):
        return rows

    with open(CSV_PATH, newline="") as f:
        reader = csv.reader(f)
        header_found = False
        headers = None

        for row in reader:
            # Skip empty rows
            if not row or all(not cell.strip() for cell in row):
                continue

            first = row[0].strip().lower()

            if not header_found:
                # Find the header row ('Ticker')
                if first == "ticker":
                    header_found = True
                    headers = row
                # keep scanning
                continue
            else:
                # After header: data rows
                if len(row) < 4:
                    continue

                ticker = row[0].strip()
                last_price = row[1].strip()
                prev_close = row[2].strip()
                ytd = row[3].strip()

                if not ticker:
                    continue

                rows.append({
                    "Ticker": ticker,
                    "Last Price": last_price,
                    "Prev Year Close": prev_close,
                    "YTD %": ytd,
                })

    return rows


def clean_money(value):
    """Turn '$355.22' or '1,017.78' into a float."""
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
      '53.22%'  -> 53.22%
      '53.22'   -> 53.22%
      '0.5322'  -> 53.22%
    """
    if value is None:
        return "0.00%"
    s = str(value).replace("%", "").strip()
    try:
        num = float(s)
    except ValueError:
        return "0.00%"
    if num <= 1:
        num *= 100
    return f"{num:.2f}%"


@app.route("/top10")
def top10_json():
    """Return data as JSON."""
    rows = load_top10()
    return jsonify(rows)


@app.route("/widget")
def top10_widget():
    """Return a simple HTML table for embedding."""
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


@app.route("/update_top10", methods=["POST"])
def update_top10():
    """
    Called by Power Automate.

    Expects:
      - URL:  /update_top10?key=YOUR_SECRET
      - Body: CSV text with a header row.
        (Either your current export, or a clean 4-column table)

    It overwrites top10.csv on disk.
    """
    # Simple shared-secret check
    if UPDATE_KEY:
        key = request.args.get("key", "")
        if key != UPDATE_KEY:
            abort(401)

    body = request.get_data(as_text=True)
    if not body.strip():
        abort(400, "Empty body")

    # Write CSV to disk
    with open(CSV_PATH, "w", newline="") as f:
        f.write(body)

    return "OK", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
