from flask import Flask, jsonify, render_template_string
import csv
import os

app = Flask(__name__)

# Path to CSV in same folder as this file
CSV_PATH = os.path.join(os.path.dirname(__file__), "top10.csv")

def load_top10():
    with open(CSV_PATH, newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    return rows

@app.route("/top10")
def top10_json():
    """Return data as JSON"""
    return jsonify(load_top10())

@app.route("/widget")
def top10_widget():
    """Return a simple HTML table for embedding"""
    rows = load_top10()

    table_rows = ""
    for r in rows:
        table_rows += f"""
        <tr>
          <td>{r['Ticker']}</td>
          <td>${float(r['Last Price']):.2f}</td>
          <td>${float(r['Prev Year Close']):.2f}</td>
          <td>{float(r['YTD %'])*100:.2f}%</td>
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

# For local testing; Azure will serve with gunicorn
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
