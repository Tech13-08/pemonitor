from flask import Flask, render_template, jsonify, request
import sensors

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/data')
def api_data():
    data = sensors.parse_sensors()
    sensors.check_for_alarms(data)
    return jsonify(data)

@app.route('/logs')
def view_logs():
    import pandas as pd
    import os
    
    if request.args.get('refresh'):
        try:
            if not os.path.exists(sensors.LOG_FILE) or os.stat(sensors.LOG_FILE).st_size == 0:
                return "<div class='empty-state'>🛡️ No critical events recorded.</div>"
            df = pd.read_csv(sensors.LOG_FILE).iloc[::-1].head(100)
            return df.to_html(index=False, classes='log-table')
        except: return "Error loading CSV"
        
    return render_template('logs.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)