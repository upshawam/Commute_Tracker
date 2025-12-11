# Quick Start Guide

## 1. Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Set up API key
cp .env.example .env
# Edit .env and add your Google Maps API key
```

## 2. Add Your Addresses

```bash
# Add your home address
python3 commute_tracker.py add home "Home" "Your full home address"

# Add your work address
python3 commute_tracker.py add work "Office" "Your full work address"

# Verify addresses were added
python3 commute_tracker.py list
```

## 3. Start Collecting Data

```bash
# Start monitoring (polls every 30 minutes by default)
python3 commute_tracker.py monitor

# Or specify a different interval (in minutes)
python3 commute_tracker.py monitor --interval 15
```

**Tip:** Run this command in a screen session or as a background service to collect data continuously throughout the day.

## 4. View Your Data

After collecting data for a few days:

```bash
# Get current commute time
python3 commute_tracker.py current 1 2

# View statistics
python3 commute_tracker.py stats 1 2

# Get optimal departure time recommendations
python3 commute_tracker.py recommend 1 2 --arrival 09:00
```

## 5. Understanding the Results

The `recommend` command analyzes your historical data to suggest when to leave. For example:

```
Optimal departure times to arrive by 09:00:

Day          Depart     Duration     Data Points
------------------------------------------------------------
Monday       08:15      35 min       12
Tuesday      08:10      40 min       15
Wednesday    08:05      45 min       18
```

This tells you:
- On Monday, leave at 8:15 AM for a ~35 minute commute
- On Tuesday, leave at 8:10 AM for a ~40 minute commute
- On Wednesday, leave at 8:05 AM for a ~45 minute commute

The more data points collected, the more accurate the recommendations become.

## Best Practices

1. **Collect data during commute hours**: Run monitoring during typical commute times (e.g., 6 AM - 10 AM and 3 PM - 7 PM)

2. **Wait for enough data**: The system requires at least 3 data points per hour to make recommendations. Collect data for at least one week for reliable results.

3. **Check regularly**: Use the `current` command before leaving to see real-time conditions.

4. **Multiple routes**: Add multiple work locations if you commute to different offices on different days.

## Troubleshooting

- **"Warning: Google Maps API key not configured"**: Set the `GOOGLE_MAPS_API_KEY` environment variable
- **"Not enough data yet"**: Keep the monitor running longer to collect more data points
- **"Could not get current commute time"**: Verify your API key is valid and the Directions API is enabled

## Running as a Service

### Linux (systemd)

Create a service file at `/etc/systemd/system/commute-tracker.service`:

```ini
[Unit]
Description=Commute Tracker Monitor
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/path/to/Commute_Tracker
Environment="GOOGLE_MAPS_API_KEY=your_key_here"
ExecStart=/usr/bin/python3 /path/to/Commute_Tracker/commute_tracker.py monitor --interval 30
Restart=always

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl daemon-reload
sudo systemctl enable commute-tracker
sudo systemctl start commute-tracker
```

### macOS (launchd)

Create a plist file at `~/Library/LaunchAgents/com.commute-tracker.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.commute-tracker</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/python3</string>
        <string>/path/to/commute_tracker.py</string>
        <string>monitor</string>
        <string>--interval</string>
        <string>30</string>
    </array>
    <key>EnvironmentVariables</key>
    <dict>
        <key>GOOGLE_MAPS_API_KEY</key>
        <string>your_key_here</string>
    </dict>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
```

Then:
```bash
launchctl load ~/Library/LaunchAgents/com.commute-tracker.plist
```
