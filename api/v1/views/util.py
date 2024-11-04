def to_dict(obj):
    return {c.key: getattr(obj, c.key) for c in obj.__table__.columns}