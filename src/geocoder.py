"""
Geocoding module for extracting latitude and longitude from addresses.
Supports multiple geocoding services: ArcGIS (recommended for Hebrew) and Nominatim (OpenStreetMap).
Includes persistent caching to avoid duplicate API calls.
"""

from geopy.geocoders import Nominatim, ArcGIS
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import time
import re
import os
import json
import hashlib


class Geocoder:
    """
    Geocoder class for converting addresses to latitude/longitude coordinates.
    Supports ArcGIS (better for Hebrew) with Nominatim fallback.
    Includes persistent file-based caching to avoid duplicate API calls.
    """
    
    def __init__(self, user_agent="therapist-admin-tool", timeout=10, arcgis_username=None, arcgis_password=None, cache_file=None):
        """
        Initialize the geocoder with multiple service options and persistent cache.
        
        Args:
            user_agent: User agent string for API requests
            timeout: Request timeout in seconds
            arcgis_username: Optional ArcGIS username (better for Hebrew addresses)
            arcgis_password: Optional ArcGIS password
            cache_file: Path to cache file (default: geocache.json in script dir)
        """
        self.timeout = timeout
        
        # Set up persistent cache
        if cache_file is None:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            cache_file = os.path.join(script_dir, 'geocache.json')
        
        self.cache_file = cache_file
        self.cache = self._load_cache()
        
        print(f"Geocoding cache loaded: {len(self.cache)} addresses cached")
        
        # Initialize geocoding services
        self.services = []
        
        # Try to initialize ArcGIS (better for Hebrew addresses)
        try:
            if arcgis_username and arcgis_password:
                self.services.append(('ArcGIS', ArcGIS(username=arcgis_username, password=arcgis_password, timeout=timeout)))
                print("ArcGIS geocoder initialized (recommended for Hebrew addresses)")
            else:
                # Try without auth (limited free tier)
                self.services.append(('ArcGIS', ArcGIS(timeout=timeout)))
                print("ArcGIS geocoder initialized in free tier mode")
        except Exception as e:
            print(f"Could not initialize ArcGIS: {e}")
        
        # Always add Nominatim as fallback
        self.services.append(('Nominatim', Nominatim(user_agent=user_agent, timeout=timeout)))
        print(f"Nominatim geocoder initialized as {'fallback' if len(self.services) > 1 else 'primary'}")
    
    def _load_cache(self):
        """Load geocoding cache from file."""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                    # Convert string keys back to tuples
                    return {k: tuple(v) if v else (None, None) for k, v in cache_data.items()}
            except Exception as e:
                print(f"Warning: Could not load cache file: {e}")
                return {}
        return {}
    
    def _save_cache(self):
        """Save geocoding cache to file."""
        try:
            # Convert tuples to lists for JSON serialization
            cache_data = {k: list(v) if v[0] is not None else None for k, v in self.cache.items()}
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Warning: Could not save cache file: {e}")
    
    def _hash_address(self, address):
        """Create a hash of the address for cache key (optional, using address directly for readability)."""
        return hashlib.md5(address.encode('utf-8')).hexdigest()
    
    def clean_address(self, address):
        """
        Clean and normalize address for better geocoding.
        Removes online/zoom mentions and extracts primary location.
        
        Args:
            address: Raw address string
            
        Returns:
            Cleaned address string or None if address is not physical
        """
        if not address:
            return None
        
        address = address.strip()
        address_lower = address.lower()
        
        # Check for online-only indicators
        online_indicators = ['זום', 'zoom', 'און ליין', 'online', 'און ליין', 'און-ליין']
        
        # If it's ONLY online (no "and"), skip it
        if any(indicator in address_lower for indicator in online_indicators):
            # Check if there's also a physical location mentioned
            if not any(word in address_lower for word in ['וגם', 'ו-', ',', 'גם ב']):
                return None
        
        # Extract first location if multiple are mentioned (split by ו or comma)
        # Handle cases like "זכרון יעקב ות״א" -> take "זכרון יעקב"
        if ' ו' in address or ', ' in address:
            parts = re.split(r'\s+ו|,\s*', address)
            # Find the first part that doesn't contain online indicators
            for part in parts:
                part_clean = part.strip()
                if part_clean and not any(ind in part_clean.lower() for ind in online_indicators):
                    address = part_clean
                    break
        
        # Remove parenthetical notes like "(מרכז חיבורים)"
        address = re.sub(r'\([^)]*\)', '', address).strip()
        
        # Remove floor/apartment info for better geocoding (keep street address)
        # But keep the base address
        address = address.replace('קומה', '').replace('דירה', '')
        
        return address if address else None
        
    def geocode_address(self, address, retry_count=2, retry_delay=1):
        """
        Convert an address string to latitude and longitude.
        Tries multiple geocoding services (ArcGIS first, then Nominatim) with Hebrew address support.
        
        Args:
            address: Address string to geocode
            retry_count: Number of retries on timeout per service
            retry_delay: Delay between retries in seconds
            
        Returns:
            Tuple of (latitude, longitude) or (None, None) if geocoding fails
        """
        if not address or not isinstance(address, str):
            return None, None
            
        original_address = address.strip()
        
        # Check cache first (using original address as key)
        if original_address in self.cache:
            return self.cache[original_address]
        
        # Clean the address
        cleaned_address = self.clean_address(original_address)
        
        if not cleaned_address:
            # Address is online-only or invalid
            print(f"Skipping non-physical address: {original_address}")
            self.cache[original_address] = (None, None)
            return None, None
        
        # Try each geocoding service
        for service_name, geolocator in self.services:
            # Prepare address variants based on service
            if service_name == 'ArcGIS':
                # ArcGIS handles Hebrew well, try with and without country
                address_variants = [
                    cleaned_address,
                    cleaned_address + ", Israel",
                ]
            else:  # Nominatim
                address_variants = [
                    cleaned_address + ", Israel",
                    cleaned_address + ", ישראל",
                    cleaned_address,
                ]
            
            # Try variants with retries
            for variant in address_variants:
                for attempt in range(retry_count):
                    try:
                        if service_name == 'Nominatim':
                            location = geolocator.geocode(variant, language='he')
                        else:
                            location = geolocator.geocode(variant)
                        
                        if location:
                            lat, lng = location.latitude, location.longitude
                            self.cache[original_address] = (lat, lng)
                            self._save_cache()  # Persist to file immediately
                            if service_name != 'Nominatim':
                                print(f"Geocoded with {service_name}: {original_address}")
                            return lat, lng
                            
                    except GeocoderTimedOut:
                        if attempt < retry_count - 1:
                            time.sleep(retry_delay)
                            continue
                            
                    except GeocoderServiceError:
                        # Service error, try next variant or service
                        break
                        
                    except Exception as e:
                        # Unexpected error, try next variant or service
                        if "rate limit" in str(e).lower():
                            print(f"{service_name} rate limit reached, trying next service...")
                            break
                        break
        
        # All services and variants failed
        print(f"Geocoding failed for address: {original_address}")
        self.cache[original_address] = (None, None)
        self._save_cache()  # Persist failures too to avoid retrying
        return None, None
    
    def get_cache_stats(self):
        """
        Get statistics about the geocoding cache.
        
        Returns:
            Dictionary with cache statistics
        """
        total = len(self.cache)
        successful = sum(1 for v in self.cache.values() if v[0] is not None)
        failed = total - successful
        
        return {
            'total_addresses': total,
            'successful_geocodes': successful,
            'failed_geocodes': failed
        }
