from typing import TYPE_CHECKING

from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy import UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from hushline.db import db
from hushline.model.enums import FieldType

if TYPE_CHECKING:
    from flask_sqlalchemy.model import Model

    from hushline.model.username import Username
else:
    Model = db.Model


class FieldDefinition(Model):
    __tablename__ = "field_definitions"
    __table_args__ = (UniqueConstraint("username_id", "sort_order"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    username_id: Mapped[int] = mapped_column(db.ForeignKey("usernames.id"), index=True)
    username: Mapped["Username"] = relationship(back_populates="message_fields")
    label: Mapped[str] = mapped_column(db.String(255))
    field_type: Mapped[FieldType] = mapped_column(SQLAlchemyEnum(FieldType), default=FieldType.TEXT)
    required: Mapped[bool] = mapped_column(default=False)
    enabled: Mapped[bool] = mapped_column(default=True)
    encrypted: Mapped[bool] = mapped_column(default=False)
    choices: Mapped[list[str]] = mapped_column(type_=JSONB, default=[])
    sort_order: Mapped[int] = mapped_column(default=0)

    def __init__(  # noqa: PLR0913
        self,
        username: "Username",
        label: str,
        field_type: FieldType,
        required: bool,
        enabled: bool,
        encrypted: bool,
        choices: list[str],
    ) -> None:
        self.username = username
        self.label = label
        self.field_type = field_type
        self.required = required
        self.enabled = enabled
        self.encrypted = encrypted
        self.choices = choices

        # Calculate sort_order
        self.sort_order = (
            db.session.query(FieldDefinition)
            .filter(FieldDefinition.username_id == username.id)
            .count()
        )

    def move_up(self) -> None:
        if self.sort_order == 0:
            return

        # Select the field above the current field
        field_above = (
            db.session.query(FieldDefinition)
            .filter(
                FieldDefinition.username_id == self.username.id,
                FieldDefinition.sort_order == self.sort_order - 1,
            )
            .one_or_none()
        )

        if field_above:
            above_sort_order = field_above.sort_order
            below_sort_order = self.sort_order

            # Set sort orders to temp values first to avoid unique constraint violation
            field_above.sort_order = -1
            self.sort_order = -2
            db.session.commit()

            # Swap the sort orders
            field_above.sort_order = below_sort_order
            self.sort_order = above_sort_order
            db.session.commit()

    def move_down(self) -> None:
        # Select the field below the current field
        field_below = (
            db.session.query(FieldDefinition)
            .filter(
                FieldDefinition.username_id == self.username.id,
                FieldDefinition.sort_order == self.sort_order + 1,
            )
            .one_or_none()
        )

        if field_below:
            above_sort_order = self.sort_order
            below_sort_order = field_below.sort_order

            # Set sort orders to temp values first to avoid unique constraint violation
            self.sort_order = -1
            field_below.sort_order = -2
            db.session.commit()

            # Swap the sort orders
            self.sort_order = below_sort_order
            field_below.sort_order = above_sort_order
            db.session.commit()

    def __repr__(self) -> str:
        return f"<FieldDefinition {self.username.username}, {self.label}>"
