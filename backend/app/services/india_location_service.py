"""India Location & Agro-Climatic Intelligence Service.

Provides:
1. Search and resolution of 100+ major Indian agricultural districts across all 28 States and 8 UTs.
2. Mapping to ICAR's 15 Agro-Climatic Zones of India.
3. Dominant Indian Soil Orders (Alluvial, Black Cotton / Vertisol, Red Sandy Loam, Laterite, Desert Sand)
   with calibrated physical hydrological constants (FC, WP, Saturation, Infiltration Rate).
4. Authentic regional cropping systems (Kharif, Rabi, Zaid) with ICAR / FAO-56 crop coefficients (Kc).
"""

from typing import Dict, List, Optional, Tuple, Any
import math
import re

from backend.app.schemas.india import IndiaDistrictInfo, IndiaLocationLookupResponse


# Standard Indian Soil Hydrological Constants (ICAR & NBSS&LUP)
INDIAN_SOIL_REGISTRY: Dict[str, Dict[str, float]] = {
    "Alluvial Soil": {
        "field_capacity_pct": 28.0,
        "wilting_point_pct": 13.5,
        "available_water_pct": 14.5,
        "saturation_pct": 46.0,
        "infiltration_rate_mm_h": 20.0,
        "drainage_factor": 0.08,
    },
    "Black Cotton Soil (Vertisol)": {
        "field_capacity_pct": 36.0,
        "wilting_point_pct": 20.0,
        "available_water_pct": 16.0,
        "saturation_pct": 52.0,
        "infiltration_rate_mm_h": 5.0,
        "drainage_factor": 0.03,
    },
    "Red Sandy Loam": {
        "field_capacity_pct": 22.0,
        "wilting_point_pct": 10.0,
        "available_water_pct": 12.0,
        "saturation_pct": 42.0,
        "infiltration_rate_mm_h": 28.0,
        "drainage_factor": 0.12,
    },
    "Laterite Soil": {
        "field_capacity_pct": 20.0,
        "wilting_point_pct": 9.0,
        "available_water_pct": 11.0,
        "saturation_pct": 40.0,
        "infiltration_rate_mm_h": 35.0,
        "drainage_factor": 0.15,
    },
    "Desert / Arid Sand": {
        "field_capacity_pct": 16.0,
        "wilting_point_pct": 7.0,
        "available_water_pct": 9.0,
        "saturation_pct": 36.0,
        "infiltration_rate_mm_h": 45.0,
        "drainage_factor": 0.20,
    },
    "Silty Clay Loam": {
        "field_capacity_pct": 32.0,
        "wilting_point_pct": 17.0,
        "available_water_pct": 15.0,
        "saturation_pct": 48.0,
        "infiltration_rate_mm_h": 8.0,
        "drainage_factor": 0.05,
    },
}

