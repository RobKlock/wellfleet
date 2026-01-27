"""
Comprehensive city configuration for climate markets
Contains coordinates, timezones, and NWS station IDs for major US cities
"""

# Comprehensive list of US cities that may have climate markets
# Format: "City, ST": {"lat": float, "lon": float, "timezone": str, "station_id": str}
CITY_DATABASE = {
    # Major cities (most likely to have climate markets)
    "New York, NY": {
        "lat": 40.7128,
        "lon": -74.0060,
        "timezone": "America/New_York",
        "station_id": "KJFK"
    },
    "Los Angeles, CA": {
        "lat": 34.0522,
        "lon": -118.2437,
        "timezone": "America/Los_Angeles",
        "station_id": "KLAX"
    },
    "Chicago, IL": {
        "lat": 41.8781,
        "lon": -87.6298,
        "timezone": "America/Chicago",
        "station_id": "KORD"
    },
    "Houston, TX": {
        "lat": 29.7604,
        "lon": -95.3698,
        "timezone": "America/Chicago",
        "station_id": "KIAH"
    },
    "Phoenix, AZ": {
        "lat": 33.4484,
        "lon": -112.0740,
        "timezone": "America/Phoenix",
        "station_id": "KPHX"
    },
    "Philadelphia, PA": {
        "lat": 39.9526,
        "lon": -75.1652,
        "timezone": "America/New_York",
        "station_id": "KPHL"
    },
    "San Antonio, TX": {
        "lat": 29.4241,
        "lon": -98.4936,
        "timezone": "America/Chicago",
        "station_id": "KSAT"
    },
    "San Diego, CA": {
        "lat": 32.7157,
        "lon": -117.1611,
        "timezone": "America/Los_Angeles",
        "station_id": "KSAN"
    },
    "Dallas, TX": {
        "lat": 32.7767,
        "lon": -96.7970,
        "timezone": "America/Chicago",
        "station_id": "KDFW"
    },
    "San Jose, CA": {
        "lat": 37.3382,
        "lon": -121.8863,
        "timezone": "America/Los_Angeles",
        "station_id": "KSJC"
    },
    "Austin, TX": {
        "lat": 30.2672,
        "lon": -97.7431,
        "timezone": "America/Chicago",
        "station_id": "KAUS"
    },
    "Jacksonville, FL": {
        "lat": 30.3322,
        "lon": -81.6557,
        "timezone": "America/New_York",
        "station_id": "KJAX"
    },
    "Fort Worth, TX": {
        "lat": 32.7555,
        "lon": -97.3308,
        "timezone": "America/Chicago",
        "station_id": "KFTW"
    },
    "Columbus, OH": {
        "lat": 39.9612,
        "lon": -82.9988,
        "timezone": "America/New_York",
        "station_id": "KCMH"
    },
    "Charlotte, NC": {
        "lat": 35.2271,
        "lon": -80.8431,
        "timezone": "America/New_York",
        "station_id": "KCLT"
    },
    "San Francisco, CA": {
        "lat": 37.7749,
        "lon": -122.4194,
        "timezone": "America/Los_Angeles",
        "station_id": "KSFO"
    },
    "Indianapolis, IN": {
        "lat": 39.7684,
        "lon": -86.1581,
        "timezone": "America/Indiana/Indianapolis",
        "station_id": "KIND"
    },
    "Seattle, WA": {
        "lat": 47.6062,
        "lon": -122.3321,
        "timezone": "America/Los_Angeles",
        "station_id": "KSEA"
    },
    "Denver, CO": {
        "lat": 39.7392,
        "lon": -104.9903,
        "timezone": "America/Denver",
        "station_id": "KDEN"
    },
    "Washington, DC": {
        "lat": 38.9072,
        "lon": -77.0369,
        "timezone": "America/New_York",
        "station_id": "KDCA"
    },
    "Boston, MA": {
        "lat": 42.3601,
        "lon": -71.0589,
        "timezone": "America/New_York",
        "station_id": "KBOS"
    },
    "El Paso, TX": {
        "lat": 31.7619,
        "lon": -106.4850,
        "timezone": "America/Denver",
        "station_id": "KELP"
    },
    "Nashville, TN": {
        "lat": 36.1627,
        "lon": -86.7816,
        "timezone": "America/Chicago",
        "station_id": "KBNA"
    },
    "Detroit, MI": {
        "lat": 42.3314,
        "lon": -83.0458,
        "timezone": "America/Detroit",
        "station_id": "KDTW"
    },
    "Oklahoma City, OK": {
        "lat": 35.4676,
        "lon": -97.5164,
        "timezone": "America/Chicago",
        "station_id": "KOKC"
    },
    "Portland, OR": {
        "lat": 45.5152,
        "lon": -122.6784,
        "timezone": "America/Los_Angeles",
        "station_id": "KPDX"
    },
    "Las Vegas, NV": {
        "lat": 36.1699,
        "lon": -115.1398,
        "timezone": "America/Los_Angeles",
        "station_id": "KLAS"
    },
    "Memphis, TN": {
        "lat": 35.1495,
        "lon": -90.0490,
        "timezone": "America/Chicago",
        "station_id": "KMEM"
    },
    "Louisville, KY": {
        "lat": 38.2527,
        "lon": -85.7585,
        "timezone": "America/Kentucky/Louisville",
        "station_id": "KSDF"
    },
    "Baltimore, MD": {
        "lat": 39.2904,
        "lon": -76.6122,
        "timezone": "America/New_York",
        "station_id": "KBWI"
    },
    "Milwaukee, WI": {
        "lat": 43.0389,
        "lon": -87.9065,
        "timezone": "America/Chicago",
        "station_id": "KMKE"
    },
    "Albuquerque, NM": {
        "lat": 35.0844,
        "lon": -106.6504,
        "timezone": "America/Denver",
        "station_id": "KABQ"
    },
    "Tucson, AZ": {
        "lat": 32.2226,
        "lon": -110.9747,
        "timezone": "America/Phoenix",
        "station_id": "KTUS"
    },
    "Fresno, CA": {
        "lat": 36.7378,
        "lon": -119.7871,
        "timezone": "America/Los_Angeles",
        "station_id": "KFAT"
    },
    "Mesa, AZ": {
        "lat": 33.4152,
        "lon": -111.8315,
        "timezone": "America/Phoenix",
        "station_id": "KIWA"
    },
    "Sacramento, CA": {
        "lat": 38.5816,
        "lon": -121.4944,
        "timezone": "America/Los_Angeles",
        "station_id": "KSAC"
    },
    "Atlanta, GA": {
        "lat": 33.7490,
        "lon": -84.3880,
        "timezone": "America/New_York",
        "station_id": "KATL"
    },
    "Kansas City, MO": {
        "lat": 39.0997,
        "lon": -94.5786,
        "timezone": "America/Chicago",
        "station_id": "KMCI"
    },
    "Colorado Springs, CO": {
        "lat": 38.8339,
        "lon": -104.8214,
        "timezone": "America/Denver",
        "station_id": "KCOS"
    },
    "Miami, FL": {
        "lat": 25.7617,
        "lon": -80.1918,
        "timezone": "America/New_York",
        "station_id": "KMIA"
    },
    "Raleigh, NC": {
        "lat": 35.7796,
        "lon": -78.6382,
        "timezone": "America/New_York",
        "station_id": "KRDU"
    },
    "Omaha, NE": {
        "lat": 41.2565,
        "lon": -95.9345,
        "timezone": "America/Chicago",
        "station_id": "KOMA"
    },
    "Long Beach, CA": {
        "lat": 33.7701,
        "lon": -118.1937,
        "timezone": "America/Los_Angeles",
        "station_id": "KLGB"
    },
    "Virginia Beach, VA": {
        "lat": 36.8529,
        "lon": -75.9780,
        "timezone": "America/New_York",
        "station_id": "KNTU"
    },
    "Oakland, CA": {
        "lat": 37.8044,
        "lon": -122.2712,
        "timezone": "America/Los_Angeles",
        "station_id": "KOAK"
    },
    "Minneapolis, MN": {
        "lat": 44.9778,
        "lon": -93.2650,
        "timezone": "America/Chicago",
        "station_id": "KMSP"
    },
    "Tulsa, OK": {
        "lat": 36.1540,
        "lon": -95.9928,
        "timezone": "America/Chicago",
        "station_id": "KTUL"
    },
    "Tampa, FL": {
        "lat": 27.9506,
        "lon": -82.4572,
        "timezone": "America/New_York",
        "station_id": "KTPA"
    },
    "Arlington, TX": {
        "lat": 32.7357,
        "lon": -97.1081,
        "timezone": "America/Chicago",
        "station_id": "KDFW"
    },
    "New Orleans, LA": {
        "lat": 29.9511,
        "lon": -90.0715,
        "timezone": "America/Chicago",
        "station_id": "KMSY"
    },
    "Wichita, KS": {
        "lat": 37.6872,
        "lon": -97.3301,
        "timezone": "America/Chicago",
        "station_id": "KICT"
    },
    "Cleveland, OH": {
        "lat": 41.4993,
        "lon": -81.6944,
        "timezone": "America/New_York",
        "station_id": "KCLE"
    },
    "Bakersfield, CA": {
        "lat": 35.3733,
        "lon": -119.0187,
        "timezone": "America/Los_Angeles",
        "station_id": "KBFL"
    },
    "Aurora, CO": {
        "lat": 39.7294,
        "lon": -104.8319,
        "timezone": "America/Denver",
        "station_id": "KAPA"
    },
    "Anaheim, CA": {
        "lat": 33.8366,
        "lon": -117.9143,
        "timezone": "America/Los_Angeles",
        "station_id": "KSNA"
    },
    "Honolulu, HI": {
        "lat": 21.3099,
        "lon": -157.8581,
        "timezone": "Pacific/Honolulu",
        "station_id": "PHNL"
    },
    "Riverside, CA": {
        "lat": 33.9533,
        "lon": -117.3962,
        "timezone": "America/Los_Angeles",
        "station_id": "KRAL"
    },
    "Corpus Christi, TX": {
        "lat": 27.8006,
        "lon": -97.3964,
        "timezone": "America/Chicago",
        "station_id": "KCRP"
    },
    "Lexington, KY": {
        "lat": 38.0406,
        "lon": -84.5037,
        "timezone": "America/Kentucky/Louisville",
        "station_id": "KLEX"
    },
    "Henderson, NV": {
        "lat": 36.0395,
        "lon": -114.9817,
        "timezone": "America/Los_Angeles",
        "station_id": "KHND"
    },
    "Stockton, CA": {
        "lat": 37.9577,
        "lon": -121.2908,
        "timezone": "America/Los_Angeles",
        "station_id": "KSCK"
    },
    "Saint Paul, MN": {
        "lat": 44.9537,
        "lon": -93.0900,
        "timezone": "America/Chicago",
        "station_id": "KSTP"
    },
    "St. Louis, MO": {
        "lat": 38.6270,
        "lon": -90.1994,
        "timezone": "America/Chicago",
        "station_id": "KSTL"
    },
    "Cincinnati, OH": {
        "lat": 39.1031,
        "lon": -84.5120,
        "timezone": "America/New_York",
        "station_id": "KCVG"
    },
    "Pittsburgh, PA": {
        "lat": 40.4406,
        "lon": -79.9959,
        "timezone": "America/New_York",
        "station_id": "KPIT"
    },
    "Greensboro, NC": {
        "lat": 36.0726,
        "lon": -79.7920,
        "timezone": "America/New_York",
        "station_id": "KGSO"
    },
    "Anchorage, AK": {
        "lat": 61.2181,
        "lon": -149.9003,
        "timezone": "America/Anchorage",
        "station_id": "PANC"
    },
    "Plano, TX": {
        "lat": 33.0198,
        "lon": -96.6989,
        "timezone": "America/Chicago",
        "station_id": "KDTO"
    },
    "Lincoln, NE": {
        "lat": 40.8136,
        "lon": -96.7026,
        "timezone": "America/Chicago",
        "station_id": "KLNK"
    },
    "Orlando, FL": {
        "lat": 28.5383,
        "lon": -81.3792,
        "timezone": "America/New_York",
        "station_id": "KMCO"
    },
    "Irvine, CA": {
        "lat": 33.6846,
        "lon": -117.8265,
        "timezone": "America/Los_Angeles",
        "station_id": "KSNA"
    },
    "Newark, NJ": {
        "lat": 40.7357,
        "lon": -74.1724,
        "timezone": "America/New_York",
        "station_id": "KEWR"
    },
    "Durham, NC": {
        "lat": 35.9940,
        "lon": -78.8986,
        "timezone": "America/New_York",
        "station_id": "KRDU"
    },
    "Chula Vista, CA": {
        "lat": 32.6401,
        "lon": -117.0842,
        "timezone": "America/Los_Angeles",
        "station_id": "KSDM"
    },
    "Toledo, OH": {
        "lat": 41.6528,
        "lon": -83.5379,
        "timezone": "America/New_York",
        "station_id": "KTOL"
    },
    "Fort Wayne, IN": {
        "lat": 41.0793,
        "lon": -85.1394,
        "timezone": "America/Indiana/Indianapolis",
        "station_id": "KFWA"
    },
    "St. Petersburg, FL": {
        "lat": 27.7676,
        "lon": -82.6403,
        "timezone": "America/New_York",
        "station_id": "KPIE"
    },
    "Laredo, TX": {
        "lat": 27.5306,
        "lon": -99.4803,
        "timezone": "America/Chicago",
        "station_id": "KLRD"
    },
    "Jersey City, NJ": {
        "lat": 40.7178,
        "lon": -74.0431,
        "timezone": "America/New_York",
        "station_id": "KTEB"
    },
    "Chandler, AZ": {
        "lat": 33.3062,
        "lon": -111.8413,
        "timezone": "America/Phoenix",
        "station_id": "KCHD"
    },
    "Madison, WI": {
        "lat": 43.0731,
        "lon": -89.4012,
        "timezone": "America/Chicago",
        "station_id": "KMSN"
    },
    "Lubbock, TX": {
        "lat": 33.5779,
        "lon": -101.8552,
        "timezone": "America/Chicago",
        "station_id": "KLBB"
    },
    "Scottsdale, AZ": {
        "lat": 33.4942,
        "lon": -111.9261,
        "timezone": "America/Phoenix",
        "station_id": "KSDL"
    },
    "Reno, NV": {
        "lat": 39.5296,
        "lon": -119.8138,
        "timezone": "America/Los_Angeles",
        "station_id": "KRNO"
    },
    "Buffalo, NY": {
        "lat": 42.8864,
        "lon": -78.8784,
        "timezone": "America/New_York",
        "station_id": "KBUF"
    },
    "Gilbert, AZ": {
        "lat": 33.3528,
        "lon": -111.7890,
        "timezone": "America/Phoenix",
        "station_id": "KIWA"
    },
    "Glendale, AZ": {
        "lat": 33.5387,
        "lon": -112.1860,
        "timezone": "America/Phoenix",
        "station_id": "KGYR"
    },
    "North Las Vegas, NV": {
        "lat": 36.1989,
        "lon": -115.1175,
        "timezone": "America/Los_Angeles",
        "station_id": "KVGT"
    },
    "Winston-Salem, NC": {
        "lat": 36.0999,
        "lon": -80.2442,
        "timezone": "America/New_York",
        "station_id": "KINT"
    },
    "Chesapeake, VA": {
        "lat": 36.7682,
        "lon": -76.2875,
        "timezone": "America/New_York",
        "station_id": "KNGU"
    },
    "Norfolk, VA": {
        "lat": 36.8508,
        "lon": -76.2859,
        "timezone": "America/New_York",
        "station_id": "KORF"
    },
    "Fremont, CA": {
        "lat": 37.5485,
        "lon": -121.9886,
        "timezone": "America/Los_Angeles",
        "station_id": "KNUQ"
    },
    "Garland, TX": {
        "lat": 32.9126,
        "lon": -96.6389,
        "timezone": "America/Chicago",
        "station_id": "KDAL"
    },
    "Irving, TX": {
        "lat": 32.8140,
        "lon": -96.9489,
        "timezone": "America/Chicago",
        "station_id": "KDAL"
    },
    "Hialeah, FL": {
        "lat": 25.8576,
        "lon": -80.2781,
        "timezone": "America/New_York",
        "station_id": "KOPF"
    },
    "Richmond, VA": {
        "lat": 37.5407,
        "lon": -77.4360,
        "timezone": "America/New_York",
        "station_id": "KRIC"
    },
    "Boise, ID": {
        "lat": 43.6150,
        "lon": -116.2023,
        "timezone": "America/Boise",
        "station_id": "KBOI"
    },
    "Spokane, WA": {
        "lat": 47.6588,
        "lon": -117.4260,
        "timezone": "America/Los_Angeles",
        "station_id": "KGEG"
    }
}

