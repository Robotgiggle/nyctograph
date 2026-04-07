CREATE VIEW research_entries AS
SELECT de.title, de.description, STRING_AGG((SELECT t.value WHERE t.category = 'dream_content'), ';') AS content_tags,
       STRING_AGG((SELECT t.value WHERE t.category = 'dream_type'), ';') AS type_tags, de.sense_sight, de.sense_sound, 
	   de.sense_touch, de.sense_smell, de.sense_taste, de.sense_pain, de.sense_other, de.created_at, de.context, 
	   STRING_AGG((SELECT t.value WHERE t.category = 'irl_context'), ';') AS context_tags, de.bed_time, de.wake_time,
	   de.country, de.state, de.city, de.reflection, de.rfln_timestamp,
	   (SELECT COUNT(*) FROM follow_up_reflections fur WHERE fur.entry_id = de.id) AS follow_up_count,
	   (SELECT STRING_AGG(fur.text, E'\n---\n' ORDER BY fur.created_at) FROM follow_up_reflections fur WHERE fur.entry_id = de.id) AS follow_up_reflections,
	   u.username, u.gender AS user_gender,
	   EXTRACT(DAY FROM (NOW()-u.birth_date))/365.25 AS user_age, u.med_conditions AS user_med_conditions
FROM dream_entries AS de
LEFT OUTER JOIN dream_entry_tags AS det ON de.id = det.entry_id
LEFT OUTER JOIN tags AS t ON det.tag_val = t.value
LEFT OUTER JOIN users AS u ON u.id = de.user_id
WHERE de.public = true
GROUP BY de.id, u.id
ORDER BY de.id ASC