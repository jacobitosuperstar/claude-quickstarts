"""Base database interactions used across the app.
"""


def get_instance():
    ...


def filter_instances(model, session, filters: dict, limit: int = 100, offset: int = 0):
    """
    General utility to filter instances of a SQLAlchemy model with pagination.
    Args:
        model: SQLAlchemy model class
        session: SQLAlchemy session
        filters: dict of field names and values to filter by
        limit: max number of results to return
        offset: number of results to skip
    Returns:
        (results, total_count):
            results: List of model instances matching the filters (paginated)
            total_count: Total number of matching records (before pagination)
    """
    query = session.query(model)
    for key, value in filters.items():
        if hasattr(model, key) and value is not None:
            query = query.filter(getattr(model, key) == value)
    total_count = query.count()
    results = query.offset(offset).limit(limit).all()
    return results, total_count