# Common abbreviations used in Kalshi market tickers
# Maps short forms to full city names
CITY_ABBREVIATIONS = {
    # Three-letter airport codes (most common in tickers)
    "JFK": "New York, NY",
    "NYC": "New York, NY",
    "LAX": "Los Angeles, CA",
    "LA": "Los Angeles, CA",
    "ORD": "Chicago, IL",
    "CHI": "Chicago, IL",
    "IAH": "Houston, TX",
    "HOU": "Houston, TX",
    "PHX": "Phoenix, AZ",
    "PHL": "Philadelphia, PA",
    "SAT": "San Antonio, TX",
    "SAN": "San Diego, CA",
    "DFW": "Dallas, TX",
    "DAL": "Dallas, TX",
    "SJC": "San Jose, CA",
    "AUS": "Austin, TX",
    "JAX": "Jacksonville, FL",
    "FTW": "Fort Worth, TX",
    "CMH": "Columbus, OH",
    "CLT": "Charlotte, NC",
    "SFO": "San Francisco, CA",
    "SF": "San Francisco, CA",
    "IND": "Indianapolis, IN",
    "SEA": "Seattle, WA",
    "DEN": "Denver, CO",
    "DCA": "Washington, DC",
    "DC": "Washington, DC",
    "BOS": "Boston, MA",
    "ELP": "El Paso, TX",
    "BNA": "Nashville, TN",
    "DTW": "Detroit, MI",
    "OKC": "Oklahoma City, OK",
    "PDX": "Portland, OR",
    "LAS": "Las Vegas, NV",
    "MEM": "Memphis, TN",
    "SDF": "Louisville, KY",
    "BWI": "Baltimore, MD",
    "MKE": "Milwaukee, WI",
    "ABQ": "Albuquerque, NM",
    "TUS": "Tucson, AZ",
    "FAT": "Fresno, CA",
    "SAC": "Sacramento, CA",
    "ATL": "Atlanta, GA",
    "MCI": "Kansas City, MO",
    "COS": "Colorado Springs, CO",
    "MIA": "Miami, FL",
    "RDU": "Raleigh, NC",
    "OMA": "Omaha, NE",
    "LGB": "Long Beach, CA",
    "NTU": "Virginia Beach, VA",
    "OAK": "Oakland, CA",
    "MSP": "Minneapolis, MN",
    "TUL": "Tulsa, OK",
    "TPA": "Tampa, FL",
    "MSY": "New Orleans, LA",
    "ICT": "Wichita, KS",
    "CLE": "Cleveland, OH",
    "BFL": "Bakersfield, CA",
    "HNL": "Honolulu, HI",
    "CRP": "Corpus Christi, TX",
    "LEX": "Lexington, KY",
    "SCK": "Stockton, CA",
    "STL": "St. Louis, MO",
    "CVG": "Cincinnati, OH",
    "PIT": "Pittsburgh, PA",
    "GSO": "Greensboro, NC",
    "ANC": "Anchorage, AK",
    "LNK": "Lincoln, NE",
    "MCO": "Orlando, FL",
    "EWR": "Newark, NJ",
    "TOL": "Toledo, OH",
    "FWA": "Fort Wayne, IN",
    "PIE": "St. Petersburg, FL",
    "LRD": "Laredo, TX",
    "MSN": "Madison, WI",
    "LBB": "Lubbock, TX",
    "RNO": "Reno, NV",
    "BUF": "Buffalo, NY",
    "ORF": "Norfolk, VA",
    "RIC": "Richmond, VA",
    "BOI": "Boise, ID",
    "GEG": "Spokane, WA",

    # City name variations
    "DENVER": "Denver, CO",
    "MIAMI": "Miami, FL",
    "NEWYORK": "New York, NY",
    "LOSANGELES": "Los Angeles, CA",
    "CHICAGO": "Chicago, IL",
    "HOUSTON": "Houston, TX",
    "PHOENIX": "Phoenix, AZ",
    "PHILADELPHIA": "Philadelphia, PA",
    "SANANTONIO": "San Antonio, TX",
    "SANDIEGO": "San Diego, CA",
    "DALLAS": "Dallas, TX",
    "SANJOSE": "San Jose, CA",
    "AUSTIN": "Austin, TX",
    "JACKSONVILLE": "Jacksonville, FL",
    "FORTWORTH": "Fort Worth, TX",
    "COLUMBUS": "Columbus, OH",
    "CHARLOTTE": "Charlotte, NC",
    "SANFRANCISCO": "San Francisco, CA",
    "INDIANAPOLIS": "Indianapolis, IN",
    "SEATTLE": "Seattle, WA",
    "WASHINGTON": "Washington, DC",
    "BOSTON": "Boston, MA",
    "NASHVILLE": "Nashville, TN",
    "DETROIT": "Detroit, MI",
    "PORTLAND": "Portland, OR",
    "LASVEGAS": "Las Vegas, NV",
    "MEMPHIS": "Memphis, TN",
    "LOUISVILLE": "Louisville, KY",
    "BALTIMORE": "Baltimore, MD",
    "MILWAUKEE": "Milwaukee, WI",
    "ALBUQUERQUE": "Albuquerque, NM",
    "TUCSON": "Tucson, AZ",
    "FRESNO": "Fresno, CA",
    "SACRAMENTO": "Sacramento, CA",
    "ATLANTA": "Atlanta, GA",
    "KANSASCITY": "Kansas City, MO",
    "RALEIGH": "Raleigh, NC",
    "OMAHA": "Omaha, NE",
    "TAMPA": "Tampa, FL",
    "NEWORLEANS": "New Orleans, LA",
    "WICHITA": "Wichita, KS",
    "CLEVELAND": "Cleveland, OH",
    "HONOLULU": "Honolulu, HI",
    "ORLANDO": "Orlando, FL",
    "CINCINNATI": "Cincinnati, OH",
    "PITTSBURGH": "Pittsburgh, PA",
    "ANCHORAGE": "Anchorage, AK",
    "MINNEAPOLIS": "Minneapolis, IN",
    "STLOUIS": "St. Louis, MO",
    "RICHMOND": "Richmond, VA",
    "BOISE": "Boise, ID",
    "SPOKANE": "Spokane, WA",
}


