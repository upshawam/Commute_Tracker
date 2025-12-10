#!/usr/bin/env python3
"""
Commute Tracker - A smart commute tracking application
Monitors commute times and suggests optimal departure times
"""

import os
from datetime import datetime
from typing import List, Dict, Optional
import sqlite3
import time
import schedule
import googlemaps
from collections import defaultdict
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class CommuteTracker:
    """Main class for tracking commute times and providing recommendations"""
    
    def __init__(self, db_path: str = "commute_data.db", api_key: Optional[str] = None):
        """
        Initialize the Commute Tracker
        
        Args:
            db_path: Path to SQLite database file
            api_key: Google Maps API key (can also be set via GOOGLE_MAPS_API_KEY env var)
        """
        self.db_path = db_path
        self.api_key = api_key or os.environ.get('GOOGLE_MAPS_API_KEY')
        self.gmaps = None
        
        if self.api_key:
            self.gmaps = googlemaps.Client(key=self.api_key)
        
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Table for storing addresses
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS addresses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                label TEXT NOT NULL,
                address TEXT NOT NULL,
                type TEXT NOT NULL CHECK(type IN ('home', 'work')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Table for storing commute logs
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS commute_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                origin_id INTEGER NOT NULL,
                destination_id INTEGER NOT NULL,
                duration_seconds INTEGER NOT NULL,
                duration_in_traffic_seconds INTEGER,
                distance_meters INTEGER NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                day_of_week INTEGER NOT NULL,
                hour INTEGER NOT NULL,
                FOREIGN KEY (origin_id) REFERENCES addresses(id),
                FOREIGN KEY (destination_id) REFERENCES addresses(id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_address(self, label: str, address: str, addr_type: str) -> int:
        """
        Add a new address (home or work location)
        
        Args:
            label: Descriptive label (e.g., "Main Office", "Home")
            address: Full address string
            addr_type: Type of address ("home" or "work")
        
        Returns:
            ID of the newly created address
        """
        if addr_type not in ['home', 'work']:
            raise ValueError("Address type must be 'home' or 'work'")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            'INSERT INTO addresses (label, address, type) VALUES (?, ?, ?)',
            (label, address, addr_type)
        )
        
        address_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return address_id
    
    def list_addresses(self, addr_type: Optional[str] = None) -> List[Dict]:
        """
        List all addresses or filter by type
        
        Args:
            addr_type: Optional filter by "home" or "work"
        
        Returns:
            List of address dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if addr_type:
            cursor.execute(
                'SELECT id, label, address, type FROM addresses WHERE type = ?',
                (addr_type,)
            )
        else:
            cursor.execute('SELECT id, label, address, type FROM addresses')
        
        addresses = []
        for row in cursor.fetchall():
            addresses.append({
                'id': row[0],
                'label': row[1],
                'address': row[2],
                'type': row[3]
            })
        
        conn.close()
        return addresses
    
    def delete_address(self, address_id: int) -> bool:
        """
        Delete an address by ID
        
        Returns:
            True if address was deleted, False if it didn't exist
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if address exists
        cursor.execute('SELECT id FROM addresses WHERE id = ?', (address_id,))
        if not cursor.fetchone():
            conn.close()
            return False
        
        cursor.execute('DELETE FROM addresses WHERE id = ?', (address_id,))
        conn.commit()
        conn.close()
        return True
    
    def poll_commute_times(self):
        """
        Poll current commute times for all home-work address pairs
        Stores results in the database
        """
        if not self.gmaps:
            print("Warning: Google Maps API key not configured. Cannot poll commute times.")
            return
        
        homes = self.list_addresses('home')
        workplaces = self.list_addresses('work')
        
        if not homes or not workplaces:
            print("No home or work addresses configured yet.")
            return
        
        now = datetime.now()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Poll commute times for all combinations
        for home in homes:
            for work in workplaces:
                try:
                    # Get directions with traffic
                    result = self.gmaps.directions(
                        home['address'],
                        work['address'],
                        mode="driving",
                        departure_time=now
                    )
                    
                    if result:
                        leg = result[0]['legs'][0]
                        duration = leg['duration']['value']  # seconds
                        duration_in_traffic = leg.get('duration_in_traffic', {}).get('value', duration)
                        distance = leg['distance']['value']  # meters
                        
                        # Store in database
                        cursor.execute('''
                            INSERT INTO commute_logs 
                            (origin_id, destination_id, duration_seconds, 
                             duration_in_traffic_seconds, distance_meters, 
                             day_of_week, hour)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            home['id'], work['id'], duration, duration_in_traffic,
                            distance, now.weekday(), now.hour
                        ))
                        
                        print(f"Logged: {home['label']} → {work['label']}: "
                              f"{duration_in_traffic // 60} min")
                
                except Exception as e:
                    print(f"Error polling {home['label']} → {work['label']}: {e}")
        
        conn.commit()
        conn.close()
    
    def get_current_commute_time(self, origin_id: int, destination_id: int) -> Optional[Dict]:
        """
        Get the current commute time for a specific route
        
        Returns:
            Dictionary with duration information or None
        """
        if not self.gmaps:
            return None
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT address FROM addresses WHERE id = ?', (origin_id,))
        origin = cursor.fetchone()
        cursor.execute('SELECT address FROM addresses WHERE id = ?', (destination_id,))
        destination = cursor.fetchone()
        
        conn.close()
        
        if not origin or not destination:
            return None
        
        try:
            result = self.gmaps.directions(
                origin[0],
                destination[0],
                mode="driving",
                departure_time=datetime.now()
            )
            
            if result:
                leg = result[0]['legs'][0]
                return {
                    'duration_minutes': leg['duration']['value'] // 60,
                    'duration_in_traffic_minutes': leg.get('duration_in_traffic', {}).get('value', 0) // 60,
                    'distance_km': leg['distance']['value'] / 1000
                }
        except Exception as e:
            print(f"Error getting current commute time: {e}")
        
        return None
    
    def get_optimal_departure_times(self, origin_id: int, destination_id: int, 
                                   target_arrival: str = "09:00") -> List[Dict]:
        """
        Analyze historical data to find optimal departure times
        
        Args:
            origin_id: Starting address ID
            destination_id: Destination address ID
            target_arrival: Target arrival time (HH:MM format)
        
        Returns:
            List of recommendations by day of week
        
        Raises:
            ValueError: If target_arrival is not in HH:MM format
        """
        # Validate target_arrival format
        try:
            parts = target_arrival.split(':')
            if len(parts) != 2:
                raise ValueError
            target_hour, target_minute = int(parts[0]), int(parts[1])
            if not (0 <= target_hour <= 23 and 0 <= target_minute <= 59):
                raise ValueError
        except (ValueError, AttributeError):
            raise ValueError(f"Invalid time format '{target_arrival}'. Expected HH:MM (e.g., 09:00)")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get historical data for this route
        cursor.execute('''
            SELECT day_of_week, hour, 
                   AVG(duration_in_traffic_seconds) as avg_duration,
                   COUNT(*) as sample_count
            FROM commute_logs
            WHERE origin_id = ? AND destination_id = ?
            GROUP BY day_of_week, hour
            HAVING sample_count >= 3
            ORDER BY day_of_week, hour
        ''', (origin_id, destination_id))
        
        data = cursor.fetchall()
        conn.close()
        
        if not data:
            return []
        target_minutes = target_hour * 60 + target_minute
        
        # Organize by day of week
        by_day = defaultdict(list)
        for row in data:
            day, hour, avg_duration, count = row
            by_day[day].append({
                'hour': hour,
                'avg_duration_minutes': avg_duration / 60,
                'sample_count': count
            })
        
        # Find optimal departure times for each day
        recommendations = []
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        for day in range(7):
            if day not in by_day:
                continue
            
            # Find the hour with minimum average duration
            best_hour = min(by_day[day], key=lambda x: x['avg_duration_minutes'])
            
            # Calculate suggested departure time
            departure_minutes = target_minutes - int(best_hour['avg_duration_minutes'])
            if departure_minutes < 0:
                departure_minutes += 24 * 60
            
            departure_hour = departure_minutes // 60
            departure_min = departure_minutes % 60
            
            recommendations.append({
                'day': day_names[day],
                'optimal_departure': f"{departure_hour:02d}:{departure_min:02d}",
                'expected_duration_minutes': int(best_hour['avg_duration_minutes']),
                'data_points': best_hour['sample_count']
            })
        
        return recommendations
    
    def get_statistics(self, origin_id: int, destination_id: int) -> Dict:
        """
        Get statistical summary for a route
        
        Returns:
            Dictionary with min, max, avg commute times
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                MIN(duration_in_traffic_seconds) / 60 as min_minutes,
                MAX(duration_in_traffic_seconds) / 60 as max_minutes,
                AVG(duration_in_traffic_seconds) / 60 as avg_minutes,
                COUNT(*) as total_logs
            FROM commute_logs
            WHERE origin_id = ? AND destination_id = ?
        ''', (origin_id, destination_id))
        
        row = cursor.fetchone()
        conn.close()
        
        if row and row[3] > 0:
            return {
                'min_minutes': int(row[0]),
                'max_minutes': int(row[1]),
                'avg_minutes': int(row[2]),
                'total_logs': row[3]
            }
        
        return {'min_minutes': 0, 'max_minutes': 0, 'avg_minutes': 0, 'total_logs': 0}


def main():
    """Main entry point for CLI interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Commute Tracker - Smart commute monitoring')
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Add address command
    add_parser = subparsers.add_parser('add', help='Add a new address')
    add_parser.add_argument('type', choices=['home', 'work'], help='Address type')
    add_parser.add_argument('label', help='Label for the address')
    add_parser.add_argument('address', help='Full address')
    
    # List addresses command
    list_parser = subparsers.add_parser('list', help='List addresses')
    list_parser.add_argument('--type', choices=['home', 'work'], help='Filter by type')
    
    # Delete address command
    delete_parser = subparsers.add_parser('delete', help='Delete an address')
    delete_parser.add_argument('id', type=int, help='Address ID')
    
    # Poll command
    poll_parser = subparsers.add_parser('poll', help='Poll current commute times')
    
    # Start monitoring command
    start_parser = subparsers.add_parser('monitor', help='Start continuous monitoring')
    start_parser.add_argument('--interval', type=int, default=30, 
                            help='Polling interval in minutes (default: 30)')
    
    # Get recommendations command
    recommend_parser = subparsers.add_parser('recommend', help='Get optimal departure times')
    recommend_parser.add_argument('origin_id', type=int, help='Origin address ID')
    recommend_parser.add_argument('destination_id', type=int, help='Destination address ID')
    recommend_parser.add_argument('--arrival', default='09:00', 
                                 help='Target arrival time (HH:MM)')
    
    # Statistics command
    stats_parser = subparsers.add_parser('stats', help='Get route statistics')
    stats_parser.add_argument('origin_id', type=int, help='Origin address ID')
    stats_parser.add_argument('destination_id', type=int, help='Destination address ID')
    
    # Current commute command
    current_parser = subparsers.add_parser('current', help='Get current commute time')
    current_parser.add_argument('origin_id', type=int, help='Origin address ID')
    current_parser.add_argument('destination_id', type=int, help='Destination address ID')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    tracker = CommuteTracker()
    
    if args.command == 'add':
        address_id = tracker.add_address(args.label, args.address, args.type)
        print(f"Added {args.type} address '{args.label}' with ID {address_id}")
    
    elif args.command == 'list':
        addresses = tracker.list_addresses(args.type)
        if not addresses:
            print("No addresses found")
        else:
            print(f"\n{'ID':<5} {'Type':<10} {'Label':<20} Address")
            print("-" * 80)
            for addr in addresses:
                print(f"{addr['id']:<5} {addr['type']:<10} {addr['label']:<20} {addr['address']}")
    
    elif args.command == 'delete':
        if tracker.delete_address(args.id):
            print(f"Deleted address with ID {args.id}")
        else:
            print(f"Error: Address with ID {args.id} not found")
    
    elif args.command == 'poll':
        print("Polling current commute times...")
        tracker.poll_commute_times()
    
    elif args.command == 'monitor':
        print(f"Starting continuous monitoring (polling every {args.interval} minutes)")
        print("Press Ctrl+C to stop")
        
        # Schedule periodic polling
        schedule.every(args.interval).minutes.do(tracker.poll_commute_times)
        
        # Run immediately once
        tracker.poll_commute_times()
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)
        except KeyboardInterrupt:
            print("\nMonitoring stopped")
    
    elif args.command == 'recommend':
        try:
            recommendations = tracker.get_optimal_departure_times(
                args.origin_id, args.destination_id, args.arrival
            )
            
            if not recommendations:
                print("Not enough data yet. Run 'monitor' to collect commute data.")
            else:
                print(f"\nOptimal departure times to arrive by {args.arrival}:")
                print(f"\n{'Day':<12} {'Depart':<10} {'Duration':<12} Data Points")
                print("-" * 60)
                for rec in recommendations:
                    print(f"{rec['day']:<12} {rec['optimal_departure']:<10} "
                          f"{rec['expected_duration_minutes']} min{'':<7} {rec['data_points']}")
        except ValueError as e:
            print(f"Error: {e}")
    
    elif args.command == 'stats':
        stats = tracker.get_statistics(args.origin_id, args.destination_id)
        
        if stats['total_logs'] == 0:
            print("No data available for this route yet.")
        else:
            print(f"\nRoute Statistics:")
            print(f"  Total data points: {stats['total_logs']}")
            print(f"  Minimum time:      {stats['min_minutes']} minutes")
            print(f"  Average time:      {stats['avg_minutes']} minutes")
            print(f"  Maximum time:      {stats['max_minutes']} minutes")
    
    elif args.command == 'current':
        result = tracker.get_current_commute_time(args.origin_id, args.destination_id)
        
        if result:
            print(f"\nCurrent commute time:")
            print(f"  Without traffic: {result['duration_minutes']} minutes")
            print(f"  With traffic:    {result['duration_in_traffic_minutes']} minutes")
            print(f"  Distance:        {result['distance_km']:.1f} km")
        else:
            print("Could not get current commute time. Check API key configuration.")


if __name__ == '__main__':
    main()
