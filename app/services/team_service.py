from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.database import get_db


# -----------------------------
# Get Referral Tree
# -----------------------------
async def get_referral_tree(user_id: str, db: AsyncSession = Depends(get_db)):
    """
    Returns the referral tree for a given user as a nested structure with children.
    """

    # Fetch the user's referral_code
    query = text("SELECT referral_code FROM users WHERE id = :id")
    result = await db.execute(query, {"id": user_id})
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="User not found")

    referral_code = row.referral_code

    # Recursive CTE to get all referrals
    tree_query = text("""
        WITH RECURSIVE referral_tree AS (
            SELECT id, username, email, referral_code, referred_by_code, 1 as level
            FROM users
            WHERE referred_by_code = :referral_code
            UNION ALL
            SELECT u.id, u.username, u.email, u.referral_code, u.referred_by_code, rt.level + 1
            FROM users u
            INNER JOIN referral_tree rt ON u.referred_by_code = rt.referral_code
        )
        SELECT * FROM referral_tree ORDER BY level, username;
    """)

    result = await db.execute(tree_query, {"referral_code": referral_code})
    rows = result.fetchall()

    # Convert to dicts
    referrals = [
        {
            "id": str(r.id),
            "username": r.username,
            "email": r.email,
            "referral_code": r.referral_code,
            "referred_by_code": r.referred_by_code,
            "level": r.level,
            "children": []  # initialize empty children list
        }
        for r in rows
    ]

    # Build nested tree
    lookup = {r["referral_code"]: r for r in referrals}
    root_nodes = []

    for r in referrals:
        parent_code = r["referred_by_code"]
        if parent_code and parent_code in lookup:
            lookup[parent_code]["children"].append(r)
        else:
            root_nodes.append(r)

    return root_nodes
