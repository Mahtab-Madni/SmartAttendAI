"""
Geofencing Module
Verifies user location is within authorized boundaries
"""
import math
from typing import Tuple, Dict, Optional
from dataclasses import dataclass
import requests
import json

@dataclass
class Location:
    """Represents a geographic location"""
    latitude: float
    longitude: float
    accuracy: float = 0.0  # meters
    
    def __str__(self):
        return f"({self.latitude:.6f}, {self.longitude:.6f})"


class GeofenceValidator:
    """
    Validates if a location is within allowed geofence boundaries
    """
    def __init__(self, config: Dict):
        self.config = config
        self.radius_meters = config["RADIUS_METERS"]
        self.classroom_locations = config["CLASSROOM_LOCATIONS"]
    
    def haversine_distance(self, loc1: Location, loc2: Location) -> float:
        """
        Calculate distance between two points using Haversine formula
        
        Returns distance in meters
        """
        # Earth radius in meters
        R = 6371000
        
        # Convert to radians
        lat1_rad = math.radians(loc1.latitude)
        lat2_rad = math.radians(loc2.latitude)
        delta_lat = math.radians(loc2.latitude - loc1.latitude)
        delta_lon = math.radians(loc2.longitude - loc1.longitude)
        
        # Haversine formula
        a = (math.sin(delta_lat / 2) ** 2 +
             math.cos(lat1_rad) * math.cos(lat2_rad) *
             math.sin(delta_lon / 2) ** 2)
        
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        distance = R * c
        return distance
    
    def is_within_geofence(self, user_location: Location, 
                          classroom_name: str) -> Tuple[bool, float, str]:
        """
        Check if user is within the geofence of specified classroom
        
        Returns:
            Tuple of (is_valid, distance_meters, message)
        """
        if classroom_name not in self.classroom_locations:
            return False, 0, f"Classroom '{classroom_name}' not configured"
        
        classroom_coords = self.classroom_locations[classroom_name]
        classroom_location = Location(
            latitude=classroom_coords["lat"],
            longitude=classroom_coords["lon"]
        )
        
        distance = self.haversine_distance(user_location, classroom_location)
        
        if distance <= self.radius_meters:
            return True, distance, f"Within geofence ({distance:.1f}m from classroom)"
        else:
            return False, distance, f"Outside geofence ({distance:.1f}m from classroom, max: {self.radius_meters}m)"
    
    def get_nearest_classroom(self, user_location: Location) -> Tuple[Optional[str], float]:
        """
        Find the nearest classroom to user's location
        
        Returns:
            Tuple of (classroom_name, distance_meters)
        """
        if not self.classroom_locations:
            return None, float('inf')
        
        nearest_classroom = None
        min_distance = float('inf')
        
        for classroom_name, coords in self.classroom_locations.items():
            classroom_location = Location(
                latitude=coords["lat"],
                longitude=coords["lon"]
            )
            
            distance = self.haversine_distance(user_location, classroom_location)
            
            if distance < min_distance:
                min_distance = distance
                nearest_classroom = classroom_name
        
        return nearest_classroom, min_distance
    
    def add_classroom(self, name: str, latitude: float, longitude: float):
        """Add a new classroom location"""
        self.classroom_locations[name] = {
            "lat": latitude,
            "lon": longitude
        }
    
    def remove_classroom(self, name: str) -> bool:
        """Remove a classroom location"""
        if name in self.classroom_locations:
            del self.classroom_locations[name]
            return True
        return False
    
    def list_classrooms(self) -> Dict:
        """Get list of all configured classrooms"""
        return self.classroom_locations.copy()


class LocationProvider:
    """
    Provides user's current location using various methods
    """
    
    @staticmethod
    def get_location_from_ip() -> Optional[Location]:
        """
        Get approximate location based on IP address
        Note: This is less accurate but works as fallback
        """
        try:
            response = requests.get('https://ipapi.co/json/', timeout=5)
            if response.status_code == 200:
                data = response.json()
                return Location(
                    latitude=data['latitude'],
                    longitude=data['longitude'],
                    accuracy=data.get('accuracy', 1000)  # IP-based is ~1km accurate
                )
        except Exception as e:
            print(f"Error getting location from IP: {e}")
        
        return None
    
    @staticmethod
    def get_location_from_gps(latitude: float, longitude: float, 
                            accuracy: float = 10.0) -> Location:
        """
        Create location from GPS coordinates (from mobile app)
        
        Args:
            latitude: GPS latitude
            longitude: GPS longitude  
            accuracy: GPS accuracy in meters
        """
        return Location(latitude, longitude, accuracy)
    
    @staticmethod
    def get_location_from_browser() -> str:
        """
        Returns JavaScript code to get location from browser
        This would be used in the web interface
        """
        js_code = """
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                function(position) {
                    const location = {
                        latitude: position.coords.latitude,
                        longitude: position.coords.longitude,
                        accuracy: position.coords.accuracy
                    };
                    // Send to backend
                    fetch('/api/attendance/submit', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify(location)
                    });
                },
                function(error) {
                    console.error('Geolocation error:', error);
                    alert('Please enable location access to mark attendance');
                },
                {
                    enableHighAccuracy: true,
                    timeout: 10000,
                    maximumAge: 0
                }
            );
        } else {
            alert('Geolocation is not supported by this browser');
        }
        """
        return js_code


