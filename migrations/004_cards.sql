CREATE TABLE IF NOT EXISTS cards (
  id SERIAL PRIMARY KEY,
  deck_id INTEGER NOT NULL REFERENCES decks(id) ON DELETE CASCADE,
  question TEXT NOT NULL,
  answer TEXT NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE cards ADD COLUMN IF NOT EXISTS question TEXT;
ALTER TABLE cards ADD COLUMN IF NOT EXISTS answer TEXT;

UPDATE cards SET question = '' WHERE question IS NULL;
UPDATE cards SET answer = '' WHERE answer IS NULL;

ALTER TABLE cards ALTER COLUMN question SET NOT NULL;
ALTER TABLE cards ALTER COLUMN answer SET NOT NULL;

INSERT INTO cards (deck_id, question, answer)
SELECT seed.deck_id, seed.question, seed.answer
FROM (
  VALUES
    (1, 'What does HTTP stand for?', 'HyperText Transfer Protocol'),
    (1, 'What status code means Not Found?', '404'),
    (2, 'Which SQL command retrieves rows?', 'SELECT')
) AS seed(deck_id, question, answer)
WHERE NOT EXISTS (
  SELECT 1
  FROM cards existing
  WHERE existing.deck_id = seed.deck_id
    AND existing.question = seed.question
    AND existing.answer = seed.answer
);