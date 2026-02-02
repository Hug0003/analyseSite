"""
DNS & Email Deliverability Analyzer
Checks SPF and DMARC records to evaluate email security.
"""
import dns.resolver
from urllib.parse import urlparse
from ..models.schemas import DNSHealthResult

class DNSAnalyzer:
    def __init__(self):
        pass

    async def analyze(self, url: str) -> DNSHealthResult:
        result = DNSHealthResult()
        
        try:
            # Extract clean domain
            # e.g. https://www.example.com/foo -> www.example.com
            hostname = urlparse(url).netloc.split(':')[0]
            
            # Simple heuristic: if www. probably check root domain for email compliance
            # but keep hostname for IP check
            email_domain = hostname
            if email_domain.startswith("www.") and email_domain.count('.') == 2:
                email_domain = email_domain[4:]
                
            result.domain = email_domain
            
            # 1. Get Server IP (from hostname)
            try:
                answers = dns.resolver.resolve(hostname, 'A')
                if answers:
                     result.server_ip = answers[0].to_text()
            except:
                pass # Not critical

            # 2. SPF Check
            try:
                # SPF is a TXT record on the domain
                spf_answers = dns.resolver.resolve(email_domain, 'TXT')
                for rdata in spf_answers:
                    txt = rdata.to_text().strip('"')
                    # Handle multiple strings in one record
                    if hasattr(rdata, 'strings'):
                        txt = "".join([s.decode('utf-8') for s in rdata.strings])
                    
                    if "v=spf1" in txt:
                        result.spf.present = True
                        result.spf.record = txt
                        
                        if "-all" in txt:
                            result.spf.status = "valid" # Strict Fail (Secure)
                        elif "~all" in txt:
                            result.spf.status = "warning" # Soft Fail (Common but less strict)
                            result.spf.warnings.append("Politique ~all (SoftFail) détectée. '-all' est recommandé pour une sécurité maximale.")
                        elif "+all" in txt:
                             result.spf.status = "critical"
                             result.spf.warnings.append("Politique +all DANGEREUSE : autorise n'importe qui à envoyer des emails en votre nom.")
                        else:
                             result.spf.status = "warning"
                             result.spf.warnings.append("Pas de mécanisme de fin (-all ou ~all).")
                        break
                
                if not result.spf.present:
                    result.spf.status = "missing"
                    result.spf.warnings.append("Enregistrement SPF introuvable.")
            except:
                result.spf.status = "missing"
                result.spf.warnings.append("Enregistrement SPF introuvable (Erreur DNS).")
            
            # 3. DMARC Check
            try:
                # DMARC is at _dmarc.domain.com
                dmarc_answers = dns.resolver.resolve(f"_dmarc.{email_domain}", 'TXT')
                for rdata in dmarc_answers:
                     txt = rdata.to_text().strip('"')
                     if hasattr(rdata, 'strings'):
                        txt = "".join([s.decode('utf-8') for s in rdata.strings])

                     if "v=DMARC1" in txt.upper() or "v=dmarc1" in txt:
                         result.dmarc.present = True
                         result.dmarc.record = txt
                         
                         if "p=reject" in txt:
                             result.dmarc.policy = "reject"
                             result.dmarc.status = "valid"
                         elif "p=quarantine" in txt:
                             result.dmarc.policy = "quarantine"
                             result.dmarc.status = "valid"
                         elif "p=none" in txt:
                             result.dmarc.policy = "none"
                             result.dmarc.status = "warning" # Observation only
                         else:
                             result.dmarc.policy = "unknown"
                             result.dmarc.status = "warning"
                         
                         break
                
                if not result.dmarc.present:
                     result.dmarc.status = "missing"
            except:
                 result.dmarc.status = "missing"

            # 4. DKIM Check (Heuristic)
            # DKIM requires knowing the "selector". We can't know it for sure, 
            # but we can try common ones.
            common_selectors = ["default", "google", "mail", "k1", "smtp", "sig1"]
            result.dkim.selectors_checked = common_selectors
            
            for selector in common_selectors:
                try:
                    dkim_domain = f"{selector}._domainkey.{email_domain}"
                    dns.resolver.resolve(dkim_domain, 'TXT')
                    # If we find it, it exists!
                    result.dkim.selectors_found.append(selector)
                    result.dkim.present = True
                except:
                    pass
            
            if result.dkim.present:
                result.dkim.status = "found"
                result.dkim.note = f"Detected active DKIM selectors: {', '.join(result.dkim.selectors_found)}"
            else:
                result.dkim.status = "missing" # likely just unknown selector
                result.dkim.note = "No common DKIM selectors found. Please verify manually in your email provider settings."

            # Scoring Logic
            score = 100
            
            # SPF (Weight 50)
            if result.spf.status == "missing": score -= 50
            elif result.spf.status == "critical": score -= 50
            elif result.spf.status == "warning": score -= 20 # ~all is okay but not perfect
            
            # DMARC (Weight 40)
            if result.dmarc.status == "missing": score -= 40
            elif result.dmarc.status == "warning": score -= 20 # p=none is weak
            
            # Bonus/Malus
            # If both missing, score 10 max
            if result.spf.status == "missing" and result.dmarc.status == "missing":
                score = 0
            
            result.score = max(0, score)

        except Exception as e:
            result.error = f"Analysis failed: {str(e)}"
            
        return result
