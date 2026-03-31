from app.database import AsyncSessionLocal
from sqlalchemy import text


async def read_funnel_file(path: str, funnel_id: str, db=None) -> str:
    """
    Reads a single file from funnel_projects.files JSONB.
    Returns the file content string or empty string when not found.
    """
    if db is None:
        async with AsyncSessionLocal() as session:
            return await _read_funnel_file_impl(path, funnel_id, session)
    return await _read_funnel_file_impl(path, funnel_id, db)


async def _read_funnel_file_impl(path: str, funnel_id: str, db) -> str:
    query = text(
        """
        SELECT files->>:path AS content
        FROM funnel_projects
        WHERE funnel_id = :funnel_id
        """
    )
    result = await db.execute(query, {"path": path, "funnel_id": funnel_id})
    content = result.scalar_one_or_none()
    return content or ""


async def write_funnel_file(path: str, content: str, funnel_id: str, db=None) -> str:
    """
    Writes a complete file to funnel_projects.files JSONB.
    """
    if db is None:
        async with AsyncSessionLocal() as session:
            return await _write_funnel_file_impl(path, content, funnel_id, session)
    return await _write_funnel_file_impl(path, content, funnel_id, db)


async def _write_funnel_file_impl(path: str, content: str, funnel_id: str, db) -> str:
    query = text(
        """
        UPDATE funnel_projects
        SET files = jsonb_set(
                COALESCE(files, '{}'::jsonb),
                ARRAY[:path],
                to_jsonb(CAST(:content AS text)),
                true
            ),
            updated_at = now()
        WHERE funnel_id = :funnel_id
        """
    )
    await db.execute(query, {"path": path, "content": content, "funnel_id": funnel_id})
    await db.commit()
    return f"Written: {path}"


async def edit_funnel_file(path: str, old_str: str, new_str: str, funnel_id: str, db=None) -> str:
    """
    Makes a surgical replacement in an existing file.
    Replaces only the first occurrence of old_str.
    """
    if db is None:
        async with AsyncSessionLocal() as session:
            return await _edit_funnel_file_impl(path, old_str, new_str, funnel_id, session)
    return await _edit_funnel_file_impl(path, old_str, new_str, funnel_id, db)


async def _edit_funnel_file_impl(path: str, old_str: str, new_str: str, funnel_id: str, db) -> str:
    current_content = await _read_funnel_file_impl(path, funnel_id, db)
    if not current_content:
        return f"File {path} not found. Use write_funnel_file to create it."

    if not old_str or old_str not in current_content:
        return (
            f"String not found in {path}. Call read_funnel_file first and "
            "use the exact text you want to replace."
        )

    updated_content = current_content.replace(old_str, new_str, 1)
    await _write_funnel_file_impl(path, updated_content, funnel_id, db)
    return f"Edited: {path}"


async def delete_funnel_file(path: str, funnel_id: str, db=None) -> str:
    """
    Removes a file key from funnel_projects.files JSONB.
    """
    if db is None:
        async with AsyncSessionLocal() as session:
            return await _delete_funnel_file_impl(path, funnel_id, session)
    return await _delete_funnel_file_impl(path, funnel_id, db)


async def _delete_funnel_file_impl(path: str, funnel_id: str, db) -> str:
    remove_file_query = text(
        """
        UPDATE funnel_projects
        SET files = files - :path,
            updated_at = now()
        WHERE funnel_id = :funnel_id
        """
    )
    await db.execute(remove_file_query, {"path": path, "funnel_id": funnel_id})
    await db.commit()
    return f"Deleted: {path}"
