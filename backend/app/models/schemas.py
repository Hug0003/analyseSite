"""
Pydantic schemas for request/response validation
"""
from pydantic import BaseModel, HttpUrl, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# ============================================
# Enums
# ============================================

class AuditStatus(str, Enum):
    """Status of an audit task"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class SeverityLevel(str, Enum):
    """Severity level for security issues"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"
    OK = "ok"

class TaskResponse(BaseModel):
    """Response when a background task is created"""
    task_id: str
    status: str = "pending"
    url: str

# ============================================
# Request Models
# ============================================

class AnalyzeRequest(BaseModel):
    """Request model for URL analysis"""
    url: str = Field(..., description="URL to analyze", examples=["https://example.com"])
    competitor_url: Optional[str] = Field(None, description="Competitor URL to compare against", examples=["https://competitor.com"])
    lang: str = Field("en", description="Language for analysis results (en, fr)", examples=["en", "fr"])
    
    @field_validator("url", "competitor_url")
    @classmethod
    def validate_url(cls, v: str) -> Optional[str]:
        """Ensure URL has proper scheme"""
        if v is None:
            return None
        v = v.strip()
        if not v.startswith(("http://", "https://")):
            v = f"https://{v}"
        return v


# ============================================
# SEO & Performance Models
# ============================================

class CoreWebVitals(BaseModel):
    """Core Web Vitals metrics from Lighthouse"""
    lcp: Optional[float] = Field(None, description="Largest Contentful Paint (seconds)")
    lcp_score: Optional[str] = Field(None, description="LCP rating: good/needs-improvement/poor")
    fid: Optional[float] = Field(None, description="First Input Delay (milliseconds)")  
    fid_score: Optional[str] = Field(None, description="FID rating")
    cls: Optional[float] = Field(None, description="Cumulative Layout Shift")
    cls_score: Optional[str] = Field(None, description="CLS rating")
    fcp: Optional[float] = Field(None, description="First Contentful Paint (seconds)")
    ttfb: Optional[float] = Field(None, description="Time to First Byte (milliseconds)")
    inp: Optional[float] = Field(None, description="Interaction to Next Paint (milliseconds)")


class LighthouseScores(BaseModel):
    """Lighthouse category scores"""
    performance: Optional[int] = Field(None, ge=0, le=100)
    seo: Optional[int] = Field(None, ge=0, le=100)
    accessibility: Optional[int] = Field(None, ge=0, le=100)
    best_practices: Optional[int] = Field(None, ge=0, le=100)


class SEOResult(BaseModel):
    """SEO and Performance analysis results"""
    scores: LighthouseScores = Field(default_factory=LighthouseScores)
    core_web_vitals: CoreWebVitals = Field(default_factory=CoreWebVitals)
    audits: List[Dict[str, Any]] = Field(default_factory=list, description="Detailed audit items")
    opportunities: List[Dict[str, Any]] = Field(default_factory=list, description="Performance opportunities")
    diagnostics: List[Dict[str, Any]] = Field(default_factory=list, description="Diagnostic information")
    error: Optional[str] = None


# ============================================
# Security Models
# ============================================

class SecurityHeader(BaseModel):
    """Security header analysis"""
    name: str
    value: Optional[str] = None
    present: bool = False
    severity: SeverityLevel = SeverityLevel.INFO
    recommendation: Optional[str] = None
    description: Optional[str] = None


class SSLInfo(BaseModel):
    """SSL/TLS certificate information"""
    valid: bool = False
    issuer: Optional[str] = None
    subject: Optional[str] = None
    expires_at: Optional[datetime] = None
    days_until_expiry: Optional[int] = None
    protocol_version: Optional[str] = None
    cipher_suite: Optional[str] = None
    is_expired: bool = False
    is_expiring_soon: bool = Field(False, description="Expires within 30 days")
    error: Optional[str] = None


class ExposedFile(BaseModel):
    """Exposed sensitive file detection"""
    path: str
    accessible: bool = False
    severity: SeverityLevel = SeverityLevel.INFO
    description: Optional[str] = None


