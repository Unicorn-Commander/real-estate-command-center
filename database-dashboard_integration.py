class DashboardWidget(QWidget):
    # ... existing code ...

    async def fetch_metrics(self):
        """Fetch metrics from PostgreSQL database"""
        code = '''
import json
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text

# Connect to database
engine = create_engine("postgresql://realestate:commander123@localhost:5432/realestate_db")

with engine.connect() as conn:
    # Get today's date
    today = datetime.now().date()
    
    # CMAs today
    cmas_today = conn.execute(text(
        "SELECT COUNT(*) FROM cmas WHERE created_at::date = :today"
    ), {"today": today}).scalar()
    
    # New leads today
    new_leads = conn.execute(text(
        "SELECT COUNT(*) FROM leads WHERE created_at::date = :today"
    ), {"today": today}).scalar()
    
    # Showings today
    showings = conn.execute(text(
        "SELECT COUNT(*) FROM events WHERE event_type = 'showing' AND start_time::date = :today"
    ), {"today": today}).scalar()
    
    # Pending tasks
    tasks = conn.execute(text(
        "SELECT COUNT(*) FROM tasks WHERE completed = FALSE AND due_date <= :today"
    ), {"today": today}).scalar()
    
    metrics = {
        "cmas_today": cmas_today,
        "new_leads": new_leads,
        "showings": showings,
        "tasks": tasks
    }
    
    print(json.dumps(metrics))
'''
        
        result = await self.colonel.execute_python(code)
        if result.get("output"):
            try:
                metrics = json.loads(result["output"])
                self.cma_card.update_value(metrics["cmas_today"])
                self.leads_card.update_value(metrics["new_leads"])
                self.showings_card.update_value(metrics["showings"])
                self.tasks_card.update_value(metrics["tasks"])
            except Exception as e:
                print(f"Error updating metrics: {e}")