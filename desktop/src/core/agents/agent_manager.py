"""
Agent Manager - Coordinates all autonomous agents
"""

import logging
from typing import Dict, List, Optional, Any
from PySide6.QtCore import QObject, Signal, QTimer

from .base_agent import BaseAgent, AgentStatus, AgentTask
from ..ai_providers import AIProviderManager


class AgentManager(QObject):
    """
    Manages all autonomous agents in the system.
    
    Responsibilities:
    - Starting/stopping agents
    - Injecting dependencies
    - Monitoring agent health
    - Coordinating inter-agent communication
    - Managing agent configurations
    """
    
    # Signals
    agent_status_changed = Signal(str, str)  # agent_name, status
    agent_notification = Signal(str, str, str)  # agent_name, type, message
    agent_error = Signal(str, str)  # agent_name, error
    
    def __init__(self, 
                 ai_provider_manager: AIProviderManager,
                 colonel_client=None,
                 property_service=None,
                 mls_client=None,
                 database=None):
        """
        Initialize the agent manager
        
        Args:
            ai_provider_manager: AI provider manager for agent AI capabilities
            colonel_client: Colonel client for specialized real estate AI
            property_service: Property service for property data
            mls_client: MLS client for real estate data
            database: Database connection
        """
        super().__init__()
        
        self.logger = logging.getLogger("AgentManager")
        self.agents: Dict[str, BaseAgent] = {}
        
        # Services to inject into agents
        self.ai_provider_manager = ai_provider_manager
        self.colonel_client = colonel_client
        self.property_service = property_service
        self.mls_client = mls_client
        self.database = database
        
        # Health check timer
        self.health_check_timer = QTimer()
        self.health_check_timer.timeout.connect(self._check_agent_health)
        self.health_check_timer.start(30000)  # Check every 30 seconds
        
        # Agent configurations
        self.agent_configs = self._load_agent_configs()
    
    def register_agent(self, agent: BaseAgent, auto_start: bool = True):
        """
        Register an agent with the manager
        
        Args:
            agent: The agent to register
            auto_start: Whether to start the agent immediately
        """
        # Inject services
        agent.set_services(
            ai_provider=self.ai_provider_manager,
            colonel_client=self.colonel_client,
            property_service=self.property_service,
            mls_client=self.mls_client,
            database=self.database
        )
        
        # Connect signals
        agent.status_changed.connect(self._on_agent_status_changed)
        agent.notification.connect(self._on_agent_notification)
        agent.error_occurred.connect(self._on_agent_error)
        
        # Store agent
        self.agents[agent.name] = agent
        
        # Start if requested
        if auto_start and self._is_agent_enabled(agent.name):
            self.start_agent(agent.name)
        
        self.logger.info(f"Registered agent: {agent.name}")
    
    def start_agent(self, agent_name: str):
        """Start a specific agent"""
        if agent_name in self.agents:
            agent = self.agents[agent_name]
            if not agent.isRunning():
                agent.start()
                self.logger.info(f"Started agent: {agent_name}")
            else:
                self.logger.warning(f"Agent {agent_name} is already running")
        else:
            self.logger.error(f"Unknown agent: {agent_name}")
    
    def stop_agent(self, agent_name: str):
        """Stop a specific agent"""
        if agent_name in self.agents:
            agent = self.agents[agent_name]
            if agent.isRunning():
                agent.stop()
                self.logger.info(f"Stopped agent: {agent_name}")
            else:
                self.logger.warning(f"Agent {agent_name} is not running")
        else:
            self.logger.error(f"Unknown agent: {agent_name}")
    
    def start_all_agents(self):
        """Start all registered agents that are enabled"""
        for name, agent in self.agents.items():
            if self._is_agent_enabled(name) and not agent.isRunning():
                self.start_agent(name)
    
    def stop_all_agents(self):
        """Stop all running agents"""
        for name, agent in self.agents.items():
            if agent.isRunning():
                self.stop_agent(name)
    
    def get_agent_status(self, agent_name: str) -> Optional[AgentStatus]:
        """Get the status of a specific agent"""
        if agent_name in self.agents:
            return self.agents[agent_name].status
        return None
    
    def get_all_agent_statuses(self) -> Dict[str, str]:
        """Get status of all agents"""
        return {
            name: agent.status.value 
            for name, agent in self.agents.items()
        }
    
    def add_task_to_agent(self, agent_name: str, task: AgentTask):
        """Add a task to a specific agent"""
        if agent_name in self.agents:
            self.agents[agent_name].add_task(task)
            self.logger.info(f"Added task {task.id} to agent {agent_name}")
        else:
            self.logger.error(f"Cannot add task to unknown agent: {agent_name}")
    
    def broadcast_task(self, task_type: str, data: Dict[str, Any]):
        """
        Broadcast a task to all agents that can handle it
        
        Args:
            task_type: Type of task
            data: Task data
        """
        import uuid
        for name, agent in self.agents.items():
            # Check if agent can handle this task type
            if hasattr(agent, 'can_handle_task') and agent.can_handle_task(task_type):
                task = AgentTask(
                    id=str(uuid.uuid4()),
                    type=task_type,
                    data=data
                )
                agent.add_task(task)
                self.logger.info(f"Broadcast task {task_type} to agent {name}")
    
    def _check_agent_health(self):
        """Check health of all agents"""
        for name, agent in self.agents.items():
            if self._is_agent_enabled(name):
                if agent.status == AgentStatus.ERROR:
                    # Try to restart errored agents
                    self.logger.warning(f"Agent {name} in error state, attempting restart")
                    self.stop_agent(name)
                    self.start_agent(name)
                elif agent.status == AgentStatus.STOPPED and agent.isRunning():
                    # Agent thread died unexpectedly
                    self.logger.error(f"Agent {name} thread died unexpectedly")
                    self.agent_error.emit(name, "Agent thread died unexpectedly")
    
    def _on_agent_status_changed(self, agent_name: str, status: str):
        """Handle agent status change"""
        self.agent_status_changed.emit(agent_name, status)
        self.logger.debug(f"Agent {agent_name} status changed to {status}")
    
    def _on_agent_notification(self, agent_name: str, type: str, message: str):
        """Handle agent notification"""
        self.agent_notification.emit(agent_name, type, message)
    
    def _on_agent_error(self, agent_name: str, error: str):
        """Handle agent error"""
        self.agent_error.emit(agent_name, error)
        self.logger.error(f"Agent {agent_name} error: {error}")
    
    def _is_agent_enabled(self, agent_name: str) -> bool:
        """Check if an agent is enabled in configuration"""
        return self.agent_configs.get(agent_name, {}).get("enabled", True)
    
    def _load_agent_configs(self) -> Dict[str, Dict[str, Any]]:
        """Load agent configurations from settings"""
        # TODO: Load from settings manager
        return {
            "Market Monitor": {"enabled": True, "check_interval": 300},  # 5 minutes
            "Lead Scoring": {"enabled": True, "check_interval": 600},     # 10 minutes
            "Property Watcher": {"enabled": True, "check_interval": 300}, # 5 minutes
            "Campaign Optimizer": {"enabled": True, "check_interval": 3600}  # 1 hour
        }
    
    def update_agent_config(self, agent_name: str, config: Dict[str, Any]):
        """Update configuration for a specific agent"""
        self.agent_configs[agent_name] = config
        
        # If agent exists and running, apply config changes
        if agent_name in self.agents:
            agent = self.agents[agent_name]
            if "check_interval" in config:
                agent.check_interval = config["check_interval"]
            
            # Handle enable/disable
            if "enabled" in config:
                if config["enabled"] and not agent.isRunning():
                    self.start_agent(agent_name)
                elif not config["enabled"] and agent.isRunning():
                    self.stop_agent(agent_name)
    
    def cleanup(self):
        """Clean up all agents on shutdown"""
        self.health_check_timer.stop()
        self.stop_all_agents()
        self.logger.info("Agent manager cleanup complete")