def get_city_config(city_name: str):
    """
    Get configuration for a city by name
    Handles various forms: "Denver, CO", "Denver", "DEN", etc.
    """
    # Try exact match first
    if city_name in CITY_DATABASE:
        return CITY_DATABASE[city_name]

    # Try abbreviation lookup
    city_upper = city_name.upper().replace(" ", "").replace(",", "")
    if city_upper in CITY_ABBREVIATIONS:
        full_name = CITY_ABBREVIATIONS[city_upper]
        if full_name in CITY_DATABASE:
            return CITY_DATABASE[full_name]

    # Try partial match (case insensitive)
    city_lower = city_name.lower()
    for full_name in CITY_DATABASE:
        if city_lower in full_name.lower():
            return CITY_DATABASE[full_name]

    return None


def normalize_city_name(city_name: str) -> str:
    """
    Normalize a city name to the standard format used in CITY_DATABASE
    Returns None if city is not recognized
    """
    # Try exact match
    if city_name in CITY_DATABASE:
        return city_name

    # Try abbreviation lookup
    city_upper = city_name.upper().replace(" ", "").replace(",", "")
    if city_upper in CITY_ABBREVIATIONS:
        return CITY_ABBREVIATIONS[city_upper]

    # Try partial match
    city_lower = city_name.lower()
    for full_name in CITY_DATABASE:
        if city_lower in full_name.lower():
            return full_name

    return None


def get_all_cities():
    """Get list of all supported cities"""
    return list(CITY_DATABASE.keys())
