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
        p.credential_id,
        p.likes_count,
        p.created_at,
        s.profile_visibility,
        (SELECT COUNT(*) FROM community_comments c WHERE c.post_id = p.id) AS comments_count,
        (SELECT COUNT(*) FROM community_likes l WHERE l.post_id = p.id AND l.user_id = ?) AS user_has_liked,
        uc.slug AS cred_slug,
        uc.title AS cred_title,
        uc.description AS cred_desc,
        uc.tier AS cred_tier,
        uc.xp_value AS cred_xp,
        uc.credential_type AS cred_type,
        uc.issued_at AS cred_issued_at
    FROM community_posts p
    LEFT JOIN user_settings s ON s.user_id = p.user_id
    LEFT JOIN user_credentials uc ON uc.id = p.credential_id
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

        if post.get("credential_id") and post.get("cred_title"):
            post["credential"] = {
                "id": post["credential_id"],
                "slug": post["cred_slug"],
                "title": post["cred_title"],
                "description": post["cred_desc"],
                "tier": post["cred_tier"] or "bronze",
                "xp_value": post["cred_xp"] or 50,
                "credential_type": post["cred_type"],
                "issued_at": str(post["cred_issued_at"]) if post["cred_issued_at"] else None
            }
        else:
            post["credential"] = None

        # Clean temporary join columns
        for k in ["cred_slug", "cred_title", "cred_desc", "cred_tier", "cred_xp", "cred_type", "cred_issued_at"]:
            post.pop(k, None)

        result.append(post)
    return result