class SecurityResult(BaseModel):
    """Security analysis results"""
    score: int = Field(0, ge=0, le=100)
    headers: List[SecurityHeader] = Field(default_factory=list)
    ssl: SSLInfo = Field(default_factory=SSLInfo)
    exposed_files: List[ExposedFile] = Field(default_factory=list)
    vulnerabilities: List[Dict[str, Any]] = Field(default_factory=list)
    error: Optional[str] = None


# ============================================
# Technology Stack Models
# ============================================

class Technology(BaseModel):
    """Detected technology information"""
    name: str
    categories: List[str] = Field(default_factory=list)
    version: Optional[str] = None
    latest_version: Optional[str] = None
    is_outdated: bool = False
    confidence: int = Field(100, ge=0, le=100)
    icon: Optional[str] = None
    website: Optional[str] = None
    severity: SeverityLevel = SeverityLevel.OK


class CompanyInfo(BaseModel):
    """Company information from Wappalyzer"""
    name: Optional[str] = None
    description: Optional[str] = None
    industry: Optional[str] = None
    size: Optional[str] = None
    founded: Optional[int] = None
    location: Optional[str] = None


class ContactInfo(BaseModel):
    """Contact information from Wappalyzer"""
    emails: List[str] = Field(default_factory=list)
    phones: List[str] = Field(default_factory=list)
    twitter: List[str] = Field(default_factory=list)
    linkedin: List[str] = Field(default_factory=list)
    facebook: List[str] = Field(default_factory=list)


class TechStackResult(BaseModel):
    """Technology stack detection results"""
    # Source of data: 'local' or 'api'
    source: str = "local"
    
    technologies: List[Technology] = Field(default_factory=list)
    
    # Enriched data
    company: Optional[CompanyInfo] = Field(default_factory=CompanyInfo)
    contacts: Optional[ContactInfo] = Field(default_factory=ContactInfo)
    
    cms: Optional[str] = None

    framework: Optional[str] = None
    server: Optional[str] = None
    programming_language: Optional[str] = None
    cdn: Optional[str] = None
    analytics: List[str] = Field(default_factory=list)
    outdated_count: int = 0
    error: Optional[str] = None


# ============================================
# Broken Links Models
# ============================================

class BrokenLink(BaseModel):
    """Broken link information"""
    url: str
    status_code: int
    source_text: Optional[str] = None
    is_internal: bool = True
    error_type: str = Field("http_error", description="http_error, timeout, connection_error")


class BrokenLinksResult(BaseModel):
    """Broken links analysis results"""
    total_links_checked: int = 0
    broken_links: List[BrokenLink] = Field(default_factory=list)
    broken_count: int = 0
    internal_broken: int = 0
    external_broken: int = 0
    error: Optional[str] = None


# ============================================
# GDPR & Compliance Models
# ============================================

class CookieItem(BaseModel):
    """Cookie detected during analysis"""
    name: str
    domain: str
    secure: bool
    http_only: bool
    path: str
    expires: Optional[float] = None
    is_session: bool
    same_site: Optional[str] = None
    
    # Analysis
    is_compliant: bool = True
    category: str = "Unknown"  # Essential, Marketing, Analytics, etc.
    risk_level: SeverityLevel = SeverityLevel.INFO


class GDPRResult(BaseModel):
    """GDPR compliance analysis results"""
    compliant: bool = True
    cookies: List[CookieItem] = Field(default_factory=list)
    violation_count: int = 0
    cmp_detected: Optional[str] = None
    privacy_policy_detected: bool = False
    privacy_policy_url: Optional[str] = None
    score: int = Field(100, ge=0, le=100)
    error: Optional[str] = None



# ============================================
# Social Media Optimization (SMO) Models
# ============================================

