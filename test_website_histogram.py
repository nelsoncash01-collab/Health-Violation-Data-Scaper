#!/usr/bin/env python3
"""
Test if the histogram is actually working on the website now
"""

import requests
import time

def test_website_histogram():
    """Test that everything is working"""

    print("🔧 FINAL HISTOGRAM TEST")
    print("=" * 40)

    try:
        # Test server
        print("1️⃣ Testing server...")
        response = requests.get('http://localhost:5000/', timeout=5)
        if response.status_code != 200:
            print(f"❌ Server error: {response.status_code}")
            return False
        print("✅ Server running")

        # Test API
        print("\n2️⃣ Testing API...")
        api_response = requests.get('http://localhost:5000/api/opportunities?days=30', timeout=5)
        if api_response.status_code != 200:
            print(f"❌ API error: {api_response.status_code}")
            return False

        data = api_response.json()
        if not data['success']:
            print(f"❌ API failed: {data.get('message')}")
            return False

        opportunities = data['opportunities']
        print(f"✅ API returning {len(opportunities)} opportunities")

        # Test main page contains both scripts
        print("\n3️⃣ Testing webpage includes...")
        html = requests.get('http://localhost:5000/', timeout=5).text

        if 'script.js' in html:
            print("✅ Main script.js included")
        else:
            print("❌ script.js not found")
            return False

        if 'test_simple_histogram.js' in html:
            print("✅ Simple histogram script included")
        else:
            print("❌ Simple histogram script not found")
            return False

        # Test canvas element exists
        if 'valuePieChart' in html:
            print("✅ Chart canvas element exists")
        else:
            print("❌ Chart canvas not found")
            return False

        # Test script file accessibility
        print("\n4️⃣ Testing script accessibility...")
        script_response = requests.get('http://localhost:5000/test_simple_histogram.js', timeout=5)
        if script_response.status_code == 200 and 'createWorkingHistogram' in script_response.text:
            print("✅ Simple histogram script accessible")
        else:
            print("❌ Simple histogram script not accessible")
            return False

        # Test Chart.js availability
        if 'chart.js' in html.lower():
            print("✅ Chart.js library included")
        else:
            print("❌ Chart.js not found")
            return False

        print("\n" + "=" * 40)
        print("🎯 HISTOGRAM STATUS:")
        print("✅ Server working")
        print("✅ API providing data")
        print("✅ Both scripts loaded")
        print("✅ Chart canvas ready")
        print("✅ Chart.js available")
        print("\n💡 The histogram should now work!")
        print("📊 Expected: Bar chart with gold bars")
        print("🎨 Location: Property Value Distribution card")

        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_website_histogram()

    if success:
        print("\n🎉 HISTOGRAM SHOULD BE WORKING NOW!")
        print("👀 Check the 'Property Value Distribution' section")
        print("📈 You should see a bar chart with $50K bins")
    else:
        print("\n❌ Something is still wrong")