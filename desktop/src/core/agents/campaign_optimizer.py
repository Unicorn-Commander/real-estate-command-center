"""
Campaign Optimization Agent - Optimizes marketing campaigns using AI
"""

import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
import random

from .base_agent import BaseAgent, AgentTask


class CampaignOptimizerAgent(BaseAgent):
    """
    Optimizes marketing campaigns through:
    - A/B testing of messaging
    - Performance tracking
    - Audience segmentation
    - Content optimization
    - Budget allocation
    - Timing optimization
    """
    
    # Performance thresholds
    PERFORMANCE_THRESHOLDS = {
        "min_open_rate": 15.0,          # 15% minimum open rate
        "min_click_rate": 2.0,           # 2% minimum click rate
        "min_conversion_rate": 0.5,      # 0.5% minimum conversion
        "underperforming_threshold": 0.7, # 70% of average
        "test_sample_size": 100,         # Minimum sample for decisions
        "confidence_level": 0.95         # Statistical confidence
    }
    
    def __init__(self):
        super().__init__(
            name="Campaign Optimizer",
            check_interval=3600  # Check every hour
        )
        
        # Campaign tracking
        self.active_campaigns: Dict[str, Dict[str, Any]] = {}
        self.campaign_history: List[Dict[str, Any]] = []
        self.ab_tests: Dict[str, Dict[str, Any]] = {}
        self.performance_benchmarks: Dict[str, float] = {}
        self.content_templates: Dict[str, List[Dict]] = self._default_templates()
    
    def execute_task(self, task: AgentTask) -> Dict[str, Any]:
        """Execute a campaign optimization task"""
        task_handlers = {
            "optimize_campaign": self._optimize_campaign,
            "create_ab_test": self._create_ab_test,
            "analyze_ab_test": self._analyze_ab_test,
            "segment_audience": self._segment_audience,
            "generate_content": self._generate_content,
            "allocate_budget": self._allocate_budget,
            "analyze_timing": self._analyze_timing,
            "generate_report": self._generate_campaign_report
        }
        
        handler = task_handlers.get(task.type)
        if handler:
            return handler(task.data)
        else:
            raise ValueError(f"Unknown task type: {task.type}")
    
    def perform_scheduled_check(self):
        """Perform scheduled campaign optimization"""
        # Check all active campaigns
        for campaign_id, campaign in self.active_campaigns.items():
            self.add_task(AgentTask(
                id=str(uuid.uuid4()),
                type="optimize_campaign",
                data={"campaign_id": campaign_id},
                priority=3
            ))
        
        # Analyze running A/B tests
        for test_id, test in self.ab_tests.items():
            if test["status"] == "running" and self._has_sufficient_data(test):
                self.add_task(AgentTask(
                    id=str(uuid.uuid4()),
                    type="analyze_ab_test",
                    data={"test_id": test_id},
                    priority=2
                ))
        
        # Generate weekly performance report
        if datetime.now().weekday() == 0 and datetime.now().hour == 9:  # Monday 9 AM
            self.add_task(AgentTask(
                id=str(uuid.uuid4()),
                type="generate_report",
                data={"period": "weekly"},
                priority=4
            ))
    
    def _optimize_campaign(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize a specific campaign"""
        campaign_id = data.get("campaign_id")
        
        if campaign_id not in self.active_campaigns:
            return {"status": "error", "message": "Campaign not found"}
        
        campaign = self.active_campaigns[campaign_id]
        metrics = self._get_campaign_metrics(campaign_id)
        
        optimizations = []
        
        # Check performance against thresholds
        if metrics["open_rate"] < self.PERFORMANCE_THRESHOLDS["min_open_rate"]:
            # Optimize subject line
            optimization = self._optimize_subject_line(campaign)
            optimizations.append(optimization)
        
        if metrics["click_rate"] < self.PERFORMANCE_THRESHOLDS["min_click_rate"]:
            # Optimize content
            optimization = self._optimize_content(campaign)
            optimizations.append(optimization)
        
        if metrics["conversion_rate"] < self.PERFORMANCE_THRESHOLDS["min_conversion_rate"]:
            # Optimize call-to-action
            optimization = self._optimize_cta(campaign)
            optimizations.append(optimization)
        
        # Segment underperforming audiences
        underperforming_segments = self._find_underperforming_segments(campaign_id)
        if underperforming_segments:
            optimization = self._optimize_segments(campaign, underperforming_segments)
            optimizations.append(optimization)
        
        # AI-powered optimization suggestions
        if self.ai_provider and optimizations:
            ai_suggestions = self._get_ai_optimization_suggestions(campaign, metrics)
            if ai_suggestions:
                optimizations.append({
                    "type": "ai_suggestions",
                    "suggestions": ai_suggestions
                })
        
        # Apply optimizations
        for opt in optimizations:
            self._apply_optimization(campaign_id, opt)
        
        # Notify about optimizations
        if optimizations:
            self.emit_notification(
                "info",
                f"Campaign '{campaign['name']}' optimized with {len(optimizations)} improvements"
            )
        
        return {
            "status": "success",
            "campaign_id": campaign_id,
            "metrics": metrics,
            "optimizations_applied": len(optimizations),
            "optimizations": optimizations
        }
    
    def _create_ab_test(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create an A/B test for campaign element"""
        campaign_id = data.get("campaign_id")
        test_element = data.get("element")  # subject_line, content, cta, timing
        variations = data.get("variations", [])
        
        if not variations or len(variations) < 2:
            return {"status": "error", "message": "At least 2 variations required"}
        
        test_id = str(uuid.uuid4())
        ab_test = {
            "id": test_id,
            "campaign_id": campaign_id,
            "element": test_element,
            "variations": variations,
            "start_date": datetime.now(),
            "status": "running",
            "results": {
                var["id"]: {
                    "sent": 0,
                    "opened": 0,
                    "clicked": 0,
                    "converted": 0
                } for var in variations
            }
        }
        
        self.ab_tests[test_id] = ab_test
        
        self.emit_notification(
            "info",
            f"A/B test created for {test_element} with {len(variations)} variations"
        )
        
        return {
            "status": "success",
            "test_id": test_id,
            "test": ab_test
        }
    
    def _analyze_ab_test(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze A/B test results and declare winner"""
        test_id = data.get("test_id")
        
        if test_id not in self.ab_tests:
            return {"status": "error", "message": "Test not found"}
        
        test = self.ab_tests[test_id]
        
        # Calculate performance for each variation
        performances = {}
        for var_id, results in test["results"].items():
            if results["sent"] > 0:
                performances[var_id] = {
                    "open_rate": (results["opened"] / results["sent"]) * 100,
                    "click_rate": (results["clicked"] / results["sent"]) * 100,
                    "conversion_rate": (results["converted"] / results["sent"]) * 100,
                    "sample_size": results["sent"]
                }
        
        # Determine winner based on primary metric
        winner = self._determine_test_winner(performances, test["element"])
        
        if winner:
            test["status"] = "completed"
            test["winner"] = winner
            test["completed_date"] = datetime.now()
            
            # Apply winning variation
            self._apply_test_winner(test["campaign_id"], test["element"], winner)
            
            self.emit_notification(
                "success",
                f"A/B test completed. Winner: Variation {winner} with "
                f"{performances[winner]['conversion_rate']:.2f}% conversion rate"
            )
        
        return {
            "status": "success",
            "test_id": test_id,
            "performances": performances,
            "winner": winner
        }
    
    def _segment_audience(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Segment audience for better targeting"""
        campaign_id = data.get("campaign_id")
        
        # Get audience data
        audience = self._get_campaign_audience(campaign_id)
        
        # Create segments based on behavior and attributes
        segments = {
            "high_engagement": [],
            "price_sensitive": [],
            "luxury_seekers": [],
            "first_time_buyers": [],
            "investors": [],
            "urgent_buyers": []
        }
        
        for contact in audience:
            # High engagement
            if contact.get("engagement_score", 0) > 80:
                segments["high_engagement"].append(contact)
            
            # Price sensitive
            if contact.get("budget", 0) < 300000:
                segments["price_sensitive"].append(contact)
            
            # Luxury seekers
            if contact.get("budget", 0) > 1000000:
                segments["luxury_seekers"].append(contact)
            
            # First time buyers
            if contact.get("first_time_buyer", False):
                segments["first_time_buyers"].append(contact)
            
            # Investors
            if "investment" in contact.get("interests", []):
                segments["investors"].append(contact)
            
            # Urgent buyers
            if contact.get("timeline", "") in ["immediate", "1 month"]:
                segments["urgent_buyers"].append(contact)
        
        # Create targeted campaigns for each segment
        targeted_campaigns = []
        for segment_name, contacts in segments.items():
            if len(contacts) > 10:  # Minimum segment size
                targeted_campaign = self._create_targeted_campaign(
                    campaign_id, segment_name, contacts
                )
                targeted_campaigns.append(targeted_campaign)
        
        return {
            "status": "success",
            "campaign_id": campaign_id,
            "segments_created": len(targeted_campaigns),
            "segments": {k: len(v) for k, v in segments.items()},
            "targeted_campaigns": targeted_campaigns
        }
    
    def _generate_content(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate optimized content using AI"""
        campaign_type = data.get("campaign_type", "general")
        target_segment = data.get("target_segment", "all")
        property_type = data.get("property_type", "all")
        
        if not self.ai_provider:
            return {"status": "error", "message": "AI provider not available"}
        
        # Generate content variations
        content_variations = []
        
        # Email subject lines
        subject_prompt = f"""Generate 5 compelling email subject lines for a real estate {campaign_type} campaign targeting {target_segment} interested in {property_type} properties. Make them urgent, personal, and under 50 characters."""
        
        try:
            subjects = self.ai_provider.chat(
                messages=[{"role": "user", "content": subject_prompt}],
                model="good"
            )
            
            # Email body
            body_prompt = f"""Write a compelling 150-word email for a real estate {campaign_type} campaign. Target audience: {target_segment}. Property focus: {property_type}. Include:
1. Personal greeting
2. Value proposition
3. 2-3 key benefits
4. Strong call-to-action
5. Sense of urgency

Keep it conversational and benefit-focused."""

            body = self.ai_provider.chat(
                messages=[{"role": "user", "content": body_prompt}],
                model="good"
            )
            
            # SMS message
            sms_prompt = f"""Write a compelling 160-character SMS for real estate {campaign_type} targeting {target_segment}. Include CTA and urgency."""
            
            sms = self.ai_provider.chat(
                messages=[{"role": "user", "content": sms_prompt}],
                model="cheap"
            )
            
            content_variations.append({
                "id": str(uuid.uuid4()),
                "type": campaign_type,
                "segment": target_segment,
                "subject_lines": subjects.split('\n') if subjects else [],
                "email_body": body,
                "sms_message": sms,
                "created_at": datetime.now()
            })
            
            # Store for future use
            if campaign_type not in self.content_templates:
                self.content_templates[campaign_type] = []
            self.content_templates[campaign_type].append(content_variations[0])
            
        except Exception as e:
            self.logger.error(f"Content generation failed: {str(e)}")
            return {"status": "error", "message": str(e)}
        
        return {
            "status": "success",
            "content_generated": len(content_variations),
            "content": content_variations
        }
    
    def _allocate_budget(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Allocate budget across campaigns based on performance"""
        total_budget = data.get("total_budget", 10000)
        
        # Get all active campaigns with performance
        campaign_performances = []
        for campaign_id, campaign in self.active_campaigns.items():
            metrics = self._get_campaign_metrics(campaign_id)
            roi = self._calculate_campaign_roi(campaign_id)
            
            campaign_performances.append({
                "campaign_id": campaign_id,
                "name": campaign["name"],
                "current_spend": campaign.get("budget_spent", 0),
                "roi": roi,
                "conversion_rate": metrics["conversion_rate"],
                "cost_per_conversion": metrics["cost_per_conversion"]
            })
        
        # Sort by ROI
        campaign_performances.sort(key=lambda x: x["roi"], reverse=True)
        
        # Allocate budget proportionally to ROI
        total_roi = sum(max(cp["roi"], 0.1) for cp in campaign_performances)
        allocations = []
        
        for cp in campaign_performances:
            # Base allocation on ROI
            roi_weight = max(cp["roi"], 0.1) / total_roi
            base_allocation = total_budget * roi_weight
            
            # Apply constraints
            min_budget = total_budget * 0.05  # 5% minimum
            max_budget = total_budget * 0.40  # 40% maximum
            
            allocated = max(min_budget, min(base_allocation, max_budget))
            
            allocations.append({
                "campaign_id": cp["campaign_id"],
                "campaign_name": cp["name"],
                "current_spend": cp["current_spend"],
                "new_allocation": allocated,
                "change": allocated - cp["current_spend"],
                "roi": cp["roi"]
            })
        
        # Notify about major changes
        for alloc in allocations:
            if abs(alloc["change"]) > total_budget * 0.1:
                direction = "increased" if alloc["change"] > 0 else "decreased"
                self.emit_notification(
                    "info",
                    f"Budget {direction} for '{alloc['campaign_name']}' by "
                    f"${abs(alloc['change']):,.0f} based on {alloc['roi']:.1f}x ROI"
                )
        
        return {
            "status": "success",
            "total_budget": total_budget,
            "allocations": allocations
        }
    
    def _analyze_timing(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze optimal timing for campaigns"""
        campaign_id = data.get("campaign_id")
        
        # Get historical performance by time
        time_performance = self._get_time_based_performance(campaign_id)
        
        # Find optimal times
        optimal_times = {
            "best_day": max(time_performance["by_day"].items(), 
                          key=lambda x: x[1]["open_rate"])[0],
            "best_hour": max(time_performance["by_hour"].items(), 
                           key=lambda x: x[1]["open_rate"])[0],
            "worst_day": min(time_performance["by_day"].items(), 
                           key=lambda x: x[1]["open_rate"])[0],
            "worst_hour": min(time_performance["by_hour"].items(), 
                            key=lambda x: x[1]["open_rate"])[0]
        }
        
        # AI analysis of timing patterns
        if self.ai_provider:
            prompt = f"""Analyze these email campaign timing patterns:

Best day: {optimal_times['best_day']} (highest open rate)
Best hour: {optimal_times['best_hour']}:00
Worst day: {optimal_times['worst_day']} (lowest open rate)
Worst hour: {optimal_times['worst_hour']}:00

Provide specific recommendations for scheduling future campaigns."""

            recommendations = self.ai_provider.chat(
                messages=[{"role": "user", "content": prompt}],
                model="cheap"
            )
            
            optimal_times["recommendations"] = recommendations
        
        return {
            "status": "success",
            "campaign_id": campaign_id,
            "time_performance": time_performance,
            "optimal_times": optimal_times
        }
    
    def _generate_campaign_report(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive campaign performance report"""
        period = data.get("period", "weekly")
        
        # Aggregate performance across all campaigns
        total_sent = 0
        total_opened = 0
        total_clicked = 0
        total_converted = 0
        total_spent = 0
        total_revenue = 0
        
        campaign_summaries = []
        
        for campaign_id, campaign in self.active_campaigns.items():
            metrics = self._get_campaign_metrics(campaign_id)
            
            total_sent += metrics["sent"]
            total_opened += metrics["opened"]
            total_clicked += metrics["clicked"]
            total_converted += metrics["converted"]
            total_spent += campaign.get("budget_spent", 0)
            total_revenue += campaign.get("revenue_generated", 0)
            
            campaign_summaries.append({
                "name": campaign["name"],
                "metrics": metrics,
                "roi": self._calculate_campaign_roi(campaign_id),
                "status": campaign.get("status", "active")
            })
        
        # Overall metrics
        overall_metrics = {
            "total_campaigns": len(self.active_campaigns),
            "total_sent": total_sent,
            "avg_open_rate": (total_opened / max(total_sent, 1)) * 100,
            "avg_click_rate": (total_clicked / max(total_sent, 1)) * 100,
            "avg_conversion_rate": (total_converted / max(total_sent, 1)) * 100,
            "total_spent": total_spent,
            "total_revenue": total_revenue,
            "overall_roi": (total_revenue / max(total_spent, 1)) - 1
        }
        
        # Top performers
        campaign_summaries.sort(key=lambda x: x["roi"], reverse=True)
        top_performers = campaign_summaries[:3]
        
        # Generate AI insights
        insights = None
        if self.ai_provider:
            prompt = f"""Analyze this {period} marketing performance:

Overall:
- Campaigns: {overall_metrics['total_campaigns']}
- Emails sent: {overall_metrics['total_sent']:,}
- Open rate: {overall_metrics['avg_open_rate']:.1f}%
- Click rate: {overall_metrics['avg_click_rate']:.1f}%
- Conversion rate: {overall_metrics['avg_conversion_rate']:.2f}%
- ROI: {overall_metrics['overall_roi']:.1f}x

Top performers: {', '.join(c['name'] for c in top_performers)}

Provide 3 actionable recommendations for next {period}."""

            try:
                insights = self.ai_provider.chat(
                    messages=[{"role": "user", "content": prompt}],
                    model="good"
                )
            except Exception as e:
                self.logger.error(f"Failed to generate insights: {str(e)}")
        
        # Notify about report
        self.emit_notification(
            "success",
            f"{period.capitalize()} report generated: "
            f"{overall_metrics['overall_roi']:.1f}x ROI on ${total_spent:,.0f} spend"
        )
        
        return {
            "status": "success",
            "period": period,
            "overall_metrics": overall_metrics,
            "campaign_summaries": campaign_summaries,
            "top_performers": top_performers,
            "insights": insights
        }
    
    def _optimize_subject_line(self, campaign: Dict) -> Dict[str, Any]:
        """Optimize email subject line"""
        current_subject = campaign.get("subject_line", "")
        
        # Generate variations
        variations = []
        
        # Add emoji variation
        variations.append({
            "id": "emoji",
            "subject": f"🏠 {current_subject}"
        })
        
        # Add urgency
        variations.append({
            "id": "urgency",
            "subject": f"Last Chance: {current_subject}"
        })
        
        # Add personalization
        variations.append({
            "id": "personal",
            "subject": f"{{first_name}}, {current_subject}"
        })
        
        return {
            "type": "subject_line",
            "current": current_subject,
            "variations": variations,
            "recommendation": "Test variations to improve open rate"
        }
    
    def _optimize_content(self, campaign: Dict) -> Dict[str, Any]:
        """Optimize email content"""
        return {
            "type": "content",
            "recommendations": [
                "Shorten email to under 150 words",
                "Add more visual content (property photos)",
                "Include social proof (testimonials)",
                "Simplify call-to-action"
            ]
        }
    
    def _optimize_cta(self, campaign: Dict) -> Dict[str, Any]:
        """Optimize call-to-action"""
        return {
            "type": "cta",
            "recommendations": [
                "Use action-oriented language",
                "Create urgency with limited-time offers",
                "Make CTA button more prominent",
                "Reduce number of CTAs to one primary action"
            ]
        }
    
    def _find_underperforming_segments(self, campaign_id: str) -> List[str]:
        """Find audience segments that are underperforming"""
        # Simplified - would analyze actual segment performance
        return ["price_sensitive", "first_time_buyers"]
    
    def _optimize_segments(self, campaign: Dict, segments: List[str]) -> Dict[str, Any]:
        """Optimize underperforming segments"""
        return {
            "type": "segmentation",
            "underperforming_segments": segments,
            "recommendations": [
                f"Create targeted content for {segment}" for segment in segments
            ]
        }
    
    def _get_ai_optimization_suggestions(self, campaign: Dict, metrics: Dict) -> str:
        """Get AI-powered optimization suggestions"""
        if not self.ai_provider:
            return None
        
        try:
            prompt = f"""Analyze this real estate marketing campaign and suggest optimizations:

Campaign: {campaign['name']}
Type: {campaign.get('type', 'email')}
Target: {campaign.get('target_segment', 'all buyers')}

Performance:
- Open rate: {metrics['open_rate']:.1f}% (industry avg: 20%)
- Click rate: {metrics['click_rate']:.1f}% (industry avg: 2.5%)
- Conversion rate: {metrics['conversion_rate']:.2f}% (industry avg: 1%)

Provide 3 specific optimization tactics."""

            return self.ai_provider.chat(
                messages=[{"role": "user", "content": prompt}],
                model="good"
            )
            
        except Exception as e:
            self.logger.error(f"AI suggestions failed: {str(e)}")
            return None
    
    def _apply_optimization(self, campaign_id: str, optimization: Dict):
        """Apply optimization to campaign"""
        # In real implementation, would update campaign settings
        self.logger.info(f"Applied {optimization['type']} optimization to campaign {campaign_id}")
    
    def _apply_test_winner(self, campaign_id: str, element: str, winner_id: str):
        """Apply winning variation from A/B test"""
        # In real implementation, would update campaign with winning variation
        self.logger.info(f"Applied winning {element} variation {winner_id} to campaign {campaign_id}")
    
    def _get_campaign_metrics(self, campaign_id: str) -> Dict[str, float]:
        """Get campaign performance metrics"""
        # Simplified - would get from actual campaign platform
        sent = random.randint(1000, 5000)
        opened = random.randint(100, int(sent * 0.3))
        clicked = random.randint(10, int(opened * 0.2))
        converted = random.randint(1, int(clicked * 0.2))
        spent = random.uniform(100, 1000)
        
        return {
            "sent": sent,
            "opened": opened,
            "clicked": clicked,
            "converted": converted,
            "open_rate": (opened / max(sent, 1)) * 100,
            "click_rate": (clicked / max(sent, 1)) * 100,
            "conversion_rate": (converted / max(sent, 1)) * 100,
            "cost_per_conversion": spent / max(converted, 1)
        }
    
    def _calculate_campaign_roi(self, campaign_id: str) -> float:
        """Calculate campaign ROI"""
        campaign = self.active_campaigns.get(campaign_id, {})
        spent = campaign.get("budget_spent", 1)
        revenue = campaign.get("revenue_generated", 0)
        
        return (revenue / spent) - 1
    
    def _get_campaign_audience(self, campaign_id: str) -> List[Dict]:
        """Get campaign audience data"""
        # Simplified - would get from CRM
        return [
            {
                "id": f"contact_{i}",
                "engagement_score": random.randint(0, 100),
                "budget": random.randint(200000, 2000000),
                "timeline": random.choice(["immediate", "1 month", "3 months", "6 months"]),
                "first_time_buyer": random.choice([True, False]),
                "interests": random.choice([["investment"], ["luxury"], ["starter home"]])
            }
            for i in range(100)
        ]
    
    def _create_targeted_campaign(self, base_campaign_id: str, 
                                 segment_name: str, 
                                 contacts: List[Dict]) -> Dict:
        """Create targeted campaign for segment"""
        return {
            "id": str(uuid.uuid4()),
            "base_campaign_id": base_campaign_id,
            "segment": segment_name,
            "contact_count": len(contacts),
            "created_at": datetime.now()
        }
    
    def _has_sufficient_data(self, test: Dict) -> bool:
        """Check if A/B test has sufficient data"""
        min_sample = self.PERFORMANCE_THRESHOLDS["test_sample_size"]
        
        for results in test["results"].values():
            if results["sent"] < min_sample:
                return False
        
        return True
    
    def _determine_test_winner(self, performances: Dict, element: str) -> Optional[str]:
        """Determine A/B test winner based on statistical significance"""
        if len(performances) < 2:
            return None
        
        # Use conversion rate as primary metric
        best_var = max(performances.items(), key=lambda x: x[1]["conversion_rate"])
        
        # Simple significance check (would use proper stats in production)
        second_best = sorted(performances.items(), 
                           key=lambda x: x[1]["conversion_rate"], 
                           reverse=True)[1]
        
        if best_var[1]["conversion_rate"] > second_best[1]["conversion_rate"] * 1.1:
            return best_var[0]
        
        return None
    
    def _get_time_based_performance(self, campaign_id: str) -> Dict:
        """Get performance metrics by time"""
        # Simplified - would analyze actual send times
        return {
            "by_day": {
                "Monday": {"open_rate": 18.5},
                "Tuesday": {"open_rate": 22.3},
                "Wednesday": {"open_rate": 21.8},
                "Thursday": {"open_rate": 23.1},
                "Friday": {"open_rate": 19.2},
                "Saturday": {"open_rate": 15.6},
                "Sunday": {"open_rate": 16.8}
            },
            "by_hour": {
                str(h): {"open_rate": 20 + random.uniform(-5, 5)}
                for h in range(24)
            }
        }
    
    def _default_templates(self) -> Dict[str, List[Dict]]:
        """Default content templates"""
        return {
            "new_listing": [],
            "price_reduction": [],
            "open_house": [],
            "market_update": [],
            "buyer_tips": [],
            "seller_tips": []
        }
    
    def get_custom_state(self) -> Dict[str, Any]:
        """Save custom state data"""
        return {
            "active_campaigns": {
                cid: {
                    **campaign,
                    "created_at": campaign.get("created_at").isoformat() 
                        if campaign.get("created_at") else None
                }
                for cid, campaign in self.active_campaigns.items()
            },
            "performance_benchmarks": self.performance_benchmarks
        }
    
    def load_custom_state(self, state: Dict[str, Any]):
        """Load custom state data"""
        # Restore campaigns
        self.active_campaigns = {}
        for cid, campaign in state.get("active_campaigns", {}).items():
            campaign_data = {**campaign}
            if campaign.get("created_at"):
                campaign_data["created_at"] = datetime.fromisoformat(campaign["created_at"])
            self.active_campaigns[cid] = campaign_data
        
        self.performance_benchmarks = state.get("performance_benchmarks", {})