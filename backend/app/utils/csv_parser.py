"""
CSV Parser Utility
Parses uploaded CSV files and extracts lead data
"""

import csv
import io
from typing import List, Dict, Tuple


class CSVParser:
    """Parse CSV files for lead import"""
    
    # Expected column names (flexible mapping)
    COLUMN_MAPPING = {
        # Email variations
        "email": "email",
        "e-mail": "email",
        "email_address": "email",
        "emailaddress": "email",
        
        # First name variations
        "first_name": "first_name",
        "firstname": "first_name",
        "first": "first_name",
        "fname": "first_name",
        "name": "first_name",
        
        # Last name variations
        "last_name": "last_name",
        "lastname": "last_name",
        "last": "last_name",
        "lname": "last_name",
        "surname": "last_name",
        
        # Company variations
        "company": "company",
        "company_name": "company",
        "business": "company",
        "organization": "company",
        
        # Phone variations
        "phone": "phone",
        "phone_number": "phone",
        "telephone": "phone",
        "mobile": "phone",
        "cell": "phone",
        
        # Address variations
        "address": "address",
        "property_address": "address",
        "street_address": "address",
        "location": "address",
        
        # Property type variations
        "property_type": "property_type",
        "propertytype": "property_type",
        "type": "property_type",
        
        # Estimated value variations
        "estimated_value": "estimated_value",
        "estimatedvalue": "estimated_value",
        "value": "estimated_value",
        "price": "estimated_value",
        "asking_price": "estimated_value",
    }
    
    REQUIRED_FIELDS = ["email", "first_name"]
    
    @classmethod
    def parse(cls, file_content: bytes) -> Tuple[List[Dict], List[str]]:
        """
        Parse CSV file content and return leads data.
        
        Args:
            file_content: Raw bytes from uploaded file
            
        Returns:
            Tuple of (valid_leads, errors)
        """
        valid_leads = []
        errors = []
        
        try:
            # Decode bytes to string
            content = file_content.decode("utf-8")
        except UnicodeDecodeError:
            try:
                content = file_content.decode("latin-1")
            except Exception as e:
                return [], [f"Failed to decode file: {str(e)}"]
        
        # Parse CSV
        reader = csv.DictReader(io.StringIO(content))
        
        # Map headers to standard field names
        if not reader.fieldnames:
            return [], ["CSV file is empty or has no headers"]
        
        header_mapping = cls._map_headers(reader.fieldnames)
        
        # Check required fields
        mapped_fields = set(header_mapping.values())
        missing_required = [f for f in cls.REQUIRED_FIELDS if f not in mapped_fields]
        
        if missing_required:
            return [], [f"Missing required columns: {', '.join(missing_required)}"]
        
        # Process rows
        for row_num, row in enumerate(reader, start=2):  # Start at 2 (header is row 1)
            lead_data, row_errors = cls._process_row(row, header_mapping, row_num)
            
            if row_errors:
                errors.extend(row_errors)
            elif lead_data:
                valid_leads.append(lead_data)
        
        return valid_leads, errors
    
    @classmethod
    def _map_headers(cls, headers: List[str]) -> Dict[str, str]:
        """Map CSV headers to standard field names"""
        mapping = {}
        
        for header in headers:
            # Normalize header: lowercase, strip whitespace
            normalized = header.lower().strip().replace(" ", "_")
            
            if normalized in cls.COLUMN_MAPPING:
                mapping[header] = cls.COLUMN_MAPPING[normalized]
            else:
                # Keep original for unknown columns (might be useful)
                mapping[header] = normalized
        
        return mapping
    
    @classmethod
    def _process_row(
        cls, 
        row: Dict, 
        header_mapping: Dict, 
        row_num: int
    ) -> Tuple[Dict, List[str]]:
        """Process a single CSV row"""
        errors = []
        lead_data = {}
        
        for original_header, mapped_field in header_mapping.items():
            value = row.get(original_header, "").strip()
            
            if value:
                lead_data[mapped_field] = value
        
        # Validate required fields
        if not lead_data.get("email"):
            errors.append(f"Row {row_num}: Missing email")
            return None, errors
        
        if not lead_data.get("first_name"):
            errors.append(f"Row {row_num}: Missing first name")
            return None, errors
        
        # Validate email format (basic check)
        email = lead_data.get("email", "")
        if "@" not in email or "." not in email:
            errors.append(f"Row {row_num}: Invalid email format '{email}'")
            return None, errors
        
        # Normalize email to lowercase
        lead_data["email"] = email.lower()
        
        return lead_data, errors
    
    @classmethod
    def get_sample_csv(cls) -> str:
        """Generate a sample CSV template"""
        headers = ["email", "first_name", "last_name", "phone", "address", "property_type", "estimated_value"]
        sample_data = [
            ["john.doe@email.com", "John", "Doe", "555-1234", "123 Oak Street", "Single Family", "$450,000"],
            ["jane.smith@email.com", "Jane", "Smith", "555-5678", "456 Elm Avenue", "Condo", "$320,000"],
        ]
        
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(headers)
        writer.writerows(sample_data)
        
        return output.getvalue()