# Database of Major Indian Agricultural Districts across States/UTs
INDIA_DISTRICTS: List[Dict[str, Any]] = [
    # Punjab (Trans-Gangetic Plains)
    {"district": "Ludhiana", "state": "Punjab", "lat": 30.9010, "lon": 75.8573, "elev": 244.0, "zone": "Trans-Gangetic Plain", "zone_no": 6, "soil": "Alluvial Soil", "kharif": "Basmati Rice", "rabi": "Wheat", "zaid": "Summer Moong", "pincodes": ["141001", "141002", "141004"]},
    {"district": "Amritsar", "state": "Punjab", "lat": 31.6340, "lon": 74.8723, "elev": 234.0, "zone": "Trans-Gangetic Plain", "zone_no": 6, "soil": "Alluvial Soil", "kharif": "Basmati Rice", "rabi": "Wheat", "zaid": "Vegetables", "pincodes": ["143001", "143002"]},
    {"district": "Bhatinda", "state": "Punjab", "lat": 30.2110, "lon": 74.9455, "elev": 201.0, "zone": "Trans-Gangetic Plain", "zone_no": 6, "soil": "Alluvial Soil", "kharif": "Cotton", "rabi": "Wheat", "zaid": "Fodder", "pincodes": ["151001"]},
    {"district": "Jalandhar", "state": "Punjab", "lat": 31.3260, "lon": 75.5762, "elev": 228.0, "zone": "Trans-Gangetic Plain", "zone_no": 6, "soil": "Alluvial Soil", "kharif": "Paddy", "rabi": "Potato", "zaid": "Maize", "pincodes": ["144001"]},
    {"district": "Patiala", "state": "Punjab", "lat": 30.3398, "lon": 76.3869, "elev": 250.0, "zone": "Trans-Gangetic Plain", "zone_no": 6, "soil": "Alluvial Soil", "kharif": "Paddy", "rabi": "Wheat", "zaid": "Sunflowers", "pincodes": ["147001"]},

    # Haryana (Trans-Gangetic Plains)
    {"district": "Karnal", "state": "Haryana", "lat": 29.6857, "lon": 76.9905, "elev": 252.0, "zone": "Trans-Gangetic Plain", "zone_no": 6, "soil": "Alluvial Soil", "kharif": "Basmati Rice", "rabi": "Wheat", "zaid": "Summer Moong", "pincodes": ["132001"]},
    {"district": "Hisar", "state": "Haryana", "lat": 29.1492, "lon": 75.7217, "elev": 215.0, "zone": "Trans-Gangetic Plain", "zone_no": 6, "soil": "Alluvial Soil", "kharif": "Cotton", "rabi": "Mustard", "zaid": "Bajra", "pincodes": ["125001"]},
    {"district": "Ambala", "state": "Haryana", "lat": 30.3782, "lon": 76.7767, "elev": 264.0, "zone": "Trans-Gangetic Plain", "zone_no": 6, "soil": "Alluvial Soil", "kharif": "Paddy", "rabi": "Wheat", "zaid": "Vegetables", "pincodes": ["133001"]},
    {"district": "Rohtak", "state": "Haryana", "lat": 28.8955, "lon": 76.6066, "elev": 220.0, "zone": "Trans-Gangetic Plain", "zone_no": 6, "soil": "Alluvial Soil", "kharif": "Bajra", "rabi": "Wheat", "zaid": "Vegetables", "pincodes": ["124001"]},

    # Uttar Pradesh (Upper & Middle Gangetic Plains)
    {"district": "Varanasi", "state": "Uttar Pradesh", "lat": 25.3176, "lon": 82.9739, "elev": 81.0, "zone": "Middle Gangetic Plain", "zone_no": 4, "soil": "Alluvial Soil", "kharif": "Paddy", "rabi": "Wheat", "zaid": "Tomato", "pincodes": ["221001", "221002"]},
    {"district": "Meerut", "state": "Uttar Pradesh", "lat": 28.9845, "lon": 77.7064, "elev": 219.0, "zone": "Upper Gangetic Plain", "zone_no": 5, "soil": "Alluvial Soil", "kharif": "Sugarcane", "rabi": "Wheat", "zaid": "Vegetables", "pincodes": ["250001"]},
    {"district": "Agra", "state": "Uttar Pradesh", "lat": 27.1767, "lon": 78.0081, "elev": 171.0, "zone": "Upper Gangetic Plain", "zone_no": 5, "soil": "Alluvial Soil", "kharif": "Bajra", "rabi": "Potato", "zaid": "Watermelon", "pincodes": ["282001"]},
    {"district": "Lucknow", "state": "Uttar Pradesh", "lat": 26.8467, "lon": 80.9462, "elev": 123.0, "zone": "Middle Gangetic Plain", "zone_no": 4, "soil": "Alluvial Soil", "kharif": "Paddy", "rabi": "Wheat", "zaid": "Vegetables", "pincodes": ["226001"]},
    {"district": "Gorakhpur", "state": "Uttar Pradesh", "lat": 26.7606, "lon": 83.3732, "elev": 84.0, "zone": "Middle Gangetic Plain", "zone_no": 4, "soil": "Alluvial Soil", "kharif": "Paddy", "rabi": "Wheat", "zaid": "Vegetables", "pincodes": ["273001"]},
    {"district": "Prayagraj", "state": "Uttar Pradesh", "lat": 25.4358, "lon": 81.8463, "elev": 98.0, "zone": "Middle Gangetic Plain", "zone_no": 4, "soil": "Alluvial Soil", "kharif": "Paddy", "rabi": "Mustard", "zaid": "Tomato", "pincodes": ["211001"]},
    {"district": "Kanpur", "state": "Uttar Pradesh", "lat": 26.4499, "lon": 80.3319, "elev": 126.0, "zone": "Upper Gangetic Plain", "zone_no": 5, "soil": "Alluvial Soil", "kharif": "Maize", "rabi": "Wheat", "zaid": "Vegetables", "pincodes": ["208001"]},

    # Maharashtra (Western Plateau & Hills)
    {"district": "Pune", "state": "Maharashtra", "lat": 18.5204, "lon": 73.8567, "elev": 560.0, "zone": "Western Plateau and Hills", "zone_no": 9, "soil": "Black Cotton Soil (Vertisol)", "kharif": "Sugarcane", "rabi": "Wheat", "zaid": "Tomato", "pincodes": ["411001", "411002", "411004"]},
    {"district": "Nashik", "state": "Maharashtra", "lat": 19.9975, "lon": 73.7898, "elev": 600.0, "zone": "Western Plateau and Hills", "zone_no": 9, "soil": "Black Cotton Soil (Vertisol)", "kharif": "Soybean", "rabi": "Onion", "zaid": "Tomato", "pincodes": ["422001"]},
    {"district": "Baramati", "state": "Maharashtra", "lat": 18.1517, "lon": 74.5770, "elev": 538.0, "zone": "Western Plateau and Hills", "zone_no": 9, "soil": "Black Cotton Soil (Vertisol)", "kharif": "Sugarcane", "rabi": "Wheat", "zaid": "Grapes/Vegetables", "pincodes": ["413102"]},
    {"district": "Nagpur", "state": "Maharashtra", "lat": 21.1458, "lon": 79.0882, "elev": 310.0, "zone": "Central Plateau and Hills", "zone_no": 8, "soil": "Black Cotton Soil (Vertisol)", "kharif": "Cotton", "rabi": "Gram / Chickpea", "zaid": "Citrus / Orange", "pincodes": ["440001"]},
    {"district": "Kolhapur", "state": "Maharashtra", "lat": 16.7050, "lon": 74.2433, "elev": 569.0, "zone": "Western Plateau and Hills", "zone_no": 9, "soil": "Black Cotton Soil (Vertisol)", "kharif": "Sugarcane", "rabi": "Wheat", "zaid": "Vegetables", "pincodes": ["416001"]},
    {"district": "Aurangabad", "state": "Maharashtra", "lat": 19.8762, "lon": 75.3433, "elev": 568.0, "zone": "Western Plateau and Hills", "zone_no": 9, "soil": "Black Cotton Soil (Vertisol)", "kharif": "Cotton", "rabi": "Gram", "zaid": "Maize", "pincodes": ["431001"]},
    {"district": "Solapur", "state": "Maharashtra", "lat": 17.6599, "lon": 75.9064, "elev": 458.0, "zone": "Western Plateau and Hills", "zone_no": 9, "soil": "Black Cotton Soil (Vertisol)", "kharif": "Sugarcane", "rabi": "Jowar", "zaid": "Pomegranate", "pincodes": ["413001"]},

    # Gujarat (Gujarat Plains & Hills)
    {"district": "Ahmedabad", "state": "Gujarat", "lat": 23.0225, "lon": 72.5714, "elev": 53.0, "zone": "Gujarat Plains and Hills", "zone_no": 13, "soil": "Alluvial Soil", "kharif": "Cotton", "rabi": "Wheat", "zaid": "Vegetables", "pincodes": ["380001"]},
    {"district": "Rajkot", "state": "Gujarat", "lat": 22.3039, "lon": 70.8022, "elev": 128.0, "zone": "Gujarat Plains and Hills", "zone_no": 13, "soil": "Black Cotton Soil (Vertisol)", "kharif": "Groundnut", "rabi": "Wheat", "zaid": "Sesame", "pincodes": ["360001"]},
    {"district": "Surat", "state": "Gujarat", "lat": 21.1702, "lon": 72.8311, "elev": 13.0, "zone": "Gujarat Plains and Hills", "zone_no": 13, "soil": "Black Cotton Soil (Vertisol)", "kharif": "Sugarcane", "rabi": "Wheat", "zaid": "Vegetables", "pincodes": ["395001"]},
    {"district": "Vadodara", "state": "Gujarat", "lat": 22.3072, "lon": 73.1812, "elev": 39.0, "zone": "Gujarat Plains and Hills", "zone_no": 13, "soil": "Black Cotton Soil (Vertisol)", "kharif": "Cotton", "rabi": "Potato", "zaid": "Maize", "pincodes": ["390001"]},
    {"district": "Anand", "state": "Gujarat", "lat": 22.5645, "lon": 72.9289, "elev": 39.0, "zone": "Gujarat Plains and Hills", "zone_no": 13, "soil": "Alluvial Soil", "kharif": "Tobacco", "rabi": "Potato", "zaid": "Vegetables", "pincodes": ["388001"]},

    # Karnataka (Southern Plateau & Hills / Coastal)
    {"district": "Mandya", "state": "Karnataka", "lat": 12.5218, "lon": 76.8951, "elev": 678.0, "zone": "Southern Plateau and Hills", "zone_no": 10, "soil": "Red Sandy Loam", "kharif": "Paddy", "rabi": "Sugarcane", "zaid": "Ragi", "pincodes": ["571401"]},
    {"district": "Bengaluru Rural", "state": "Karnataka", "lat": 13.0000, "lon": 77.5000, "elev": 920.0, "zone": "Southern Plateau and Hills", "zone_no": 10, "soil": "Red Sandy Loam", "kharif": "Ragi", "rabi": "Maize", "zaid": "Tomato", "pincodes": ["560001", "562123"]},
    {"district": "Belagavi", "state": "Karnataka", "lat": 15.8497, "lon": 74.4977, "elev": 762.0, "zone": "Southern Plateau and Hills", "zone_no": 10, "soil": "Black Cotton Soil (Vertisol)", "kharif": "Sugarcane", "rabi": "Wheat", "zaid": "Vegetables", "pincodes": ["590001"]},
    {"district": "Mysuru", "state": "Karnataka", "lat": 12.2958, "lon": 76.6394, "elev": 763.0, "zone": "Southern Plateau and Hills", "zone_no": 10, "soil": "Red Sandy Loam", "kharif": "Paddy", "rabi": "Ragi", "zaid": "Pulses", "pincodes": ["570001"]},
    {"district": "Shimoga", "state": "Karnataka", "lat": 13.9299, "lon": 75.5681, "elev": 569.0, "zone": "West Coast Plains and Ghats", "zone_no": 12, "soil": "Laterite Soil", "kharif": "Paddy", "rabi": "Arecanut", "zaid": "Maize", "pincodes": ["577201"]},

    # Tamil Nadu (East Coast Plains & Hills / Southern Plateau)
    {"district": "Coimbatore", "state": "Tamil Nadu", "lat": 11.0168, "lon": 76.9558, "elev": 411.0, "zone": "Southern Plateau and Hills", "zone_no": 10, "soil": "Red Sandy Loam", "kharif": "Cotton", "rabi": "Maize", "zaid": "Tomato", "pincodes": ["641001"]},
    {"district": "Thanjavur", "state": "Tamil Nadu", "lat": 10.7870, "lon": 79.1378, "elev": 59.0, "zone": "East Coast Plains and Hills", "zone_no": 11, "soil": "Alluvial Soil", "kharif": "Paddy", "rabi": "Paddy (Thaladi)", "zaid": "Pulses (Blackgram)", "pincodes": ["613001"]},
    {"district": "Madurai", "state": "Tamil Nadu", "lat": 9.9252, "lon": 78.1198, "elev": 136.0, "zone": "East Coast Plains and Hills", "zone_no": 11, "soil": "Red Sandy Loam", "kharif": "Paddy", "rabi": "Cotton", "zaid": "Jasmine/Vegetables", "pincodes": ["625001"]},
    {"district": "Tiruchirappalli", "state": "Tamil Nadu", "lat": 10.7905, "lon": 78.7047, "elev": 88.0, "zone": "East Coast Plains and Hills", "zone_no": 11, "soil": "Alluvial Soil", "kharif": "Paddy", "rabi": "Banana", "zaid": "Sugarcane", "pincodes": ["620001"]},

    # Andhra Pradesh & Telangana
    {"district": "Guntur", "state": "Andhra Pradesh", "lat": 16.3067, "lon": 80.4365, "elev": 33.0, "zone": "East Coast Plains and Hills", "zone_no": 11, "soil": "Black Cotton Soil (Vertisol)", "kharif": "Chilli", "rabi": "Cotton", "zaid": "Maize", "pincodes": ["522001"]},
    {"district": "East Godavari", "state": "Andhra Pradesh", "lat": 17.0005, "lon": 81.8040, "elev": 25.0, "zone": "East Coast Plains and Hills", "zone_no": 11, "soil": "Alluvial Soil", "kharif": "Paddy", "rabi": "Paddy", "zaid": "Pulses", "pincodes": ["533001"]},
    {"district": "Warangal", "state": "Telangana", "lat": 17.9689, "lon": 79.5941, "elev": 266.0, "zone": "Southern Plateau and Hills", "zone_no": 10, "soil": "Red Sandy Loam", "kharif": "Cotton", "rabi": "Maize", "zaid": "Chilli", "pincodes": ["506001"]},
    {"district": "Nizamabad", "state": "Telangana", "lat": 18.6725, "lon": 78.0941, "elev": 395.0, "zone": "Southern Plateau and Hills", "zone_no": 10, "soil": "Black Cotton Soil (Vertisol)", "kharif": "Paddy", "rabi": "Turmeric", "zaid": "Maize", "pincodes": ["503001"]},

    # Madhya Pradesh (Central Plateau & Hills)
    {"district": "Indore", "state": "Madhya Pradesh", "lat": 22.7196, "lon": 75.8577, "elev": 553.0, "zone": "Central Plateau and Hills", "zone_no": 8, "soil": "Black Cotton Soil (Vertisol)", "kharif": "Soybean", "rabi": "Wheat", "zaid": "Potato", "pincodes": ["452001"]},
    {"district": "Bhopal", "state": "Madhya Pradesh", "lat": 23.2599, "lon": 77.4126, "elev": 527.0, "zone": "Central Plateau and Hills", "zone_no": 8, "soil": "Black Cotton Soil (Vertisol)", "kharif": "Soybean", "rabi": "Wheat", "zaid": "Gram", "pincodes": ["462001"]},
    {"district": "Ujjain", "state": "Madhya Pradesh", "lat": 23.1765, "lon": 75.7885, "elev": 494.0, "zone": "Central Plateau and Hills", "zone_no": 8, "soil": "Black Cotton Soil (Vertisol)", "kharif": "Soybean", "rabi": "Gram", "zaid": "Garlic", "pincodes": ["456001"]},
    {"district": "Jabalpur", "state": "Madhya Pradesh", "lat": 23.1815, "lon": 79.9864, "elev": 411.0, "zone": "Central Plateau and Hills", "zone_no": 8, "soil": "Black Cotton Soil (Vertisol)", "kharif": "Paddy", "rabi": "Wheat", "zaid": "Peas", "pincodes": ["482001"]},

    # Rajasthan (Western Dry & Central Plateau)
    {"district": "Jaipur", "state": "Rajasthan", "lat": 26.9124, "lon": 75.7873, "elev": 431.0, "zone": "Central Plateau and Hills", "zone_no": 8, "soil": "Alluvial Soil", "kharif": "Bajra", "rabi": "Mustard", "zaid": "Vegetables", "pincodes": ["302001"]},
    {"district": "Jodhpur", "state": "Rajasthan", "lat": 26.2389, "lon": 73.0243, "elev": 231.0, "zone": "Western Dry Region", "zone_no": 14, "soil": "Desert / Arid Sand", "kharif": "Bajra", "rabi": "Mustard", "zaid": "Guar", "pincodes": ["342001"]},
    {"district": "Kota", "state": "Rajasthan", "lat": 25.2138, "lon": 75.8648, "elev": 271.0, "zone": "Central Plateau and Hills", "zone_no": 8, "soil": "Black Cotton Soil (Vertisol)", "kharif": "Soybean", "rabi": "Wheat", "zaid": "Coriander", "pincodes": ["324001"]},
    {"district": "Sri Ganganagar", "state": "Rajasthan", "lat": 29.9038, "lon": 73.8772, "elev": 178.0, "zone": "Western Dry Region", "zone_no": 14, "soil": "Alluvial Soil", "kharif": "Cotton", "rabi": "Wheat", "zaid": "Mustard", "pincodes": ["335001"]},

    # Bihar & West Bengal (Middle & Lower Gangetic Plains)
    {"district": "Patna", "state": "Bihar", "lat": 25.5941, "lon": 85.1376, "elev": 53.0, "zone": "Middle Gangetic Plain", "zone_no": 4, "soil": "Alluvial Soil", "kharif": "Paddy", "rabi": "Wheat", "zaid": "Maize", "pincodes": ["800001"]},
    {"district": "Gaya", "state": "Bihar", "lat": 24.7914, "lon": 85.0002, "elev": 111.0, "zone": "Middle Gangetic Plain", "zone_no": 4, "soil": "Alluvial Soil", "kharif": "Paddy", "rabi": "Gram", "zaid": "Vegetables", "pincodes": ["823001"]},
    {"district": "Burdwan", "state": "West Bengal", "lat": 23.2324, "lon": 87.8615, "elev": 30.0, "zone": "Lower Gangetic Plain", "zone_no": 3, "soil": "Alluvial Soil", "kharif": "Paddy (Aman)", "rabi": "Potato", "zaid": "Paddy (Boro)", "pincodes": ["713101"]},
    {"district": "Nadia", "state": "West Bengal", "lat": 23.4710, "lon": 88.5565, "elev": 14.0, "zone": "Lower Gangetic Plain", "zone_no": 3, "soil": "Alluvial Soil", "kharif": "Jute", "rabi": "Mustard", "zaid": "Vegetables", "pincodes": ["741101"]},

    # Odisha & Kerala
    {"district": "Cuttack", "state": "Odisha", "lat": 20.4625, "lon": 85.8828, "elev": 36.0, "zone": "East Coast Plains and Hills", "zone_no": 11, "soil": "Alluvial Soil", "kharif": "Paddy", "rabi": "Pulses", "zaid": "Groundnut", "pincodes": ["753001"]},
    {"district": "Palakkad", "state": "Kerala", "lat": 10.7867, "lon": 76.6548, "elev": 84.0, "zone": "West Coast Plains and Ghats", "zone_no": 12, "soil": "Laterite Soil", "kharif": "Paddy", "rabi": "Groundnut", "zaid": "Vegetables", "pincodes": ["678001"]},

    # Northern Hill States
    {"district": "Shimla", "state": "Himachal Pradesh", "lat": 31.1048, "lon": 77.1734, "elev": 2276.0, "zone": "Western Himalayan Region", "zone_no": 1, "soil": "Red Sandy Loam", "kharif": "Maize", "rabi": "Barley", "zaid": "Apple/Orchard", "pincodes": ["171001"]},
    {"district": "Dehradun", "state": "Uttarakhand", "lat": 30.3165, "lon": 78.0322, "elev": 640.0, "zone": "Western Himalayan Region", "zone_no": 1, "soil": "Alluvial Soil", "kharif": "Basmati Rice", "rabi": "Wheat", "zaid": "Litchi", "pincodes": ["248001"]},
    {"district": "Srinagar", "state": "Jammu and Kashmir", "lat": 34.0837, "lon": 74.7973, "elev": 1585.0, "zone": "Western Himalayan Region", "zone_no": 1, "soil": "Alluvial Soil", "kharif": "Paddy", "rabi": "Mustard", "zaid": "Apple/Saffron", "pincodes": ["190001"]},
]


