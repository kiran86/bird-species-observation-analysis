-- 1. Which habitat has more recorded bird observations?
SELECT
  habitat_type,
  COUNT(*) AS total_observations,
  COUNT(DISTINCT common_name) AS unique_species
FROM bird_observations
GROUP BY habitat_type
ORDER BY total_observations DESC;

-- 2. Which admin units have the highest bird activity?
SELECT
  habitat_type,
  admin_unit_code,
  COUNT(*) AS total_observations,
  COUNT(DISTINCT common_name) AS unique_species
FROM bird_observations
GROUP BY habitat_type, admin_unit_code
ORDER BY total_observations DESC;

-- 3. Which bird species prefer forest vs grassland?
SELECT
  common_name,
  habitat_type,
  COUNT(*) AS total_observations
FROM bird_observations
GROUP BY common_name, habitat_type
ORDER BY common_name, total_observations DESC;

-- 4. Which species appear only in one habitat?
WITH species_habitats AS (
  SELECT
    common_name,
    COUNT(DISTINCT habitat_type) AS habitat_count,
    MIN(habitat_type) AS habitat_type
  FROM bird_observations
  GROUP BY common_name
)
SELECT common_name, habitat_type
FROM species_habitats
WHERE habitat_count = 1
ORDER BY habitat_type, common_name;

-- 5. How does weather relate to bird observations per survey event?
SELECT
  habitat_type,
  ROUND(AVG(bird_observation_count), 2) AS avg_bird_observations,
  ROUND(AVG(unique_species_count), 2) AS avg_unique_species,
  ROUND(AVG(temperature), 2) AS avg_temperature,
  ROUND(AVG(humidity), 2) AS avg_humidity
FROM survey_event_summary
GROUP BY habitat_type
ORDER BY avg_bird_observations DESC;

-- 6. Which temperature bands have the highest average bird activity?
SELECT
  habitat_type,
  temperature_band,
  avg_bird_observations,
  avg_unique_species,
  survey_events
FROM weather_summary
ORDER BY habitat_type, avg_bird_observations DESC;

-- 7. Morning activity check using the start hour.
SELECT
  habitat_type,
  start_hour,
  COUNT(*) AS total_observations
FROM bird_observations
GROUP BY habitat_type, start_hour
ORDER BY habitat_type, total_observations DESC;
