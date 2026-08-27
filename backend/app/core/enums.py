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
