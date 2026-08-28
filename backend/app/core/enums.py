"""Shared domain enums."""

import enum


class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    USER = "USER"


class RegistrationStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    SUSPENDED = "SUSPENDED"
    UNKNOWN = "UNKNOWN"


class ProjectStatus(str, enum.Enum):
    COMPLETED = "COMPLETED"
    ONGOING = "ONGOING"
    CANCELLED = "CANCELLED"
    UNKNOWN = "UNKNOWN"


class OwnershipType(str, enum.Enum):
    OWNED = "OWNED"
    LEASED = "LEASED"
    RENTED = "RENTED"
    OTHER = "OTHER"


class DocumentEntityType(str, enum.Enum):
    COMPANY = "COMPANY"
    REGISTRATION = "REGISTRATION"
    CONTRACTOR_REGISTRATION = "CONTRACTOR_REGISTRATION"
    FINANCIAL_RECORD = "FINANCIAL_RECORD"
    EXPERIENCE = "EXPERIENCE"
    MACHINERY = "MACHINERY"
    PERSONNEL = "PERSONNEL"
    OTHER = "OTHER"


class DocumentStatus(str, enum.Enum):
    VALID = "VALID"
    EXPIRING_SOON = "EXPIRING_SOON"
    EXPIRED = "EXPIRED"
    UNKNOWN = "UNKNOWN"


class FinancialRecordType(str, enum.Enum):
    TURNOVER = "TURNOVER"
    SOLVENCY = "SOLVENCY"
    NET_WORTH = "NET_WORTH"
    FINANCIAL_CAPACITY = "FINANCIAL_CAPACITY"
    OTHER = "OTHER"


class TenderSourceType(str, enum.Enum):
    GOVERNMENT_PORTAL = "GOVERNMENT_PORTAL"
    API = "API"
    PUBLIC_DATA = "PUBLIC_DATA"
    OTHER = "OTHER"


class CollectionMethod(str, enum.Enum):
    HTTP = "HTTP"
    API = "API"
    HTML = "HTML"
    DOCUMENT = "DOCUMENT"
    OTHER = "OTHER"


class CollectionJobStatus(str, enum.Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class SourceHealthStatus(str, enum.Enum):
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    FAILED = "FAILED"
    UNKNOWN = "UNKNOWN"


class CollectionEventLevel(str, enum.Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class CollectionErrorType(str, enum.Enum):
    NETWORK = "NETWORK"
    TIMEOUT = "TIMEOUT"
    HTTP = "HTTP"
    PARSING = "PARSING"
    VALIDATION = "VALIDATION"
    SOURCE_UNAVAILABLE = "SOURCE_UNAVAILABLE"
    UNEXPECTED = "UNEXPECTED"


class TenderStatus(str, enum.Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"
    AWARDED = "AWARDED"
    UNKNOWN = "UNKNOWN"


class IndianStateCode(str, enum.Enum):
    UTTAR_PRADESH = "UTTAR_PRADESH"
    MADHYA_PRADESH = "MADHYA_PRADESH"
    UNKNOWN = "UNKNOWN"


class NormalizationStatus(str, enum.Enum):
    NOT_PROCESSED = "NOT_PROCESSED"
    NORMALIZED = "NORMALIZED"
    FAILED = "FAILED"
    NEEDS_REVIEW = "NEEDS_REVIEW"


class DuplicateMatchType(str, enum.Enum):
    EXACT_DUPLICATE = "EXACT_DUPLICATE"
    LIKELY_DUPLICATE = "LIKELY_DUPLICATE"
    POSSIBLE_DUPLICATE = "POSSIBLE_DUPLICATE"
    NOT_DUPLICATE = "NOT_DUPLICATE"


class DuplicateReviewStatus(str, enum.Enum):
    PENDING = "PENDING"
    CONFIRMED_DUPLICATE = "CONFIRMED_DUPLICATE"
    NOT_DUPLICATE = "NOT_DUPLICATE"
    IGNORED = "IGNORED"
