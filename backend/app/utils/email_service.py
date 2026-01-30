"""
Email Service
Handles email sending - Mock for demo, SendGrid for production
"""

import re
from typing import Dict, Optional
from datetime import datetime

from app.config import get_settings

settings = get_settings()


class EmailService:
    """
    Email sending service.
    - Demo mode: Logs emails to console
    - Production mode: Sends via SendGrid
    """
    
    @staticmethod
    def personalize_template(template: str, lead_data: Dict) -> str:
        """
        Replace {{placeholders}} with actual lead data.
        
        Supported placeholders:
        - {{first_name}}
        - {{last_name}}
        - {{email}}
        - {{phone}}
        - {{address}}
        - {{property_type}}
        - {{estimated_value}}
        """
        result = template
        
        # Map of placeholder to lead field
        placeholders = {
            "{{first_name}}": lead_data.get("first_name", ""),
            "{{last_name}}": lead_data.get("last_name", ""),
            "{{email}}": lead_data.get("email", ""),
            "{{phone}}": lead_data.get("phone", ""),
            "{{address}}": lead_data.get("address", ""),
            "{{property_type}}": lead_data.get("property_type", ""),
            "{{estimated_value}}": lead_data.get("estimated_value", ""),
            "{{full_name}}": f"{lead_data.get('first_name', '')} {lead_data.get('last_name', '')}".strip(),
        }
        
        for placeholder, value in placeholders.items():
            result = result.replace(placeholder, str(value) if value else "")
        
        return result
    
    @staticmethod
    def extract_placeholders(template: str) -> list:
        """Extract all {{placeholder}} from template"""
        pattern = r'\{\{(\w+)\}\}'
        return re.findall(pattern, template)
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        from_email: Optional[str] = None
    ) -> Dict:
        """
        Send an email.
        
        Returns:
            Dict with success status and message_id
        """
        from_email = from_email or settings.SENDGRID_FROM_EMAIL
        
        # Check if SendGrid is configured
        if settings.sendgrid_configured:
            return await self._send_via_sendgrid(to_email, subject, body, from_email)
        else:
            return await self._send_mock(to_email, subject, body, from_email)
    
    async def _send_mock(
        self,
        to_email: str,
        subject: str,
        body: str,
        from_email: str
    ) -> Dict:
        """
        Mock email sending for demo.
        Logs email to console instead of actually sending.
        """
        # Generate fake message ID
        import uuid
        message_id = f"mock_{uuid.uuid4().hex[:12]}"
        
        # Log the email
        print("\n" + "=" * 50)
        print("📧 MOCK EMAIL SENT (Demo Mode)")
        print("=" * 50)
        print(f"From: {from_email or 'noreply@demo.com'}")
        print(f"To: {to_email}")
        print(f"Subject: {subject}")
        print("-" * 50)
        print(f"Body:\n{body[:200]}..." if len(body) > 200 else f"Body:\n{body}")
        print("=" * 50)
        print(f"Message ID: {message_id}")
        print(f"Time: {datetime.now().isoformat()}")
        print("=" * 50 + "\n")
        
        return {
            "success": True,
            "message_id": message_id,
            "mode": "mock",
            "timestamp": datetime.now().isoformat()
        }
    
    async def _send_via_sendgrid(
        self,
        to_email: str,
        subject: str,
        body: str,
        from_email: str
    ) -> Dict:
        """
        Send email via SendGrid API.
        Only used when SENDGRID_API_KEY is configured.
        """
        try:
            from sendgrid import SendGridAPIClient
            from sendgrid.helpers.mail import Mail, Email, To, Content
            
            message = Mail(
                from_email=Email(from_email, settings.SENDGRID_FROM_NAME),
                to_emails=To(to_email),
                subject=subject,
                html_content=Content("text/html", body)
            )
            
            sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
            response = sg.send(message)
            
            # Extract message ID from response headers
            message_id = response.headers.get("X-Message-Id", "unknown")
            
            print(f"✅ Email sent to {to_email} via SendGrid (ID: {message_id})")
            
            return {
                "success": True,
                "message_id": message_id,
                "mode": "sendgrid",
                "status_code": response.status_code,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"❌ SendGrid error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "mode": "sendgrid",
                "timestamp": datetime.now().isoformat()
            }
    
    async def send_bulk(
        self,
        emails: list,
        subject_template: str,
        body_template: str
    ) -> Dict:
        """
        Send personalized emails to multiple leads.
        
        Args:
            emails: List of dicts with lead data and email
            subject_template: Subject with {{placeholders}}
            body_template: Body with {{placeholders}}
        
        Returns:
            Summary of sent emails
        """
        results = {
            "total": len(emails),
            "sent": 0,
            "failed": 0,
            "details": []
        }
        
        for lead_data in emails:
            to_email = lead_data.get("email")
            
            # Personalize templates
            subject = self.personalize_template(subject_template, lead_data)
            body = self.personalize_template(body_template, lead_data)
            
            # Send email
            result = await self.send_email(to_email, subject, body)
            
            if result.get("success"):
                results["sent"] += 1
            else:
                results["failed"] += 1
            
            results["details"].append({
                "email": to_email,
                "success": result.get("success"),
                "message_id": result.get("message_id"),
                "error": result.get("error")
            })
        
        return results


# Singleton instance
email_service = EmailService()
