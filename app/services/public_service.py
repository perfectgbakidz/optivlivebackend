from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from datetime import datetime
from uuid import uuid4
from app.database import get_db


# -----------------------------
# CONTACT FORM SUBMISSION
# -----------------------------
async def contact_form(payload: dict, db: AsyncSession = Depends(get_db)):
    """
    Store contact form submissions in the database.
    Optionally, could also forward to email via utils/email_handler.
    """
    cid = str(uuid4())

    insert_q = text("""
        INSERT INTO contacts (id, name, email, subject, message, submitted_at)
        VALUES (:id, :name, :email, :subject, :message, :submitted_at)
    """)
    values = {
        "id": cid,
        "name": payload.get("name"),
        "email": payload.get("email"),
        "subject": payload.get("subject"),
        "message": payload.get("message"),
        "submitted_at": datetime.utcnow(),
    }

    await db.execute(insert_q, values)
    await db.commit()

    return {
        "success": True,
        "message": "Your message has been received.",
        "contact_id": cid
    }
