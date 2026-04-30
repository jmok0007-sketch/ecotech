"""SQL strings for heavy_metal_state and heavy_metal_facility tables."""

SELECT_BY_STATE = """
    SELECT report_year, state, metal,
           total_air_emission_kg, total_water_emission_kg, total_land_emission_kg,
           facility_count
    FROM heavy_metal_state
    ORDER BY report_year, state, metal
"""

SELECT_BY_FACILITY = """
    SELECT report_year, facility_id, facility_name, state, postcode,
           latitude, longitude, metal,
           total_air_emission_kg, total_water_emission_kg, total_land_emission_kg
    FROM heavy_metal_facility
    WHERE latitude IS NOT NULL AND longitude IS NOT NULL
    ORDER BY total_air_emission_kg DESC, report_year DESC
    LIMIT %s OFFSET %s
"""

# Count total facilities for pagination metadata
COUNT_FACILITIES = """
    SELECT COUNT(*) as total
    FROM heavy_metal_facility
    WHERE latitude IS NOT NULL AND longitude IS NOT NULL
"""
