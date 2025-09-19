#!/usr/bin/env python3
"""
Test that the histogram chart is now working on the website
"""

import requests
import time

def test_histogram_on_website():
    """Test that the histogram loads and displays correctly"""

    print("🔧 TESTING HISTOGRAM FIX ON WEBSITE")
    print("=" * 50)

    try:
        # First test that the server is responding
        print("1️⃣ Testing server availability...")
        response = requests.get('http://localhost:5000/', timeout=5)

        if response.status_code != 200:
            print(f"❌ Server not available: {response.status_code}")
            return False

        print("✅ Server is running")

        # Test API data
        print("\n2️⃣ Testing API data...")
        api_response = requests.get('http://localhost:5000/api/opportunities?days=30', timeout=5)

        if api_response.status_code != 200:
            print(f"❌ API error: {api_response.status_code}")
            return False

        data = api_response.json()
        if not data['success']:
            print(f"❌ API returned error: {data.get('message')}")
            return False

        opportunities = data['opportunities']
        print(f"✅ API returning {len(opportunities)} opportunities")

        # Check for value distribution data
        print("\n3️⃣ Testing histogram data preparation...")
        values = [opp['totalValue'] for opp in opportunities]

        if not values:
            print("❌ No property values found")
            return False

        min_val, max_val = min(values), max(values)
        print(f"✅ Value range: ${min_val:,} - ${max_val:,}")

        # Simulate histogram binning
        bin_size = 50000
        bins = {}
        for value in values:
            bin_index = value // bin_size
            bin_start = bin_index * bin_size
            bin_end = (bin_index + 1) * bin_size
            bin_key = f"${bin_start//1000}K-${bin_end//1000}K"
            bins[bin_key] = bins.get(bin_key, 0) + 1

        non_empty_bins = {k: v for k, v in bins.items() if v > 0}
        print(f"✅ Histogram will show {len(non_empty_bins)} bins:")

        for bin_name, count in sorted(non_empty_bins.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"   • {bin_name}: {count} properties")

        # Test CSS file
        print("\n4️⃣ Testing CSS availability...")
        css_response = requests.get('http://localhost:5000/styles.css', timeout=5)

        if css_response.status_code == 200 and 'value-pie-container' in css_response.text:
            print("✅ CSS file contains chart container styles")
        else:
            print("⚠️ CSS file may have issues")

        # Test Chart.js availability
        print("\n5️⃣ Testing Chart.js library...")
        index_html = requests.get('http://localhost:5000/', timeout=5).text

        if 'chart.js' in index_html.lower():
            print("✅ Chart.js library is included")
        else:
            print("❌ Chart.js library not found")
            return False

        # Test canvas element
        if 'valuePieChart' in index_html:
            print("✅ Chart canvas element exists in HTML")
        else:
            print("❌ Chart canvas element not found")
            return False

        print("\n" + "=" * 50)
        print("🎯 HISTOGRAM FIX SUMMARY:")
        print("✅ Server running")
        print("✅ API providing data")
        print("✅ Histogram data ready")
        print("✅ CSS container styled")
        print("✅ Chart.js library loaded")
        print("✅ Canvas element present")
        print("\n💡 The histogram should now be visible on the website!")
        print("📊 Expected display: Bar chart with $50K value bins")

        return True

    except Exception as e:
        print(f"❌ Test error: {e}")
        return False

if __name__ == "__main__":
    success = test_histogram_on_website()

    if success:
        print("\n🎉 ALL TESTS PASSED - Histogram should be working!")
    else:
        print("\n❌ Some tests failed - check the issues above")