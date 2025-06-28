"""
Lead Generation System - Multiple sources for real estate leads
"""
import requests
import json
import csv
import io
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import random
import re


class LeadGenerator:
    """Generate leads from multiple sources"""
    
    def __init__(self):
        self.sources = {
            'web_forms': [],
            'social_media': [],
            'referrals': [],
            'cold_leads': [],
            'imported_csv': []
        }
    
    def generate_sample_leads(self, count: int = 10) -> List[Dict[str, Any]]:
        """Generate realistic sample leads for testing"""
        
        first_names = ['John', 'Sarah', 'Michael', 'Emily', 'David', 'Jessica', 'Robert', 'Ashley', 'James', 'Amanda']
        last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis', 'Rodriguez', 'Martinez']
        
        lead_sources = ['Website Contact Form', 'Zillow Inquiry', 'Social Media', 'Referral', 'Cold Call', 'Open House']
        property_types = ['Single Family', 'Condo', 'Townhouse', 'Investment Property']
        budget_ranges = ['$200k-300k', '$300k-500k', '$500k-750k', '$750k-1M', '$1M+']
        
        leads = []
        
        for i in range(count):
            first_name = random.choice(first_names)
            last_name = random.choice(last_names)
            
            lead = {
                'id': f'lead_{i+1:03d}',
                'first_name': first_name,
                'last_name': last_name,
                'full_name': f'{first_name} {last_name}',
                'email': f'{first_name.lower()}.{last_name.lower()}@{random.choice(["gmail.com", "yahoo.com", "hotmail.com", "outlook.com"])}',
                'phone': f'{random.randint(200, 999)}-{random.randint(200, 999)}-{random.randint(1000, 9999)}',
                'source': random.choice(lead_sources),
                'status': random.choice(['New', 'Contacted', 'Qualified', 'Nurturing', 'Converted', 'Lost']),
                'property_type_interest': random.choice(property_types),
                'budget_range': random.choice(budget_ranges),
                'location_preference': random.choice(['Downtown', 'Suburbs', 'Waterfront', 'Mountains', 'No Preference']),
                'timeline': random.choice(['Immediate (0-3 months)', 'Soon (3-6 months)', 'Future (6+ months)', 'Just Looking']),
                'first_time_buyer': random.choice([True, False]),
                'pre_approved': random.choice([True, False, None]),
                'notes': self._generate_lead_notes(),
                'lead_score': random.randint(1, 100),
                'created_date': (datetime.now() - timedelta(days=random.randint(0, 90))).isoformat(),
                'last_contact': (datetime.now() - timedelta(days=random.randint(0, 30))).isoformat(),
                'next_follow_up': (datetime.now() + timedelta(days=random.randint(1, 14))).isoformat(),
                'tags': random.sample(['Hot Lead', 'Cold Lead', 'Investor', 'First-Time Buyer', 'Luxury', 'Relocating'], k=random.randint(1, 3))
            }
            
            leads.append(lead)
        
        return leads
    
    def _generate_lead_notes(self) -> str:
        """Generate realistic lead notes"""
        note_templates = [
            "Interested in {property_type} properties. Budget around {budget}. Looking to move {timeline}.",
            "Referral from {referrer}. Very motivated buyer. Pre-approved for {budget}.",
            "Called about listing on {street}. Wants to see similar properties in the area.",
            "First-time buyer. Needs education on the process. Budget is {budget}.",
            "Investor looking for rental properties. Cash buyer with {budget} budget.",
            "Relocating from {city} for work. Needs to close by {date}.",
            "Downsizing from larger home. Interested in condos or townhouses.",
            "Growing family needs more space. Current home too small."
        ]
        
        template = random.choice(note_templates)
        
        # Fill in template variables
        replacements = {
            'property_type': random.choice(['single-family', 'condo', 'townhouse']),
            'budget': random.choice(['$400k', '$600k', '$800k', '$1.2M']),
            'timeline': random.choice(['next month', 'this quarter', 'by year-end']),
            'referrer': random.choice(['John Smith', 'past client', 'neighbor']),
            'street': random.choice(['Main St', 'Oak Ave', 'Pine Dr']),
            'city': random.choice(['Seattle', 'San Francisco', 'New York']),
            'date': random.choice(['March 1st', 'end of month', 'Q2'])
        }
        
        for key, value in replacements.items():
            template = template.replace(f'{{{key}}}', value)
        
        return template
    
    def import_leads_from_csv(self, csv_content: str) -> List[Dict[str, Any]]:
        """Import leads from CSV data"""
        try:
            leads = []
            csv_reader = csv.DictReader(io.StringIO(csv_content))
            
            for row in csv_reader:
                # Standardize field names
                lead = {
                    'id': row.get('id') or f'imported_{len(leads)+1}',
                    'first_name': row.get('first_name') or row.get('First Name') or '',
                    'last_name': row.get('last_name') or row.get('Last Name') or '',
                    'email': row.get('email') or row.get('Email') or '',
                    'phone': row.get('phone') or row.get('Phone') or '',
                    'source': 'CSV Import',
                    'status': row.get('status') or 'New',
                    'notes': row.get('notes') or row.get('Notes') or '',
                    'created_date': datetime.now().isoformat(),
                    'lead_score': 50,  # Default score for imported leads
                }
                
                # Generate full name if not provided
                if not lead.get('full_name'):
                    lead['full_name'] = f"{lead['first_name']} {lead['last_name']}".strip()
                
                leads.append(lead)
            
            return leads
            
        except Exception as e:
            print(f"CSV import error: {e}")
            return []
    
    def create_web_form_lead(self, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a lead from web form submission"""
        
        lead = {
            'id': f'web_{datetime.now().strftime("%Y%m%d_%H%M%S")}',
            'source': 'Website Contact Form',
            'status': 'New',
            'created_date': datetime.now().isoformat(),
            'lead_score': self._calculate_lead_score(form_data),
            'first_name': form_data.get('first_name', ''),
            'last_name': form_data.get('last_name', ''),
            'full_name': f"{form_data.get('first_name', '')} {form_data.get('last_name', '')}".strip(),
            'email': form_data.get('email', ''),
            'phone': form_data.get('phone', ''),
            'message': form_data.get('message', ''),
            'property_interest': form_data.get('property_type', ''),
            'budget_range': form_data.get('budget', ''),
            'timeline': form_data.get('timeline', ''),
            'location_preference': form_data.get('location', ''),
            'tags': ['New Lead', 'Website']
        }
        
        return lead
    
    def _calculate_lead_score(self, form_data: Dict[str, Any]) -> int:
        """Calculate lead score based on form data"""
        score = 50  # Base score
        
        # Higher score for complete information
        if form_data.get('phone'):
            score += 15
        if form_data.get('budget'):
            score += 10
        if form_data.get('timeline') == 'Immediate':
            score += 20
        elif form_data.get('timeline') == 'Soon':
            score += 10
        
        # Budget-based scoring
        budget = form_data.get('budget', '')
        if '1M+' in budget:
            score += 15
        elif '750k' in budget:
            score += 10
        
        # Message length indicates interest level
        message_length = len(form_data.get('message', ''))
        if message_length > 100:
            score += 10
        elif message_length > 50:
            score += 5
        
        return min(score, 100)  # Cap at 100
    
    def generate_social_media_leads(self, platform: str, count: int = 5) -> List[Dict[str, Any]]:
        """Generate leads from social media platforms"""
        
        platforms = {
            'facebook': {
                'source': 'Facebook Ad',
                'typical_age_range': (25, 55),
                'interests': ['Home Buying', 'Real Estate Investment', 'First-Time Buyer']
            },
            'instagram': {
                'source': 'Instagram Ad',
                'typical_age_range': (22, 40),
                'interests': ['Luxury Homes', 'Modern Design', 'Home Staging']
            },
            'linkedin': {
                'source': 'LinkedIn Message',
                'typical_age_range': (28, 50),
                'interests': ['Investment Property', 'Corporate Relocation', 'Networking']
            }
        }
        
        platform_data = platforms.get(platform.lower(), platforms['facebook'])
        leads = []
        
        for i in range(count):
            lead = {
                'id': f'{platform}_{i+1:03d}',
                'source': platform_data['source'],
                'status': 'New',
                'created_date': datetime.now().isoformat(),
                'platform_specific_data': {
                    'platform': platform,
                    'campaign_id': f'camp_{random.randint(1000, 9999)}',
                    'ad_set': f'ad_set_{random.randint(100, 999)}',
                    'estimated_age': random.randint(*platform_data['typical_age_range']),
                    'interests': random.sample(platform_data['interests'], k=random.randint(1, 2))
                },
                'lead_score': random.randint(40, 85),
                'tags': ['Social Media', platform.title()]
            }
            
            leads.append(lead)
        
        return leads
    
    def get_lead_analytics(self, leads: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze lead data and provide insights"""
        
        if not leads:
            return {'error': 'No leads to analyze'}
        
        # Calculate analytics
        total_leads = len(leads)
        sources = {}
        statuses = {}
        scores = [lead.get('lead_score', 50) for lead in leads]
        
        # Count by source and status
        for lead in leads:
            source = lead.get('source', 'Unknown')
            status = lead.get('status', 'Unknown')
            
            sources[source] = sources.get(source, 0) + 1
            statuses[status] = statuses.get(status, 0) + 1
        
        # Calculate conversion metrics
        converted = statuses.get('Converted', 0)
        qualified = statuses.get('Qualified', 0)
        conversion_rate = (converted / total_leads * 100) if total_leads > 0 else 0
        qualification_rate = ((qualified + converted) / total_leads * 100) if total_leads > 0 else 0
        
        return {
            'total_leads': total_leads,
            'conversion_rate': conversion_rate,
            'qualification_rate': qualification_rate,
            'average_lead_score': sum(scores) / len(scores) if scores else 0,
            'sources_breakdown': sources,
            'status_breakdown': statuses,
            'top_performing_source': max(sources.items(), key=lambda x: x[1])[0] if sources else 'None',
            'leads_this_month': len([l for l in leads if self._is_this_month(l.get('created_date'))]),
            'follow_ups_needed': len([l for l in leads if l.get('status') in ['New', 'Contacted']]),
            'last_updated': datetime.now().isoformat()
        }
    
    def _is_this_month(self, date_str: str) -> bool:
        """Check if date string is from this month"""
        try:
            if not date_str:
                return False
            
            date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            now = datetime.now()
            
            return date.year == now.year and date.month == now.month
            
        except Exception:
            return False