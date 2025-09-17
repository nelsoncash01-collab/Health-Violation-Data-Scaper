#!/usr/bin/env python3
"""
Test script to compare Colab notebook logic vs Flask app results
"""

import requests
import pandas as pd
from datetime import datetime, timedelta
import json

class CoLabTestScraper:
    def __init__(self):
        self.api_base_url = "https://data.cityofnewyork.us/resource/43nn-pn8j.json"

    def get_closed_restaurants_colab_style(self, days_back=30, limit=1000):
        """Exact logic from your Colab notebook"""
        try:
            print(f"🎯 COLAB STYLE: Using exactly {days_back} days lookback period")
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)
            start_date_str = start_date.strftime('%Y-%m-%dT%H:%M:%S.000')

            params = {
                '$limit': limit,
                '$where': f"inspection_date >= '{start_date_str}' AND (action LIKE '%Closed%' OR action LIKE '%Suspended%')",
                '$order': 'inspection_date DESC'
            }

            print(f"📅 Searching from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')} ({days_back} days)")
            print(f"🔍 API Query: inspection_date >= '{start_date_str}'")
            print(f"🔍 Query params: {params}")

            response = requests.get(self.api_base_url, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()
            print(f"✅ COLAB STYLE: Retrieved {len(data)} records for the selected {days_back} day period")
            return data

        except Exception as e:
            print(f"❌ Error fetching data: {e}")
            return []

def test_flask_api(days=30):
    """Test the Flask API"""
    print(f"\n🌐 TESTING FLASK API for {days} days:")
    try:
        response = requests.get(f"http://localhost:5000/api/opportunities?days={days}")
        data = response.json()

        if data['success']:
            print(f"✅ Flask API: {len(data['opportunities'])} opportunities")
            print(f"📊 Flask message: {data['message']}")
        else:
            print(f"❌ Flask API failed: {data['message']}")

        return data
    except Exception as e:
        print(f"❌ Flask API error: {e}")
        return {}

def compare_results():
    """Compare both approaches"""
    print("=" * 80)
    print("🔍 COMPARING COLAB NOTEBOOK LOGIC VS FLASK APP")
    print("=" * 80)

    # Test Colab style
    colab_scraper = CoLabTestScraper()
    colab_raw_data = colab_scraper.get_closed_restaurants_colab_style(days_back=30, limit=1000)

    # Group by restaurant like in Colab
    restaurant_groups = {}
    for record in colab_raw_data:
        try:
            restaurant_name = record.get('dba', '').strip()
            action = record.get('action', '').strip()

            if (restaurant_name and action and
                ('closed' in action.lower() or 'suspended' in action.lower())):

                key = f"{restaurant_name}|{record.get('building', '')} {record.get('street', '')}|{record.get('camis', '')}"

                if key not in restaurant_groups:
                    restaurant_groups[key] = {
                        'name': restaurant_name,
                        'address': f"{record.get('building', '')} {record.get('street', '')}".strip(),
                        'borough': record.get('boro', '').strip(),
                        'inspection_date': record.get('inspection_date', ''),
                        'action': action,
                    }
        except Exception as e:
            continue

    colab_unique_restaurants = len(restaurant_groups)
    print(f"🎯 COLAB LOGIC: {colab_unique_restaurants} unique closed/suspended restaurants")

    # Test Flask API
    flask_data = test_flask_api(30)
    flask_count = len(flask_data.get('opportunities', []))

    print(f"\n📊 COMPARISON RESULTS:")
    print(f"   Colab Logic: {colab_unique_restaurants} restaurants")
    print(f"   Flask API:   {flask_count} restaurants")
    print(f"   Difference:  {colab_unique_restaurants - flask_count}")

    if colab_unique_restaurants != flask_count:
        print(f"\n⚠️  MISMATCH DETECTED!")
        print(f"   Raw records from API: {len(colab_raw_data)}")
        print(f"   After grouping: {colab_unique_restaurants}")
        print(f"   Flask result: {flask_count}")

        # Show some sample data
        print(f"\n📋 Sample raw records from Colab query:")
        for i, record in enumerate(colab_raw_data[:5]):
            print(f"  {i+1}. {record.get('dba', 'NO_NAME')} - {record.get('action', 'NO_ACTION')} - {record.get('inspection_date', '')}")

    return colab_unique_restaurants, flask_count

if __name__ == "__main__":
    compare_results()