def get_post_by_id(post_id: int) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT 
            p.*,
            uc.slug AS cred_slug,
            uc.title AS cred_title,
            uc.description AS cred_desc,
            uc.tier AS cred_tier,
            uc.xp_value AS cred_xp,
            uc.credential_type AS cred_type,
            uc.issued_at AS cred_issued_at
        FROM community_posts p
        LEFT JOIN user_credentials uc ON uc.id = p.credential_id
        WHERE p.id = ?
        """,
        (post_id,)
    )
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    post = dict(row)
    post["author_name"] = _mask_author_name(post["user_id"], post["author_name"])
    if post.get("credential_id") and post.get("cred_title"):
        post["credential"] = {
            "id": post["credential_id"],
            "slug": post["cred_slug"],
            "title": post["cred_title"],
            "description": post["cred_desc"],
            "tier": post["cred_tier"] or "bronze",
            "xp_value": post["cred_xp"] or 50,
            "credential_type": post["cred_type"],
            "issued_at": str(post["cred_issued_at"]) if post["cred_issued_at"] else None
        }
    else:
        post["credential"] = None

    for k in ["cred_slug", "cred_title", "cred_desc", "cred_tier", "cred_xp", "cred_type", "cred_issued_at"]:
        post.pop(k, None)

    return post


def create_community_post(
    user_id: int, 
    author_name: str, 
    content: str, 
    category: str,
    credential_id: Optional[int] = None
) -> Dict[str, Any]:
    display_author = _mask_author_name(user_id, author_name)
    conn = get_connection()
    cursor = conn.cursor()

    if credential_id is not None:
        cursor.execute("SELECT id FROM user_credentials WHERE id = ? AND user_id = ?", (credential_id, user_id))
        cred_row = cursor.fetchone()
        if not cred_row:
            conn.close()
            raise ValueError("Invalid or unauthorized credential attachment")

    cursor.execute(
        """
        INSERT INTO community_posts (user_id, author_name, content, category, credential_id)
        VALUES (?, ?, ?, ?, ?)
        """,
        (user_id, display_author, content, category, credential_id),
    )
    conn.commit()
    post_id = cursor.lastrowid
    conn.close()

    return get_post_by_id(post_id)


def update_community_post(user_id: int, post_id: int, content: str) -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM community_posts WHERE id = ?", (post_id,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        raise ValueError("Post not found")

    if row["user_id"] != user_id:
        conn.close()
        raise PermissionError("User does not own this post")

    cursor.execute("UPDATE community_posts SET content = ? WHERE id = ?", (content, post_id))
    conn.commit()
    conn.close()
    return get_post_by_id(post_id)


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


async def toggle_community_like(user_id: int, post_id: int) -> Dict[str, Any]:
    from .notifications import create_notification
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id, user_id FROM community_posts WHERE id = ?", (post_id,))
    post_row = cursor.fetchone()
    if not post_row:
        conn.close()
        raise ValueError("Post not found")

    post_author_id = post_row["user_id"]

    cursor.execute("SELECT id FROM community_likes WHERE post_id = ? AND user_id = ?", (post_id, user_id))
    like_row = cursor.fetchone()

    if like_row:
        # Unlike
        cursor.execute("DELETE FROM community_likes WHERE post_id = ? AND user_id = ?", (post_id, user_id))
        cursor.execute("UPDATE community_posts SET likes_count = MAX(0, likes_count - 1) WHERE id = ?", (post_id,))
        user_has_liked = False
        conn.commit()
    else:
        # Like
        cursor.execute("INSERT INTO community_likes (post_id, user_id) VALUES (?, ?)", (post_id, user_id))
        cursor.execute("UPDATE community_posts SET likes_count = likes_count + 1 WHERE id = ?", (post_id,))
        user_has_liked = True
        conn.commit()

        # Trigger notification for post author if not self
        if post_author_id != user_id:
            cursor.execute("SELECT username, full_name FROM users WHERE id = ?", (user_id,))
            liker_row = cursor.fetchone()
            liker_name = (liker_row["full_name"] or liker_row["username"]) if liker_row else "Someone"
            await create_notification(
                user_id=post_author_id,
                type='community_like',
                title='New Post Like',
                message=f"{liker_name} liked your post",
                reference_type='post',
                reference_id=post_id
            )

    cursor.execute("SELECT likes_count FROM community_posts WHERE id = ?", (post_id,))
    likes_count = cursor.fetchone()["likes_count"]
    conn.close()

    return {
        "post_id": post_id,
        "likes_count": likes_count,
        "user_has_liked": user_has_liked,
    }


def delete_community_like(user_id: int, post_id: int) -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM community_posts WHERE id = ?", (post_id,))
    if not cursor.fetchone():
        conn.close()
        raise ValueError("Post not found")

    cursor.execute("DELETE FROM community_likes WHERE post_id = ? AND user_id = ?", (post_id, user_id))
    cursor.execute("UPDATE community_posts SET likes_count = MAX(0, likes_count - 1) WHERE id = ?", (post_id,))
    conn.commit()

    cursor.execute("SELECT likes_count FROM community_posts WHERE id = ?", (post_id,))
    likes_count = cursor.fetchone()["likes_count"]
    conn.close()

    return {
        "post_id": post_id,
        "likes_count": likes_count,
        "user_has_liked": False,
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


async def create_community_comment(user_id: int, author_name: str, post_id: int, content: str) -> Dict[str, Any]:
    from .notifications import create_notification
    display_author = _mask_author_name(user_id, author_name)
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id, user_id FROM community_posts WHERE id = ?", (post_id,))
    post_row = cursor.fetchone()
    if not post_row:
        conn.close()
        raise ValueError("Post not found")

    post_author_id = post_row["user_id"]

    cursor.execute(
        """
        INSERT INTO community_comments (post_id, user_id, author_name, content)
        VALUES (?, ?, ?, ?)
        """,
        (post_id, user_id, display_author, content),
    )
    comment_id = cursor.lastrowid
    conn.commit()

    # Trigger notification for post author if not self
    if post_author_id != user_id:
        cursor.execute("SELECT username, full_name FROM users WHERE id = ?", (user_id,))
        commenter_row = cursor.fetchone()
        commenter_name = (commenter_row["full_name"] or commenter_row["username"]) if commenter_row else "Someone"
        await create_notification(
            user_id=post_author_id,
            type='community_comment',
            title='New Comment',
            message=f"{commenter_name} commented on your post",
            reference_type='post',
            reference_id=post_id
        )

    cursor.execute("SELECT * FROM community_comments WHERE id = ?", (comment_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row)


def update_community_comment(user_id: int, comment_id: int, content: str) -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, post_id FROM community_comments WHERE id = ?", (comment_id,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        raise ValueError("Comment not found")

    if row["user_id"] != user_id:
        conn.close()
        raise PermissionError("User does not own this comment")

    cursor.execute("UPDATE community_comments SET content = ? WHERE id = ?", (content, comment_id))
    conn.commit()

    cursor.execute("SELECT * FROM community_comments WHERE id = ?", (comment_id,))
    comment_row = cursor.fetchone()
    conn.close()
    return dict(comment_row)


def delete_community_comment(user_id: int, comment_id: int) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM community_comments WHERE id = ?", (comment_id,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        return False

    if row["user_id"] != user_id:
        conn.close()
        raise PermissionError("User does not own this comment")

    cursor.execute("DELETE FROM community_comments WHERE id = ?", (comment_id,))
    conn.commit()
    conn.close()
    return True