class SMOResult(BaseModel):
    """Social Media Optimization analysis results"""
    title: Optional[str] = None
    description: Optional[str] = None
    image: Optional[str] = None
    url: Optional[str] = None
    site_name: Optional[str] = None
    twitter_card: Optional[str] = None
    twitter_title: Optional[str] = None
    twitter_description: Optional[str] = None
    twitter_image: Optional[str] = None
    
    # Analysis
    image_status: str = "missing" # valid, broken, missing
    missing_tags: List[str] = Field(default_factory=list)
    score: int = Field(0, ge=0, le=100)
    error: Optional[str] = None


# ============================================
# Green IT Models
# ============================================

class GreenResult(BaseModel):
    """Green IT / Carbon Footprint analysis results"""
    co2_grams: float = 0.0
    grade: str = "Unknown" # A-G
    total_size_mb: float = 0.0
    resource_count: int = 0
    score: int = Field(0, ge=0, le=100) # 0-100 metric based on grade
    error: Optional[str] = None


# ============================================
# DNS & Email Health Models
# ============================================

class SPFInfo(BaseModel):
    present: bool = False
    record: Optional[str] = None
    status: str = "missing" # valid, warning, critical, missing
    warnings: List[str] = Field(default_factory=list)

class DMARCInfo(BaseModel):
    present: bool = False
    record: Optional[str] = None
    policy: Optional[str] = None # none, quarantine, reject
    status: str = "missing"

class DKIMInfo(BaseModel):
    present: bool = False
    selectors_checked: List[str] = Field(default_factory=list)
    selectors_found: List[str] = Field(default_factory=list)
    status: str = "manual_check" # found, missing, manual_check
    note: str = "DKIM uses cryptic selectors (e.g. google._domainkey). We checked common ones but a manual check is recommended."

class DNSHealthResult(BaseModel):
    spf: SPFInfo = Field(default_factory=SPFInfo)
    dmarc: DMARCInfo = Field(default_factory=DMARCInfo)
    dkim: DKIMInfo = Field(default_factory=DKIMInfo)
    domain: Optional[str] = None
    server_ip: Optional[str] = None
    score: int = Field(0, ge=0, le=100)
    error: Optional[str] = None


# ============================================
# Main Response Model
# ============================================

