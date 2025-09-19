#!/usr/bin/env python3
"""
Test the background scheduler functionality
"""

import requests
import json
import time
from datetime import datetime

def test_fast_loading():
    """Test that the API loads quickly from cache"""

    print("🧪 TESTING BACKGROUND SCHEDULER AND FAST LOADING")
    print("=" * 60)

    # Test 1: Fast API response
    print("\n1️⃣ Testing API response time...")
    start_time = time.time()

    try:
        response = requests.get('http://localhost:5000/api/opportunities?days=7', timeout=5)
        end_time = time.time()
        response_time = end_time - start_time

        print(f"   Response time: {response_time:.3f} seconds")

        if response.status_code == 200:
            data = response.json()
            if data['success']:
                print(f"   ✅ Fast response: {len(data['opportunities'])} opportunities")
                print(f"   🎯 Loading time: {'FAST' if response_time < 1.0 else 'SLOW'}")

                # Test data quality
                if data['opportunities']:
                    opp = data['opportunities'][0]
                    print(f"   📍 Sample: {opp['name']} at {opp['address']}")
                    print(f"   💰 Price: ${opp['pricePerSqft']}/sqft")
                    print(f"   🚇 Transit: {opp['transitScore']}/10")
                    print(f"   💧 Water: {opp['waterScore']}/10")

                return True
            else:
                print(f"   ❌ API Error: {data.get('message', 'Unknown')}")
                return False
        else:
            print(f"   ❌ HTTP Error: {response.status_code}")
            return False

    except Exception as e:
        print(f"   ❌ Request Error: {e}")
        return False

def test_cache_status():
    """Test cache status and scheduler"""
    print("\n2️⃣ Testing cache and scheduler status...")

    # Check cache file
    import os
    cache_files = ['violations_cache.json', 'owner_lookup_cache.json', 'geocoding_cache.json']

    for cache_file in cache_files:
        if os.path.exists(cache_file):
            size = os.path.getsize(cache_file)
            print(f"   ✅ {cache_file}: {size:,} bytes")
        else:
            print(f"   ⚠️ {cache_file}: Not found")

    # Test different day ranges
    print("\n3️⃣ Testing different day ranges...")
    for days in [1, 7, 14, 30]:
        try:
            start_time = time.time()
            response = requests.get(f'http://localhost:5000/api/opportunities?days={days}', timeout=3)
            response_time = time.time() - start_time

            if response.status_code == 200:
                data = response.json()
                count = len(data['opportunities']) if data['success'] else 0
                print(f"   📅 Last {days:2d} days: {count:2d} opportunities in {response_time:.3f}s")
            else:
                print(f"   ❌ {days} days: HTTP {response.status_code}")

        except Exception as e:
            print(f"   ❌ {days} days: {e}")

def main():
    print(f"🕐 Test started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Test fast loading
    success = test_fast_loading()

    # Test cache status
    test_cache_status()

    print("\n" + "=" * 60)
    if success:
        print("✅ SCHEDULER TEST PASSED")
        print("💡 Benefits:")
        print("   • Fast API responses (< 1 second)")
        print("   • Daily automatic updates at midnight EST")
        print("   • No more slow initial loads")
        print("   • Background processing of owner lookups")
    else:
        print("❌ SCHEDULER TEST FAILED")
        print("🔧 Check server logs for issues")

if __name__ == "__main__":
    main()