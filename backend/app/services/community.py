import sqlite3
from typing import Any, Dict, List, Optional

from ..database import get_connection


def _mask_author_name(user_id: int, original_author_name: str) -> str:
    """Helper to check author's profile_visibility and return 'Anonymous Member' if set to private."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT profile_visibility FROM user_settings WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row and row["profile_visibility"] == "private":
        return "Anonymous Member"
    return original_author_name


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
        s.profile_visibility,
        (SELECT COUNT(*) FROM community_comments c WHERE c.post_id = p.id) AS comments_count,
        (SELECT COUNT(*) FROM community_likes l WHERE l.post_id = p.id AND l.user_id = ?) AS user_has_liked
    FROM community_posts p
    LEFT JOIN user_settings s ON s.user_id = p.user_id
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
        if post.get("profile_visibility") == "private":
            post["author_name"] = "Anonymous Member"
        post.pop("profile_visibility", None)
        result.append(post)
    return result


def get_post_by_id(post_id: int) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM community_posts WHERE id = ?", (post_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    post = dict(row)
    post["author_name"] = _mask_author_name(post["user_id"], post["author_name"])
    return post


def create_community_post(user_id: int, author_name: str, content: str, category: str) -> Dict[str, Any]:
    display_author = _mask_author_name(user_id, author_name)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO community_posts (user_id, author_name, content, category)
        VALUES (?, ?, ?, ?)
        """,
        (user_id, display_author, content, category),
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
        SELECT
            c.id,
            c.post_id,
            c.user_id,
            c.author_name,
            c.content,
            c.created_at,
            s.profile_visibility
        FROM community_comments c
        LEFT JOIN user_settings s ON s.user_id = c.user_id
        WHERE c.post_id = ?
        ORDER BY c.created_at ASC, c.id ASC
        """,
        (post_id,),
    )
    rows = cursor.fetchall()
    conn.close()

    result = []
    for r in rows:
        comment = dict(r)
        if comment.get("profile_visibility") == "private":
            comment["author_name"] = "Anonymous Member"
        comment.pop("profile_visibility", None)
        result.append(comment)
    return result


def create_community_comment(user_id: int, author_name: str, post_id: int, content: str) -> Dict[str, Any]:
    display_author = _mask_author_name(user_id, author_name)
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
        (post_id, user_id, display_author, content),
    )
    conn.commit()
    comment_id = cursor.lastrowid

    cursor.execute("SELECT * FROM community_comments WHERE id = ?", (comment_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row)
