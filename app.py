import csv
import os
import requests
from flask import Flask, render_template, request, jsonify, send_file, make_response

app = Flask(__name__)

def fetch_data(location, query, user_agent):
    payload = {
        'source': 'google_ads',
        'geo_location': location,
        'domain': 'com',
        'locale': 'en-us',
        'user_agent_type': user_agent,
        'query': query,
        'parse': True,
        'context': [{'key': 'results_language', 'value': 'en'}]
    }

    response = requests.post(
        'https://realtime.oxylabs.io/v1/queries',
        auth=('al001_ucZmV', 'YeJ85Qj+wQMbzUz'),
        json=payload,
    )

    if response.status_code == 200:
        try:
            data = response.json()
            safe_location = location.replace(",", "_").replace(" ", "_")
            file_name = f"oxylabs_results_{query}_{safe_location}.csv"
            file_path = os.path.join(os.getcwd(), file_name)

            paid_found = False

            with open(file_path, 'w', newline='', encoding='utf-8') as csv_file:
                fieldnames = ["query", "location", "user_agent", "result_type", "pos", "title", "url", "__url_shown", "desc"]
                writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
                writer.writeheader()

                for result in data.get("results", []):
                    content = result.get("content", {})
                    search_results = content.get("results", {})

                    for organic in search_results.get("organic", []):
                        writer.writerow({
                            "query": query,
                            "location": location,
                            "user_agent": user_agent,
                            "result_type": "organic",
                            "pos": organic.get("pos", ""),
                            "title": organic.get("title", ""),
                            "url": organic.get("url", ""),
                            "__url_shown": organic.get("url_shown", ""),
                            "desc": organic.get("desc", "")
                        })

                    for paid in search_results.get("paid", []):
                        paid_found = True
                        writer.writerow({
                            "query": query,
                            "location": location,
                            "user_agent": user_agent,
                            "result_type": "paid",
                            "pos": paid.get("pos", ""),
                            "title": paid.get("title", ""),
                            "url": paid.get("url", ""),  
                            "__url_shown": paid.get("url_shown", ""),
                            "desc": paid.get("desc", "")
                        })

            return file_path, paid_found

        except Exception as e:
            print(f"Error processing response: {e}")
            return None

    return None


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit():
    data = request.json
    location = data.get("location")
    query = data.get("query")
    user_agent = data.get("userAgent", "desktop")

    if not location or not query:
        return jsonify({"success": False, "message": "Location and query are required"})

    result = fetch_data(location, query, user_agent)
    if result:
        file_path, paid_found = result
        if file_path and os.path.exists(file_path):
            response = make_response(send_file(file_path, as_attachment=True, mimetype="text/csv"))
            response.headers["X-Paid-Found"] = "true" if paid_found else "false"
            return response
    return jsonify({"success": False, "message": "Failed to fetch or format data"})

if __name__ == '__main__':
    app.run(debug=True)
