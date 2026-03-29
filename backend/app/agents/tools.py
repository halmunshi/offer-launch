from sqlalchemy import text


async def read_funnel_file(path: str, funnel_id: str, db) -> str:
    """
    Reads a single file from funnel_projects.files JSONB.
    Returns the file content string. Returns empty string if not found.
    """
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


async def write_funnel_file(path: str, content: str, funnel_id: str, db) -> str:
    """
    Writes a complete file to funnel_projects.files JSONB.
    ONE DB effect: jsonb_set patches only the specific path key.
    """
    query = text(
        """
        UPDATE funnel_projects
        SET files = jsonb_set(
                COALESCE(files, '{}'::jsonb),
                ARRAY[:path],
                to_jsonb(CAST(:content AS text))
            ),
            updated_at = now()
        WHERE funnel_id = :funnel_id
        """
    )
    await db.execute(query, {"path": path, "content": content, "funnel_id": funnel_id})
    await db.commit()
    return f"Written: {path}"


async def edit_funnel_file(path: str, old_str: str, new_str: str, funnel_id: str, db) -> str:
    """
    Makes a surgical replacement within an existing file.
    Replaces only the first occurrence of old_str.
    """
    select_query = text(
        """
        SELECT
            files ? :path AS file_exists,
            files->>:path AS content
        FROM funnel_projects
        WHERE funnel_id = :funnel_id
        """
    )
    result = await db.execute(select_query, {"path": path, "funnel_id": funnel_id})
    row = result.mappings().first()

    if not row or not row["file_exists"]:
        return f"File {path} not found. Use write_funnel_file to create it."

    current_content = row["content"] or ""
    if not old_str or old_str not in current_content:
        return (
            f"String not found in {path}. Call read_funnel_file first and "
            "use the exact text you want to replace."
        )

    updated_content = current_content.replace(old_str, new_str, 1)

    update_query = text(
        """
        UPDATE funnel_projects
        SET files = jsonb_set(
                COALESCE(files, '{}'::jsonb),
                ARRAY[:path],
                to_jsonb(CAST(:content AS text))
            ),
            updated_at = now()
        WHERE funnel_id = :funnel_id
        """
    )
    await db.execute(update_query, {"path": path, "content": updated_content, "funnel_id": funnel_id})
    await db.commit()

    return f"Edited: {path}"


async def delete_funnel_file(path: str, step_id: str, funnel_id: str, db) -> str:
    """
    Removes a file from funnel_projects.files JSONB and deletes funnel_steps row.
    """
    remove_file_query = text(
        """
        UPDATE funnel_projects
        SET files = COALESCE(files, '{}'::jsonb) - :path,
            updated_at = now()
        WHERE funnel_id = :funnel_id
        """
    )
    delete_step_query = text(
        """
        DELETE FROM funnel_steps
        WHERE id = :step_id
        """
    )

    try:
        await db.execute(remove_file_query, {"path": path, "funnel_id": funnel_id})
        await db.execute(delete_step_query, {"step_id": step_id})
        await db.commit()
    except Exception:
        await db.rollback()
        raise

    return f"Deleted: {path}"
