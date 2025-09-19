#!/usr/bin/env python3
"""
Test script to compare price predictions between backend and expected Colab results
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import NYCRealEstatePricePredictor

def test_colab_equivalent_predictions():
    """Test predictions that should match Colab notebook results"""
    print("🧪 TESTING COLAB EQUIVALENT PREDICTIONS:")

    predictor = NYCRealEstatePricePredictor()

    # Test cases based on Colab notebook examples
    test_cases = [
        {
            "address": "123 Broadway",
            "borough": "Manhattan",
            "expected_neighborhood": "Financial District",
            "expected_price_range": (150, 800)
        },
        {
            "address": "456 Spring Street",
            "borough": "Manhattan",
            "expected_neighborhood": "SoHo",
            "expected_price_range": (180, 900)
        },
        {
            "address": "789 Bedford Avenue",
            "borough": "Brooklyn",
            "expected_neighborhood": "Williamsburg",
            "expected_price_range": (120, 500)
        },
        {
            "address": "321 23rd Street",
            "borough": "Manhattan",
            "expected_neighborhood": "Chelsea",
            "expected_price_range": (400, 800)
        }
    ]

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🏢 Test {i}: {test_case['address']}, {test_case['borough']}")
        print("-" * 50)

        try:
            # Test geocoding - should match Colab pattern matching
            coords = predictor.geocode_address(test_case['address'], test_case['borough'])
            print(f"📍 Coordinates: {coords['lat']:.4f}, {coords['lng']:.4f}")

            # Test neighborhood detection
            neighborhood = predictor.find_neighborhood(coords['lat'], coords['lng'])
            print(f"🏘️ Detected neighborhood: {neighborhood['name']}")

            # Check if neighborhood matches expected
            neighborhood_match = test_case['expected_neighborhood'].lower() in neighborhood['name'].lower()
            print(f"✅ Neighborhood match: {neighborhood_match}")

            # Test full prediction - should match Colab Random Forest
            prediction = predictor.predict_real_estate_value(test_case['address'], test_case['borough'])

            print(f"💰 Price per sq ft: ${prediction['price_per_sqft']}")
            print(f"📐 Estimated sq ft: {prediction['estimated_sqft']:,}")
            print(f"💵 Total value: ${prediction['total_value']:,}")
            print(f"🎯 ML confidence: {prediction['ml_confidence']}%")
            print(f"💧 Water score: {prediction.get('water_score', 'N/A')}")
            print(f"🚇 Transit score: {prediction.get('transit_score', 'N/A')}")
            print(f"🛡️ Safety score: {prediction.get('safety_score', 'N/A')}")

            # Check if price is in expected range
            min_price, max_price = test_case['expected_price_range']
            price_in_range = min_price <= prediction['price_per_sqft'] <= max_price
            print(f"✅ Price in expected range (${min_price}-${max_price}): {price_in_range}")

            if not price_in_range:
                print(f"⚠️ Price ${prediction['price_per_sqft']} is outside expected range!")

        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()

    return True

def test_direct_price_prediction():
    """Test the price prediction directly"""
    print("\n🧪 TESTING DIRECT PRICE PREDICTION:")

    # Test addresses from different neighborhoods
    test_addresses = [
        ("123 Broadway", "Manhattan"),
        ("456 Park Slope", "Brooklyn"),
        ("789 Astoria Blvd", "Queens"),
        ("321 Grand Concourse", "Bronx")
    ]

    predictor = NYCRealEstatePricePredictor()

    for address, borough in test_addresses:
        print(f"\n📍 Testing: {address}, {borough}")
        try:
            result = predictor.predict_real_estate_value(address, borough)
            print(f"  💰 Price per sqft: ${result['price_per_sqft']}")
            print(f"  📐 Estimated sqft: {result['estimated_sqft']}")
            print(f"  💵 Total value: ${result['total_value']:,}")
            print(f"  🏘️ Neighborhood: {result['neighborhood']}")
            print(f"  🏙️ Borough: {result['borough']}")
            print(f"  🎯 ML Confidence: {result['ml_confidence']}%")

            # Verify reasonable ranges
            if 50 <= result['price_per_sqft'] <= 1500:
                print(f"  ✅ Price per sqft is reasonable")
            else:
                print(f"  ⚠️ Price per sqft seems unreasonable: ${result['price_per_sqft']}")

            if 1000 <= result['estimated_sqft'] <= 6000:
                print(f"  ✅ Square footage is reasonable")
            else:
                print(f"  ⚠️ Square footage seems unreasonable: {result['estimated_sqft']}")

        except Exception as e:
            print(f"  ❌ Error: {e}")

def test_geocoding_accuracy():
    """Test geocoding accuracy"""
    print("\n🗺️ TESTING GEOCODING ACCURACY:")

    predictor = NYCRealEstatePricePredictor()

    # Known addresses with expected neighborhoods
    known_addresses = [
        ("123 Broadway", "Manhattan", "Financial District"),
        ("456 Fifth Avenue", "Manhattan", "Midtown"),
        ("789 Park Avenue", "Manhattan", "Upper East Side"),
        ("123 Atlantic Avenue", "Brooklyn", "Brooklyn Heights"),
        ("456 Bedford Avenue", "Brooklyn", "Williamsburg")
    ]

    for address, borough, expected_area in known_addresses:
        coords = predictor.geocode_address(address, borough)
        neighborhood = predictor.find_neighborhood(coords['lat'], coords['lng'])

        print(f"📍 {address}, {borough}")
        print(f"  📌 Coordinates: {coords['lat']:.4f}, {coords['lng']:.4f}")
        print(f"  🏘️ Detected neighborhood: {neighborhood['name']}")
        print(f"  🎯 Expected area contains '{expected_area}': {expected_area.lower() in neighborhood['name'].lower()}")

if __name__ == "__main__":
    print("🔬 TESTING REAL ESTATE PRICE PREDICTIONS")
    print("=" * 60)

    # Test Colab equivalent predictions
    test_colab_equivalent_predictions()

    print("\n" + "=" * 60)
    print("✅ ALL TESTS COMPLETED")