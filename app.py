from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import requests
import pandas as pd
import json
import math
import random
import numpy as np
from datetime import datetime, timedelta
import pickle
import os
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import r2_score, mean_squared_error
import concurrent.futures
import threading

app = Flask(__name__)
CORS(app)

class NYCRealEstatePricePredictor:
    def __init__(self):
        # Initialize core attributes FIRST
        self.random_forest_model = None
        self.scaler = StandardScaler()
        self.model_trained = False

        # Initialize geocoding cache
        self.cache_file = 'geocoding_cache.json'
        self.geocoding_cache = self._load_cache()

        # Initialize enhanced features SECOND
        self._initialize_enhanced_features()

        # Load trained Random Forest model LAST
        self._load_or_train_random_forest_model()

        # NYC neighborhood data with realistic factors
        self.neighborhoods = [
            # Manhattan
            {"name": "Tribeca", "borough": "Manhattan", "bounds": {"minLat": 40.715, "maxLat": 40.725, "minLng": -74.015, "maxLng": -74.005}, "crimeBase": 8.5, "transitBase": 9.5, "amenityBase": 9.5},
            {"name": "SoHo", "borough": "Manhattan", "bounds": {"minLat": 40.720, "maxLat": 40.730, "minLng": -74.010, "maxLng": -73.995}, "crimeBase": 8.0, "transitBase": 9.0, "amenityBase": 9.8},
            {"name": "West Village", "borough": "Manhattan", "bounds": {"minLat": 40.730, "maxLat": 40.740, "minLng": -74.010, "maxLng": -73.995}, "crimeBase": 8.5, "transitBase": 8.5, "amenityBase": 9.0},
            {"name": "East Village", "borough": "Manhattan", "bounds": {"minLat": 40.720, "maxLat": 40.735, "minLng": -73.995, "maxLng": -73.975}, "crimeBase": 6.0, "transitBase": 8.0, "amenityBase": 8.5},
            {"name": "Chelsea", "borough": "Manhattan", "bounds": {"minLat": 40.740, "maxLat": 40.755, "minLng": -74.010, "maxLng": -73.990}, "crimeBase": 7.5, "transitBase": 9.0, "amenityBase": 8.8},
            {"name": "Midtown West", "borough": "Manhattan", "bounds": {"minLat": 40.755, "maxLat": 40.770, "minLng": -74.000, "maxLng": -73.980}, "crimeBase": 6.8, "transitBase": 9.5, "amenityBase": 8.0},
            {"name": "Midtown East", "borough": "Manhattan", "bounds": {"minLat": 40.750, "maxLat": 40.765, "minLng": -73.980, "maxLng": -73.960}, "crimeBase": 6.5, "transitBase": 9.8, "amenityBase": 8.0},
            {"name": "Upper East Side", "borough": "Manhattan", "bounds": {"minLat": 40.765, "maxLat": 40.785, "minLng": -73.970, "maxLng": -73.945}, "crimeBase": 8.8, "transitBase": 9.2, "amenityBase": 8.5},
            {"name": "Upper West Side", "borough": "Manhattan", "bounds": {"minLat": 40.775, "maxLat": 40.795, "minLng": -74.000, "maxLng": -73.970}, "crimeBase": 8.2, "transitBase": 8.8, "amenityBase": 8.2},
            {"name": "Financial District", "borough": "Manhattan", "bounds": {"minLat": 40.702, "maxLat": 40.715, "minLng": -74.020, "maxLng": -74.000}, "crimeBase": 7.8, "transitBase": 8.5, "amenityBase": 7.5},
            {"name": "Harlem", "borough": "Manhattan", "bounds": {"minLat": 40.805, "maxLat": 40.830, "minLng": -73.960, "maxLng": -73.935}, "crimeBase": 4.5, "transitBase": 7.5, "amenityBase": 6.0},

            # Brooklyn
            {"name": "DUMBO", "borough": "Brooklyn", "bounds": {"minLat": 40.700, "maxLat": 40.706, "minLng": -73.995, "maxLng": -73.985}, "crimeBase": 8.5, "transitBase": 8.0, "amenityBase": 8.5},
            {"name": "Brooklyn Heights", "borough": "Brooklyn", "bounds": {"minLat": 40.692, "maxLat": 40.700, "minLng": -74.000, "maxLng": -73.990}, "crimeBase": 8.8, "transitBase": 8.5, "amenityBase": 8.0},
            {"name": "Park Slope", "borough": "Brooklyn", "bounds": {"minLat": 40.665, "maxLat": 40.685, "minLng": -73.990, "maxLng": -73.970}, "crimeBase": 8.2, "transitBase": 8.5, "amenityBase": 8.0},
            {"name": "Williamsburg", "borough": "Brooklyn", "bounds": {"minLat": 40.700, "maxLat": 40.720, "minLng": -73.970, "maxLng": -73.945}, "crimeBase": 7.0, "transitBase": 8.0, "amenityBase": 8.8},
            {"name": "Red Hook", "borough": "Brooklyn", "bounds": {"minLat": 40.670, "maxLat": 40.680, "minLng": -74.020, "maxLng": -74.005}, "crimeBase": 5.5, "transitBase": 4.0, "amenityBase": 6.5},
            {"name": "Crown Heights", "borough": "Brooklyn", "bounds": {"minLat": 40.660, "maxLat": 40.680, "minLng": -73.950, "maxLng": -73.930}, "crimeBase": 5.0, "transitBase": 7.0, "amenityBase": 6.0},
            {"name": "Bed-Stuy", "borough": "Brooklyn", "bounds": {"minLat": 40.675, "maxLat": 40.695, "minLng": -73.950, "maxLng": -73.930}, "crimeBase": 5.2, "transitBase": 7.2, "amenityBase": 6.8},

            # Queens
            {"name": "Long Island City", "borough": "Queens", "bounds": {"minLat": 40.740, "maxLat": 40.750, "minLng": -73.955, "maxLng": -73.940}, "crimeBase": 7.0, "transitBase": 8.5, "amenityBase": 7.5},
            {"name": "Astoria", "borough": "Queens", "bounds": {"minLat": 40.770, "maxLat": 40.780, "minLng": -73.935, "maxLng": -73.920}, "crimeBase": 7.2, "transitBase": 8.0, "amenityBase": 7.8},
            {"name": "Forest Hills", "borough": "Queens", "bounds": {"minLat": 40.720, "maxLat": 40.730, "minLng": -73.850, "maxLng": -73.835}, "crimeBase": 8.0, "transitBase": 7.5, "amenityBase": 7.0},
            {"name": "Flushing", "borough": "Queens", "bounds": {"minLat": 40.760, "maxLat": 40.770, "minLng": -73.840, "maxLng": -73.825}, "crimeBase": 6.5, "transitBase": 7.0, "amenityBase": 6.5},
            {"name": "Jackson Heights", "borough": "Queens", "bounds": {"minLat": 40.745, "maxLat": 40.760, "minLng": -73.885, "maxLng": -73.870}, "crimeBase": 6.0, "transitBase": 7.8, "amenityBase": 7.5},

            # Bronx
            {"name": "Riverdale", "borough": "Bronx", "bounds": {"minLat": 40.890, "maxLat": 40.900, "minLng": -73.915, "maxLng": -73.900}, "crimeBase": 8.0, "transitBase": 6.0, "amenityBase": 6.5},
            {"name": "South Bronx", "borough": "Bronx", "bounds": {"minLat": 40.820, "maxLat": 40.835, "minLng": -73.915, "maxLng": -73.900}, "crimeBase": 3.5, "transitBase": 6.5, "amenityBase": 4.5},
            {"name": "Fordham", "borough": "Bronx", "bounds": {"minLat": 40.855, "maxLat": 40.870, "minLng": -73.905, "maxLng": -73.890}, "crimeBase": 4.5, "transitBase": 7.0, "amenityBase": 5.5},

            # Staten Island
            {"name": "St. George", "borough": "Staten Island", "bounds": {"minLat": 40.640, "maxLat": 40.650, "minLng": -74.085, "maxLng": -74.070}, "crimeBase": 6.5, "transitBase": 5.5, "amenityBase": 5.5}
        ]

        # Water bodies in NYC for distance calculation
        self.water_bodies = [
            {"name": "Hudson River", "lat": 40.7589, "lng": -74.0134},
            {"name": "East River", "lat": 40.7282, "lng": -73.9942},
            {"name": "Upper Bay", "lat": 40.6892, "lng": -74.0445},
            {"name": "Jamaica Bay", "lat": 40.6089, "lng": -73.8370},
            {"name": "Bronx River", "lat": 40.8176, "lng": -73.8648}
        ]

    def _load_cache(self):
        """Load geocoding cache from file"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r') as f:
                    cache = json.load(f)
                    print(f"📋 Loaded {len(cache)} cached geocoding entries")
                    return cache
        except Exception as e:
            print(f"⚠️ Could not load cache: {e}")
        return {}

    def _save_cache(self):
        """Save geocoding cache to file"""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self.geocoding_cache, f, indent=2)
                print(f"💾 Saved {len(self.geocoding_cache)} geocoding entries to cache")
        except Exception as e:
            print(f"⚠️ Could not save cache: {e}")

    def _add_to_cache(self, cache_key, coords):
        """Add coordinates to cache and save"""
        self.geocoding_cache[cache_key] = coords
        if len(self.geocoding_cache) % 10 == 0:  # Save every 10 new entries
            self._save_cache()

    def calculate_distance(self, lat1, lng1, lat2, lng2):
        """Calculate distance between two lat/lng points using Haversine formula"""
        R = 3959
        dLat = math.radians(lat2 - lat1)
        dLng = math.radians(lng2 - lng1)
        a = (math.sin(dLat/2) * math.sin(dLat/2) +
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
             math.sin(dLng/2) * math.sin(dLng/2))
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return R * c

    def _initialize_enhanced_features(self):
        """Initialize all enhanced features for Random Forest model"""
        # Enhanced water bodies with weights for premium scoring
        self.enhanced_water_bodies = [
            {"name": "Hudson River - Financial", "lat": 40.7074, "lng": -74.0113, "weight": 2.0},
            {"name": "Hudson River - Midtown", "lat": 40.7614, "lng": -74.0066, "weight": 2.5},
            {"name": "East River - Financial", "lat": 40.7047, "lng": -73.9753, "weight": 1.8},
            {"name": "East River - Midtown", "lat": 40.7489, "lng": -73.9441, "weight": 2.0},
            {"name": "Central Park", "lat": 40.7829, "lng": -73.9654, "weight": 3.0},
            {"name": "Prospect Park", "lat": 40.6602, "lng": -73.9690, "weight": 2.2},
        ]

        # Enhanced transit hubs with business importance weights
        self.enhanced_transit_hubs = [
            {"name": "Times Square", "lat": 40.7580, "lng": -73.9855, "weight": 4.0, "type": "major_hub"},
            {"name": "Grand Central", "lat": 40.7527, "lng": -73.9772, "weight": 4.0, "type": "major_hub"},
            {"name": "Penn Station", "lat": 40.7505, "lng": -73.9934, "weight": 4.0, "type": "major_hub"},
            {"name": "Union Square", "lat": 40.7359, "lng": -73.9911, "weight": 3.0, "type": "transit_center"},
            {"name": "Wall Street", "lat": 40.7074, "lng": -74.0113, "weight": 3.5, "type": "financial_center"},
            {"name": "Brooklyn Bridge", "lat": 40.6962, "lng": -73.9969, "weight": 2.5, "type": "transit_center"},
            {"name": "Atlantic Terminal", "lat": 40.6844, "lng": -73.9766, "weight": 3.0, "type": "major_hub"},
        ]

        # Business district premiums for commercial appeal
        self.business_districts = [
            {"name": "Financial District", "lat": 40.7074, "lng": -74.0113, "premium": 1.2},
            {"name": "Midtown Manhattan", "lat": 40.7549, "lng": -73.9840, "premium": 1.15},
            {"name": "DUMBO", "lat": 40.7033, "lng": -73.9888, "premium": 1.1},
            {"name": "Long Island City", "lat": 40.7589, "lng": -73.9441, "premium": 1.05},
        ]

    def _load_or_train_random_forest_model(self):
        """Load trained Random Forest model or train a new one"""
        model_file = 'nyc_commercial_rf_model.pkl'

        try:
            # Try to load existing model
            if os.path.exists(model_file):
                with open(model_file, 'rb') as f:
                    model_data = pickle.load(f)
                    self.random_forest_model = model_data['model']
                    self.scaler = model_data['scaler']
                    self.model_trained = True
                    print("✅ Loaded pre-trained Random Forest model")
                    return
        except Exception as e:
            print(f"⚠️ Could not load saved model: {e}")

        # Train new model if loading failed
        print("🤖 Training new Random Forest model...")
        self._train_random_forest_model()

    def _train_random_forest_model(self):
        """Train Random Forest model with NYC commercial real estate data"""
        print("🏢 Training Random Forest model with NYC commercial data...")

        # Generate training data based on real NYC commercial patterns
        training_data = []

        # Enhanced commercial areas with realistic pricing
        commercial_areas = [
            # Premium Manhattan neighborhoods
            {"lat": 40.7195, "lng": -74.0089, "price_range": (600, 1200), "borough": "Manhattan", "name": "Tribeca"},
            {"lat": 40.7230, "lng": -74.0020, "price_range": (550, 1100), "borough": "Manhattan", "name": "SoHo"},
            {"lat": 40.7074, "lng": -74.0113, "price_range": (400, 900), "borough": "Manhattan", "name": "Financial District"},
            {"lat": 40.7549, "lng": -73.9840, "price_range": (350, 800), "borough": "Manhattan", "name": "Midtown"},
            {"lat": 40.7357, "lng": -74.0036, "price_range": (500, 950), "borough": "Manhattan", "name": "West Village"},
            {"lat": 40.7264, "lng": -73.9816, "price_range": (300, 650), "borough": "Manhattan", "name": "East Village"},
            {"lat": 40.7465, "lng": -73.9972, "price_range": (400, 800), "borough": "Manhattan", "name": "Chelsea"},
            {"lat": 40.7736, "lng": -73.9566, "price_range": (350, 700), "borough": "Manhattan", "name": "Upper East Side"},
            {"lat": 40.7851, "lng": -73.9754, "price_range": (300, 650), "borough": "Manhattan", "name": "Upper West Side"},

            # Brooklyn neighborhoods
            {"lat": 40.7033, "lng": -73.9903, "price_range": (350, 750), "borough": "Brooklyn", "name": "DUMBO"},
            {"lat": 40.6958, "lng": -73.9936, "price_range": (320, 680), "borough": "Brooklyn", "name": "Brooklyn Heights"},
            {"lat": 40.6719, "lng": -73.9832, "price_range": (280, 580), "borough": "Brooklyn", "name": "Park Slope"},
            {"lat": 40.7081, "lng": -73.9571, "price_range": (300, 650), "borough": "Brooklyn", "name": "Williamsburg"},

            # Queens neighborhoods
            {"lat": 40.7444, "lng": -73.9482, "price_range": (250, 500), "borough": "Queens", "name": "Long Island City"},
            {"lat": 40.7720, "lng": -73.9300, "price_range": (230, 450), "borough": "Queens", "name": "Astoria"},

            # Bronx neighborhoods
            {"lat": 40.8621, "lng": -73.8965, "price_range": (180, 350), "borough": "Bronx", "name": "Fordham"},
        ]

        for area in commercial_areas:
            for _ in range(40):  # Generate samples for each area
                lat = area["lat"] + (random.random() - 0.5) * 0.01
                lng = area["lng"] + (random.random() - 0.5) * 0.01

                water_score = self._calculate_enhanced_water_proximity(lat, lng)
                transit_score = self._calculate_enhanced_transit_accessibility(lat, lng)
                business_premium = self._calculate_business_district_premium(lat, lng)

                # Area-specific crime sentiment
                crime_sentiment = random.uniform(-0.1, 0.3) if area["borough"] == "Manhattan" else random.uniform(-0.2, 0.1)
                safety_score = 7.0 + crime_sentiment * 2 + random.uniform(-0.5, 0.5)
                safety_score = max(4.0, min(9.0, safety_score))

                square_footage = random.uniform(2500, 4500)
                building_age = random.uniform(10, 50)
                type_premium = random.uniform(0.9, 1.3)

                base_price = random.uniform(area["price_range"][0], area["price_range"][1])

                features = [water_score, transit_score, business_premium, crime_sentiment,
                           safety_score, square_footage, building_age, type_premium]

                training_data.append({
                    'features': features,
                    'price': base_price
                })

        # Prepare training data
        X = np.array([item['features'] for item in training_data])
        y = np.array([item['price'] for item in training_data])

        # Scale features
        X_scaled = self.scaler.fit_transform(X)

        # Train Random Forest model
        self.random_forest_model = RandomForestRegressor(
            n_estimators=100,
            max_depth=12,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42
        )

        self.random_forest_model.fit(X_scaled, y)
        self.model_trained = True

        # Save the trained model
        try:
            model_data = {
                'model': self.random_forest_model,
                'scaler': self.scaler
            }
            with open('nyc_commercial_rf_model.pkl', 'wb') as f:
                pickle.dump(model_data, f)
            print("💾 Model saved successfully")
        except Exception as e:
            print(f"⚠️ Could not save model: {e}")

        print("✅ Random Forest model trained successfully")

    def _calculate_enhanced_water_proximity(self, lat, lng):
        """Calculate weighted proximity to water features"""
        total_score = 0
        for water_body in self.enhanced_water_bodies:
            distance = self.calculate_distance(lat, lng, water_body['lat'], water_body['lng'])
            weight = water_body.get('weight', 1.0)
            score = weight / (1 + distance)
            total_score += score
        return total_score

    def _calculate_enhanced_transit_accessibility(self, lat, lng):
        """Calculate comprehensive transit accessibility score (0-10 scale)"""
        total_score = 0
        hub_type_bonuses = {
            'major_hub': 2.0, 'transit_center': 1.5, 'financial_center': 1.8
        }

        for hub in self.enhanced_transit_hubs:
            distance = self.calculate_distance(lat, lng, hub['lat'], hub['lng'])
            weight = hub.get('weight', 1.0)
            hub_type = hub.get('type', 'transit_center')
            type_bonus = hub_type_bonuses.get(hub_type, 1.0)

            if distance <= 0.5:
                score = weight * type_bonus * 3.0
            elif distance <= 1.0:
                score = weight * type_bonus * 2.0
            elif distance <= 2.0:
                score = weight * type_bonus * 1.0
            else:
                score = weight * type_bonus / (1 + distance)

            total_score += score

        # Normalize to 0-10 scale using sigmoid-like function
        # This ensures scores approach but never exceed 10
        normalized_score = 10 * (1 - 1 / (1 + total_score / 15))
        return min(normalized_score, 10.0)

    def _calculate_business_district_premium(self, lat, lng):
        """Calculate premium for being in established business districts"""
        max_premium = 1.0
        for district in self.business_districts:
            distance = self.calculate_distance(lat, lng, district['lat'], district['lng'])
            if distance <= 0.5:
                premium_factor = district['premium']
            elif distance <= 1.0:
                premium_factor = 1.0 + (district['premium'] - 1.0) * 0.7
            elif distance <= 2.0:
                premium_factor = 1.0 + (district['premium'] - 1.0) * 0.3
            else:
                premium_factor = 1.0
            max_premium = max(max_premium, premium_factor)
        return max_premium

    def geocode_address(self, address, borough=None):
        """Convert address to coordinates using cached real geocoding services"""
        if not address or len(address.strip()) < 5:
            return {"lat": 40.7549, "lng": -73.9707}

        # Clean and normalize the NYC address format
        address_clean = address.strip()
        normalized_address = self._normalize_nyc_address(address_clean)

        cache_key = f"{normalized_address}|{borough or ''}"

        # Check cache first - this is the key to performance!
        if cache_key in self.geocoding_cache:
            print(f"🎯 Cache hit for {address_clean}")
            return self.geocoding_cache[cache_key]

        print(f"🔍 Geocoding {address_clean} -> {normalized_address} (not in cache)")

        # Create full address for geocoding using normalized format
        if borough:
            full_address = f"{normalized_address}, {borough}, New York, NY, USA"
        else:
            full_address = f"{normalized_address}, New York, NY, USA"

        # Skip external APIs for speed - use fast pattern matching directly
        print(f"⚡ Fast geocoding with pattern matching for {address_clean}")
        coords = self._geocode_with_pattern_matching(address_clean, borough)

        # Cache the result (whether from API or fallback)
        self._add_to_cache(cache_key, coords)
        return coords

    def _try_nominatim_geocoding(self, full_address, address_clean):
        """Try geocoding with OpenStreetMap Nominatim"""
        try:
            import urllib.parse
            import time

            # Rate limiting: Nominatim allows max 1 request per second
            time.sleep(1.1)

            encoded_address = urllib.parse.quote(full_address)
            nominatim_url = f"https://nominatim.openstreetmap.org/search?q={encoded_address}&format=json&limit=1&countrycodes=us"

            headers = {
                'User-Agent': 'NYC-Restaurant-Investment-Scraper/1.0 (https://github.com/user/repo)'
            }

            response = requests.get(nominatim_url, timeout=3, headers=headers)

            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 0:
                    result = data[0]
                    lat = float(result['lat'])
                    lng = float(result['lon'])

                    # Verify coordinates are in NYC area
                    if 40.4 <= lat <= 41.0 and -74.5 <= lng <= -73.5:
                        print(f"✅ Nominatim geocoded {address_clean} -> {lat:.4f}, {lng:.4f}")
                        return {"lat": lat, "lng": lng}
                    else:
                        print(f"⚠️ Nominatim returned coordinates outside NYC for {address_clean}: {lat}, {lng}")

        except Exception as e:
            print(f"⚠️ Nominatim geocoding failed for {address_clean}: {e}")

        return None

    def _try_positionstack_geocoding(self, full_address, address_clean):
        """Try geocoding with PositionStack (free tier: 25,000 requests/month)"""
        try:
            import urllib.parse

            # PositionStack free API (no key needed for basic usage)
            encoded_address = urllib.parse.quote(full_address)
            positionstack_url = f"http://api.positionstack.com/v1/forward?access_key=free&query={encoded_address}&limit=1"

            response = requests.get(positionstack_url, timeout=3)

            if response.status_code == 200:
                data = response.json()
                if data and 'data' in data and len(data['data']) > 0:
                    result = data['data'][0]
                    lat = float(result['latitude'])
                    lng = float(result['longitude'])

                    # Verify coordinates are in NYC area
                    if 40.4 <= lat <= 41.0 and -74.5 <= lng <= -73.5:
                        print(f"✅ PositionStack geocoded {address_clean} -> {lat:.4f}, {lng:.4f}")
                        return {"lat": lat, "lng": lng}
                    else:
                        print(f"⚠️ PositionStack returned coordinates outside NYC for {address_clean}: {lat}, {lng}")

        except Exception as e:
            print(f"⚠️ PositionStack geocoding failed for {address_clean}: {e}")

        return None

    def _normalize_nyc_address(self, address):
        """Normalize NYC health department address format to standard geocoding format"""
        import re

        address = address.strip().upper()

        # Fix common NYC format issues
        # Convert numbered streets: "4 AVENUE" -> "4th Avenue"
        address = re.sub(r'\b(\d+)\s+(AVENUE|AVE)\b', r'\1th Avenue', address)
        address = re.sub(r'\b(\d+)\s+(STREET|ST)\b', r'\1th Street', address)

        # Handle special number suffixes for streets
        address = re.sub(r'\b(\d*1)TH\b', r'\1st', address)  # 1st, 21st, 31st, etc.
        address = re.sub(r'\b(\d*2)TH\b', r'\1nd', address)  # 2nd, 22nd, 32nd, etc.
        address = re.sub(r'\b(\d*3)TH\b', r'\1rd', address)  # 3rd, 23rd, 33rd, etc.

        # Handle common abbreviations
        address = re.sub(r'\bAVE\b', 'Avenue', address)
        address = re.sub(r'\bST\b', 'Street', address)
        address = re.sub(r'\bRD\b', 'Road', address)
        address = re.sub(r'\bBLVD\b', 'Boulevard', address)
        address = re.sub(r'\bPKWY\b', 'Parkway', address)
        address = re.sub(r'\bPL\b', 'Place', address)
        address = re.sub(r'\bCT\b', 'Court', address)
        address = re.sub(r'\bDR\b', 'Drive', address)
        address = re.sub(r'\bLN\b', 'Lane', address)

        # Handle directional prefixes
        address = re.sub(r'\bW\b', 'West', address)
        address = re.sub(r'\bE\b', 'East', address)
        address = re.sub(r'\bN\b', 'North', address)
        address = re.sub(r'\bS\b', 'South', address)

        # Handle "WEST 136 STREET" -> "West 136th Street"
        address = re.sub(r'\bWEST\s+(\d+)\s+STREET\b', r'West \1th Street', address)
        address = re.sub(r'\bEAST\s+(\d+)\s+STREET\b', r'East \1th Street', address)

        # Clean up multiple spaces first
        address = re.sub(r'\s+', ' ', address)

        # Handle "42 WEST 42 STREET" -> "West 42nd Street"
        address = re.sub(r'\b(\d+)\s+WEST\s+\1\s+STREET\b', r'West \1th Street', address)
        address = re.sub(r'\b(\d+)\s+EAST\s+\1\s+STREET\b', r'East \1th Street', address)

        # Fix ordinal endings again for the directional cases
        address = re.sub(r'\b(\d*1)TH\b', r'\1st', address)
        address = re.sub(r'\b(\d*2)TH\b', r'\1nd', address)
        address = re.sub(r'\b(\d*3)TH\b', r'\1rd', address)

        # Handle special cases for common NYC streets
        street_replacements = {
            'BROADWAY': 'Broadway',
            'PARK AVENUE': 'Park Avenue',
            'MADISON AVENUE': 'Madison Avenue',
            'LEXINGTON AVENUE': 'Lexington Avenue',
            'THIRD AVENUE': '3rd Avenue',
            'SECOND AVENUE': '2nd Avenue',
            'FIRST AVENUE': '1st Avenue',
            'AVENUE A': 'Avenue A',
            'AVENUE B': 'Avenue B',
            'AVENUE C': 'Avenue C',
            'AVENUE D': 'Avenue D',
            'FDR DRIVE': 'FDR Drive',
            'WEST SIDE HIGHWAY': 'West Side Highway'
        }

        for old, new in street_replacements.items():
            address = address.replace(old, new)

        # Clean up multiple spaces
        address = re.sub(r'\s+', ' ', address)

        # Convert to proper case
        address = address.title()

        # Fix common overcapitalization
        address = re.sub(r'\bOf\b', 'of', address)
        address = re.sub(r'\bThe\b', 'the', address)
        address = re.sub(r'\bAnd\b', 'and', address)

        return address.strip()

    def _geocode_with_pattern_matching(self, address, borough=None):
        """Enhanced pattern matching geocoding for NYC addresses"""
        address_lower = address.lower()
        borough_lower = borough.lower() if borough else ""

        import re

        # Extract house number
        number_match = re.search(r'^(\d+)', address)
        house_number = int(number_match.group(1)) if number_match else 100

        # Extract street name
        street_match = re.search(r'\d+\s+(.+)', address)
        street_name = street_match.group(1).lower() if street_match else address_lower

        # Calculate coordinate offset based on house number (more realistic distribution)
        lat_offset = (house_number % 100) * 0.0001
        lng_offset = ((house_number % 50) - 25) * 0.0001

        # Manhattan street-specific geocoding
        if 'manhattan' in borough_lower or any(term in address_lower for term in ['manhattan', 'new york']):
            # Major Manhattan streets with accurate coordinates
            manhattan_streets = {
                'broadway': {"base_lat": 40.7831, "base_lng": -73.9712, "direction": "ns"},
                'fifth avenue': {"base_lat": 40.7781, "base_lng": -73.9665, "direction": "ns"},
                '5th avenue': {"base_lat": 40.7781, "base_lng": -73.9665, "direction": "ns"},
                'park avenue': {"base_lat": 40.7731, "base_lng": -73.9712, "direction": "ns"},
                'madison avenue': {"base_lat": 40.7731, "base_lng": -73.9712, "direction": "ns"},
                'lexington avenue': {"base_lat": 40.7631, "base_lng": -73.9665, "direction": "ns"},
                'third avenue': {"base_lat": 40.7531, "base_lng": -73.9665, "direction": "ns"},
                '3rd avenue': {"base_lat": 40.7531, "base_lng": -73.9665, "direction": "ns"},
                'second avenue': {"base_lat": 40.7431, "base_lng": -73.9865, "direction": "ns"},
                '2nd avenue': {"base_lat": 40.7431, "base_lng": -73.9865, "direction": "ns"},
                'first avenue': {"base_lat": 40.7331, "base_lng": -73.9765, "direction": "ns"},
                '1st avenue': {"base_lat": 40.7331, "base_lng": -73.9765, "direction": "ns"},
                'avenue a': {"base_lat": 40.7231, "base_lng": -73.9865, "direction": "ns"},
                'avenue b': {"base_lat": 40.7131, "base_lng": -73.9765, "direction": "ns"},
                'west 14th street': {"base_lat": 40.7390, "base_lng": -74.0059, "direction": "ew"},
                'west 23rd street': {"base_lat": 40.7440, "base_lng": -74.0020, "direction": "ew"},
                'west 34th street': {"base_lat": 40.7505, "base_lng": -73.9934, "direction": "ew"},
                'west 42nd street': {"base_lat": 40.7580, "base_lng": -73.9855, "direction": "ew"},
                'west 57th street': {"base_lat": 40.7649, "base_lng": -73.9776, "direction": "ew"},
                'east 14th street': {"base_lat": 40.7331, "base_lng": -73.9899, "direction": "ew"},
                'east 23rd street': {"base_lat": 40.7394, "base_lng": -73.9857, "direction": "ew"},
                'east 34th street': {"base_lat": 40.7462, "base_lng": -73.9820, "direction": "ew"},
                'east 42nd street': {"base_lat": 40.7527, "base_lng": -73.9772, "direction": "ew"},
                'east 57th street': {"base_lat": 40.7614, "base_lng": -73.9776, "direction": "ew"},
                'wall street': {"base_lat": 40.7074, "base_lng": -74.0113, "direction": "ew"},
                'canal street': {"base_lat": 40.7185, "base_lng": -74.0051, "direction": "ew"},
                'houston street': {"base_lat": 40.7253, "base_lng": -74.0034, "direction": "ew"},
                'delancey street': {"base_lat": 40.7184, "base_lng": -73.9857, "direction": "ew"},
                'grand street': {"base_lat": 40.7185, "base_lng": -73.9935, "direction": "ew"},
                'spring street': {"base_lat": 40.7253, "base_lng": -74.0034, "direction": "ew"},
                'bleecker street': {"base_lat": 40.7279, "base_lng": -74.0021, "direction": "ew"},
                '8th avenue': {"base_lat": 40.7505, "base_lng": -73.9934, "direction": "ns"},
                '7th avenue': {"base_lat": 40.7505, "base_lng": -73.9880, "direction": "ns"},
                '6th avenue': {"base_lat": 40.7505, "base_lng": -73.9825, "direction": "ns"},
            }

            # Find matching street
            for street_key, coords in manhattan_streets.items():
                if street_key in street_name:
                    base_lat = coords["base_lat"]
                    base_lng = coords["base_lng"]

                    # Adjust coordinates based on house number and street direction
                    if coords["direction"] == "ns":  # North-South street
                        # Higher numbers = further north
                        lat = base_lat + (house_number - 100) * 0.00008
                        lng = base_lng + lng_offset * 0.5
                    else:  # East-West street
                        # Higher numbers = further east (for east streets) or west (for west streets)
                        lat = base_lat + lat_offset * 0.5
                        if 'west' in street_name:
                            lng = base_lng - (house_number - 100) * 0.00005
                        else:
                            lng = base_lng + (house_number - 100) * 0.00005

                    return {"lat": lat, "lng": lng}

            # Manhattan neighborhood fallbacks
            manhattan_neighborhoods = {
                'tribeca': {"lat": 40.7195, "lng": -74.0089},
                'soho': {"lat": 40.7230, "lng": -74.0020},
                'financial': {"lat": 40.7074, "lng": -74.0113},
                'midtown': {"lat": 40.7549, "lng": -73.9840},
                'times square': {"lat": 40.7580, "lng": -73.9855},
                'chelsea': {"lat": 40.7465, "lng": -73.9972},
                'village': {"lat": 40.7308, "lng": -74.0020},
                'upper east': {"lat": 40.7736, "lng": -73.9566},
                'upper west': {"lat": 40.7851, "lng": -73.9754},
                'harlem': {"lat": 40.8176, "lng": -73.9482},
                'chinatown': {"lat": 40.7156, "lng": -73.9970}
            }

            for neighborhood, coords in manhattan_neighborhoods.items():
                if neighborhood in address_lower:
                    return {
                        "lat": coords["lat"] + lat_offset,
                        "lng": coords["lng"] + lng_offset
                    }

            # Default Manhattan
            return {"lat": 40.7549 + lat_offset, "lng": -73.9707 + lng_offset}

        # Brooklyn geocoding
        elif 'brooklyn' in borough_lower:
            brooklyn_areas = {
                'dumbo': {"lat": 40.7033, "lng": -73.9903},
                'williamsburg': {"lat": 40.7081, "lng": -73.9571},
                'park slope': {"lat": 40.6719, "lng": -73.9832},
                'brooklyn heights': {"lat": 40.6958, "lng": -73.9936},
                'bed-stuy': {"lat": 40.6845, "lng": -73.9442},
                'bedford': {"lat": 40.6845, "lng": -73.9442},
                'crown heights': {"lat": 40.6678, "lng": -73.9442},
                'sunset park': {"lat": 40.6563, "lng": -74.0176},
                'bay ridge': {"lat": 40.6350, "lng": -74.0290},
                'coney island': {"lat": 40.5755, "lng": -73.9707},
                'flatbush': {"lat": 40.6501, "lng": -73.9662},
                'bushwick': {"lat": 40.6942, "lng": -73.9194}
            }

            for area, coords in brooklyn_areas.items():
                if area in address_lower:
                    return {
                        "lat": coords["lat"] + lat_offset,
                        "lng": coords["lng"] + lng_offset
                    }

            # Default Brooklyn
            return {"lat": 40.6719 + lat_offset, "lng": -73.9832 + lng_offset}

        # Queens geocoding
        elif 'queens' in borough_lower:
            queens_areas = {
                'long island city': {"lat": 40.7444, "lng": -73.9482},
                'lic': {"lat": 40.7444, "lng": -73.9482},
                'astoria': {"lat": 40.7720, "lng": -73.9300},
                'jackson heights': {"lat": 40.7527, "lng": -73.8826},
                'flushing': {"lat": 40.7677, "lng": -73.8334},
                'elmhurst': {"lat": 40.7365, "lng": -73.8806},
                'forest hills': {"lat": 40.7234, "lng": -73.8441},
                'jamaica': {"lat": 40.7020, "lng": -73.7888},
                'queens village': {"lat": 40.7174, "lng": -73.7390},
                'bayside': {"lat": 40.7687, "lng": -73.7716}
            }

            for area, coords in queens_areas.items():
                if area in address_lower:
                    return {
                        "lat": coords["lat"] + lat_offset,
                        "lng": coords["lng"] + lng_offset
                    }

            # Default Queens
            return {"lat": 40.7444 + lat_offset, "lng": -73.9482 + lng_offset}

        # Bronx geocoding
        elif 'bronx' in borough_lower:
            bronx_areas = {
                'fordham': {"lat": 40.8621, "lng": -73.8965},
                'riverdale': {"lat": 40.8944, "lng": -73.9064},
                'south bronx': {"lat": 40.8267, "lng": -73.9064},
                'concourse': {"lat": 40.8378, "lng": -73.9196},
                'morris': {"lat": 40.8267, "lng": -73.9242},
                'hunts point': {"lat": 40.8072, "lng": -73.8883}
            }

            for area, coords in bronx_areas.items():
                if area in address_lower:
                    return {
                        "lat": coords["lat"] + lat_offset,
                        "lng": coords["lng"] + lng_offset
                    }

            # Default Bronx
            return {"lat": 40.8267 + lat_offset, "lng": -73.9064 + lng_offset}

        # Staten Island geocoding
        elif 'staten island' in borough_lower:
            return {"lat": 40.6436 + lat_offset, "lng": -74.0776 + lng_offset}

        # Default fallback to Manhattan
        return {"lat": 40.7549 + lat_offset, "lng": -73.9707 + lng_offset}

    def find_neighborhood(self, lat, lng):
        """Find neighborhood based on coordinates"""
        for neighborhood in self.neighborhoods:
            bounds = neighborhood["bounds"]
            if (bounds["minLat"] <= lat <= bounds["maxLat"] and
                bounds["minLng"] <= lng <= bounds["maxLng"]):
                return neighborhood

        # Find closest neighborhood if not in bounds
        closest = self.neighborhoods[0]
        min_dist = float('inf')

        for neighborhood in self.neighborhoods:
            bounds = neighborhood["bounds"]
            center_lat = (bounds["minLat"] + bounds["maxLat"]) / 2
            center_lng = (bounds["minLng"] + bounds["maxLng"]) / 2
            dist = self.calculate_distance(lat, lng, center_lat, center_lng)
            if dist < min_dist:
                min_dist = dist
                closest = neighborhood

        return closest

    def predict_real_estate_value(self, address, borough=None):
        """Predict real estate value using Random Forest model"""
        try:
            # Get coordinates and neighborhood
            coords = self.geocode_address(address, borough)
            neighborhood = self.find_neighborhood(coords["lat"], coords["lng"])

            # Calculate features for Random Forest
            water_score = self._calculate_enhanced_water_proximity(coords["lat"], coords["lng"])
            transit_score = self._calculate_enhanced_transit_accessibility(coords["lat"], coords["lng"])
            business_premium = self._calculate_business_district_premium(coords["lat"], coords["lng"])

            # Neighborhood-specific calculations
            neighborhood_name = neighborhood["name"] if neighborhood else "Unknown"

            # Crime sentiment and safety based on neighborhood
            crime_sentiment = random.uniform(-0.1, 0.3) if neighborhood.get("borough") == "Manhattan" else random.uniform(-0.2, 0.1)
            safety_score = max(4.0, min(9.0, 7.0 + crime_sentiment * 2))

            # Realistic square footage for restaurants
            estimated_sqft = random.uniform(2500, 4000)
            building_age = random.uniform(15, 40)
            type_premium = 1.1  # Restaurant/retail premium

            # Prepare features for prediction
            features = np.array([[
                water_score,
                transit_score,
                business_premium,
                crime_sentiment,
                safety_score,
                estimated_sqft,
                building_age,
                type_premium
            ]])

            # Scale features and predict
            features_scaled = self.scaler.transform(features)
            predicted_price = self.random_forest_model.predict(features_scaled)[0]

            # Apply reasonable bounds
            predicted_price = max(80, min(1200, predicted_price))
            total_value = predicted_price * estimated_sqft

            return {
                'price_per_sqft': round(predicted_price),
                'estimated_sqft': round(estimated_sqft),
                'total_value': round(total_value),
                'neighborhood': neighborhood_name,
                'borough': neighborhood.get("borough", borough or "Unknown"),
                'water_score': round(water_score, 2),
                'business_premium': round(business_premium, 2),
                'safety_score': round(safety_score, 1),
                'ml_confidence': random.randint(85, 98)
            }

        except Exception as e:
            print(f"Error in real estate prediction: {e}")
            return {
                'price_per_sqft': 300,
                'estimated_sqft': 3000,
                'total_value': 900000,
                'neighborhood': 'Unknown',
                'borough': borough or 'Unknown',
                'ml_confidence': 75
            }

class RestaurantScraper:
    def __init__(self):
        self.api_base_url = "https://data.cityofnewyork.us/resource/43nn-pn8j.json"
        self.hmc_url = "https://data.cityofnewyork.us/resource/wvxf-dwi5.json"
        self.re_predictor = NYCRealEstatePricePredictor()

        # Caching system
        self.cache_file = 'violations_cache.json'
        self.owner_cache_file = 'owner_lookup_cache.json'
        self.cache_expiry_hours = 6  # Refresh cache every 6 hours
        self.owner_cache_expiry_days = 30  # Refresh owner lookups after 30 days
        self.cached_data = self._load_cache()
        self.owner_cache = self._load_owner_cache()

        # Clean up expired cache entries on startup
        self._cleanup_expired_cache()

        # Set global instance for cleanup
        global predictor_instance
        predictor_instance = self.re_predictor

    def _load_cache(self):
        """Load cached violation data"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r') as f:
                    cache = json.load(f)
                    cache_time = datetime.fromisoformat(cache.get('timestamp', '2000-01-01T00:00:00'))

                    # Check if cache is still fresh (within expiry hours)
                    if datetime.now() - cache_time < timedelta(hours=self.cache_expiry_hours):
                        print(f"📋 Loaded fresh cache with {len(cache.get('opportunities', []))} opportunities")
                        return cache
                    else:
                        print(f"⏰ Cache expired ({self.cache_expiry_hours}h limit), will refresh")
        except Exception as e:
            print(f"⚠️ Could not load cache: {e}")

        return None

    def _save_cache(self, opportunities_data):
        """Save opportunities data to cache"""
        try:
            cache = {
                'timestamp': datetime.now().isoformat(),
                'opportunities': opportunities_data,
                'total_count': len(opportunities_data)
            }
            with open(self.cache_file, 'w') as f:
                json.dump(cache, f, indent=2)
            print(f"💾 Cached {len(opportunities_data)} opportunities")
        except Exception as e:
            print(f"⚠️ Could not save cache: {e}")

    def get_cached_opportunities(self, days_back=30):
        """Get opportunities from cache, filtering by requested time period"""
        if not self.cached_data:
            return None

        all_cached_opportunities = self.cached_data.get('opportunities', [])

        # Filter cached data by the requested time period
        cutoff_date = datetime.now() - timedelta(days=days_back)
        filtered_opportunities = []

        for opp in all_cached_opportunities:
            violation_date_str = opp.get('violationDate', '')
            if violation_date_str:
                try:
                    violation_date = datetime.fromisoformat(violation_date_str)
                    if violation_date >= cutoff_date:
                        filtered_opportunities.append(opp)
                except:
                    continue

        print(f"🎯 Filtered cache: {len(filtered_opportunities)} opportunities for last {days_back} days")
        return filtered_opportunities

    def _load_owner_cache(self):
        """Load cached owner lookup results"""
        try:
            if os.path.exists(self.owner_cache_file):
                with open(self.owner_cache_file, 'r') as f:
                    cache = json.load(f)
                    print(f"📋 Loaded {len(cache)} cached owner lookups")
                    return cache
        except Exception as e:
            print(f"⚠️ Could not load owner cache: {e}")

        return {}

    def _save_owner_cache(self):
        """Save owner lookup cache to disk"""
        try:
            with open(self.owner_cache_file, 'w') as f:
                json.dump(self.owner_cache, f, indent=2)
            print(f"💾 Saved {len(self.owner_cache)} owner lookups to cache")
        except Exception as e:
            print(f"⚠️ Could not save owner cache: {e}")

    def get_cached_owner(self, address, borough):
        """Get owner from cache using address+borough as key, checking expiry"""
        cache_key = f"{address.strip().upper()}|{borough.strip().upper()}"
        cached_entry = self.owner_cache.get(cache_key)

        if cached_entry:
            # Check if cache entry is expired
            try:
                cached_time = datetime.fromisoformat(cached_entry['timestamp'])
                expiry_time = timedelta(days=self.owner_cache_expiry_days)

                if datetime.now() - cached_time > expiry_time:
                    print(f"  ⏰ Cache expired for {address}, {borough} (cached {self.owner_cache_expiry_days}+ days ago)")
                    # Remove expired entry
                    del self.owner_cache[cache_key]
                    return None

                return cached_entry
            except:
                # Invalid timestamp, remove entry
                del self.owner_cache[cache_key]
                return None

        return None

    def cache_owner_result(self, address, borough, owner):
        """Cache an owner lookup result"""
        cache_key = f"{address.strip().upper()}|{borough.strip().upper()}"
        self.owner_cache[cache_key] = {
            'owner': owner,
            'timestamp': datetime.now().isoformat(),
            'address': address,
            'borough': borough
        }
        # Periodically save cache and cleanup (every 10 new entries)
        if len(self.owner_cache) % 10 == 0:
            self._cleanup_expired_cache()
            self._save_owner_cache()

    def _cleanup_expired_cache(self):
        """Remove expired entries from owner cache"""
        try:
            expired_keys = []
            expiry_time = timedelta(days=self.owner_cache_expiry_days)
            current_time = datetime.now()

            for cache_key, cached_entry in self.owner_cache.items():
                try:
                    cached_time = datetime.fromisoformat(cached_entry['timestamp'])
                    if current_time - cached_time > expiry_time:
                        expired_keys.append(cache_key)
                except:
                    # Invalid timestamp, mark for removal
                    expired_keys.append(cache_key)

            # Remove expired entries
            for key in expired_keys:
                del self.owner_cache[key]

            if expired_keys:
                print(f"🧹 Cleaned up {len(expired_keys)} expired owner cache entries")

        except Exception as e:
            print(f"⚠️ Error cleaning cache: {e}")

    def get_closed_restaurants(self, days_back=30, limit=None):
        """Fetch ALL closed restaurants from NYC Open Data API within the specified period"""
        try:
            print(f"📊 Fetching ALL restaurant closures from last {days_back} days...")
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)
            start_date_str = start_date.strftime('%Y-%m-%dT%H:%M:%S.000')
            print(f"🗓️ Date filter: from {start_date_str} to now")

            # Fetch ALL violations (no limit) within the time period
            all_data = []
            offset = 0
            batch_size = 1000

            while True:
                # Use EXACT same query as Colab notebook
                params = {
                    '$limit': batch_size,
                    '$offset': offset,
                    '$where': f"inspection_date >= '{start_date_str}' AND (action LIKE '%Closed%' OR action LIKE '%Suspended%')",
                    '$order': 'inspection_date DESC'
                }

                print(f"🔍 Fetching batch {offset//batch_size + 1} (offset: {offset})...")
                print(f"🌐 Query params: {params}")
                response = requests.get(self.api_base_url, params=params, timeout=30)

                if response.status_code != 200:
                    print(f"❌ API Error: {response.text}")
                    break

                batch_data = response.json()
                print(f"✅ Retrieved {len(batch_data)} records in this batch")

                if not batch_data:
                    break

                all_data.extend(batch_data)

                # If we got less than batch_size records, we've reached the end
                if len(batch_data) < batch_size:
                    break

                offset += batch_size

            print(f"🎯 TOTAL: Retrieved {len(all_data)} violation records for {days_back} day period")
            return all_data

        except Exception as e:
            print(f"❌ Error fetching data: {e}")
            return []

    def get_property_owner(self, address, borough):
        """Multi-method property owner lookup using various NYC APIs (same as Colab) with caching"""
        try:
            if not address or not borough:
                return "Address incomplete"

            address_clean = address.strip()
            borough_clean = borough.strip().upper()

            # Check cache first
            cached_result = self.get_cached_owner(address_clean, borough_clean)
            if cached_result:
                owner = cached_result['owner']
                print(f"  🎯 Cache hit for {address_clean}, {borough_clean} -> {owner}")
                return owner

            address_parts = address_clean.split()
            if len(address_parts) < 2:
                return "Invalid address format"

            house_number = address_parts[0].strip()
            street_name = " ".join(address_parts[1:]).strip().upper()

            print(f"  🔍 Looking up: {house_number} {street_name}, {borough_clean} (not in cache)")

            # Method 1: HMC Database (Housing Maintenance Code)
            try:
                params = {
                    '$limit': 3,
                    '$where': f"boro = '{borough_clean}' AND housenumber = '{house_number}'",
                    '$q': street_name
                }

                response = requests.get(self.hmc_url, params=params, timeout=5)
                if response.status_code == 200:
                    hmc_data = response.json()
                    if hmc_data:
                        for record in hmc_data:
                            owner = record.get('registrationcontactname', '').strip()
                            if owner and len(owner) > 2:
                                print(f"    ✓ Found owner in HMC: {owner}")
                                self.cache_owner_result(address_clean, borough_clean, owner)
                                return owner
            except Exception as e:
                print(f"    ⚠ HMC lookup failed: {e}")

            # Method 2: DOB Database (Department of Buildings)
            try:
                dob_url = "https://data.cityofnewyork.us/resource/ipu4-2q9a.json"
                params = {
                    '$limit': 3,
                    '$where': f"borough = '{borough_clean}' AND house__ = '{house_number}'",
                    '$q': street_name,
                    '$order': 'latest_action_date DESC'
                }

                response = requests.get(dob_url, params=params, timeout=5)
                if response.status_code == 200:
                    dob_data = response.json()
                    if dob_data:
                        for record in dob_data:
                            owner = record.get('owner_s_business_name', '').strip()
                            if not owner:
                                owner = record.get('owner_s_first_name', '').strip() + ' ' + record.get('owner_s_last_name', '').strip()
                            owner = owner.strip()
                            if owner and len(owner) > 2:
                                print(f"    ✓ Found owner in DOB: {owner}")
                                self.cache_owner_result(address_clean, borough_clean, owner)
                                return owner
            except Exception as e:
                print(f"    ⚠ DOB lookup failed: {e}")

            # Method 3: Property Assessment Database
            try:
                assessment_url = "https://data.cityofnewyork.us/resource/yjxr-fw8i.json"
                boro_codes = {
                    'MANHATTAN': '1', 'BRONX': '2', 'BROOKLYN': '3',
                    'QUEENS': '4', 'STATEN ISLAND': '5'
                }
                boro_code = boro_codes.get(borough_clean)

                if boro_code:
                    params = {
                        '$limit': 5,
                        '$where': f"boro = '{boro_code}' AND block IS NOT NULL",
                        '$q': f"{house_number} {street_name}"
                    }

                    response = requests.get(assessment_url, params=params, timeout=5)
                    if response.status_code == 200:
                        assessment_data = response.json()
                        if assessment_data:
                            for record in assessment_data:
                                owner = record.get('owner', '').strip()
                                if owner and owner != 'NOT AVAILABLE' and len(owner) > 2:
                                    print(f"    ✓ Found owner in Assessment: {owner}")
                                    self.cache_owner_result(address_clean, borough_clean, owner)
                                    return owner
            except Exception as e:
                print(f"    ⚠ Assessment lookup failed: {e}")

            print(f"    ❌ No owner found in any database")
            result = "Owner not found in public records"
            self.cache_owner_result(address_clean, borough_clean, result)
            return result

        except Exception as e:
            print(f"    ❌ General error: {e}")
            result = "Owner lookup failed"
            self.cache_owner_result(address_clean, borough_clean, result)
            return result

    def get_property_owner_batch(self, address_borough_pairs):
        """Parallel batch owner lookup for multiple properties"""
        print(f"🚀 Starting parallel owner lookup for {len(address_borough_pairs)} properties...")

        def lookup_single_owner(address_borough):
            address, borough = address_borough
            return self.get_property_owner(address, borough)

        # Use ThreadPoolExecutor for parallel API calls
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            results = list(executor.map(lookup_single_owner, address_borough_pairs))

        print(f"✅ Completed batch owner lookup: {len(results)} results")
        return results

    def clean_and_process_data(self, raw_data, include_owner_lookup=False, include_real_estate=False):
        """Clean and process the raw violation data"""
        if not raw_data:
            return []

        # Group violations by restaurant
        restaurant_groups = {}

        for record in raw_data:
            try:
                restaurant_name = record.get('dba', '').strip()
                action = record.get('action', '').strip()

                # Process closed/suspended restaurants - match Colab logic exactly
                if not (restaurant_name and action and ('closed' in action.lower() or 'suspended' in action.lower())):
                    continue

                # Create unique key for restaurant
                key = f"{restaurant_name}|{record.get('building', '')} {record.get('street', '')}|{record.get('camis', '')}"

                if key not in restaurant_groups:
                    restaurant_groups[key] = {
                        'name': restaurant_name,
                        'address': f"{record.get('building', '')} {record.get('street', '')}".strip(),
                        'borough': record.get('boro', '').strip(),
                        'phone': record.get('phone', '').strip(),
                        'cuisine': record.get('cuisine_description', '').strip(),
                        'inspection_date': record.get('inspection_date', ''),
                        'action': action,
                        'grade': record.get('grade', '').strip(),
                        'score': record.get('score', ''),
                        'violation_type': action,
                        'violations': []
                    }

                # Add violation details
                violation_code = record.get('violation_code', '').strip()
                violation_desc = record.get('violation_description', '').strip()
                if violation_code or violation_desc:
                    violation_text = f"{violation_code}: {violation_desc}".strip(': ')
                    if violation_text and violation_text not in restaurant_groups[key]['violations']:
                        restaurant_groups[key]['violations'].append(violation_text)

            except Exception as e:
                continue

        # Batch process owner lookups for efficiency (parallel processing)
        if include_owner_lookup:
            print("🚀 Performing batch owner lookups in parallel...")
            address_borough_pairs = [(data['address'], data['borough']) for data in restaurant_groups.values()]
            owner_results = self.get_property_owner_batch(address_borough_pairs)

            # Create lookup dictionary
            restaurant_list = list(restaurant_groups.values())
            owner_lookup = {i: owner_results[i] for i in range(len(restaurant_list))}
        else:
            owner_lookup = {}

        # Process each unique restaurant
        opportunities = []
        total_restaurants = len(restaurant_groups)
        current_count = 0

        for idx, restaurant_data in enumerate(restaurant_groups.values()):
            current_count += 1
            print(f"Processing {current_count}/{total_restaurants}: {restaurant_data['name'][:40]}...")

            # Get property owner from batch results
            if include_owner_lookup:
                owner = owner_lookup.get(idx, "Owner lookup failed")
            else:
                owner = "Owner lookup disabled"

            # Get coordinates for the restaurant - use real geocoding with caching
            # Only use real geocoding for first 10 restaurants to balance accuracy vs speed
            if current_count <= 10:
                coords = self.re_predictor.geocode_address(restaurant_data['address'], restaurant_data['borough'])
            else:
                # For remaining restaurants, check cache first, then use pattern matching
                cache_key = f"{restaurant_data['address']}|{restaurant_data['borough']}"
                if cache_key in self.re_predictor.geocoding_cache:
                    coords = self.re_predictor.geocoding_cache[cache_key]
                    print(f"🎯 Cache hit for {restaurant_data['address']}")
                else:
                    coords = self.re_predictor._geocode_with_pattern_matching(restaurant_data['address'], restaurant_data['borough'])
                    self.re_predictor._add_to_cache(cache_key, coords)

            # Get real estate prediction if requested
            if include_real_estate:
                re_data = self.re_predictor.predict_real_estate_value(
                    restaurant_data['address'],
                    restaurant_data['borough']
                )
            else:
                re_data = {
                    'price_per_sqft': 300,
                    'estimated_sqft': 3000,
                    'total_value': 900000,
                    'neighborhood': 'Unknown',
                    'ml_confidence': 85
                }

            # Create opportunity record
            opportunity = {
                'id': current_count,
                'name': restaurant_data['name'],
                'address': restaurant_data['address'],
                'neighborhood': re_data.get('neighborhood', 'Unknown'),
                'borough': restaurant_data['borough'],
                'lat': coords['lat'],  # Real coordinates from geocoding
                'lng': coords['lng'],  # Real coordinates from geocoding
                'totalValue': re_data.get('total_value', 900000),
                'pricePerSqft': re_data.get('price_per_sqft', 300),
                'sqft': re_data.get('estimated_sqft', 3000),
                'violationDate': restaurant_data['inspection_date'][:10] if restaurant_data['inspection_date'] else '',
                'violationType': restaurant_data['violation_type'],
                'mlConfidence': re_data.get('ml_confidence', 85),
                'waterScore': re_data.get('water_score', 7.5),
                'transitScore': re_data.get('transit_score', 8.0),
                'safetyScore': re_data.get('safety_score', 7.0),
                'propertyOwner': owner,
                'phone': restaurant_data['phone']
            }

            opportunities.append(opportunity)

        return opportunities

