"""
Lead Scoring Agent - Automatically qualifies and scores leads
"""

import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple

from .base_agent import BaseAgent, AgentTask


class LeadScoringAgent(BaseAgent):
    """
    Automatically scores and qualifies leads based on:
    - Financial qualification
    - Engagement level
    - Timeline urgency
    - Property match quality
    - Behavioral patterns
    """
    
    # Scoring weights
    SCORING_WEIGHTS = {
        "financial_qualification": 0.30,
        "engagement_level": 0.25,
        "timeline_urgency": 0.20,
        "property_match": 0.15,
        "behavioral_score": 0.10
    }
    
    # Engagement actions and their points
    ENGAGEMENT_POINTS = {
        "property_view": 1,
        "property_favorite": 3,
        "contact_form": 5,
        "phone_call": 10,
        "property_tour": 15,
        "offer_discussion": 20
    }
    
    def __init__(self):
        super().__init__(
            name="Lead Scoring",
            check_interval=600  # Check every 10 minutes
        )
        
        # Lead tracking
        self.lead_scores: Dict[str, Dict[str, Any]] = {}
        self.scoring_history: Dict[str, List[Dict[str, Any]]] = {}
        self.qualification_rules: List[Dict[str, Any]] = self._default_qualification_rules()
    
    def execute_task(self, task: AgentTask) -> Dict[str, Any]:
        """Execute a lead scoring task"""
        task_handlers = {
            "score_lead": self._score_single_lead,
            "score_all_leads": self._score_all_leads,
            "update_engagement": self._update_lead_engagement,
            "qualify_lead": self._qualify_lead,
            "analyze_lead_behavior": self._analyze_lead_behavior,
            "generate_lead_insights": self._generate_lead_insights
        }
        
        handler = task_handlers.get(task.type)
        if handler:
            return handler(task.data)
        else:
            raise ValueError(f"Unknown task type: {task.type}")
    
    def perform_scheduled_check(self):
        """Perform scheduled lead scoring"""
        # Score all leads periodically
        self.add_task(AgentTask(
            id=str(uuid.uuid4()),
            type="score_all_leads",
            data={},
            priority=3
        ))
        
        # Generate insights for high-value leads
        high_value_leads = [
            lead_id for lead_id, score_data in self.lead_scores.items()
            if score_data.get("total_score", 0) >= 80
        ]
        
        if high_value_leads:
            self.add_task(AgentTask(
                id=str(uuid.uuid4()),
                type="generate_lead_insights",
                data={"lead_ids": high_value_leads[:5]},  # Top 5
                priority=4
            ))
    
    def _score_single_lead(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Score a single lead"""
        lead_id = data.get("lead_id")
        if not lead_id:
            raise ValueError("Lead ID required for scoring")
        
        # Get lead data from database
        lead_data = self._get_lead_data(lead_id)
        if not lead_data:
            return {"status": "error", "message": "Lead not found"}
        
        # Calculate component scores
        scores = {
            "financial_qualification": self._calculate_financial_score(lead_data),
            "engagement_level": self._calculate_engagement_score(lead_data),
            "timeline_urgency": self._calculate_timeline_score(lead_data),
            "property_match": self._calculate_property_match_score(lead_data),
            "behavioral_score": self._calculate_behavioral_score(lead_data)
        }
        
        # Calculate weighted total score
        total_score = sum(
            scores[component] * self.SCORING_WEIGHTS[component]
            for component in scores
        )
        
        # Determine lead grade
        grade = self._determine_lead_grade(total_score)
        
        # Store scores
        self.lead_scores[lead_id] = {
            "lead_id": lead_id,
            "name": lead_data.get("name", "Unknown"),
            "scores": scores,
            "total_score": round(total_score, 2),
            "grade": grade,
            "scored_at": datetime.now(),
            "qualification_status": self._determine_qualification_status(lead_data, scores)
        }
        
        # Add to history
        if lead_id not in self.scoring_history:
            self.scoring_history[lead_id] = []
        
        self.scoring_history[lead_id].append({
            "timestamp": datetime.now(),
            "score": total_score,
            "grade": grade
        })
        
        # Notify if score changed significantly
        self._check_score_changes(lead_id, lead_data, total_score, grade)
        
        return {
            "status": "success",
            "lead_id": lead_id,
            "score": total_score,
            "grade": grade,
            "details": scores
        }
    
    def _score_all_leads(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Score all active leads"""
        scored_count = 0
        error_count = 0
        
        # Get all active leads from database
        active_leads = self._get_active_leads()
        
        for i, lead in enumerate(active_leads):
            try:
                self.update_progress(
                    (i + 1) * 100 // len(active_leads),
                    f"Scoring lead: {lead.get('name', 'Unknown')}"
                )
                
                result = self._score_single_lead({"lead_id": lead["id"]})
                if result["status"] == "success":
                    scored_count += 1
                else:
                    error_count += 1
                    
            except Exception as e:
                self.logger.error(f"Error scoring lead {lead['id']}: {str(e)}")
                error_count += 1
        
        # Identify top movers
        top_movers = self._identify_top_movers()
        
        return {
            "status": "completed",
            "total_leads": len(active_leads),
            "scored": scored_count,
            "errors": error_count,
            "top_movers": top_movers
        }
    
    def _update_lead_engagement(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update lead engagement data"""
        lead_id = data.get("lead_id")
        action = data.get("action")
        
        if not lead_id or not action:
            raise ValueError("Lead ID and action required")
        
        # Update engagement in database
        # This would normally update the database
        # For now, we'll just trigger a rescore
        
        return self._score_single_lead({"lead_id": lead_id})
    
    def _qualify_lead(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Qualify a lead based on rules"""
        lead_id = data.get("lead_id")
        lead_data = self._get_lead_data(lead_id)
        
        if not lead_data:
            return {"status": "error", "message": "Lead not found"}
        
        # Check qualification rules
        qualified = True
        failed_rules = []
        
        for rule in self.qualification_rules:
            if not self._check_qualification_rule(lead_data, rule):
                qualified = False
                failed_rules.append(rule["name"])
        
        return {
            "status": "success",
            "lead_id": lead_id,
            "qualified": qualified,
            "failed_rules": failed_rules
        }
    
    def _analyze_lead_behavior(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze lead behavior patterns"""
        lead_id = data.get("lead_id")
        
        # Get lead activity history
        activities = self._get_lead_activities(lead_id)
        
        # Analyze patterns
        patterns = {
            "most_active_time": self._find_most_active_time(activities),
            "preferred_property_type": self._find_preferred_property_type(activities),
            "price_range_drift": self._analyze_price_drift(activities),
            "engagement_trend": self._analyze_engagement_trend(activities)
        }
        
        return {
            "status": "success",
            "lead_id": lead_id,
            "patterns": patterns
        }
    
    def _generate_lead_insights(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate AI-powered insights for high-value leads"""
        lead_ids = data.get("lead_ids", [])
        insights = []
        
        for lead_id in lead_ids:
            lead_data = self._get_lead_data(lead_id)
            if not lead_data:
                continue
            
            score_data = self.lead_scores.get(lead_id, {})
            
            # Use AI to generate insights
            if self.ai_provider:
                prompt = f"""Analyze this high-value real estate lead and provide actionable insights:

Lead: {lead_data.get('name')}
Score: {score_data.get('total_score', 0)}/100 (Grade: {score_data.get('grade', 'Unknown')})
Budget: ${lead_data.get('budget', 0):,.0f}
Timeline: {lead_data.get('timeline', 'Unknown')}
Property Preferences: {lead_data.get('property_preferences', 'Unknown')}

Component Scores:
- Financial: {score_data.get('scores', {}).get('financial_qualification', 0)}/100
- Engagement: {score_data.get('scores', {}).get('engagement_level', 0)}/100
- Timeline: {score_data.get('scores', {}).get('timeline_urgency', 0)}/100
- Property Match: {score_data.get('scores', {}).get('property_match', 0)}/100

Provide 3 specific actions the agent should take with this lead in the next 48 hours."""

                try:
                    response = self.ai_provider.chat(
                        messages=[{"role": "user", "content": prompt}],
                        model="good"
                    )
                    
                    if response:
                        insights.append({
                            "lead_id": lead_id,
                            "lead_name": lead_data.get('name'),
                            "insights": response
                        })
                        
                        # Notify about high-value lead insights
                        self.emit_notification(
                            "success",
                            f"New insights for high-value lead {lead_data.get('name')}: {response[:100]}..."
                        )
                        
                except Exception as e:
                    self.logger.error(f"AI insight generation failed: {str(e)}")
        
        return {
            "status": "success",
            "insights_generated": len(insights),
            "insights": insights
        }
    
    def _calculate_financial_score(self, lead_data: Dict[str, Any]) -> float:
        """Calculate financial qualification score (0-100)"""
        score = 0
        
        # Budget relative to market
        budget = lead_data.get("budget", 0)
        avg_market_price = lead_data.get("target_area_avg_price", 500000)
        
        if budget > 0:
            budget_ratio = budget / avg_market_price
            if budget_ratio >= 1.2:
                score += 40  # Well above market
            elif budget_ratio >= 0.8:
                score += 30  # Market appropriate
            elif budget_ratio >= 0.6:
                score += 20  # Below market but viable
            else:
                score += 10  # Challenging budget
        
        # Pre-approval status
        if lead_data.get("pre_approved"):
            score += 40
        elif lead_data.get("pre_qualified"):
            score += 20
        
        # Down payment
        down_payment = lead_data.get("down_payment_amount", 0)
        if budget > 0 and down_payment > 0:
            down_payment_ratio = down_payment / budget
            if down_payment_ratio >= 0.20:
                score += 20  # Strong down payment
            elif down_payment_ratio >= 0.10:
                score += 10  # Acceptable down payment
        
        return min(score, 100)
    
    def _calculate_engagement_score(self, lead_data: Dict[str, Any]) -> float:
        """Calculate engagement level score (0-100)"""
        score = 0
        
        # Recent activities
        activities = lead_data.get("recent_activities", [])
        activity_points = 0
        
        for activity in activities:
            activity_type = activity.get("type")
            if activity_type in self.ENGAGEMENT_POINTS:
                # Recent activities worth more
                days_ago = (datetime.now() - activity.get("timestamp", datetime.now())).days
                if days_ago <= 7:
                    activity_points += self.ENGAGEMENT_POINTS[activity_type]
                elif days_ago <= 30:
                    activity_points += self.ENGAGEMENT_POINTS[activity_type] * 0.5
        
        # Convert to 0-100 scale (cap at 100)
        score = min(activity_points * 2, 100)
        
        # Response rate
        messages_sent = lead_data.get("messages_sent", 0)
        messages_responded = lead_data.get("messages_responded", 0)
        
        if messages_sent > 0:
            response_rate = messages_responded / messages_sent
            score = score * 0.7 + (response_rate * 30)  # 30% weight for response rate
        
        return min(score, 100)
    
    def _calculate_timeline_score(self, lead_data: Dict[str, Any]) -> float:
        """Calculate timeline urgency score (0-100)"""
        timeline = lead_data.get("timeline", "").lower()
        
        timeline_scores = {
            "immediate": 100,
            "asap": 100,
            "1 month": 90,
            "1-3 months": 80,
            "3-6 months": 60,
            "6-12 months": 40,
            "1 year+": 20,
            "just looking": 10,
            "not sure": 15
        }
        
        for key, score in timeline_scores.items():
            if key in timeline:
                return score
        
        return 30  # Default for unknown timeline
    
    def _calculate_property_match_score(self, lead_data: Dict[str, Any]) -> float:
        """Calculate property match quality score (0-100)"""
        score = 0
        
        # Check if we have matching properties
        matching_properties = lead_data.get("matching_properties_count", 0)
        total_inventory = lead_data.get("total_area_inventory", 100)
        
        if total_inventory > 0:
            match_ratio = matching_properties / total_inventory
            
            if match_ratio >= 0.10:
                score += 50  # Good selection available
            elif match_ratio >= 0.05:
                score += 30  # Moderate selection
            elif match_ratio >= 0.01:
                score += 15  # Limited selection
            else:
                score += 5   # Very limited
        
        # Flexibility indicators
        if lead_data.get("flexible_on_location"):
            score += 20
        if lead_data.get("flexible_on_price"):
            score += 20
        if lead_data.get("flexible_on_features"):
            score += 10
        
        return min(score, 100)
    
    def _calculate_behavioral_score(self, lead_data: Dict[str, Any]) -> float:
        """Calculate behavioral pattern score (0-100)"""
        score = 50  # Start at neutral
        
        # Consistency in searches
        if lead_data.get("search_consistency_score", 0) > 0.7:
            score += 20  # Knows what they want
        
        # Decision-making patterns
        if lead_data.get("properties_toured", 0) > 0:
            tour_to_view_ratio = lead_data.get("properties_toured", 0) / max(lead_data.get("properties_viewed", 1), 1)
            if tour_to_view_ratio > 0.2:
                score += 20  # Serious about viewing
        
        # Communication patterns
        if lead_data.get("preferred_contact_method"):
            score += 10  # Has preferences
        
        return min(score, 100)
    
    def _determine_lead_grade(self, score: float) -> str:
        """Determine lead grade based on score"""
        if score >= 90:
            return "A+"
        elif score >= 80:
            return "A"
        elif score >= 70:
            return "B"
        elif score >= 60:
            return "C"
        elif score >= 50:
            return "D"
        else:
            return "F"
    
    def _determine_qualification_status(self, lead_data: Dict, scores: Dict) -> str:
        """Determine qualification status"""
        if scores["financial_qualification"] < 40:
            return "Not Qualified - Financial"
        elif scores["timeline_urgency"] < 20:
            return "Not Qualified - No Urgency"
        elif scores["engagement_level"] < 20:
            return "Not Qualified - Low Engagement"
        elif scores["financial_qualification"] >= 70 and scores["timeline_urgency"] >= 70:
            return "Highly Qualified"
        else:
            return "Qualified"
    
    def _check_score_changes(self, lead_id: str, lead_data: Dict, 
                            new_score: float, new_grade: str):
        """Check for significant score changes and notify"""
        if lead_id in self.scoring_history and len(self.scoring_history[lead_id]) > 1:
            previous = self.scoring_history[lead_id][-2]
            score_change = new_score - previous["score"]
            
            # Notify on significant changes
            if abs(score_change) >= 10:
                direction = "increased" if score_change > 0 else "decreased"
                self.emit_notification(
                    "warning" if score_change < 0 else "success",
                    f"Lead {lead_data.get('name')} score {direction} by {abs(score_change):.0f} points to {new_score:.0f} ({new_grade})"
                )
            
            # Grade change
            if previous["grade"] != new_grade:
                self.emit_notification(
                    "info",
                    f"Lead {lead_data.get('name')} grade changed from {previous['grade']} to {new_grade}"
                )
    
    def _default_qualification_rules(self) -> List[Dict[str, Any]]:
        """Default lead qualification rules"""
        return [
            {
                "name": "Minimum Budget",
                "field": "budget",
                "operator": ">=",
                "value": 100000
            },
            {
                "name": "Timeline",
                "field": "timeline",
                "operator": "not_contains",
                "value": "just looking"
            },
            {
                "name": "Contact Info",
                "field": "email",
                "operator": "exists",
                "value": True
            }
        ]
    
    def _check_qualification_rule(self, lead_data: Dict, rule: Dict) -> bool:
        """Check if lead meets a qualification rule"""
        field_value = lead_data.get(rule["field"])
        
        if rule["operator"] == ">=":
            return field_value >= rule["value"]
        elif rule["operator"] == "<=":
            return field_value <= rule["value"]
        elif rule["operator"] == "==":
            return field_value == rule["value"]
        elif rule["operator"] == "!=":
            return field_value != rule["value"]
        elif rule["operator"] == "contains":
            return rule["value"] in str(field_value).lower()
        elif rule["operator"] == "not_contains":
            return rule["value"] not in str(field_value).lower()
        elif rule["operator"] == "exists":
            return bool(field_value) == rule["value"]
        
        return True
    
    def _get_lead_data(self, lead_id: str) -> Optional[Dict[str, Any]]:
        """Get lead data from database"""
        # TODO: Implement actual database query
        # For now, return mock data
        return {
            "id": lead_id,
            "name": f"Lead {lead_id}",
            "budget": 500000,
            "timeline": "1-3 months",
            "pre_approved": True,
            "down_payment_amount": 100000,
            "recent_activities": [],
            "messages_sent": 5,
            "messages_responded": 4,
            "matching_properties_count": 15,
            "total_area_inventory": 200,
            "flexible_on_location": True,
            "properties_viewed": 20,
            "properties_toured": 3,
            "email": f"lead{lead_id}@example.com"
        }
    
    def _get_active_leads(self) -> List[Dict[str, Any]]:
        """Get all active leads from database"""
        # TODO: Implement actual database query
        # For now, return mock data
        return [
            self._get_lead_data(f"lead_{i}")
            for i in range(1, 6)
        ]
    
    def _get_lead_activities(self, lead_id: str) -> List[Dict[str, Any]]:
        """Get lead activity history"""
        # TODO: Implement actual database query
        return []
    
    def _find_most_active_time(self, activities: List[Dict]) -> str:
        """Find when lead is most active"""
        # TODO: Implement time analysis
        return "Evenings (6-9 PM)"
    
    def _find_preferred_property_type(self, activities: List[Dict]) -> str:
        """Find preferred property type from activities"""
        # TODO: Implement preference analysis
        return "Single Family Home"
    
    def _analyze_price_drift(self, activities: List[Dict]) -> str:
        """Analyze how price preferences have changed"""
        # TODO: Implement price drift analysis
        return "Stable"
    
    def _analyze_engagement_trend(self, activities: List[Dict]) -> str:
        """Analyze engagement trend over time"""
        # TODO: Implement trend analysis
        return "Increasing"
    
    def _identify_top_movers(self) -> List[Dict[str, Any]]:
        """Identify leads with biggest score changes"""
        movers = []
        
        for lead_id, history in self.scoring_history.items():
            if len(history) >= 2:
                current = history[-1]
                previous = history[-2]
                change = current["score"] - previous["score"]
                
                if abs(change) >= 5:
                    movers.append({
                        "lead_id": lead_id,
                        "name": self.lead_scores.get(lead_id, {}).get("name", "Unknown"),
                        "change": change,
                        "current_score": current["score"],
                        "current_grade": current["grade"]
                    })
        
        # Sort by absolute change
        movers.sort(key=lambda x: abs(x["change"]), reverse=True)
        return movers[:5]  # Top 5 movers
    
    def get_custom_state(self) -> Dict[str, Any]:
        """Save custom state data"""
        return {
            "lead_scores": {
                lead_id: {
                    **scores,
                    "scored_at": scores["scored_at"].isoformat() if scores.get("scored_at") else None
                }
                for lead_id, scores in self.lead_scores.items()
            },
            "qualification_rules": self.qualification_rules
        }
    
    def load_custom_state(self, state: Dict[str, Any]):
        """Load custom state data"""
        # Restore lead scores
        self.lead_scores = {}
        for lead_id, scores in state.get("lead_scores", {}).items():
            score_data = {**scores}
            if scores.get("scored_at"):
                score_data["scored_at"] = datetime.fromisoformat(scores["scored_at"])
            self.lead_scores[lead_id] = score_data
        
        # Restore qualification rules
        if "qualification_rules" in state:
            self.qualification_rules = state["qualification_rules"]