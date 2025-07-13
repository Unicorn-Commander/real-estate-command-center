"""
Market Monitor Agent - Tracks real estate market changes 24/7
"""

import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from .base_agent import BaseAgent, AgentTask


class MarketMonitorAgent(BaseAgent):
    """
    Monitors real estate markets for significant changes:
    - Price changes in tracked properties
    - New listings matching saved searches
    - Market trend shifts
    - Inventory level changes
    - Price reduction alerts
    """
    
    def __init__(self):
        super().__init__(
            name="Market Monitor",
            check_interval=300  # Check every 5 minutes
        )
        
        # Tracking data
        self.tracked_properties: Dict[str, Dict[str, Any]] = {}
        self.saved_searches: List[Dict[str, Any]] = []
        self.market_baselines: Dict[str, Dict[str, Any]] = {}
        self.last_full_scan = None
    
    def execute_task(self, task: AgentTask) -> Dict[str, Any]:
        """Execute a market monitoring task"""
        task_handlers = {
            "track_property": self._track_property,
            "untrack_property": self._untrack_property,
            "add_search": self._add_saved_search,
            "remove_search": self._remove_saved_search,
            "check_property_changes": self._check_property_changes,
            "scan_new_listings": self._scan_new_listings,
            "analyze_market_trends": self._analyze_market_trends
        }
        
        handler = task_handlers.get(task.type)
        if handler:
            return handler(task.data)
        else:
            raise ValueError(f"Unknown task type: {task.type}")
    
    def perform_scheduled_check(self):
        """Perform scheduled market monitoring"""
        current_time = datetime.now()
        
        # Check tracked properties every cycle
        if self.tracked_properties:
            self.add_task(AgentTask(
                id=str(uuid.uuid4()),
                type="check_property_changes",
                data={},
                priority=3
            ))
        
        # Scan for new listings every cycle
        if self.saved_searches:
            self.add_task(AgentTask(
                id=str(uuid.uuid4()),
                type="scan_new_listings",
                data={},
                priority=4
            ))
        
        # Full market analysis every hour
        if (self.last_full_scan is None or 
            current_time - self.last_full_scan > timedelta(hours=1)):
            self.add_task(AgentTask(
                id=str(uuid.uuid4()),
                type="analyze_market_trends",
                data={},
                priority=5
            ))
            self.last_full_scan = current_time
    
    def _track_property(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Start tracking a property for changes"""
        property_id = data.get("property_id")
        address = data.get("address")
        
        if not property_id:
            raise ValueError("Property ID required for tracking")
        
        # Get current property data
        if self.property_service:
            property_data = self.property_service.get_property_details(address)
            if property_data:
                self.tracked_properties[property_id] = {
                    "address": address,
                    "initial_data": property_data,
                    "last_checked": datetime.now(),
                    "changes": []
                }
                
                self.emit_notification(
                    "info",
                    f"Now tracking property: {address}"
                )
                
                return {"status": "tracking", "property_id": property_id}
        
        return {"status": "error", "message": "Could not fetch property data"}
    
    def _untrack_property(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Stop tracking a property"""
        property_id = data.get("property_id")
        
        if property_id in self.tracked_properties:
            address = self.tracked_properties[property_id]["address"]
            del self.tracked_properties[property_id]
            
            self.emit_notification(
                "info",
                f"Stopped tracking property: {address}"
            )
            
            return {"status": "untracked", "property_id": property_id}
        
        return {"status": "error", "message": "Property not being tracked"}
    
    def _add_saved_search(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Add a saved search to monitor"""
        search_criteria = {
            "id": str(uuid.uuid4()),
            "name": data.get("name", "Untitled Search"),
            "criteria": data.get("criteria", {}),
            "created_at": datetime.now(),
            "last_checked": None,
            "found_properties": []
        }
        
        self.saved_searches.append(search_criteria)
        
        self.emit_notification(
            "info",
            f"Added saved search: {search_criteria['name']}"
        )
        
        return {"status": "added", "search_id": search_criteria["id"]}
    
    def _remove_saved_search(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Remove a saved search"""
        search_id = data.get("search_id")
        
        self.saved_searches = [
            s for s in self.saved_searches if s["id"] != search_id
        ]
        
        return {"status": "removed", "search_id": search_id}
    
    def _check_property_changes(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Check all tracked properties for changes"""
        changes_found = []
        
        for property_id, tracking_data in self.tracked_properties.items():
            try:
                address = tracking_data["address"]
                self.update_progress(
                    len(changes_found) * 100 // len(self.tracked_properties),
                    f"Checking {address}"
                )
                
                # Get current data
                current_data = self.property_service.get_property_details(address)
                if not current_data:
                    continue
                
                # Compare with tracked data
                initial_data = tracking_data["initial_data"]
                changes = self._compare_property_data(initial_data, current_data)
                
                if changes:
                    # Record changes
                    tracking_data["changes"].append({
                        "timestamp": datetime.now(),
                        "changes": changes
                    })
                    tracking_data["last_checked"] = datetime.now()
                    
                    # Notify about significant changes
                    for change in changes:
                        if change["type"] == "price_change":
                            old_price = change["old_value"]
                            new_price = change["new_value"]
                            percent_change = ((new_price - old_price) / old_price) * 100
                            
                            notification_type = "warning" if percent_change < 0 else "info"
                            self.emit_notification(
                                notification_type,
                                f"Price {'decreased' if percent_change < 0 else 'increased'} "
                                f"by {abs(percent_change):.1f}% for {address}: "
                                f"${old_price:,.0f} → ${new_price:,.0f}"
                            )
                            
                            changes_found.append({
                                "property_id": property_id,
                                "address": address,
                                "change": change
                            })
                    
                    # Use AI to analyze the changes
                    if self.ai_provider:
                        analysis = self._analyze_property_changes_with_ai(
                            address, initial_data, current_data, changes
                        )
                        if analysis:
                            self.emit_notification("info", analysis)
                
            except Exception as e:
                self.logger.error(f"Error checking property {property_id}: {str(e)}")
        
        return {
            "status": "completed",
            "properties_checked": len(self.tracked_properties),
            "changes_found": len(changes_found),
            "changes": changes_found
        }
    
    def _scan_new_listings(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Scan for new listings matching saved searches"""
        new_listings_found = 0
        
        for search in self.saved_searches:
            try:
                self.update_progress(
                    self.saved_searches.index(search) * 100 // len(self.saved_searches),
                    f"Scanning: {search['name']}"
                )
                
                # Search for properties
                if self.mls_client:
                    results = self.mls_client.search_properties(**search["criteria"])
                    
                    if results and results.get("listings"):
                        # Find new listings
                        previous_ids = set(search.get("found_properties", []))
                        current_ids = {p["id"] for p in results["listings"]}
                        new_ids = current_ids - previous_ids
                        
                        if new_ids:
                            new_listings = [
                                p for p in results["listings"] 
                                if p["id"] in new_ids
                            ]
                            
                            # Update found properties
                            search["found_properties"] = list(current_ids)
                            search["last_checked"] = datetime.now()
                            
                            # Notify about new listings
                            for listing in new_listings[:5]:  # Limit notifications
                                self.emit_notification(
                                    "success",
                                    f"New listing for '{search['name']}': "
                                    f"{listing.get('address', 'Unknown')} - "
                                    f"${listing.get('price', 0):,.0f}"
                                )
                            
                            new_listings_found += len(new_ids)
                            
                            # AI analysis of new listings
                            if self.ai_provider and new_listings:
                                analysis = self._analyze_new_listings_with_ai(
                                    search["name"], new_listings
                                )
                                if analysis:
                                    self.emit_notification("info", analysis)
                
            except Exception as e:
                self.logger.error(f"Error scanning search {search['id']}: {str(e)}")
        
        return {
            "status": "completed",
            "searches_checked": len(self.saved_searches),
            "new_listings_found": new_listings_found
        }
    
    def _analyze_market_trends(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze overall market trends"""
        try:
            # Get market statistics for tracked areas
            areas_analyzed = set()
            trend_data = []
            
            # Analyze areas from tracked properties
            for tracking in self.tracked_properties.values():
                area = tracking["initial_data"].get("city", "Unknown")
                if area not in areas_analyzed and self.mls_client:
                    stats = self.mls_client.get_market_statistics(city=area)
                    if stats:
                        trend_data.append({
                            "area": area,
                            "stats": stats,
                            "timestamp": datetime.now()
                        })
                        areas_analyzed.add(area)
            
            # Compare with baselines
            significant_changes = []
            for trend in trend_data:
                area = trend["area"]
                current_stats = trend["stats"]
                
                if area in self.market_baselines:
                    baseline = self.market_baselines[area]
                    changes = self._compare_market_stats(baseline, current_stats)
                    
                    if changes:
                        significant_changes.append({
                            "area": area,
                            "changes": changes
                        })
                
                # Update baseline
                self.market_baselines[area] = current_stats
            
            # AI analysis of market trends
            if self.ai_provider and significant_changes:
                prompt = f"""Analyze these real estate market changes and provide insights:

{significant_changes}

Focus on:
1. What these changes mean for buyers and sellers
2. Potential opportunities or risks
3. Predictions for the next 30 days

Keep response under 200 words."""

                response = self.ai_provider.chat(
                    messages=[{"role": "user", "content": prompt}],
                    model="good"
                )
                
                if response:
                    self.emit_notification(
                        "info",
                        f"Market Analysis: {response}"
                    )
            
            return {
                "status": "completed",
                "areas_analyzed": len(areas_analyzed),
                "significant_changes": len(significant_changes)
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing market trends: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    def _compare_property_data(self, old_data: Dict, new_data: Dict) -> List[Dict]:
        """Compare property data and return list of changes"""
        changes = []
        
        # Price changes
        if old_data.get("price") != new_data.get("price"):
            changes.append({
                "type": "price_change",
                "field": "price",
                "old_value": old_data.get("price", 0),
                "new_value": new_data.get("price", 0)
            })
        
        # Status changes
        if old_data.get("status") != new_data.get("status"):
            changes.append({
                "type": "status_change",
                "field": "status",
                "old_value": old_data.get("status"),
                "new_value": new_data.get("status")
            })
        
        # Days on market
        old_dom = old_data.get("days_on_market", 0)
        new_dom = new_data.get("days_on_market", 0)
        if new_dom > old_dom + 7:  # Significant increase
            changes.append({
                "type": "dom_increase",
                "field": "days_on_market",
                "old_value": old_dom,
                "new_value": new_dom
            })
        
        return changes
    
    def _compare_market_stats(self, old_stats: Dict, new_stats: Dict) -> List[Dict]:
        """Compare market statistics and return significant changes"""
        changes = []
        threshold = 0.05  # 5% change threshold
        
        metrics = [
            ("median_price", "Median Price"),
            ("avg_price_sqft", "Price per Sq Ft"),
            ("inventory", "Inventory"),
            ("avg_days_on_market", "Avg Days on Market")
        ]
        
        for metric, label in metrics:
            old_val = old_stats.get(metric, 0)
            new_val = new_stats.get(metric, 0)
            
            if old_val > 0:
                percent_change = (new_val - old_val) / old_val
                
                if abs(percent_change) >= threshold:
                    changes.append({
                        "metric": label,
                        "old_value": old_val,
                        "new_value": new_val,
                        "percent_change": percent_change * 100
                    })
        
        return changes
    
    def _analyze_property_changes_with_ai(self, address: str, 
                                         old_data: Dict, 
                                         new_data: Dict, 
                                         changes: List[Dict]) -> Optional[str]:
        """Use AI to analyze property changes"""
        if not self.ai_provider:
            return None
        
        try:
            prompt = f"""Analyze this property change for: {address}

Changes detected: {changes}
Old data: Price=${old_data.get('price', 0):,.0f}, Status={old_data.get('status')}, DOM={old_data.get('days_on_market')}
New data: Price=${new_data.get('price', 0):,.0f}, Status={new_data.get('status')}, DOM={new_data.get('days_on_market')}

Provide a brief (1-2 sentence) insight about what this means for potential buyers/sellers."""

            response = self.ai_provider.chat(
                messages=[{"role": "user", "content": prompt}],
                model="cheap"
            )
            
            return response
            
        except Exception as e:
            self.logger.error(f"AI analysis failed: {str(e)}")
            return None
    
    def _analyze_new_listings_with_ai(self, search_name: str, 
                                     listings: List[Dict]) -> Optional[str]:
        """Use AI to analyze new listings"""
        if not self.ai_provider:
            return None
        
        try:
            # Summarize listings
            summary = f"Found {len(listings)} new listings for '{search_name}':\n"
            for listing in listings[:3]:  # Top 3
                summary += f"- {listing.get('address')}: ${listing.get('price', 0):,.0f}\n"
            
            prompt = f"""{summary}

Provide a brief insight about these new listings and any opportunities they might represent."""

            response = self.ai_provider.chat(
                messages=[{"role": "user", "content": prompt}],
                model="cheap"
            )
            
            return response
            
        except Exception as e:
            self.logger.error(f"AI analysis failed: {str(e)}")
            return None
    
    def get_custom_state(self) -> Dict[str, Any]:
        """Save custom state data"""
        return {
            "tracked_properties": self.tracked_properties,
            "saved_searches": [
                {
                    **s,
                    "created_at": s["created_at"].isoformat() if s.get("created_at") else None,
                    "last_checked": s["last_checked"].isoformat() if s.get("last_checked") else None
                }
                for s in self.saved_searches
            ],
            "market_baselines": self.market_baselines,
            "last_full_scan": self.last_full_scan.isoformat() if self.last_full_scan else None
        }
    
    def load_custom_state(self, state: Dict[str, Any]):
        """Load custom state data"""
        self.tracked_properties = state.get("tracked_properties", {})
        
        # Restore saved searches with datetime conversion
        self.saved_searches = []
        for s in state.get("saved_searches", []):
            search = {**s}
            if s.get("created_at"):
                search["created_at"] = datetime.fromisoformat(s["created_at"])
            if s.get("last_checked"):
                search["last_checked"] = datetime.fromisoformat(s["last_checked"])
            self.saved_searches.append(search)
        
        self.market_baselines = state.get("market_baselines", {})
        
        if state.get("last_full_scan"):
            self.last_full_scan = datetime.fromisoformat(state["last_full_scan"])