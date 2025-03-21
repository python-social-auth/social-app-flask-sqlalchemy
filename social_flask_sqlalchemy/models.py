"""Flask SQLAlchemy ORM models for Social Auth"""

from social_core.utils import module_member, setting_name
from social_sqlalchemy.storage import (
    BaseSQLAlchemyStorage,
    SQLAlchemyAssociationMixin,
    SQLAlchemyCodeMixin,
    SQLAlchemyNonceMixin,
    SQLAlchemyPartialMixin,
    SQLAlchemyUserMixin,
)
from sqlalchemy import ForeignKey
from sqlalchemy.orm import (  # fmt: skip
    DeclarativeBase,
    backref,
    mapped_column,
    relationship,
)
from sqlalchemy.schema import UniqueConstraint


class PSABase(DeclarativeBase):
    pass


class _AppSession(PSABase):
    __abstract__ = True

    @classmethod
    def _set_session(cls, app_session):
        cls.app_session = app_session

    @classmethod
    def _session(cls):
        return cls.app_session


class UserSocialAuth(_AppSession, SQLAlchemyUserMixin):
    """Social Auth association model"""

    # Temporary override of constraints to avoid an error on the still-to-be
    # missing column uid.

    @classmethod
    def user_model(cls):
        return cls.user.property.argument

    @classmethod
    def username_max_length(cls):
        user_model = cls.user_model()
        return user_model.__table__.columns.get("username").type.length


class Nonce(_AppSession, SQLAlchemyNonceMixin):
    """One use numbers"""


class Association(_AppSession, SQLAlchemyAssociationMixin):
    """OpenId account association"""


class Code(_AppSession, SQLAlchemyCodeMixin):
    """Mail validation single one time use code"""


class Partial(_AppSession, SQLAlchemyPartialMixin):
    """Partial pipeline storage"""


class FlaskStorage(BaseSQLAlchemyStorage):
    user = UserSocialAuth
    nonce = Nonce
    association = Association
    code = Code
    partial = Partial


def init_social(app, session):
    User = module_member(app.config[setting_name("USER_MODEL")])
    _AppSession._set_session(session)
    UserSocialAuth.__table_args__ = (UniqueConstraint("provider", "uid"),)
    UserSocialAuth.user_id = mapped_column(
        ForeignKey(User.id), nullable=False, index=True
    )
    UserSocialAuth.user = relationship(
        User, backref=backref("social_auth", lazy="dynamic")
    )
