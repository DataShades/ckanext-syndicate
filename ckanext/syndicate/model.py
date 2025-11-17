from __future__ import annotations

import logging
from datetime import datetime as dt
from datetime import timezone as tz

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Index,
    PrimaryKeyConstraint,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, relationship

import ckan.plugins.toolkit as tk
from ckan import model

log = logging.getLogger(__name__)


class SyndicationLog(tk.BaseModel):
    __tablename__ = "syndication_log"

    __table_args__ = (
        PrimaryKeyConstraint("local_id", "profile_id"),
        Index("ix_syndication_log_local_profile", "local_id", "profile_id"),
    )

    class State:
        STOPPED = "stopped"
        FAILED = "failed"
        SYNCED = "synced"

    local_id: Mapped[str] = Column(ForeignKey(model.Package.id, ondelete="CASCADE"), nullable=False)  # type: ignore
    profile_id: Mapped[str] = Column(String(length=255), nullable=False)  # type: ignore
    target_id: Mapped[str] = Column(String(length=255), nullable=False, default="-")  # type: ignore

    state: Mapped[str] = Column(String(length=50), nullable=False)  # type: ignore
    error: Mapped[str | None] = Column(Text)  # type: ignore
    timestamp: Mapped[dt] = Column(DateTime(timezone=True), default=lambda: dt.now(tz=tz.utc), nullable=False)  # type: ignore

    local_package: Mapped[model.Package] = relationship(  # type: ignore
        "Package", backref="syndication_logs"
    )

    @classmethod
    def write(  # noqa: PLR0913
        cls,
        local_id: str,
        profile_id: str,
        target_id: str | None = None,
        state: str = State.SYNCED,
        error: str | None = None,
        defer_commit: bool = False,
    ) -> SyndicationLog:
        log_entry = cls.get(local_id, profile_id)

        if not log_entry:
            log_entry = cls(
                local_id=local_id,
                profile_id=profile_id,
                target_id=target_id or "-",
                state=state,
                error=error,
                timestamp=dt.now(tz=tz.utc),
            )
            model.Session.add(log_entry)

        else:
            # TODO: should we allow updating it?
            # we don't want to lose the target_id once set
            if target_id is not None:
                log_entry.target_id = target_id
            log_entry.state = state
            log_entry.error = error
            log_entry.timestamp = dt.now(tz=tz.utc)

        if not defer_commit:
            model.Session.commit()

        return log_entry

    @classmethod
    def get(cls, local_id: str, profile_id: str) -> SyndicationLog | None:
        return (
            model.Session.query(SyndicationLog)
            .filter(
                SyndicationLog.local_id == local_id,
                SyndicationLog.profile_id == profile_id,
            )
            .first()
        )
