#!/usr/bin/env python3
"""
Test the API to ensure it returns properly formatted data for the frontend
"""

from app import app
import json

def test_api():
    app.config['TESTING'] = True
    with app.test_client() as client:
        response = client.get('/api/opportunities?days=7')
        print('Status:', response.status_code)

        if response.status_code == 200:
            data = response.get_json()
            if data['success'] and data['opportunities']:
                opp = data['opportunities'][0]
                print('Sample opportunity:')
                print(f'  Address: {opp["address"]}')
                print(f'  Price/sqft: ${opp["pricePerSqft"]}')
                print(f'  Transit Score: {opp["transitScore"]}')
                print(f'  Water Score: {opp["waterScore"]}')
                print(f'  Safety Score: {opp["safetyScore"]}')
                print(f'  Total Value: ${opp["totalValue"]:,}')
                print('✅ API working correctly')
                return True
            else:
                print('❌ No opportunities returned:', data.get('message', 'Unknown'))
                return False
        else:
            print('❌ API error')
            return False

if __name__ == "__main__":
    test_api()