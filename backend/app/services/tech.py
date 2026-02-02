"""
Technology Stack Detection Service
Fingerprints technologies used by the website
"""
import httpx
import re
from typing import Optional, Dict, Any, List, Set
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from ..config import get_settings
from ..models import TechStackResult, Technology, CompanyInfo, ContactInfo, SeverityLevel


class TechStackAnalyzer:
    """Detects technologies used by a website"""
    
    # Technology signatures for detection
    TECH_SIGNATURES = {
        # CMS
        "WordPress": {
            "categories": ["CMS", "Blogs"],
            "icon": "WordPress.svg",
            "patterns": [
                {"type": "meta", "key": "generator", "pattern": r"WordPress ?([\d.]+)?", "confidence": 100},
                {"type": "html", "pattern": r"wp-content/themes/", "confidence": 100},
                {"type": "html", "pattern": r"wp-includes/", "confidence": 100},
                {"type": "cookie", "key": "wp-settings-", "confidence": 100}
            ],
            "website": "https://wordpress.org"
        },
        "Drupal": {
            "categories": ["CMS"],
            "icon": "Drupal.svg",
            "patterns": [
                {"type": "meta", "key": "generator", "pattern": r"Drupal ?([\d.]+)?", "confidence": 100},
                {"type": "headers", "key": "X-Generator", "pattern": r"Drupal ?([\d.]+)?", "confidence": 100},
                {"type": "html", "pattern": r"sites/all/themes/", "confidence": 80}
            ],
            "website": "https://drupal.org"
        },
        "Joomla": {
            "categories": ["CMS"],
            "icon": "Joomla.svg",
            "patterns": [
                {"type": "meta", "key": "generator", "pattern": r"Joomla!?", "confidence": 100},
                {"type": "headers", "key": "X-Content-Encoded-By", "pattern": r"Joomla!?", "confidence": 100}
            ],
            "website": "https://joomla.org"
        },
        "Shopify": {
            "categories": ["Ecommerce", "CMS"],
            "icon": "Shopify.svg",
            "patterns": [
                {"type": "html", "pattern": r"cdn\.shopify\.com", "confidence": 100},
                {"type": "html", "pattern": r"Shopify\.shop", "confidence": 100}
            ],
            "website": "https://shopify.com"
        },
        "Wix": {
            "categories": ["Website Builder", "CMS"],
            "icon": "Wix.svg",
            "patterns": [
                {"type": "html", "pattern": r"wix\.com", "confidence": 80},
                {"type": "meta", "key": "generator", "pattern": r"Wix\.com Website Builder", "confidence": 100}
            ],
            "website": "https://wix.com"
        },
        "Squarespace": {
            "categories": ["Website Builder", "CMS"],
            "icon": "Squarespace.svg",
            "patterns": [
                {"type": "html", "pattern": r"static\.squarespace\.com", "confidence": 100},
                {"type": "headers", "key": "X-Served-By", "pattern": r"Squarespace", "confidence": 100}
            ],
            "website": "https://squarespace.com"
        },

        # JavaScript Frameworks & Libraries
        "React": {
            "categories": ["JavaScript Framework"],
            "icon": "React.svg",
            "patterns": [
                {"type": "html", "pattern": r"react\.production\.min\.js", "confidence": 100},
                {"type": "html", "pattern": r"react-dom", "confidence": 80},
                {"type": "html", "pattern": r"data-reactroot", "confidence": 100}
            ],
            "website": "https://reactjs.org"
        },
        "Next.js": {
            "categories": ["JavaScript Framework", "Web Framework"],
            "icon": "Next.js.svg",
            "patterns": [
                {"type": "html", "pattern": r"/_next/static/", "confidence": 100},
                {"type": "headers", "key": "X-Powered-By", "pattern": r"Next\.js", "confidence": 100},
                {"type": "html", "pattern": r"__NEXT_DATA__", "confidence": 100}
            ],
            "website": "https://nextjs.org"
        },
        "Vue.js": {
            "categories": ["JavaScript Framework"],
            "icon": "Vue.js.svg",
            "patterns": [
                {"type": "html", "pattern": r"vue\.min\.js", "confidence": 100},
                {"type": "html", "pattern": r"data-v-[a-z0-9]+", "confidence": 80}
            ],
            "website": "https://vuejs.org"
        },
        "Nuxt.js": {
            "categories": ["JavaScript Framework", "Web Framework"],
            "icon": "Nuxt.js.svg",
            "patterns": [
                {"type": "html", "pattern": r"/_nuxt/", "confidence": 100},
                {"type": "html", "pattern": r"__NUXT__", "confidence": 100}
            ],
            "website": "https://nuxtjs.org"
        },
        "Angular": {
            "categories": ["JavaScript Framework"],
            "icon": "Angular.svg",
            "patterns": [
                {"type": "html", "pattern": r"angular\.js", "confidence": 100},
                {"type": "html", "pattern": r"ng-version=", "confidence": 100}
            ],
            "website": "https://angular.io"
        },
        "jQuery": {
            "categories": ["JavaScript Library"],
            "icon": "jQuery.svg",
            "patterns": [
                {"type": "html", "pattern": r"jquery[.-]?([\d.]+)?\.min\.js", "confidence": 100},
                {"type": "script_src", "pattern": r"jquery", "confidence": 80}
            ],
            "website": "https://jquery.com"
        },
        "Alpine.js": {
            "categories": ["JavaScript Framework"],
            "icon": "Alpine.js.svg",
            "patterns": [
                {"type": "html", "pattern": r"x-data=", "confidence": 80},
                {"type": "script_src", "pattern": r"alpine\.js", "confidence": 100}
            ]
        },

        # Web Servers
        "Nginx": {
            "categories": ["Web Server"],
            "icon": "Nginx.svg",
            "patterns": [
                {"type": "headers", "key": "Server", "pattern": r"nginx/?([\d.]+)?", "confidence": 100}
            ],
            "website": "https://nginx.org"
        },
        "Apache": {
            "categories": ["Web Server"],
            "icon": "Apache.svg",
            "patterns": [
                {"type": "headers", "key": "Server", "pattern": r"Apache/?([\d.]+)?", "confidence": 100}
            ],
            "website": "https://httpd.apache.org"
        },
        "IIS": {
            "categories": ["Web Server"],
            "icon": "IIS.svg",
            "patterns": [
                {"type": "headers", "key": "Server", "pattern": r"IIS/?([\d.]+)?", "confidence": 100}
            ],
            "website": "https://www.iis.net"
        },
        "Cloudflare": {
            "categories": ["CDN", "PaaS"],
            "icon": "Cloudflare.svg",
            "patterns": [
                {"type": "headers", "key": "Server", "pattern": r"cloudflare", "confidence": 100},
                {"type": "headers", "key": "CF-RAY", "pattern": r".+", "confidence": 100}
            ],
            "website": "https://cloudflare.com"
        },
        "Vercel": {
            "categories": ["PaaS", "CDN"],
            "icon": "Vercel.svg",
            "patterns": [
                {"type": "headers", "key": "Server", "pattern": r"Vercel", "confidence": 100},
                {"type": "headers", "key": "x-vercel-id", "pattern": r".+", "confidence": 100}
            ],
            "website": "https://vercel.com"
        },
        "Netlify": {
            "categories": ["PaaS", "CDN"],
            "icon": "Netlify.svg",
            "patterns": [
                {"type": "headers", "key": "Server", "pattern": r"Netlify", "confidence": 100}
            ],
            "website": "https://netlify.com"
        },

        # CSS Frameworks
        "Bootstrap": {
            "categories": ["CSS Framework"],
            "icon": "Bootstrap.svg",
            "patterns": [
                {"type": "html", "pattern": r"bootstrap[.-]?([\d.]+)?\.min\.css", "confidence": 100},
                {"type": "html", "pattern": r"class=\"[^\"]*\b(col-[a-z]{2}-\d+|btn-primary|navbar-expand)", "confidence": 70}
            ],
            "website": "https://getbootstrap.com"
        },
        "Tailwind CSS": {
            "categories": ["CSS Framework"],
            "icon": "Tailwind CSS.svg",
            "patterns": [
                {"type": "html", "pattern": r"tailwindcss", "confidence": 100},
                {"type": "html", "pattern": r"class=\"[^\"]*\b(p-[0-9]|m-[0-9]|bg-[a-z]+-[0-9]{3}|flex|grid)", "confidence": 40}
            ],
            "website": "https://tailwindcss.com"
        },

        # Analytics
        "Google Analytics": {
            "categories": ["Analytics"],
            "icon": "Google Analytics.svg",
            "patterns": [
                {"type": "html", "pattern": r"google-analytics\.com/analytics\.js", "confidence": 100},
                {"type": "html", "pattern": r"googletagmanager\.com/gtag/js", "confidence": 100},
                {"type": "html", "pattern": r"UA-\d{4,}-\d+", "confidence": 100}
            ],
            "website": "https://analytics.google.com"
        },
        "Google Tag Manager": {
            "category": "Tag Manager",
            "patterns": [
                {"type": "html", "pattern": r"googletagmanager\.com/gtm\.js", "confidence": 100},
                {"type": "html", "pattern": r"GTM-[A-Z0-9]+", "confidence": 100}
            ],
            "website": "https://tagmanager.google.com"
        },
        "Hotjar": {
            "category": "Analytics",
            "patterns": [
                {"type": "html", "pattern": r"static\.hotjar\.com", "confidence": 100}
            ],
            "website": "https://hotjar.com"
        },
        
        # Programming Languages
        "PHP": {
            "category": "Programming Language",
            "patterns": [
                {"type": "header", "name": "x-powered-by", "pattern": r"PHP/?(\d+\.[\d.]+)?", "confidence": 100},
                {"type": "html", "pattern": r"\.php", "confidence": 60}
            ],
            "website": "https://php.net"
        },
        "ASP.NET": {
            "category": "Programming Language",
            "patterns": [
                {"type": "header", "name": "x-powered-by", "pattern": r"ASP\.NET", "confidence": 100},
                {"type": "header", "name": "x-aspnet-version", "pattern": r".*", "confidence": 100}
            ],
            "website": "https://dotnet.microsoft.com"
        },
        "Python": {
            "category": "Programming Language",
            "patterns": [
                {"type": "header", "name": "server", "pattern": r"(gunicorn|uvicorn|waitress)", "confidence": 80}
            ],
            "website": "https://python.org"
        }
    }
    
    # Mock latest versions database (in production, use a real API or database)
    LATEST_VERSIONS = {
        "WordPress": "6.4.2",
        "jQuery": "3.7.1",
        "Bootstrap": "5.3.2",
        "React": "18.2.0",
        "Vue.js": "3.4.5",
        "Angular": "17.0.8",
        "Next.js": "14.0.4",
        "Nuxt.js": "3.9.0",
        "PHP": "8.3.1",
        "nginx": "1.25.3",
        "Apache": "2.4.58"
    }
    
    def __init__(self):
        self.settings = get_settings()
    
    async def analyze(self, url: str, html_content: Optional[str] = None, headers: Optional[Dict] = None) -> TechStackResult:
        """
        Detect technologies used by the website
        
        Args:
            url: The URL to analyze
            html_content: Optional pre-rendered HTML (Deep Scan)
            headers: Optional HTTP headers
            
        Returns:
            TechStackResult with detected technologies
        """
        result = TechStackResult()
        
        try:
            # 1. Try Wappalyzer API if configured
            if self.settings.wappalyzer_api_key:
                try:
                    api_result = await self._analyze_via_api(url)
                    return api_result
                except Exception as e:
                    print(f"Advertissement: Wappalyzer API failed ({str(e)}), falling back to local detection.")
                    # Fallback to local
                    pass

            # 2. Local Detection (Fallback)
            target_html = ""
            target_headers = {}

            if html_content:
                target_html = html_content
                target_headers = headers or {}
            else:
                async with httpx.AsyncClient(
                    timeout=self.settings.request_timeout,
                    follow_redirects=True,
                    verify=False,
                    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
                ) as client:
                    response = await client.get(url)
                    target_html = response.text
                    target_headers = dict(response.headers)
            
            # Parse HTML
            soup = BeautifulSoup(target_html, "lxml")
            
            # Detect technologies
            detected_techs = await self._detect_technologies(target_html, target_headers, soup)
            result.technologies = detected_techs
                
            # Categorize
            result = self._categorize_technologies(result)
            
            # Check for outdated versions
            result = self._check_outdated(result)
                
        except httpx.TimeoutException:
            result.error = "Request timed out while fetching page"
        except Exception as e:
            result.error = f"Technology detection error: {str(e)}"
        
        return result

    async def _analyze_via_api(self, url: str) -> TechStackResult:
        """Query Wappalyzer API for comprehensive stack data"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                "https://api.wappalyzer.com/v2/lookup/",
                params={"urls": url, "sets": "all"},
                headers={"x-api-key": self.settings.wappalyzer_api_key}
            )
            
            if response.status_code != 200:
                raise Exception(f"Status {response.status_code}")
            
            data_list = response.json()
            # API returns list of results
            data = data_list[0] if isinstance(data_list, list) else data_list
            
            result = TechStackResult(source="api")
            
            # Map Technologies
            for tech in data.get("technologies", []):
                # Map categories
                categories = [cat["name"] for cat in tech.get("categories", [])]
                
                # Version
                versions = tech.get("versions", [])
                version = versions[0] if versions else None
                
                t = Technology(
                    name=tech.get("name"),
                    categories=categories,
                    version=version,
                    confidence=tech.get("confidence", 100),
                    website=tech.get("website", ""), 
                    icon=f"{tech.get('name')}.svg" # Best guess
                )
                result.technologies.append(t)
            
            # Company Info
            result.company = CompanyInfo(
                name=data.get("companyName"),
                description=data.get("about"),
                industry=data.get("industry"),
                size=data.get("companySize"),
                founded=data.get("companyFounded"),
                location=data.get("locations", [None])[0] if data.get("locations") else None
            )
            
            # Contact Info
            result.contacts = ContactInfo(
                emails=data.get("email", []),
                phones=data.get("phone", []),
                twitter=data.get("twitter", []),
                linkedin=data.get("linkedin", []),
                facebook=data.get("facebook", [])
            )
            
            # Run categorization and outdated check logic on API results too
            result = self._categorize_technologies(result)
            result = self._check_outdated(result)
            
            return result
    
    async def _detect_technologies(
        self, 
        html: str, 
        headers: Dict[str, str], 
        soup: BeautifulSoup
    ) -> List[Technology]:
        """Detect technologies from HTML, headers, and meta tags"""
        detected: Dict[str, Technology] = {}
        
        for tech_name, tech_info in self.TECH_SIGNATURES.items():
            max_confidence = 0
            detected_version = None
            
            for pattern_def in tech_info["patterns"]:
                confidence = 0
                version = None
                
                if pattern_def["type"] == "html":
                    match = re.search(pattern_def["pattern"], html, re.IGNORECASE)
                    if match:
                        confidence = pattern_def["confidence"]
                        if match.groups():
                            version = match.group(1)
                
                elif pattern_def["type"] in ["header", "headers"]:
                    target_key = pattern_def.get("key") or pattern_def.get("name")
                    if target_key:
                        header_name = target_key.lower()
                        for key, value in headers.items():
                            if key.lower() == header_name:
                                match = re.search(pattern_def["pattern"], value, re.IGNORECASE)
                                if match:
                                    confidence = pattern_def["confidence"]
                                    if match.groups():
                                        version = match.group(1)
                                break
                
                elif pattern_def["type"] == "meta":
                    target_key = pattern_def.get("key") or pattern_def.get("name")
                    if target_key:
                        # Check 'name' and 'property' attributes
                        meta_tags = soup.find_all("meta", attrs={"name": target_key}) + \
                                    soup.find_all("meta", attrs={"property": target_key})
                        for meta in meta_tags:
                            content = meta.get("content", "")
                            match = re.search(pattern_def["pattern"], content, re.IGNORECASE)
                            if match:
                                confidence = pattern_def["confidence"]
                                if match.groups():
                                    version = match.group(1)
                                break

                elif pattern_def["type"] == "cookie":
                    target_key = pattern_def.get("key") or pattern_def.get("name")
                    if target_key:
                        # Simple check in Set-Cookie header or generic headers for now
                        # Ideally, parse cookies properly. But grepping headers works for simple existence.
                        cookie_header = headers.get("set-cookie", "") + headers.get("cookie", "")
                        if target_key in cookie_header:
                             confidence = pattern_def["confidence"]
                
                if confidence > max_confidence:
                    max_confidence = confidence
                    if version:
                        detected_version = version
            
            if max_confidence >= 50:  # Threshold for detection
                # Support both new 'categories' list and legacy 'category' string
                categories = tech_info.get("categories", [])
                if not categories and "category" in tech_info:
                    categories = [tech_info["category"]]
                
                # Default icon if not specified
                icon = tech_info.get("icon", f"{tech_name}.svg")

                detected[tech_name] = Technology(
                    name=tech_name,
                    categories=categories,
                    version=detected_version,
                    confidence=max_confidence,
                    website=tech_info.get("website"),
                    icon=icon
                )
        
        return list(detected.values())
    
    def _categorize_technologies(self, result: TechStackResult) -> TechStackResult:
        """Categorize detected technologies"""
        analytics = []
        
        for tech in result.technologies:
            categories = tech.categories
            
            if "CMS" in categories:
                result.cms = tech.name
            
            if "JavaScript Framework" in categories or "CSS Framework" in categories:
                # Prioritize JS framework over CSS framework for the single 'framework' field
                if "JavaScript Framework" in categories or not result.framework:
                    result.framework = tech.name
            
            if "Web Server" in categories:
                result.server = tech.name
            
            if "Programming Language" in categories:
                result.programming_language = tech.name
            
            if "CDN" in categories:
                result.cdn = tech.name
            
            if "Analytics" in categories or "Tag Manager" in categories:
                result.analytics.append(tech.name)
        
        result.analytics = list(set(result.analytics))  # Deduplicate
        
        return result
    
    def _check_outdated(self, result: TechStackResult) -> TechStackResult:
        """Check if detected versions are outdated"""
        outdated_count = 0
        
        for tech in result.technologies:
            if tech.name in self.LATEST_VERSIONS:
                tech.latest_version = self.LATEST_VERSIONS[tech.name]
                
                if tech.version:
                    # Simple version comparison (in production, use proper semver)
                    try:
                        current = self._normalize_version(tech.version)
                        latest = self._normalize_version(tech.latest_version)
                        
                        if current < latest:
                            tech.is_outdated = True
                            tech.severity = SeverityLevel.MEDIUM
                            outdated_count += 1
                            
                            # Critical if major version behind
                            if current[0] < latest[0]:
                                tech.severity = SeverityLevel.HIGH
                    except Exception:
                        pass  # Skip comparison if version format is unusual
        
        result.outdated_count = outdated_count
        
        return result
    
    def _normalize_version(self, version: str) -> tuple:
        """Normalize version string to tuple for comparison"""
        # Extract just numbers
        parts = re.findall(r"\d+", version)
        return tuple(int(p) for p in parts[:3])  # Major, minor, patch
