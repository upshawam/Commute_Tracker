# Commute Tracker

A smart commute tracking application that monitors your daily commute times and learns the optimal times to leave for work or home. The application continuously polls Google Maps for real-time traffic data, stores historical commute information, and provides intelligent recommendations based on patterns it discovers.

## Features

- **Multiple Address Support**: Add multiple home and work locations
- **Continuous Monitoring**: Automatically polls commute times throughout the day
- **Smart Analytics**: Analyzes historical data to identify traffic patterns
- **Optimal Departure Times**: Recommends the best times to leave based on your desired arrival time
- **Real-time Updates**: Get current commute times with live traffic data
- **Statistical Insights**: View min, max, and average commute times for your routes

## Installation

1. Clone the repository:
```bash
git clone https://github.com/upshawam/Commute_Tracker.git
cd Commute_Tracker
```

2. Install required dependencies:
```bash
pip install -r requirements.txt
```

3. Set up your Google Maps API key:
   - Get an API key from [Google Maps Platform](https://developers.google.com/maps/documentation/directions/get-api-key)
   - Copy `.env.example` to `.env` and add your API key:
   ```bash
   cp .env.example .env
   # Edit .env and add your API key
   ```

   Or set it as an environment variable:
   ```bash
   export GOOGLE_MAPS_API_KEY=your_api_key_here
   ```

## Usage

### Add Addresses

First, add your home and work addresses:

```bash
# Add home address
python commute_tracker.py add home "Home" "123 Main St, San Francisco, CA"

# Add work address
python commute_tracker.py add work "Office" "456 Market St, San Francisco, CA"
```

### List Addresses

View all configured addresses:

```bash
python commute_tracker.py list

# Or filter by type
python commute_tracker.py list --type home
python commute_tracker.py list --type work
```

### Start Monitoring

Begin continuous monitoring of your commute times:

```bash
# Poll every 30 minutes (default)
python commute_tracker.py monitor

# Poll every 15 minutes
python commute_tracker.py monitor --interval 15
```

The application will poll all home-work combinations and log the data. Leave this running throughout the day to collect comprehensive data.

### Get Current Commute Time

Check the current commute time for a specific route:

```bash
python commute_tracker.py current 1 2
```
(Where 1 is your home ID and 2 is your work ID)

### Get Recommendations

After collecting data for a few days, get optimal departure time recommendations:

```bash
# Get recommendations for arriving by 9:00 AM
python commute_tracker.py recommend 1 2 --arrival 09:00

# Get recommendations for arriving by 5:30 PM
python commute_tracker.py recommend 2 1 --arrival 17:30
```

### View Statistics

See statistical summary of your commute times:

```bash
python commute_tracker.py stats 1 2
```

### Delete Address

Remove an address you no longer need:

```bash
python commute_tracker.py delete 1
```

## How It Works

1. **Data Collection**: The application uses the Google Maps Directions API to fetch real-time commute times with traffic data
2. **Storage**: All data is stored in a local SQLite database (`commute_data.db`)
3. **Pattern Analysis**: The system analyzes historical data by day of week and hour to identify traffic patterns
4. **Recommendations**: Based on collected data, it calculates optimal departure times to reach your destination at your desired time

## Data Privacy

All your data is stored locally in the `commute_data.db` file. No information is sent to any third-party services except for the Google Maps API queries needed to fetch commute times.

## Requirements

- Python 3.6+
- Google Maps API key with Directions API enabled
- Internet connection for API requests

## Tips for Best Results

- Run the monitor command during your typical commuting hours (e.g., 6 AM - 10 AM for morning, 3 PM - 7 PM for evening)
- Collect data for at least a week to get reliable patterns
- The more data collected, the better the recommendations become
- Consider running the monitor as a background service or cron job

## API Costs

The Google Maps Directions API has a free tier that includes $200 credit per month. Each direction request costs approximately $0.005. Monitoring every 30 minutes for 12 hours a day would cost roughly $3-4 per month.

## License

MIT License - Feel free to use and modify as needed.
