CREATE TABLE card_tags (
  card_id INTEGER NOT NULL REFERENCES cards(id),
  tag_id INTEGER NOT NULL REFERENCES tags(id),
  PRIMARY KEY (card_id, tag_id)
);

INSERT INTO card_tags (card_id, tag_id)
SELECT c.id, t.id
FROM cards c
JOIN tags t ON t.name = 'web'
WHERE c.question = 'What does HTTP stand for?'
ON CONFLICT DO NOTHING;

INSERT INTO card_tags (card_id, tag_id)
SELECT c.id, t.id
FROM cards c
JOIN tags t ON t.name = 'sql'
WHERE c.question = 'Which SQL command retrieves rows?'
ON CONFLICT DO NOTHING;

INSERT INTO card_tags (card_id, tag_id)
SELECT c.id, t.id
FROM cards c
JOIN tags t ON t.name = 'docker'
WHERE c.question = 'What status code means Not Found?'
ON CONFLICT DO NOTHING;