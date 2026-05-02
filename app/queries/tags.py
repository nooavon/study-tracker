def fetch_all_tags(conn):
    return conn.execute(
        "SELECT id, name FROM tags ORDER BY name ASC"
    ).fetchall()

def fetch_newest_tag(conn):
    return conn.execute(
        "SELECT id, name FROM tags ORDER BY created_at DESC, id DESC LIMIT 1"
    ).fetchone()

def fetch_tag_by_id(conn, tag_id):
    return conn.execute(
        f"SELECT id, name FROM tags WHERE id = {tag_id}",
    ).fetchone()

def insert_tag(conn, name):
    return conn.execute(
        "INSERT INTO tags (name) VALUES (%s)",
        (name,)
    )

def update_tag(conn, tag_id, name):
    return conn.execute(
        "UPDATE tags SET name = %s WHERE id = %s",
        (name, tag_id)
    )

def delete_tag(conn, tag_id):
    return conn.execute(
        "DELETE FROM tags WHERE id = %s",
        (tag_id,)
    )