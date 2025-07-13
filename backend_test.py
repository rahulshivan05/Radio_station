import requests
import sys
from datetime import datetime
import json

class RadioAPITester:
    def __init__(self, base_url="https://10f78334-d4d6-4418-bb73-da1a3ad115ea.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0

    def run_test(self, name, method, endpoint, expected_status, params=None, data=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=30)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    if isinstance(response_data, list):
                        print(f"   Response: List with {len(response_data)} items")
                        if len(response_data) > 0:
                            print(f"   Sample item keys: {list(response_data[0].keys())}")
                    else:
                        print(f"   Response keys: {list(response_data.keys()) if isinstance(response_data, dict) else 'Not a dict'}")
                except:
                    print(f"   Response: {response.text[:100]}...")
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"   Response: {response.text[:200]}...")

            return success, response.json() if response.status_code == 200 else {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_popular_stations(self):
        """Test getting popular stations"""
        success, response = self.run_test(
            "Get Popular Stations",
            "GET",
            "api/radio/popular",
            200,
            params={"limit": 10}
        )
        return success, response

    def test_search_stations(self):
        """Test station search functionality"""
        # Test basic search
        success1, response1 = self.run_test(
            "Search Stations (Basic)",
            "GET",
            "api/radio/search",
            200,
            params={"limit": 5}
        )
        
        # Test search with name filter
        success2, response2 = self.run_test(
            "Search Stations (By Name)",
            "GET",
            "api/radio/search",
            200,
            params={"name": "BBC", "limit": 5}
        )
        
        # Test search with country filter
        success3, response3 = self.run_test(
            "Search Stations (By Country)",
            "GET",
            "api/radio/search",
            200,
            params={"country": "United States", "limit": 5}
        )
        
        return success1 and success2 and success3, response1

    def test_countries_endpoint(self):
        """Test getting countries list"""
        success, response = self.run_test(
            "Get Countries",
            "GET",
            "api/radio/countries",
            200
        )
        return success, response

    def test_genres_endpoint(self):
        """Test getting genres list"""
        success, response = self.run_test(
            "Get Genres",
            "GET",
            "api/radio/genres",
            200,
            params={"limit": 20}
        )
        return success, response

    def test_station_click(self, station_uuid):
        """Test station click tracking"""
        success, response = self.run_test(
            "Station Click Tracking",
            "POST",
            f"api/radio/click/{station_uuid}",
            200
        )
        return success, response

    def test_station_details(self, station_uuid):
        """Test getting station details"""
        success, response = self.run_test(
            "Get Station Details",
            "GET",
            f"api/radio/station/{station_uuid}",
            200
        )
        return success, response

    def test_root_endpoint(self):
        """Test root API endpoint"""
        success, response = self.run_test(
            "Root API Endpoint",
            "GET",
            "api/",
            200
        )
        return success, response

def main():
    print("🎵 Starting Radio API Tests...")
    print("=" * 50)
    
    # Setup
    tester = RadioAPITester()
    
    # Test 1: Root endpoint
    print("\n📡 Testing Basic API Connectivity...")
    tester.test_root_endpoint()
    
    # Test 2: Popular stations
    print("\n🌟 Testing Popular Stations...")
    success, popular_stations = tester.test_popular_stations()
    
    # Test 3: Countries
    print("\n🌍 Testing Countries Endpoint...")
    countries_success, countries = tester.test_countries_endpoint()
    
    # Test 4: Genres
    print("\n🎼 Testing Genres Endpoint...")
    genres_success, genres = tester.test_genres_endpoint()
    
    # Test 5: Search functionality
    print("\n🔍 Testing Search Functionality...")
    search_success, search_results = tester.test_search_stations()
    
    # Test 6: Station-specific endpoints (if we have stations)
    if success and popular_stations and len(popular_stations) > 0:
        print("\n📻 Testing Station-Specific Endpoints...")
        station_uuid = popular_stations[0].get('stationuuid')
        if station_uuid:
            tester.test_station_click(station_uuid)
            tester.test_station_details(station_uuid)
        else:
            print("⚠️  No station UUID found in popular stations")
    
    # Print final results
    print("\n" + "=" * 50)
    print(f"📊 Final Results: {tester.tests_passed}/{tester.tests_run} tests passed")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All tests passed! Radio API is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the API implementation.")
        return 1

if __name__ == "__main__":
    sys.exit(main())