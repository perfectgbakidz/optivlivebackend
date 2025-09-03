import uuid
from fastapi import UploadFile
from app.utils.supabase_client import supabase

async def upload_to_supabase(file: UploadFile, folder="kyc"):
    # Ensure filename is safe
    file_ext = (file.filename or "file").split(".")[-1]
    file_name = f"{folder}/{uuid.uuid4()}.{file_ext}"

    # Read file content
    content = await file.read()

    # Upload to Supabase bucket "documents"
    res = supabase.storage.from_("documents").upload(
        file_name,
        content,
        {"cacheControl": "3600", "upsert": False}
    )

    if isinstance(res, dict) and res.get("error"):
        raise Exception(f"Supabase upload failed: {res['error']}")

    # Generate public URL
    public_url = supabase.storage.from_("documents").get_public_url(file_name)
    return public_url
