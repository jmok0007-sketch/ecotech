"""SQL strings for the health_merged table. Kept separate from business
logic so they're easy to audit and tune."""

SELECT_ALL = """
    SELECT year, sex, cancer_type, cancer_cases, cancer_deaths, fatality_ratio
    FROM health_merged
    ORDER BY year, cancer_type, sex
"""

SELECT_BY_FILTERS = """
    SELECT year, sex, cancer_type, cancer_cases, cancer_deaths, fatality_ratio
    FROM health_merged
    WHERE (%(year)s IS NULL OR year = %(year)s)
      AND (%(sex)s IS NULL OR sex = %(sex)s)
      AND (%(cancer_type)s IS NULL OR cancer_type = %(cancer_type)s)
    ORDER BY year, cancer_type, sex
"""

SELECT_DISTINCT_YEARS = "SELECT DISTINCT year FROM health_merged ORDER BY year"
SELECT_DISTINCT_SEX = "SELECT DISTINCT sex FROM health_merged ORDER BY sex"
SELECT_DISTINCT_CANCERS = "SELECT DISTINCT cancer_type FROM health_merged ORDER BY cancer_type"
