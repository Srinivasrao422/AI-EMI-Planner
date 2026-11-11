"""Data access helpers for user-owned MSME business profiles."""

from database.connection import get_connection


def _validate_profile(data):
    required = ("business_name", "business_type", "industry", "city", "state")
    cleaned = {}
    for field in required:
        value = str(data.get(field, "")).strip()
        if not value:
            raise ValueError(f"{field.replace('_', ' ').title()} is required.")
        cleaned[field] = value

    optional_text = ("registration_type", "registration_number", "country")
    for field in optional_text:
        value = data.get(field)
        cleaned[field] = str(value).strip() if value is not None else ""

    year = data.get("started_year")
    if year in (None, ""):
        cleaned["started_year"] = None
    else:
        try:
            year = int(year)
        except (TypeError, ValueError) as exc:
            raise ValueError("Business start year must be a valid year.") from exc
        if year < 1800 or year > 2100:
            raise ValueError("Business start year must be between 1800 and 2100.")
        cleaned["started_year"] = year

    cleaned["country"] = cleaned["country"] or "India"
    return cleaned


def get_user_business_profiles(user_id):
    """Return all business profiles owned by a user, newest first."""
    if not user_id:
        return []
    conn = get_connection()
    try:
        conn.row_factory = __import__("sqlite3").Row
        rows = conn.execute(
            """
            SELECT id, user_id, business_name, business_type, industry,
                   registration_type, registration_number, city, state,
                   country, started_year, created_at, updated_at
            FROM business_profiles
            WHERE user_id = ?
            ORDER BY updated_at DESC, id DESC
            """,
            (user_id,),
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def save_business_profile(user_id, data, profile_id=None):
    """Create or update a profile, enforcing user ownership."""
    if not user_id:
        raise ValueError("A signed-in user is required.")
    values = _validate_profile(data)
    conn = get_connection()
    try:
        with conn:
            if profile_id is None:
                cursor = conn.execute(
                    """
                    INSERT INTO business_profiles (
                        user_id, business_name, business_type, industry,
                        registration_type, registration_number, city, state,
                        country, started_year
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        user_id, values["business_name"], values["business_type"],
                        values["industry"], values["registration_type"],
                        values["registration_number"], values["city"], values["state"],
                        values["country"], values["started_year"],
                    ),
                )
                return cursor.lastrowid

            cursor = conn.execute(
                """
                UPDATE business_profiles
                SET business_name = ?, business_type = ?, industry = ?,
                    registration_type = ?, registration_number = ?,
                    city = ?, state = ?, country = ?, started_year = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND user_id = ?
                """,
                (
                    values["business_name"], values["business_type"], values["industry"],
                    values["registration_type"], values["registration_number"],
                    values["city"], values["state"], values["country"],
                    values["started_year"], profile_id, user_id,
                ),
            )
            if cursor.rowcount != 1:
                raise ValueError("Business profile was not found for this user.")
            return profile_id
    finally:
        conn.close()


def delete_business_profile(user_id, profile_id):
    """Delete only a profile owned by the supplied user."""
    conn = get_connection()
    try:
        with conn:
            cursor = conn.execute(
                "DELETE FROM business_profiles WHERE id = ? AND user_id = ?",
                (profile_id, user_id),
            )
            return cursor.rowcount == 1
    finally:
        conn.close()
