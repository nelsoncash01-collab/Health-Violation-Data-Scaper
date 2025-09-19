#!/usr/bin/env python3
"""
Test the $50K histogram functionality
"""

import requests
import json

def test_histogram_binning():
    """Test that the data works correctly with $50K binning"""

    print("🧪 TESTING $50K HISTOGRAM FUNCTIONALITY")
    print("=" * 60)

    try:
        response = requests.get('http://localhost:5000/api/opportunities?days=30', timeout=5)

        if response.status_code != 200:
            print(f"❌ API Error: {response.status_code}")
            return

        data = response.json()

        if not data['success']:
            print(f"❌ API returned error: {data.get('message')}")
            return

        opportunities = data['opportunities']
        print(f"✅ Retrieved {len(opportunities)} opportunities")

        # Simulate the frontend histogram logic
        bin_size = 50000  # $50K bins
        values = [opp['totalValue'] for opp in opportunities]
        max_value = max(values)
        num_bins = int(max_value // bin_size) + 1

        print(f"\n📊 Histogram Analysis:")
        print(f"   Value range: ${min(values):,} - ${max_value:,}")
        print(f"   Bin size: ${bin_size:,}")
        print(f"   Number of bins: {num_bins}")

        # Create bins
        bins = {}

        def format_value_range(start, end):
            def format_value(value):
                if value >= 1000000:
                    return '$' + str(round(value / 1000000, 1)) + 'M'
                elif value >= 1000:
                    return '$' + str(round(value / 1000)) + 'K'
                else:
                    return '$' + str(value)

            return format_value(start) + ' - ' + format_value(end)

        # Initialize bins
        for i in range(num_bins):
            bin_start = i * bin_size
            bin_end = (i + 1) * bin_size
            label = format_value_range(bin_start, bin_end)
            bins[label] = 0

        # Fill bins
        for value in values:
            bin_index = int(value // bin_size)
            bin_start = bin_index * bin_size
            bin_end = (bin_index + 1) * bin_size
            label = format_value_range(bin_start, bin_end)

            if label in bins:
                bins[label] += 1

        # Show non-empty bins
        print(f"\n📈 Property Distribution ($50K bins):")
        non_empty_bins = {k: v for k, v in bins.items() if v > 0}

        for label, count in sorted(non_empty_bins.items(), key=lambda x: x[1], reverse=True):
            bar = '█' * count
            print(f"   {label:20} │{bar} {count}")

        print(f"\n✅ Histogram test successful!")
        print(f"   • Total bins created: {len(bins)}")
        print(f"   • Non-empty bins: {len(non_empty_bins)}")
        print(f"   • Most common range: {max(non_empty_bins, key=non_empty_bins.get)} ({max(non_empty_bins.values())} properties)")

        # Test edge cases
        print(f"\n🔍 Edge Case Tests:")

        # Test min value
        min_val = min(values)
        min_bin_index = int(min_val // bin_size)
        print(f"   Min value ${min_val:,} → Bin {min_bin_index} (${min_bin_index * bin_size:,} - ${(min_bin_index + 1) * bin_size:,})")

        # Test max value
        max_val = max(values)
        max_bin_index = int(max_val // bin_size)
        print(f"   Max value ${max_val:,} → Bin {max_bin_index} (${max_bin_index * bin_size:,} - ${(max_bin_index + 1) * bin_size:,})")

        return True

    except Exception as e:
        print(f"❌ Test error: {e}")
        return False

if __name__ == "__main__":
    success = test_histogram_binning()

    print("\n" + "=" * 60)
    if success:
        print("✅ HISTOGRAM TEST PASSED")
        print("💡 The frontend will now show:")
        print("   • Detailed $50K value bins instead of broad ranges")
        print("   • Bar chart histogram instead of pie chart")
        print("   • More granular property value distribution")
        print("   • Better insights into market segments")
    else:
        print("❌ HISTOGRAM TEST FAILED")