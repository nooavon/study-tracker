INSERT INTO reviews (card_id, rating, reviewed_at)
SELECT
    c.id,
    1 + (c.id * 7) % 5,
    CURRENT_TIMESTAMP - (c.id || ' hours')::interval
FROM cards AS c;

INSERT INTO reviews (card_id, rating, reviewed_at)
SELECT
    c.id,
    1 + (c.id * 3) % 5,
    CURRENT_TIMESTAMP - ((c.id + 24) || ' hours')::interval
FROM cards AS c
WHERE c.id % 2 = 0;