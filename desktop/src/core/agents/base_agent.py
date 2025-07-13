"""
Base class for all autonomous background agents
"""

import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass, field

from PySide6.QtCore import QThread, Signal, QTimer, QMutex, QMutexLocker


class AgentStatus(Enum):
    """Status of an agent"""
    IDLE = "idle"
    RUNNING = "running"
    SLEEPING = "sleeping"
    ERROR = "error"
    STOPPED = "stopped"


@dataclass
class AgentTask:
    """Represents a task for an agent to perform"""
    id: str
    type: str
    data: Dict[str, Any]
    priority: int = 5
    created_at: datetime = field(default_factory=datetime.now)
    scheduled_for: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3
    
    def should_run_now(self) -> bool:
        """Check if task should run now"""
        if self.scheduled_for is None:
            return True
        return datetime.now() >= self.scheduled_for


class BaseAgent(QThread):
    """
    Base class for all autonomous agents.
    
    Features:
    - Background execution using QThread
    - Task queue management
    - Scheduling and periodic execution
    - Error handling and retry logic
    - State persistence
    - Signal-based communication with UI
    """
    
    # Signals
    status_changed = Signal(str, str)  # agent_name, status
    task_completed = Signal(str, dict)  # agent_name, result
    error_occurred = Signal(str, str)  # agent_name, error_message
    progress_update = Signal(str, int, str)  # agent_name, percentage, message
    notification = Signal(str, str, str)  # agent_name, type, message
    
    def __init__(self, name: str, check_interval: int = 60):
        """
        Initialize the base agent
        
        Args:
            name: Name of the agent
            check_interval: How often to check for tasks (seconds)
        """
        super().__init__()
        self.name = name
        self.check_interval = check_interval
        self.status = AgentStatus.IDLE
        self._running = False
        self._tasks: List[AgentTask] = []
        self._task_mutex = QMutex()
        self._state_file = f"agent_state_{name.lower().replace(' ', '_')}.json"
        
        # Logging
        self.logger = logging.getLogger(f"Agent.{name}")
        
        # AI provider (will be set by agent manager)
        self.ai_provider = None
        self.colonel_client = None
        
        # Services (will be injected)
        self.property_service = None
        self.mls_client = None
        self.database = None
        
        # Load saved state
        self._load_state()
    
    def set_services(self, **services):
        """Inject service dependencies"""
        for key, value in services.items():
            setattr(self, key, value)
    
    def add_task(self, task: AgentTask):
        """Add a task to the queue"""
        with QMutexLocker(self._task_mutex):
            self._tasks.append(task)
            self._tasks.sort(key=lambda t: (t.priority, t.created_at))
    
    def remove_task(self, task_id: str):
        """Remove a task from the queue"""
        with QMutexLocker(self._task_mutex):
            self._tasks = [t for t in self._tasks if t.id != task_id]
    
    def get_pending_tasks(self) -> List[AgentTask]:
        """Get all pending tasks that should run now"""
        with QMutexLocker(self._task_mutex):
            return [t for t in self._tasks if t.should_run_now()]
    
    def run(self):
        """Main agent loop"""
        self._running = True
        self._set_status(AgentStatus.RUNNING)
        self.logger.info(f"{self.name} agent started")
        
        while self._running:
            try:
                # Check for scheduled work
                self._perform_scheduled_check()
                
                # Process pending tasks
                tasks = self.get_pending_tasks()
                for task in tasks:
                    if not self._running:
                        break
                    self._process_task(task)
                
                # Sleep until next check
                if self._running:
                    self._set_status(AgentStatus.SLEEPING)
                    self.msleep(self.check_interval * 1000)
                    
            except Exception as e:
                self.logger.error(f"Error in {self.name} agent: {str(e)}")
                self.error_occurred.emit(self.name, str(e))
                self._set_status(AgentStatus.ERROR)
                self.msleep(5000)  # Wait 5 seconds before retrying
        
        self._set_status(AgentStatus.STOPPED)
        self.logger.info(f"{self.name} agent stopped")
    
    def stop(self):
        """Stop the agent"""
        self._running = False
        self._save_state()
        self.wait()  # Wait for thread to finish
    
    def _set_status(self, status: AgentStatus):
        """Update agent status"""
        self.status = status
        self.status_changed.emit(self.name, status.value)
    
    def _process_task(self, task: AgentTask):
        """Process a single task"""
        try:
            self.logger.info(f"{self.name} processing task {task.id} of type {task.type}")
            self._set_status(AgentStatus.RUNNING)
            
            # Execute the task
            result = self.execute_task(task)
            
            # Remove completed task
            self.remove_task(task.id)
            
            # Emit completion signal
            self.task_completed.emit(self.name, {
                "task_id": task.id,
                "task_type": task.type,
                "result": result
            })
            
        except Exception as e:
            self.logger.error(f"Error processing task {task.id}: {str(e)}")
            task.retry_count += 1
            
            if task.retry_count < task.max_retries:
                # Reschedule with exponential backoff
                task.scheduled_for = datetime.now() + timedelta(
                    seconds=60 * (2 ** task.retry_count)
                )
                self.logger.info(f"Rescheduling task {task.id} for retry #{task.retry_count}")
            else:
                # Max retries reached, remove task
                self.remove_task(task.id)
                self.error_occurred.emit(
                    self.name, 
                    f"Task {task.id} failed after {task.max_retries} retries: {str(e)}"
                )
    
    def _perform_scheduled_check(self):
        """Perform scheduled check - override in subclasses"""
        self.perform_scheduled_check()
    
    def _save_state(self):
        """Save agent state to disk"""
        try:
            state = {
                "name": self.name,
                "status": self.status.value,
                "tasks": [
                    {
                        "id": t.id,
                        "type": t.type,
                        "data": t.data,
                        "priority": t.priority,
                        "created_at": t.created_at.isoformat(),
                        "scheduled_for": t.scheduled_for.isoformat() if t.scheduled_for else None,
                        "retry_count": t.retry_count
                    }
                    for t in self._tasks
                ],
                "custom_state": self.get_custom_state()
            }
            
            with open(self._state_file, 'w') as f:
                json.dump(state, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Failed to save state: {str(e)}")
    
    def _load_state(self):
        """Load agent state from disk"""
        try:
            with open(self._state_file, 'r') as f:
                state = json.load(f)
                
            # Restore tasks
            for task_data in state.get("tasks", []):
                task = AgentTask(
                    id=task_data["id"],
                    type=task_data["type"],
                    data=task_data["data"],
                    priority=task_data["priority"],
                    created_at=datetime.fromisoformat(task_data["created_at"]),
                    scheduled_for=datetime.fromisoformat(task_data["scheduled_for"]) 
                        if task_data["scheduled_for"] else None,
                    retry_count=task_data["retry_count"]
                )
                self._tasks.append(task)
            
            # Restore custom state
            self.load_custom_state(state.get("custom_state", {}))
            
        except FileNotFoundError:
            pass  # No saved state
        except Exception as e:
            self.logger.error(f"Failed to load state: {str(e)}")
    
    @abstractmethod
    def execute_task(self, task: AgentTask) -> Dict[str, Any]:
        """
        Execute a task. Must be implemented by subclasses.
        
        Args:
            task: The task to execute
            
        Returns:
            Dict containing task results
        """
        pass
    
    @abstractmethod
    def perform_scheduled_check(self):
        """
        Perform scheduled check. Called periodically.
        Subclasses should implement their monitoring logic here.
        """
        pass
    
    def get_custom_state(self) -> Dict[str, Any]:
        """Override to save custom state data"""
        return {}
    
    def load_custom_state(self, state: Dict[str, Any]):
        """Override to load custom state data"""
        pass
    
    def emit_notification(self, type: str, message: str):
        """Emit a notification to the UI"""
        self.notification.emit(self.name, type, message)
    
    def update_progress(self, percentage: int, message: str = ""):
        """Update progress for long-running operations"""
        self.progress_update.emit(self.name, percentage, message)