from datetime import datetime, timezone

from app.extensions.db import db


class VideoRecording(db.Model):
    """Metadaten zu einem per Bewegung ausgelösten Video in S3/MinIO."""

    __tablename__ = "video_recordings"

    id = db.Column(db.Integer, primary_key=True)
    recorded_at = db.Column(db.DateTime(timezone=True), nullable=False)
    duration_seconds = db.Column(db.Integer, nullable=False)
    bucket = db.Column(db.String(255), nullable=False)
    object_key = db.Column(db.String(1024), nullable=False)
    content_type = db.Column(db.String(128), nullable=False, default="video/mp4")
    size_bytes = db.Column(db.BigInteger, nullable=True)
    status = db.Column(db.String(32), nullable=False, default="stored")
    error_message = db.Column(db.Text, nullable=True)
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def __repr__(self):
        return (
            f"<VideoRecording id={self.id} status={self.status} "
            f"bucket={self.bucket} object_key={self.object_key} recorded_at={self.recorded_at}>"
        )
