CREATE VIEW research_entries AS
SELECT de.id AS entry_id, de.title, de.description, STRING_AGG((SELECT t.value WHERE t.category = 'dream_content'), ';') AS content_tags,
       STRING_AGG((SELECT t.value WHERE t.category = 'dream_type'), ';') AS type_tags, de.sense_sight, de.sense_sound, 
	   de.sense_touch, de.sense_smell, de.sense_taste, de.sense_pain, de.sense_other, de.created_at, de.context, 
	   STRING_AGG((SELECT t.value WHERE t.category = 'irl_context'), ';') AS context_tags, de.bed_time, de.wake_time,
	   de.sleep_hours, de.country, de.state, de.city, BOOL_OR(t.value = 'Atypical Location') AS not_at_home, 
	   de.reflection, de.rfln_timestamp, u.username, EXTRACT(DAY FROM (NOW()-u.birth_date))/365.25 AS user_age, 
	   u.gender AS user_gender, u.med_conditions AS user_med_conditions
FROM dream_entries AS de
LEFT OUTER JOIN dream_entry_tags AS det ON de.id = det.entry_id
LEFT OUTER JOIN tags AS t ON det.tag_val = t.value
LEFT OUTER JOIN users AS u ON u.id = de.user_id
WHERE de.public = true
GROUP BY de.id, u.id
ORDER BY de.id ASC