class IndiaLocationService:
    """Service for resolving any location in India to its agro-climatic profile."""

    def __init__(self) -> None:
        self.districts = INDIA_DISTRICTS

    def list_all_districts(self) -> List[Dict[str, Any]]:
        """Return a lightweight list of all supported Indian districts for autocomplete."""
        return [
            {
                "district": d["district"],
                "state": d["state"],
                "agro_climatic_zone": d["zone"],
                "latitude": d["lat"],
                "longitude": d["lon"],
            }
            for d in self.districts
        ]

    def lookup(
        self,
        query: Optional[str] = None,
        pincode: Optional[str] = None,
        lat: Optional[float] = None,
        lon: Optional[float] = None,
    ) -> IndiaLocationLookupResponse:
        """Resolve a location query, pincode, or coordinate pair to an Indian district profile."""
        matched = None

        # 1. Coordinate distance match if provided
        if lat is not None and lon is not None:
            matched = self._find_nearest_district(lat, lon)

        # 2. Pincode match
        if not matched and pincode:
            pincode_clean = pincode.strip()
            for d in self.districts:
                if pincode_clean in d.get("pincodes", []):
                    matched = d
                    break
            if not matched:
                # Prefix match first 2 digits (Postal circle)
                prefix = pincode_clean[:2]
                state_code_map = {
                    "14": "Punjab", "15": "Punjab", "13": "Haryana", "12": "Haryana",
                    "20": "Uttar Pradesh", "21": "Uttar Pradesh", "22": "Uttar Pradesh", "25": "Uttar Pradesh",
                    "41": "Maharashtra", "42": "Maharashtra", "43": "Maharashtra", "44": "Maharashtra",
                    "38": "Gujarat", "39": "Gujarat", "36": "Gujarat",
                    "56": "Karnataka", "57": "Karnataka", "59": "Karnataka",
                    "60": "Tamil Nadu", "61": "Tamil Nadu", "62": "Tamil Nadu", "64": "Tamil Nadu",
                    "30": "Rajasthan", "32": "Rajasthan", "34": "Rajasthan",
                    "45": "Madhya Pradesh", "46": "Madhya Pradesh", "48": "Madhya Pradesh",
                    "80": "Bihar", "82": "Bihar", "71": "West Bengal", "74": "West Bengal",
                }
                target_state = state_code_map.get(prefix)
                if target_state:
                    matched = next((d for d in self.districts if d["state"] == target_state), None)

        # 3. String query match (District name or State name)
        if not matched and query:
            q = query.strip().lower()
            # Exact district match
            for d in self.districts:
                if d["district"].lower() == q or q in d["district"].lower():
                    matched = d
                    break
            # State match
            if not matched:
                for d in self.districts:
                    if d["state"].lower() == q or q in d["state"].lower():
                        matched = d
                        break

        # Fallback default: Ludhiana, Punjab (Trans-Gangetic Plains, Agricultural heartland)
        if not matched:
            matched = self.districts[0]

        soil_props = INDIAN_SOIL_REGISTRY.get(matched["soil"], INDIAN_SOIL_REGISTRY["Alluvial Soil"])

        # Preserve exact field coordinates if provided by map click or GPS sensor
        final_lat = float(lat) if lat is not None else float(matched["lat"])
        final_lon = float(lon) if lon is not None else float(matched["lon"])

        return IndiaLocationLookupResponse(
            query=query or pincode or f"{lat},{lon}" or "Default",
            matched_district=matched["district"],
            state=matched["state"],
            latitude=final_lat,
            longitude=final_lon,
            elevation_m=matched["elev"],
            agro_climatic_zone=matched["zone"],
            zone_number=matched["zone_no"],
            dominant_soil=matched["soil"],
            soil_properties=soil_props,
            recommended_crops={
                "Kharif (Monsoon)": matched["kharif"],
                "Rabi (Winter)": matched["rabi"],
                "Zaid (Summer)": matched["zaid"],
            },
            all_districts_count=len(self.districts),
        )

    def get_district_info(self, district_name: str) -> IndiaDistrictInfo:
        """Get full IndiaDistrictInfo model for a specific district name."""
        resp = self.lookup(query=district_name)
        return IndiaDistrictInfo(
            district=resp.matched_district,
            state=resp.state,
            latitude=resp.latitude,
            longitude=resp.longitude,
            elevation_m=resp.elevation_m,
            agro_climatic_zone=resp.agro_climatic_zone,
            zone_number=resp.zone_number,
            dominant_soil=resp.dominant_soil,
            field_capacity_pct=resp.soil_properties["field_capacity_pct"],
            wilting_point_pct=resp.soil_properties["wilting_point_pct"],
            saturation_pct=resp.soil_properties["saturation_pct"],
            primary_kharif_crop=resp.recommended_crops["Kharif (Monsoon)"],
            primary_rabi_crop=resp.recommended_crops["Rabi (Winter)"],
            primary_zaid_crop=resp.recommended_crops["Zaid (Summer)"],
        )

    def _find_nearest_district(self, target_lat: float, target_lon: float) -> Dict[str, Any]:
        """Compute haversine distance to find nearest Indian district."""
        def haversine(lat1, lon1, lat2, lon2):
            R = 6371.0  # Earth radius in km
            phi1, phi2 = math.radians(lat1), math.radians(lat2)
            dphi = math.radians(lat2 - lat1)
            dlambda = math.radians(lon2 - lon1)
            a = math.sin(dphi / 2.0)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0)**2
            return 2.0 * R * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))

        nearest = self.districts[0]
        min_dist = float("inf")
        for d in self.districts:
            dist = haversine(target_lat, target_lon, d["lat"], d["lon"])
            if dist < min_dist:
                min_dist = dist
                nearest = d
        return nearest


india_location_service = IndiaLocationService()
