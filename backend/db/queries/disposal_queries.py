"""SQL strings for ewaste_facilities table."""

SELECT_ALL = """
    SELECT facility_name, address, suburb, postcode, state,
           latitude, longitude, coord_source, verified
    FROM ewaste_facilities
    WHERE latitude IS NOT NULL AND longitude IS NOT NULL
    ORDER BY state, suburb, facility_name
"""

SELECT_BY_POSTCODE = """
    SELECT facility_name, address, suburb, postcode, state,
           latitude, longitude, coord_source, verified
    FROM ewaste_facilities
    WHERE postcode = %(postcode)s
      AND latitude IS NOT NULL AND longitude IS NOT NULL
    ORDER BY suburb, facility_name
"""