class GeofenceSecurity:
    """
    Additional security measures for geofencing
    """
    
    @staticmethod
    def detect_gps_spoofing(location: Location, 
                           expected_accuracy: float = 50.0) -> Tuple[bool, str]:
        """
        Detect potential GPS spoofing
        
        Returns:
            Tuple of (is_suspicious, reason)
        """
        # Check 1: Accuracy too perfect (spoofed GPS often has unrealistic accuracy)
        if location.accuracy < 1.0:
            return True, "Suspiciously high GPS accuracy (< 1m)"
        
        # Check 2: Accuracy too poor
        if location.accuracy > 500.0:
            return True, f"Poor GPS accuracy ({location.accuracy}m)"
        
        # Check 3: Invalid coordinates
        if not (-90 <= location.latitude <= 90):
            return True, "Invalid latitude"
        
        if not (-180 <= location.longitude <= 180):
            return True, "Invalid longitude"
        
        # Check 4: Null Island (0, 0) - common error/spoof location
        if abs(location.latitude) < 0.01 and abs(location.longitude) < 0.01:
            return True, "Location at 'Null Island' (likely spoofed)"
        
        return False, "GPS appears legitimate"
    
    @staticmethod
    def verify_location_consistency(locations: list, 
                                   max_speed_mps: float = 50.0) -> Tuple[bool, str]:
        """
        Verify that a series of locations are consistent with human movement
        Detects teleportation (instant location changes)
        
        Args:
            locations: List of (Location, timestamp) tuples
            max_speed_mps: Maximum realistic speed in meters per second (50 m/s = 180 km/h)
        
        Returns:
            Tuple of (is_consistent, reason)
        """
        if len(locations) < 2:
            return True, "Insufficient data"
        
        for i in range(1, len(locations)):
            loc1, time1 = locations[i-1]
            loc2, time2 = locations[i]
            
            # Calculate distance and time
            validator = GeofenceValidator({"RADIUS_METERS": 0, "CLASSROOM_LOCATIONS": {}})
            distance = validator.haversine_distance(loc1, loc2)
            time_diff = (time2 - time1).total_seconds()
            
            if time_diff > 0:
                speed = distance / time_diff
                
                if speed > max_speed_mps:
                    return False, f"Impossible speed detected: {speed:.1f} m/s ({speed*3.6:.1f} km/h)"
        
        return True, "Location changes are consistent with human movement"


if __name__ == "__main__":
    from config.settings import GEOFENCE_CONFIG
    
    # Initialize validator
    validator = GeofenceValidator(GEOFENCE_CONFIG)
    
    # Test location (simulate student location)
    # These coordinates are near the example classroom
    student_location = Location(
        latitude=18.5205,  # Slightly offset from Room_101
        longitude=73.8568,
        accuracy=15.0
    )
    
    print(f"Student location: {student_location}")
    print(f"GPS accuracy: {student_location.accuracy}m")
    
    # Check geofence
    is_valid, distance, message = validator.is_within_geofence(
        student_location, 
        "Room_101"
    )
    
    print(f"\nGeofence validation: {message}")
    print(f"Valid: {is_valid}")
    
    # Find nearest classroom
    nearest, dist = validator.get_nearest_classroom(student_location)
    print(f"\nNearest classroom: {nearest} ({dist:.1f}m away)")
    
    # Check for GPS spoofing
    security = GeofenceSecurity()
    is_suspicious, reason = security.detect_gps_spoofing(student_location)
    print(f"\nGPS spoofing check: {reason}")
    print(f"Suspicious: {is_suspicious}")
    
    # List all classrooms
    print("\nConfigured classrooms:")
    for name, coords in validator.list_classrooms().items():
        print(f"  {name}: {coords}")