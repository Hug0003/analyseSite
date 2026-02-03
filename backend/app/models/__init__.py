"""
Pydantic models for SiteAuditor
"""
from .schemas import (
    AnalyzeRequest,
    AnalyzeResponse,
    SEOResult,
    SecurityResult,
    TechStackResult,
    BrokenLinksResult,
    CoreWebVitals,
    LighthouseScores,
    SecurityHeader,
    SSLInfo,
    Technology,
    BrokenLink,
    AuditStatus,
    SeverityLevel,
    ExposedFile,
    CompanyInfo,
    ContactInfo,
    GDPRResult,
    CookieItem,
    SMOResult,
    GreenResult,
    DNSHealthResult,
    AnalyzeResponse,
    TaskResponse
)
from .task import ScanTask

__all__ = [
    "AnalyzeRequest",
    "AnalyzeResponse",
    "TaskResponse",
    "SEOResult",
    "SecurityResult",
    "TechStackResult",
    "BrokenLinksResult",
    "CoreWebVitals",
    "LighthouseScores",
    "SecurityHeader",
    "SSLInfo",
    "Technology",
    "BrokenLink",
    "AuditStatus",
    "SeverityLevel",
    "ExposedFile",
    "CompanyInfo",
    "ContactInfo",
    "GDPRResult",
    "CookieItem",
    "SMOResult",
    "GreenResult",
    "DNSHealthResult"
]
