#!/bin/bash
# Example usage script for Commute Tracker

echo "=== Commute Tracker Example Usage ==="
echo ""

# Step 1: Add addresses
echo "1. Adding home and work addresses..."
python3 commute_tracker.py add home "My Home" "1600 Amphitheatre Parkway, Mountain View, CA"
python3 commute_tracker.py add work "Google Office" "1 Infinite Loop, Cupertino, CA"
echo ""

# Step 2: List addresses
echo "2. Listing all addresses..."
python3 commute_tracker.py list
echo ""

# Step 3: Check current commute (requires API key)
echo "3. Checking current commute time..."
echo "   (Note: Requires GOOGLE_MAPS_API_KEY environment variable)"
python3 commute_tracker.py current 1 2
echo ""

# Step 4: View statistics
echo "4. Viewing route statistics..."
python3 commute_tracker.py stats 1 2
echo ""

# Step 5: Get recommendations
echo "5. Getting optimal departure time recommendations..."
python3 commute_tracker.py recommend 1 2 --arrival 09:00
echo ""

echo "=== To start continuous monitoring ==="
echo "Run: python3 commute_tracker.py monitor --interval 30"
echo ""
echo "This will poll commute times every 30 minutes and build historical data."
echo "After collecting data for several days, the 'recommend' command will provide"
echo "data-driven suggestions for optimal departure times."