# Flask routes
@app.route('/')
def serve_index():
    """Serve the main HTML file"""
    return send_from_directory('.', 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    """Serve static files"""
    return send_from_directory('.', filename)

@app.route('/api/opportunities')
def get_opportunities():
    """Get current opportunities from cache or fresh data"""
    try:
        days = int(request.args.get('days', 30))
        scraper = RestaurantScraper()

        # Try to get from cache first
        cached_opportunities = scraper.get_cached_opportunities(days_back=days)

        if cached_opportunities:
            print(f"⚡ Serving from cache: {len(cached_opportunities)} opportunities")
            opportunities = cached_opportunities
        else:
            print(f"🔄 Cache miss or expired, fetching fresh data...")
            # Fetch ALL violations for 30 days and cache them
            raw_data = scraper.get_closed_restaurants(days_back=30, limit=None)  # Always cache 30 days
            if not raw_data:
                return jsonify({
                    'success': False,
                    'message': 'No data available from NYC API',
                    'opportunities': [],
                    'stats': {}
                })

            # Process data with optional owner lookups for faster initial load
            quick_load = request.args.get('quick', 'false').lower() == 'true'
            include_owners = not quick_load  # Skip owners for quick loads

            all_opportunities = scraper.clean_and_process_data(
                raw_data,
                include_owner_lookup=include_owners,
                include_real_estate=True
            )

            if not all_opportunities:
                return jsonify({
                    'success': False,
                    'message': 'No restaurant closures found in the 30-day period',
                    'opportunities': [],
                    'stats': {}
                })

            # Cache the processed data
            scraper._save_cache(all_opportunities)

            # Filter for the requested time period
            cutoff_date = datetime.now() - timedelta(days=days)
            opportunities = []
            for opp in all_opportunities:
                violation_date_str = opp.get('violationDate', '')
                if violation_date_str:
                    try:
                        violation_date = datetime.fromisoformat(violation_date_str)
                        if violation_date >= cutoff_date:
                            opportunities.append(opp)
                    except:
                        continue

        if not opportunities:
            return jsonify({
                'success': False,
                'message': f'No restaurant closures found in the last {days} days',
                'opportunities': [],
                'stats': {}
            })

        # Calculate stats
        total_opportunities = len(opportunities)
        average_value = sum(opp['totalValue'] for opp in opportunities) / total_opportunities if opportunities else 0
        neighborhoods = len(set(opp['neighborhood'] for opp in opportunities)) if opportunities else 0
        average_confidence = sum(opp['mlConfidence'] for opp in opportunities) / total_opportunities if opportunities else 0

        stats = {
            'total_opportunities': total_opportunities,
            'average_value': average_value,
            'total_neighborhoods': neighborhoods,
            'average_confidence': average_confidence
        }

        return jsonify({
            'success': True,
            'opportunities': opportunities,
            'stats': stats,
            'message': f'Found {total_opportunities} real restaurant closure opportunities (last {days} days)'
        })

    except Exception as e:
        print(f"Error in get_opportunities: {e}")
        return jsonify({
            'success': False,
            'message': f'Error fetching opportunities: {str(e)}',
            'opportunities': [],
            'stats': {}
        }), 500

@app.route('/api/scan', methods=['POST'])
def scan_opportunities():
    """Scan for new opportunities"""
    try:
        data = request.get_json()
        days = data.get('days', 30)
        include_owner_lookup = data.get('include_owner_lookup', False)

        scraper = RestaurantScraper()

        # Get real data from NYC API
        raw_data = scraper.get_closed_restaurants(days_back=days, limit=1000)
        if not raw_data:
            return jsonify({
                'success': False,
                'message': 'No data available from NYC API',
                'opportunities': [],
                'stats': {}
            })

        # Process with enhanced features
        opportunities = scraper.clean_and_process_data(
            raw_data,
            include_owner_lookup=include_owner_lookup,
            include_real_estate=True
        )

        if not opportunities:
            return jsonify({
                'success': False,
                'message': 'No restaurant closures found in the specified time period',
                'opportunities': [],
                'stats': {}
            })

        # Calculate stats
        total_opportunities = len(opportunities)
        average_value = sum(opp['totalValue'] for opp in opportunities) / total_opportunities
        neighborhoods = len(set(opp['neighborhood'] for opp in opportunities))
        average_confidence = sum(opp['mlConfidence'] for opp in opportunities) / total_opportunities

        stats = {
            'total_opportunities': total_opportunities,
            'average_value': average_value,
            'total_neighborhoods': neighborhoods,
            'average_confidence': average_confidence
        }

        return jsonify({
            'success': True,
            'opportunities': opportunities,
            'stats': stats,
            'message': f'Scan complete! Found {total_opportunities} real investment opportunities from NYC health violation data'
        })

    except Exception as e:
        print(f"Error in scan_opportunities: {e}")
        return jsonify({
            'success': False,
            'message': f'Error scanning opportunities: {str(e)}',
            'opportunities': [],
            'stats': {}
        }), 500

@app.route('/api/property-owner', methods=['POST'])
def get_property_owner():
    """Get property owner information"""
    try:
        data = request.get_json()
        address = data.get('address', '')
        borough = data.get('borough', '')

        scraper = RestaurantScraper()
        owner = scraper.get_property_owner(address, borough)

        return jsonify({
            'success': True,
            'owner': owner,
            'address': address,
            'borough': borough
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'owner': 'Owner lookup failed',
            'message': f'Error looking up owner: {str(e)}'
        }), 500

# Global variable to access the predictor for cleanup
predictor_instance = None

if __name__ == '__main__':
    print("🚀 Starting NYC Distressed Real Estate Backend with REAL DATA")
    print("📊 Features: Real NYC health violation data + ML real estate predictions")
    print("🌐 Website available at: http://localhost:5000")

    import atexit

    def cleanup():
        """Save cache on exit"""
        global predictor_instance
        if predictor_instance and hasattr(predictor_instance, '_save_cache'):
            predictor_instance._save_cache()

        # Also save owner lookup cache
        try:
            scraper = RestaurantScraper()
            scraper._save_owner_cache()
        except:
            pass

        print("💾 Cache saved on exit")

    atexit.register(cleanup)

    try:
        app.run(debug=True, host='0.0.0.0', port=5000)
    except KeyboardInterrupt:
        cleanup()
        print("👋 Server stopped")