class AnalyzeResponse(BaseModel):
    """Complete analysis response"""
    url: str
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)
    status: AuditStatus = AuditStatus.COMPLETED
    
    # Global score (weighted average)
    global_score: int = Field(0, ge=0, le=100)
    
    # Individual module results
    seo: SEOResult = Field(default_factory=SEOResult)
    security: SecurityResult = Field(default_factory=SecurityResult)
    tech_stack: TechStackResult = Field(default_factory=TechStackResult)
    broken_links: BrokenLinksResult = Field(default_factory=BrokenLinksResult)
    gdpr: GDPRResult = Field(default_factory=GDPRResult)
    smo: SMOResult = Field(default_factory=SMOResult)
    green_it: GreenResult = Field(default_factory=GreenResult)
    dns_health: DNSHealthResult = Field(default_factory=DNSHealthResult)
    competitor: Optional['AnalyzeResponse'] = None
    
    # Metadata
    scan_duration_seconds: Optional[float] = None
    errors: List[str] = Field(default_factory=list)
    
    def calculate_global_score(self) -> int:
        """
        Calculate weighted global score.
        
        Weights:
        - Performance (Google Lighthouse): 20%
        - SEO (Google Lighthouse): 20%
        - Securité (Headers/SSL): 20%
        - Accessibility (Google Lighthouse): 15%
        - Best Practices / Tech Stack: 10%
        - GDPR / Compliance: 15%
        
        Si une valeur est null, elle contribue 0 au score mais son poids
        est redistribué proportionnellement aux autres catégories.
        Le score final est toujours entre 0 et 100.
        """
        import logging
        logger = logging.getLogger(__name__)
        
        # Define weights for each category
        weight_config = {
            "performance": 0.20,
            "seo": 0.20,
            "security": 0.20,
            "accessibility": 0.15,
            "best_practices": 0.10,
            "gdpr": 0.15,
            "green_it": 0.10
        }
        
        # Collect available scores with their weights
        available_scores = []
        total_available_weight = 0.0
        
        # Performance score from Lighthouse
        if self.seo.scores.performance is not None:
            score_val = max(0, min(100, self.seo.scores.performance))  # Clamp 0-100
            available_scores.append({
                "name": "performance",
                "score": score_val,
                "weight": weight_config["performance"]
            })
            total_available_weight += weight_config["performance"]
            logger.info(f"   📊 Performance: {score_val}/100 (weight: {weight_config['performance']})")
        else:
            logger.warning(f"   ⚠️ Performance score is null")
        
        # SEO score from Lighthouse
        if self.seo.scores.seo is not None:
            score_val = max(0, min(100, self.seo.scores.seo))
            available_scores.append({
                "name": "seo",
                "score": score_val,
                "weight": weight_config["seo"]
            })
            total_available_weight += weight_config["seo"]
            logger.info(f"   📊 SEO: {score_val}/100 (weight: {weight_config['seo']})")
        else:
            logger.warning(f"   ⚠️ SEO score is null")
        
        # Security score (our own calculation)
        # Security score should always be present (default 0)
        security_score = max(0, min(100, self.security.score))
        available_scores.append({
            "name": "security",
            "score": security_score,
            "weight": weight_config["security"]
        })
        total_available_weight += weight_config["security"]
        logger.info(f"   📊 Security: {security_score}/100 (weight: {weight_config['security']})")
        
        # Accessibility score from Lighthouse
        if self.seo.scores.accessibility is not None:
            score_val = max(0, min(100, self.seo.scores.accessibility))
            available_scores.append({
                "name": "accessibility",
                "score": score_val,
                "weight": weight_config["accessibility"]
            })
            total_available_weight += weight_config["accessibility"]
            logger.info(f"   📊 Accessibility: {score_val}/100 (weight: {weight_config['accessibility']})")
        else:
            logger.warning(f"   ⚠️ Accessibility score is null")
        
        # Best Practices score from Lighthouse
        if self.seo.scores.best_practices is not None:
            score_val = max(0, min(100, self.seo.scores.best_practices))
            available_scores.append({
                "name": "best_practices",
                "score": score_val,
                "weight": weight_config["best_practices"]
            })
            total_available_weight += weight_config["best_practices"]
            logger.info(f"   📊 Best Practices: {score_val}/100 (weight: {weight_config['best_practices']})")
        else:
            logger.warning(f"   ⚠️ Best Practices score is null")

        # GDPR Score
        gdpr_score = max(0, min(100, self.gdpr.score))
        available_scores.append({
            "name": "gdpr",
            "score": gdpr_score,
            "weight": weight_config["gdpr"]
        })
        total_available_weight += weight_config["gdpr"]
        logger.info(f"   📊 GDPR: {gdpr_score}/100 (weight: {weight_config['gdpr']})")

        # Green IT Score
        green_score = max(0, min(100, self.green_it.score))
        available_scores.append({
            "name": "green_it",
            "score": green_score,
            "weight": weight_config["green_it"]
        })
        total_available_weight += weight_config["green_it"]
        logger.info(f"   📊 Green IT: {green_score}/100 (weight: {weight_config['green_it']})")
        
        # Calculate weighted average
        if total_available_weight > 0:
            # Normalize weights to sum to 1.0
            weighted_sum = 0.0
            for item in available_scores:
                normalized_weight = item["weight"] / total_available_weight
                weighted_sum += item["score"] * normalized_weight
            
            # Clamp final score between 0 and 100
            self.global_score = max(0, min(100, int(round(weighted_sum))))
            
            logger.info(f"   ✅ Global Score: {self.global_score}/100")
            logger.info(f"   📊 Based on {len(available_scores)} categories (total weight: {total_available_weight:.2f})")
        else:
            # No scores available, default to 0
            self.global_score = 0
            logger.warning(f"   ⚠️ No scores available, global score set to 0")
        
        return self.global_score

