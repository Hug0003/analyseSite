"""
Security Analysis Service
Analyzes HTTP headers, SSL/TLS, and exposed files
"""
import httpx
import ssl
import socket
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List, Tuple
from urllib.parse import urlparse
from OpenSSL import crypto
from ..config import get_settings
from ..models import (
    SecurityResult, SecurityHeader, SSLInfo, ExposedFile,
    SeverityLevel
)


class SecurityAnalyzer:
    """Analyzes website security through passive scanning"""
    
    # Security headers to check with their recommendations
    SECURITY_HEADERS = {
        "Strict-Transport-Security": {
            "description": "HTTP Strict Transport Security (HSTS) forces browsers to use HTTPS",
            "severity_missing": SeverityLevel.HIGH,
            "recommendation": "Add 'Strict-Transport-Security: max-age=31536000; includeSubDomains; preload'"
        },
        "Content-Security-Policy": {
            "description": "CSP prevents XSS attacks by controlling resource loading",
            "severity_missing": SeverityLevel.HIGH,
            "recommendation": "Implement a Content-Security-Policy header appropriate for your site"
        },
        "X-Frame-Options": {
            "description": "Prevents clickjacking by controlling iframe embedding",
            "severity_missing": SeverityLevel.MEDIUM,
            "recommendation": "Add 'X-Frame-Options: DENY' or 'SAMEORIGIN'"
        },
        "X-Content-Type-Options": {
            "description": "Prevents MIME-type sniffing attacks",
            "severity_missing": SeverityLevel.MEDIUM,
            "recommendation": "Add 'X-Content-Type-Options: nosniff'"
        },
        "X-XSS-Protection": {
            "description": "Legacy XSS filter (deprecated but still useful)",
            "severity_missing": SeverityLevel.LOW,
            "recommendation": "Add 'X-XSS-Protection: 1; mode=block'"
        },
        "Referrer-Policy": {
            "description": "Controls referrer information sent with requests",
            "severity_missing": SeverityLevel.LOW,
            "recommendation": "Add 'Referrer-Policy: strict-origin-when-cross-origin'"
        },
        "Permissions-Policy": {
            "description": "Controls browser features and APIs",
            "severity_missing": SeverityLevel.LOW,
            "recommendation": "Add appropriate Permissions-Policy to limit browser features"
        },
        "X-Permitted-Cross-Domain-Policies": {
            "description": "Controls cross-domain policies for Flash/PDF",
            "severity_missing": SeverityLevel.INFO,
            "recommendation": "Add 'X-Permitted-Cross-Domain-Policies: none'"
        }
    }
    
    # Sensitive files to check
    SENSITIVE_FILES = [
        {
            "path": "/robots.txt",
            "severity": SeverityLevel.INFO,
            "description": "Robots.txt is publicly accessible (normal, but review contents)"
        },
        {
            "path": "/sitemap.xml",
            "severity": SeverityLevel.INFO,
            "description": "Sitemap is publicly accessible (normal for SEO)"
        },
        {
            "path": "/.git/config",
            "severity": SeverityLevel.CRITICAL,
            "description": "Git repository exposed! Attackers can download source code"
        },
        {
            "path": "/.git/HEAD",
            "severity": SeverityLevel.CRITICAL,
            "description": "Git repository exposed! Attackers can download source code"
        },
        {
            "path": "/.env",
            "severity": SeverityLevel.CRITICAL,
            "description": "Environment file exposed! May contain secrets and credentials"
        },
        {
            "path": "/.htaccess",
            "severity": SeverityLevel.HIGH,
            "description": "Apache configuration file exposed"
        },
        {
            "path": "/wp-config.php",
            "severity": SeverityLevel.CRITICAL,
            "description": "WordPress configuration file exposed (may contain DB credentials)"
        },
        {
            "path": "/config.php",
            "severity": SeverityLevel.HIGH,
            "description": "Configuration file potentially exposed"
        },
        {
            "path": "/phpinfo.php",
            "severity": SeverityLevel.HIGH,
            "description": "PHP info page exposed (reveals server configuration)"
        },
        {
            "path": "/server-status",
            "severity": SeverityLevel.MEDIUM,
            "description": "Apache server status page exposed"
        },
        {
            "path": "/.svn/entries",
            "severity": SeverityLevel.CRITICAL,
            "description": "SVN repository exposed"
        },
        {
            "path": "/backup.sql",
            "severity": SeverityLevel.CRITICAL,
            "description": "SQL backup file exposed"
        },
        {
            "path": "/database.sql",
            "severity": SeverityLevel.CRITICAL,
            "description": "SQL database file exposed"
        },
        {
            "path": "/.DS_Store",
            "severity": SeverityLevel.LOW,
            "description": "macOS file system metadata exposed"
        },
        {
            "path": "/web.config",
            "severity": SeverityLevel.HIGH,
            "description": "IIS configuration file potentially exposed"
        }
    ]
    
    def __init__(self):
        self.settings = get_settings()
    
    async def analyze(self, url: str) -> SecurityResult:
        """
        Run security analysis on the given URL
        
        Args:
            url: The URL to analyze
            
        Returns:
            SecurityResult with headers, SSL, and exposed files analysis
        """
        result = SecurityResult()
        
        try:
            parsed = urlparse(url)
            base_url = f"{parsed.scheme}://{parsed.netloc}"
            
            # Run all checks
            result.headers = await self._check_headers(url)
            result.ssl = await self._check_ssl(parsed.netloc)
            result.exposed_files = await self._check_exposed_files(base_url)
            
            # Calculate security score
            result.score = self._calculate_score(result)
            
        except Exception as e:
            result.error = f"Security analysis error: {str(e)}"
        
        return result
    
    async def _check_headers(self, url: str) -> List[SecurityHeader]:
        """Check security headers"""
        headers_result = []
        
        try:
            async with httpx.AsyncClient(
                timeout=self.settings.request_timeout,
                follow_redirects=True,
                verify=False  # We'll check SSL separately
            ) as client:
                response = await client.head(url)
                response_headers = dict(response.headers)
                
                # Also try GET if HEAD doesn't return headers
                if not response_headers:
                    response = await client.get(url)
                    response_headers = dict(response.headers)
                
                # Check each security header
                for header_name, header_info in self.SECURITY_HEADERS.items():
                    header_value = None
                    present = False
                    
                    # Case-insensitive header lookup
                    for key, value in response_headers.items():
                        if key.lower() == header_name.lower():
                            header_value = value
                            present = True
                            break
                    
                    severity = SeverityLevel.OK if present else header_info["severity_missing"]
                    
                    headers_result.append(SecurityHeader(
                        name=header_name,
                        value=header_value,
                        present=present,
                        severity=severity,
                        description=header_info["description"],
                        recommendation=None if present else header_info["recommendation"]
                    ))
                
                # Check for information disclosure headers
                info_disclosure_headers = ["Server", "X-Powered-By", "X-AspNet-Version"]
                for header_name in info_disclosure_headers:
                    for key, value in response_headers.items():
                        if key.lower() == header_name.lower():
                            headers_result.append(SecurityHeader(
                                name=header_name,
                                value=value,
                                present=True,
                                severity=SeverityLevel.LOW,
                                description=f"Information disclosure: {header_name} header reveals server info",
                                recommendation=f"Consider removing or obscuring the {header_name} header"
                            ))
                            break
                
        except httpx.TimeoutException:
            pass  # Headers check failed, but we continue
        except Exception as e:
            pass  # Log error but continue
        
        return headers_result
    
    async def _check_ssl(self, hostname: str) -> SSLInfo:
        """Check SSL/TLS certificate"""
        ssl_info = SSLInfo()
        
        # Remove port if present
        if ":" in hostname:
            hostname = hostname.split(":")[0]
            
        try:
            # 1. Try Strict Verification first
            await self._fetch_cert_details(hostname, ssl_info, verify=True)
            ssl_info.valid = True
            
        except ssl.SSLCertVerificationError as e:
            # 2. Verification failed, but we still want the details
            ssl_info.valid = False
            ssl_info.error = f"Certificate verification failed: {str(e)}"
            
            try:
                # Retry without verification to get cert details
                await self._fetch_cert_details(hostname, ssl_info, verify=False)
            except Exception as e2:
                # If even this fails, just keep the original error
                pass
                
        except socket.timeout:
            ssl_info.error = "SSL connection timed out"
        except socket.gaierror:
            ssl_info.error = "Could not resolve hostname"
        except ConnectionRefusedError:
            ssl_info.error = "Connection refused on port 443"
        except Exception as e:
            ssl_info.error = f"SSL check error: {str(e)}"
        
        return ssl_info

    async def _fetch_cert_details(self, hostname: str, ssl_info: SSLInfo, verify: bool = True):
        """Helper to fetch and parse certificate details"""
        # Create SSL context
        context = ssl.create_default_context()
        if not verify:
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
        
        # Connect and get certificate
        # Note: We use synchronous socket here because SSL handshake is blocking
        # Ideally this should be in a thread, but it's fast enough for now
        with socket.create_connection((hostname, 443), timeout=self.settings.ssl_timeout) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                # Get certificate in binary DER format
                # When verify=False, getpeercert() returns empty dict unless binary_form=True
                cert_der = ssock.getpeercert(binary_form=True)
                if not cert_der:
                    raise ValueError("No certificate retrieved")
                    
                cert = crypto.load_certificate(crypto.FILETYPE_ASN1, cert_der)
                
                # Get cipher info
                cipher = ssock.cipher()
                ssl_info.cipher_suite = cipher[0] if cipher else None
                ssl_info.protocol_version = ssock.version()
                
                # Parse certificate
                ssl_info.issuer = self._format_x509_name(cert.get_issuer())
                ssl_info.subject = self._format_x509_name(cert.get_subject())
                
                # Parse expiration date
                not_after = cert.get_notAfter()
                if not_after:
                    expiry_str = not_after.decode("utf-8")
                    try:
                        ssl_info.expires_at = datetime.strptime(expiry_str, "%Y%m%d%H%M%SZ").replace(tzinfo=timezone.utc)
                    except ValueError:
                         # Fallback for GeneralizedTime format if needed
                         ssl_info.expires_at = datetime.strptime(expiry_str, "%Y%m%d%H%M%Sz").replace(tzinfo=timezone.utc)

                    # Calculate days until expiry
                    now = datetime.now(timezone.utc)
                    delta = ssl_info.expires_at - now
                    ssl_info.days_until_expiry = delta.days
                    
                    # Check expiration status
                    ssl_info.is_expired = ssl_info.days_until_expiry < 0
                    ssl_info.is_expiring_soon = 0 <= ssl_info.days_until_expiry <= 30
    
    def _format_x509_name(self, x509_name) -> str:
        """Format X509Name object to string"""
        components = x509_name.get_components()
        return ", ".join(f"{k.decode()}={v.decode()}" for k, v in components)
    
    async def _check_exposed_files(self, base_url: str) -> List[ExposedFile]:
        """Check for exposed sensitive files"""
        exposed = []
        
        async with httpx.AsyncClient(
            timeout=10.0,
            follow_redirects=False,
            verify=False
        ) as client:
            for file_info in self.SENSITIVE_FILES:
                try:
                    url = f"{base_url}{file_info['path']}"
                    response = await client.head(url)
                    
                    # Check if file is accessible
                    accessible = response.status_code == 200
                    
                    # For critical files, also verify content
                    if accessible and file_info["severity"] == SeverityLevel.CRITICAL:
                        # Double-check with GET request
                        get_response = await client.get(url)
                        # Verify it's not a custom 404 page
                        if get_response.status_code != 200 or len(get_response.text) < 10:
                            accessible = False
                    
                    exposed.append(ExposedFile(
                        path=file_info["path"],
                        accessible=accessible,
                        severity=file_info["severity"] if accessible else SeverityLevel.OK,
                        description=file_info["description"] if accessible else None
                    ))
                    
                except Exception:
                    # File not accessible (which is good for sensitive files)
                    exposed.append(ExposedFile(
                        path=file_info["path"],
                        accessible=False,
                        severity=SeverityLevel.OK
                    ))
        
        return exposed
    
    def _calculate_score(self, result: SecurityResult) -> int:
        """Calculate security score based on findings"""
        score = 100
        
        # Deduct points for missing headers
        header_deductions = {
            SeverityLevel.CRITICAL: 15,
            SeverityLevel.HIGH: 10,
            SeverityLevel.MEDIUM: 5,
            SeverityLevel.LOW: 2,
            SeverityLevel.INFO: 0
        }
        
        for header in result.headers:
            if not header.present and header.severity in header_deductions:
                score -= header_deductions[header.severity]
        
        # Deduct points for SSL issues
        if result.ssl.error:
            score -= 20
        elif not result.ssl.valid:
            score -= 25
        elif result.ssl.is_expired:
            score -= 30
        elif result.ssl.is_expiring_soon:
            score -= 10
        
        # Deduct points for exposed files
        for file in result.exposed_files:
            if file.accessible:
                if file.severity == SeverityLevel.CRITICAL:
                    score -= 25
                elif file.severity == SeverityLevel.HIGH:
                    score -= 15
                elif file.severity == SeverityLevel.MEDIUM:
                    score -= 5
        
        return max(0, min(100, score))
