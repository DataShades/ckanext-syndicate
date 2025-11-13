from __future__ import annotations

import logging
from datetime import datetime as dt
from datetime import timezone as tz

from sqlalchemy import Column, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, relationship

import ckan.plugins.toolkit as tk
from ckan import model

log = logging.getLogger(__name__)


class SyndicationLog(tk.BaseModel):
    __tablename__ = "syndication_log"

    __table_args__ = (
        Index("ix_syndication_log_local_profile", "local_id", "profile_id"),
    )

    class State:
        PENDING = "pending"
        STOPPED = "stopped"
        FAILED = "failed"
        SYNCED = "synced"

    local_id: Mapped[str] = Column(ForeignKey(model.Package.id, ondelete="CASCADE"), nullable=False)  # type: ignore
    target_id: Mapped[str] = Column(String(length=255), nullable=False, primary_key=True)  # type: ignore
    profile_id: Mapped[str] = Column(String(length=255), nullable=False, primary_key=True)  # type: ignore

    state: Mapped[str] = Column(String(length=50), nullable=False)  # type: ignore
    error: Mapped[str | None] = Column(Text)  # type: ignore
    timestamp: Mapped[dt] = Column(DateTime(timezone=True), default=lambda: dt.now(tz=tz.utc), nullable=False)  # type: ignore

    local_package: Mapped[model.Package] = relationship(  # type: ignore
        "Package", backref="syndication_logs"
    )

    @classmethod
    def get_profile_records(cls, profile_id: str) -> list[SyndicationLog]:
        return (
            model.Session.query(SyndicationLog)
            .filter(SyndicationLog.profile_id == profile_id)
            .all()
        )

    @classmethod
    def write(
        cls,
        local_id: str,
        target_id: str,
        profile_id: str,
        state: str,
        error: str | None = None,
    ) -> SyndicationLog:
        log_entry = cls(
            local_id=local_id,
            target_id=target_id,
            profile_id=profile_id,
            state=state,
            error=error,
            timestamp=dt.now(tz.utc),
        )
        model.Session.merge(log_entry)
        model.Session.commit()
        return log_entry

        # log_entry = cls.get(local_id, target_id, profile_id)
        # now = dt.now(tz.utc)

        # if log_entry:
        #     log_entry.state = state
        #     log_entry.error = error
        #     log_entry.timestamp = now
        # else:
        #     log_entry = cls(
        #         local_id=local_id,
        #         target_id=target_id,
        #         profile_id=profile_id,
        #         state=state,
        #         error=error,
        #         timestamp=now,
        #     )
        #     model.Session.add(log_entry)

        # model.Session.commit()
        # return log_entry

    @classmethod
    def get(
        cls, local_id: str, target_id: str, profile_id: str
    ) -> SyndicationLog | None:
        return (
            model.Session.query(SyndicationLog)
            .filter(
                SyndicationLog.local_id == local_id,
                SyndicationLog.target_id == target_id,
                SyndicationLog.profile_id == profile_id,
            )
            .first()
        )
