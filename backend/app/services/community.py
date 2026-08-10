import sqlite3
from typing import Any, Dict, List, Optional

from ..database import get_connection


def list_community_posts(user_id: int, category: Optional[str] = None) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()

    sql = """
    SELECT
        p.id,
        p.user_id,
        p.author_name,
        p.content,
        p.category,
        p.likes_count,
        p.created_at,
        (SELECT COUNT(*) FROM community_comments c WHERE c.post_id = p.id) AS comments_count,
        (SELECT COUNT(*) FROM community_likes l WHERE l.post_id = p.id AND l.user_id = ?) AS user_has_liked
    FROM community_posts p
    """
    params = [user_id]

    if category and category.lower() != "all":
        sql += " WHERE LOWER(p.category) = ?"
        params.append(category.lower())

    sql += " ORDER BY p.created_at DESC"

    cursor.execute(sql, params)
    rows = cursor.fetchall()
    conn.close()

    result = []
    for r in rows:
        post = dict(r)
        post["user_has_liked"] = bool(post["user_has_liked"])
        result.append(post)
    return result


def get_post_by_id(post_id: int) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM community_posts WHERE id = ?", (post_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def create_community_post(user_id: int, author_name: str, content: str, category: str) -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO community_posts (user_id, author_name, content, category)
        VALUES (?, ?, ?, ?)
        """,
        (user_id, author_name, content, category),
    )
    conn.commit()
    post_id = cursor.lastrowid

    cursor.execute(
        """
        SELECT
            p.id,
            p.user_id,
            p.author_name,
            p.content,
            p.category,
            p.likes_count,
            p.created_at,
            0 AS comments_count,
            0 AS user_has_liked
        FROM community_posts p
        WHERE p.id = ?
        """,
        (post_id,),
    )
    row = cursor.fetchone()
    conn.close()

    post = dict(row)
    post["user_has_liked"] = False
    return post


def delete_community_post(user_id: int, post_id: int) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM community_posts WHERE id = ?", (post_id,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        return False

    if row["user_id"] != user_id:
        conn.close()
        raise PermissionError("User does not own this post")

    cursor.execute("DELETE FROM community_posts WHERE id = ?", (post_id,))
    conn.commit()
    conn.close()
    return True


def toggle_community_like(user_id: int, post_id: int) -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM community_posts WHERE id = ?", (post_id,))
    if not cursor.fetchone():
        conn.close()
        raise ValueError("Post not found")

    cursor.execute("SELECT id FROM community_likes WHERE post_id = ? AND user_id = ?", (post_id, user_id))
    like_row = cursor.fetchone()

    if like_row:
        # Unlike
        cursor.execute("DELETE FROM community_likes WHERE post_id = ? AND user_id = ?", (post_id, user_id))
        cursor.execute("UPDATE community_posts SET likes_count = MAX(0, likes_count - 1) WHERE id = ?", (post_id,))
        user_has_liked = False
    else:
        # Like
        cursor.execute("INSERT OR IGNORE INTO community_likes (post_id, user_id) VALUES (?, ?)", (post_id, user_id))
        cursor.execute("UPDATE community_posts SET likes_count = likes_count + 1 WHERE id = ?", (post_id,))
        user_has_liked = True

    conn.commit()

    cursor.execute("SELECT likes_count FROM community_posts WHERE id = ?", (post_id,))
    likes_count = cursor.fetchone()["likes_count"]
    conn.close()

    return {
        "post_id": post_id,
        "likes_count": likes_count,
        "user_has_liked": user_has_liked,
    }


def list_community_comments(post_id: int) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM community_posts WHERE id = ?", (post_id,))
    if not cursor.fetchone():
        conn.close()
        raise ValueError("Post not found")

    cursor.execute(
        """
        SELECT id, post_id, user_id, author_name, content, created_at
        FROM community_comments
        WHERE post_id = ?
        ORDER BY created_at ASC, id ASC
        """,
        (post_id,),
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def create_community_comment(user_id: int, author_name: str, post_id: int, content: str) -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM community_posts WHERE id = ?", (post_id,))
    if not cursor.fetchone():
        conn.close()
        raise ValueError("Post not found")

    cursor.execute(
        """
        INSERT INTO community_comments (post_id, user_id, author_name, content)
        VALUES (?, ?, ?, ?)
        """,
        (post_id, user_id, author_name, content),
    )
    conn.commit()
    comment_id = cursor.lastrowid

    cursor.execute("SELECT * FROM community_comments WHERE id = ?", (comment_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row)
