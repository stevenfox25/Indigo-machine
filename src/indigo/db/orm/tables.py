from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Recipe(Base):
    __tablename__ = "recipes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    lane: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    name: Mapped[str | None] = mapped_column(String(200))

    # Scalars
    cycle_type: Mapped[str] = mapped_column(String(32), default="full")
    fixed_hold_time: Mapped[bool] = mapped_column(Boolean, default=False)

    autopinbreak_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    num_autopinbreaks: Mapped[int] = mapped_column(Integer, default=0)

    attempt_time_s: Mapped[int] = mapped_column(Integer, default=0)

    thermal_temp_c: Mapped[float] = mapped_column(Float, default=0.0)
    reflux_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    reflux_temp_c: Mapped[float] = mapped_column(Float, default=0.0)

    purge_vac_switchpoint: Mapped[float] = mapped_column(Float, default=0.0)
    stir_speed_rpm: Mapped[int] = mapped_column(Integer, default=0)
    purge_set_pressure: Mapped[float] = mapped_column(Float, default=0.0)

    # Versioning / selection
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    created_ts: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    active: Mapped[bool] = mapped_column(Boolean, default=False, index=True)

    # Children
    pinbreak_steps: Mapped[list[RecipePinBreakStep]] = relationship(
        back_populates="recipe",
        cascade="all, delete-orphan",
        order_by="RecipePinBreakStep.step_index",
    )

    __table_args__ = (
        # You can enforce only one active per lane at the app level (recommended).
        UniqueConstraint("id", "lane", name="uq_recipe_id_lane"),
    )

    @staticmethod
    def compute_sha256_from_payload(payload: dict[str, Any]) -> str:
        normalized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


class RecipePinBreakStep(Base):
    __tablename__ = "recipe_pinbreak_steps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    recipe_id: Mapped[int] = mapped_column(ForeignKey("recipes.id", ondelete="CASCADE"), nullable=False, index=True)
    step_index: Mapped[int] = mapped_column(Integer, nullable=False)

    # Arrays (now rows)
    autopinbreak_time_ms: Mapped[int | None] = mapped_column(Integer)
    autopinbreak_pressure: Mapped[float | None] = mapped_column(Float)

    postpinbreak_thermal_temp_c: Mapped[float | None] = mapped_column(Float)
    postpinbreak_pressure: Mapped[float | None] = mapped_column(Float)
    postpinbreak_reflux_temp_c: Mapped[float | None] = mapped_column(Float)
    postpinbreak_stir_speed_rpm: Mapped[int | None] = mapped_column(Integer)

    recipe: Mapped[Recipe] = relationship(back_populates="pinbreak_steps")

    __table_args__ = (
        UniqueConstraint("recipe_id", "step_index", name="uq_recipe_step_index"),
    )
