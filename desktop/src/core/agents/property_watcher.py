"""
Property Watcher Agent - Monitors properties for opportunities and alerts
"""

import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple

from .base_agent import BaseAgent, AgentTask


class PropertyWatcherAgent(BaseAgent):
    """
    Watches properties for investment opportunities and alerts:
    - Undervalued properties
    - Distressed sales
    - Price drops
    - New construction opportunities
    - Flip potential properties
    - Market timing opportunities
    """
    
    # Opportunity thresholds
    OPPORTUNITY_THRESHOLDS = {
        "price_drop_percent": 5.0,          # 5% price drop
        "below_market_percent": 10.0,       # 10% below market
        "days_on_market_alert": 90,         # Long listing alert
        "price_per_sqft_discount": 15.0,    # 15% below area average
        "cap_rate_minimum": 6.0,            # Minimum cap rate for investment
        "flip_profit_minimum": 50000        # Minimum flip profit potential
    }
    
    def __init__(self):
        super().__init__(
            name="Property Watcher",
            check_interval=300  # Check every 5 minutes
        )
        
        # Tracking data
        self.watched_areas: List[Dict[str, Any]] = []
        self.opportunity_alerts: List[Dict[str, Any]] = []
        self.market_conditions: Dict[str, Any] = {}
        self.property_history: Dict[str, List[Dict]] = {}
    
    def execute_task(self, task: AgentTask) -> Dict[str, Any]:
        """Execute a property watching task"""
        task_handlers = {
            "watch_area": self._watch_area,
            "unwatch_area": self._unwatch_area,
            "scan_opportunities": self._scan_for_opportunities,
            "analyze_property": self._analyze_property_opportunity,
            "check_distressed": self._check_distressed_properties,
            "find_flips": self._find_flip_opportunities,
            "monitor_new_construction": self._monitor_new_construction,
            "calculate_investment_metrics": self._calculate_investment_metrics
        }
        
        handler = task_handlers.get(task.type)
        if handler:
            return handler(task.data)
        else:
            raise ValueError(f"Unknown task type: {task.type}")
    
    def perform_scheduled_check(self):
        """Perform scheduled property watching"""
        # Scan all watched areas for opportunities
        if self.watched_areas:
            self.add_task(AgentTask(
                id=str(uuid.uuid4()),
                type="scan_opportunities",
                data={},
                priority=3
            ))
        
        # Check for distressed properties periodically
        self.add_task(AgentTask(
            id=str(uuid.uuid4()),
            type="check_distressed",
            data={},
            priority=4
        ))
        
        # Look for flip opportunities
        self.add_task(AgentTask(
            id=str(uuid.uuid4()),
            type="find_flips",
            data={},
            priority=5
        ))
    
    def _watch_area(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Start watching an area for opportunities"""
        area_config = {
            "id": str(uuid.uuid4()),
            "city": data.get("city"),
            "state": data.get("state"),
            "zip_codes": data.get("zip_codes", []),
            "property_types": data.get("property_types", ["single_family", "condo", "multi_family"]),
            "min_price": data.get("min_price", 0),
            "max_price": data.get("max_price", float('inf')),
            "investment_focus": data.get("investment_focus", "all"),  # all, flip, rental, development
            "created_at": datetime.now()
        }
        
        self.watched_areas.append(area_config)
        
        # Get baseline market data
        if self.mls_client:
            market_stats = self.mls_client.get_market_statistics(
                city=area_config["city"],
                state=area_config["state"]
            )
            
            if market_stats:
                self.market_conditions[area_config["id"]] = {
                    "baseline_stats": market_stats,
                    "recorded_at": datetime.now()
                }
        
        self.emit_notification(
            "info",
            f"Now watching {area_config['city']}, {area_config['state']} for opportunities"
        )
        
        return {
            "status": "watching",
            "area_id": area_config["id"],
            "area": f"{area_config['city']}, {area_config['state']}"
        }
    
    def _unwatch_area(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Stop watching an area"""
        area_id = data.get("area_id")
        
        self.watched_areas = [a for a in self.watched_areas if a["id"] != area_id]
        
        return {"status": "unwatched", "area_id": area_id}
    
    def _scan_for_opportunities(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Scan watched areas for investment opportunities"""
        opportunities_found = []
        
        for area in self.watched_areas:
            try:
                self.update_progress(
                    self.watched_areas.index(area) * 100 // len(self.watched_areas),
                    f"Scanning {area['city']}, {area['state']}"
                )
                
                # Search for properties in the area
                if self.mls_client:
                    search_params = {
                        "city": area["city"],
                        "state": area["state"],
                        "min_price": area["min_price"],
                        "max_price": area["max_price"],
                        "property_types": area["property_types"],
                        "status": ["active", "pending"]
                    }
                    
                    results = self.mls_client.search_properties(**search_params)
                    
                    if results and results.get("listings"):
                        # Analyze each property for opportunities
                        for listing in results["listings"]:
                            opportunity = self._evaluate_opportunity(listing, area)
                            
                            if opportunity:
                                opportunities_found.append(opportunity)
                                self._create_opportunity_alert(opportunity)
                
            except Exception as e:
                self.logger.error(f"Error scanning area {area['id']}: {str(e)}")
        
        # AI analysis of best opportunities
        if opportunities_found and self.ai_provider:
            best_opportunities = self._rank_opportunities_with_ai(opportunities_found[:10])
            
            for opp in best_opportunities[:3]:  # Top 3
                self.emit_notification(
                    "success",
                    f"Hot opportunity: {opp['address']} - {opp['opportunity_type']}: {opp['reason']}"
                )
        
        return {
            "status": "completed",
            "areas_scanned": len(self.watched_areas),
            "opportunities_found": len(opportunities_found),
            "opportunities": opportunities_found[:10]  # Return top 10
        }
    
    def _check_distressed_properties(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Check for distressed properties (foreclosures, short sales, etc.)"""
        distressed_found = []
        
        for area in self.watched_areas:
            try:
                if self.mls_client:
                    # Search for distressed indicators
                    keywords = ["foreclosure", "short sale", "as-is", "cash only", 
                               "investor special", "handyman special", "fixer upper"]
                    
                    for keyword in keywords:
                        results = self.mls_client.search_properties(
                            city=area["city"],
                            state=area["state"],
                            keywords=keyword,
                            status=["active"]
                        )
                        
                        if results and results.get("listings"):
                            for listing in results["listings"]:
                                if self._is_distressed_opportunity(listing):
                                    distressed_found.append({
                                        "property": listing,
                                        "type": "distressed",
                                        "keyword": keyword,
                                        "area_id": area["id"]
                                    })
                
            except Exception as e:
                self.logger.error(f"Error checking distressed properties: {str(e)}")
        
        # Notify about distressed opportunities
        for opp in distressed_found[:5]:  # Top 5
            self.emit_notification(
                "warning",
                f"Distressed property alert: {opp['property'].get('address')} - "
                f"{opp['keyword']} - ${opp['property'].get('price', 0):,.0f}"
            )
        
        return {
            "status": "completed",
            "distressed_found": len(distressed_found),
            "properties": distressed_found
        }
    
    def _find_flip_opportunities(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Find properties with flip potential"""
        flip_opportunities = []
        
        for area in self.watched_areas:
            if area["investment_focus"] not in ["all", "flip"]:
                continue
            
            try:
                # Get market stats for ARV calculation
                market_stats = self.market_conditions.get(area["id"], {}).get("baseline_stats", {})
                avg_price_sqft = market_stats.get("avg_price_sqft", 0)
                
                if self.mls_client and avg_price_sqft > 0:
                    # Search for below-market properties
                    results = self.mls_client.search_properties(
                        city=area["city"],
                        state=area["state"],
                        max_price=area["max_price"] * 0.7,  # 70% of max to leave room for profit
                        property_types=["single_family"],
                        status=["active"]
                    )
                    
                    if results and results.get("listings"):
                        for listing in results["listings"]:
                            flip_analysis = self._analyze_flip_potential(listing, avg_price_sqft)
                            
                            if flip_analysis and flip_analysis["estimated_profit"] >= self.OPPORTUNITY_THRESHOLDS["flip_profit_minimum"]:
                                flip_opportunities.append(flip_analysis)
                
            except Exception as e:
                self.logger.error(f"Error finding flip opportunities: {str(e)}")
        
        # Sort by profit potential
        flip_opportunities.sort(key=lambda x: x["estimated_profit"], reverse=True)
        
        # Notify about best flips
        for flip in flip_opportunities[:3]:
            self.emit_notification(
                "success",
                f"Flip opportunity: {flip['address']} - "
                f"Buy: ${flip['purchase_price']:,.0f}, "
                f"ARV: ${flip['after_repair_value']:,.0f}, "
                f"Est. Profit: ${flip['estimated_profit']:,.0f}"
            )
        
        return {
            "status": "completed",
            "flips_found": len(flip_opportunities),
            "opportunities": flip_opportunities[:10]
        }
    
    def _monitor_new_construction(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Monitor new construction opportunities"""
        new_construction = []
        
        for area in self.watched_areas:
            if area["investment_focus"] not in ["all", "development"]:
                continue
            
            try:
                if self.mls_client:
                    # Search for new construction
                    results = self.mls_client.search_properties(
                        city=area["city"],
                        state=area["state"],
                        property_types=["land", "lot"],
                        status=["active"]
                    )
                    
                    if results and results.get("listings"):
                        for listing in results["listings"]:
                            if self._is_development_opportunity(listing, area):
                                new_construction.append({
                                    "property": listing,
                                    "type": "development",
                                    "area_id": area["id"]
                                })
                
            except Exception as e:
                self.logger.error(f"Error monitoring new construction: {str(e)}")
        
        return {
            "status": "completed",
            "opportunities_found": len(new_construction),
            "properties": new_construction
        }
    
    def _analyze_property_opportunity(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Deep analysis of a specific property opportunity"""
        property_id = data.get("property_id")
        address = data.get("address")
        
        if not address:
            return {"status": "error", "message": "Address required"}
        
        # Get property details
        property_data = self.property_service.get_property_details(address)
        if not property_data:
            return {"status": "error", "message": "Property not found"}
        
        # Calculate all investment metrics
        metrics = self._calculate_investment_metrics({
            "property_data": property_data,
            "purchase_price": property_data.get("price", 0)
        })
        
        # AI analysis
        ai_analysis = None
        if self.ai_provider:
            prompt = f"""Analyze this real estate investment opportunity:

Property: {address}
Price: ${property_data.get('price', 0):,.0f}
Size: {property_data.get('sqft', 0)} sqft
Bedrooms: {property_data.get('bedrooms', 0)}
Bathrooms: {property_data.get('bathrooms', 0)}

Investment Metrics:
- Cap Rate: {metrics.get('cap_rate', 0):.2f}%
- Cash on Cash Return: {metrics.get('cash_on_cash', 0):.2f}%
- Monthly Cash Flow: ${metrics.get('monthly_cash_flow', 0):,.0f}
- Total ROI: {metrics.get('total_roi', 0):.2f}%

Provide a brief investment recommendation (buy/hold/pass) with reasoning."""

            try:
                ai_analysis = self.ai_provider.chat(
                    messages=[{"role": "user", "content": prompt}],
                    model="good"
                )
            except Exception as e:
                self.logger.error(f"AI analysis failed: {str(e)}")
        
        return {
            "status": "success",
            "property_id": property_id,
            "address": address,
            "metrics": metrics,
            "ai_analysis": ai_analysis
        }
    
    def _calculate_investment_metrics(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate comprehensive investment metrics"""
        property_data = data.get("property_data", {})
        purchase_price = data.get("purchase_price", 0)
        
        if purchase_price == 0:
            return {}
        
        # Estimate rental income (simplified)
        bedrooms = property_data.get("bedrooms", 0)
        rent_estimate = bedrooms * 800  # Simple estimate
        
        # Operating expenses (30% rule)
        monthly_expenses = rent_estimate * 0.30
        
        # Mortgage assumptions (20% down, 7% rate, 30 years)
        down_payment = purchase_price * 0.20
        loan_amount = purchase_price * 0.80
        monthly_payment = (loan_amount * 0.07 / 12) / (1 - (1 + 0.07/12)**(-360))
        
        # Cash flow
        monthly_cash_flow = rent_estimate - monthly_expenses - monthly_payment
        annual_cash_flow = monthly_cash_flow * 12
        
        # Returns
        cap_rate = ((rent_estimate * 12 - monthly_expenses * 12) / purchase_price) * 100
        cash_on_cash = (annual_cash_flow / down_payment) * 100 if down_payment > 0 else 0
        
        # Total ROI (including appreciation at 3% annually)
        appreciation = purchase_price * 0.03
        total_annual_return = annual_cash_flow + appreciation
        total_roi = (total_annual_return / down_payment) * 100 if down_payment > 0 else 0
        
        return {
            "purchase_price": purchase_price,
            "down_payment": down_payment,
            "monthly_rent": rent_estimate,
            "monthly_expenses": monthly_expenses,
            "monthly_payment": monthly_payment,
            "monthly_cash_flow": monthly_cash_flow,
            "annual_cash_flow": annual_cash_flow,
            "cap_rate": cap_rate,
            "cash_on_cash": cash_on_cash,
            "total_roi": total_roi
        }
    
    def _evaluate_opportunity(self, listing: Dict, area: Dict) -> Optional[Dict]:
        """Evaluate if a listing is an opportunity"""
        opportunities = []
        
        # Price drop opportunity
        if "price_history" in listing:
            price_drop = self._check_price_drop(listing["price_history"])
            if price_drop >= self.OPPORTUNITY_THRESHOLDS["price_drop_percent"]:
                opportunities.append({
                    "type": "price_drop",
                    "value": price_drop,
                    "reason": f"{price_drop:.1f}% price reduction"
                })
        
        # Below market opportunity
        market_stats = self.market_conditions.get(area["id"], {}).get("baseline_stats", {})
        if market_stats:
            below_market = self._check_below_market(listing, market_stats)
            if below_market >= self.OPPORTUNITY_THRESHOLDS["below_market_percent"]:
                opportunities.append({
                    "type": "below_market",
                    "value": below_market,
                    "reason": f"{below_market:.1f}% below market value"
                })
        
        # Long listing opportunity
        days_on_market = listing.get("days_on_market", 0)
        if days_on_market >= self.OPPORTUNITY_THRESHOLDS["days_on_market_alert"]:
            opportunities.append({
                "type": "stale_listing",
                "value": days_on_market,
                "reason": f"On market for {days_on_market} days"
            })
        
        # Investment metrics opportunity
        metrics = self._calculate_investment_metrics({
            "property_data": listing,
            "purchase_price": listing.get("price", 0)
        })
        
        if metrics.get("cap_rate", 0) >= self.OPPORTUNITY_THRESHOLDS["cap_rate_minimum"]:
            opportunities.append({
                "type": "high_cap_rate",
                "value": metrics["cap_rate"],
                "reason": f"{metrics['cap_rate']:.2f}% cap rate"
            })
        
        if opportunities:
            return {
                "property_id": listing.get("id"),
                "address": listing.get("address"),
                "price": listing.get("price"),
                "opportunities": opportunities,
                "area_id": area["id"],
                "opportunity_score": sum(o["value"] for o in opportunities),
                "opportunity_type": opportunities[0]["type"],
                "reason": opportunities[0]["reason"]
            }
        
        return None
    
    def _check_price_drop(self, price_history: List[Dict]) -> float:
        """Calculate price drop percentage"""
        if len(price_history) < 2:
            return 0
        
        current_price = price_history[-1].get("price", 0)
        previous_price = price_history[-2].get("price", 0)
        
        if previous_price > 0:
            return ((previous_price - current_price) / previous_price) * 100
        
        return 0
    
    def _check_below_market(self, listing: Dict, market_stats: Dict) -> float:
        """Check how much below market a property is"""
        listing_price = listing.get("price", 0)
        sqft = listing.get("sqft", 1)
        
        if sqft > 0 and listing_price > 0:
            listing_price_sqft = listing_price / sqft
            market_price_sqft = market_stats.get("avg_price_sqft", listing_price_sqft)
            
            if market_price_sqft > 0:
                return ((market_price_sqft - listing_price_sqft) / market_price_sqft) * 100
        
        return 0
    
    def _is_distressed_opportunity(self, listing: Dict) -> bool:
        """Check if property shows distress indicators"""
        description = listing.get("description", "").lower()
        
        distress_keywords = [
            "foreclosure", "short sale", "as-is", "cash only",
            "investor", "handyman", "fixer", "needs work",
            "tlc", "bring offers", "motivated seller"
        ]
        
        return any(keyword in description for keyword in distress_keywords)
    
    def _is_development_opportunity(self, listing: Dict, area: Dict) -> bool:
        """Check if land is suitable for development"""
        # Simple check - could be enhanced with zoning data
        lot_size = listing.get("lot_size", 0)
        price_per_acre = listing.get("price", 0) / max(lot_size, 0.01)
        
        # Look for reasonably priced land
        return lot_size >= 0.25 and price_per_acre < 500000
    
    def _analyze_flip_potential(self, listing: Dict, avg_price_sqft: float) -> Optional[Dict]:
        """Analyze flip potential of a property"""
        purchase_price = listing.get("price", 0)
        sqft = listing.get("sqft", 0)
        
        if purchase_price == 0 or sqft == 0:
            return None
        
        # Estimate ARV (After Repair Value)
        arv = sqft * avg_price_sqft
        
        # Estimate rehab costs (simplified - $30-50/sqft for moderate rehab)
        condition_keywords = ["fixer", "tlc", "needs work", "as-is"]
        description = listing.get("description", "").lower()
        
        if any(keyword in description for keyword in condition_keywords):
            rehab_per_sqft = 50
        else:
            rehab_per_sqft = 30
        
        rehab_costs = sqft * rehab_per_sqft
        
        # Calculate potential profit (70% rule)
        max_offer = (arv * 0.70) - rehab_costs
        holding_costs = purchase_price * 0.05  # 5% for financing, taxes, etc.
        selling_costs = arv * 0.08  # 8% for agent fees, closing
        
        estimated_profit = arv - purchase_price - rehab_costs - holding_costs - selling_costs
        
        if estimated_profit > self.OPPORTUNITY_THRESHOLDS["flip_profit_minimum"]:
            return {
                "property_id": listing.get("id"),
                "address": listing.get("address"),
                "purchase_price": purchase_price,
                "rehab_costs": rehab_costs,
                "after_repair_value": arv,
                "holding_costs": holding_costs,
                "selling_costs": selling_costs,
                "estimated_profit": estimated_profit,
                "roi_percent": (estimated_profit / (purchase_price + rehab_costs)) * 100
            }
        
        return None
    
    def _create_opportunity_alert(self, opportunity: Dict):
        """Create and store an opportunity alert"""
        alert = {
            "id": str(uuid.uuid4()),
            "created_at": datetime.now(),
            "opportunity": opportunity,
            "status": "new",
            "notified": False
        }
        
        self.opportunity_alerts.append(alert)
        
        # Keep only recent alerts (last 100)
        self.opportunity_alerts = self.opportunity_alerts[-100:]
    
    def _rank_opportunities_with_ai(self, opportunities: List[Dict]) -> List[Dict]:
        """Use AI to rank opportunities"""
        if not self.ai_provider or not opportunities:
            return opportunities
        
        try:
            # Prepare opportunity summary
            opp_summary = "\n".join([
                f"{i+1}. {opp['address']} - ${opp['price']:,.0f} - {opp['reason']}"
                for i, opp in enumerate(opportunities)
            ])
            
            prompt = f"""Rank these real estate investment opportunities from best to worst, considering ROI potential, risk, and market timing:

{opp_summary}

For the top 3, provide specific action recommendations."""

            response = self.ai_provider.chat(
                messages=[{"role": "user", "content": prompt}],
                model="good"
            )
            
            # For now, return original order with AI insights
            # In production, would parse AI response to reorder
            return opportunities
            
        except Exception as e:
            self.logger.error(f"AI ranking failed: {str(e)}")
            return opportunities
    
    def get_custom_state(self) -> Dict[str, Any]:
        """Save custom state data"""
        return {
            "watched_areas": [
                {
                    **area,
                    "created_at": area["created_at"].isoformat() if area.get("created_at") else None
                }
                for area in self.watched_areas
            ],
            "market_conditions": {
                area_id: {
                    **conditions,
                    "recorded_at": conditions["recorded_at"].isoformat() 
                        if conditions.get("recorded_at") else None
                }
                for area_id, conditions in self.market_conditions.items()
            }
        }
    
    def load_custom_state(self, state: Dict[str, Any]):
        """Load custom state data"""
        # Restore watched areas
        self.watched_areas = []
        for area in state.get("watched_areas", []):
            area_data = {**area}
            if area.get("created_at"):
                area_data["created_at"] = datetime.fromisoformat(area["created_at"])
            self.watched_areas.append(area_data)
        
        # Restore market conditions
        self.market_conditions = {}
        for area_id, conditions in state.get("market_conditions", {}).items():
            cond_data = {**conditions}
            if conditions.get("recorded_at"):
                cond_data["recorded_at"] = datetime.fromisoformat(conditions["recorded_at"])
            self.market_conditions[area_id] = cond_data