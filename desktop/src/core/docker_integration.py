"""
Docker Services Integration for Real Estate Command Center
Manages connections to PostgreSQL and SearXNG containers
"""
import subprocess
import time
import requests
import psycopg2
from psycopg2 import pool
import logging
from typing import Optional, Dict, Any, List
from pathlib import Path

logger = logging.getLogger(__name__)

class DockerServicesManager:
    """Manages Docker services for the Real Estate Command Center"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent.parent
        self.docker_script = self.project_root / "scripts" / "docker-services.sh"
        
        # PostgreSQL configuration
        self.db_config = {
            'host': 'localhost',
            'port': 5433,
            'database': 'realestate_db',
            'user': 'realestate',
            'password': 'commander123'
        }
        
        # SearXNG configuration
        self.searxng_url = "http://localhost:8888"
        
        # Connection pool for PostgreSQL
        self.db_pool = None
        self._init_db_pool()
    
    def _init_db_pool(self):
        """Initialize PostgreSQL connection pool"""
        try:
            self.db_pool = psycopg2.pool.SimpleConnectionPool(
                1, 20, **self.db_config
            )
            logger.info("PostgreSQL connection pool initialized")
        except Exception as e:
            logger.warning(f"Could not initialize DB pool: {e}")
            self.db_pool = None
    
    def check_services_status(self) -> Dict[str, bool]:
        """Check if Docker services are running"""
        status = {
            'postgresql': False,
            'searxng': False,
            'docker': self._check_docker_installed()
        }
        
        if not status['docker']:
            return status
        
        # Check PostgreSQL
        try:
            result = subprocess.run(
                ['docker', 'ps', '--filter', 'name=real_estate_db', '--format', '{{.Status}}'],
                capture_output=True, text=True
            )
            status['postgresql'] = 'Up' in result.stdout
        except:
            pass
        
        # Check SearXNG
        try:
            result = subprocess.run(
                ['docker', 'ps', '--filter', 'name=real_estate_searxng', '--format', '{{.Status}}'],
                capture_output=True, text=True
            )
            status['searxng'] = 'Up' in result.stdout
        except:
            pass
        
        return status
    
    def _check_docker_installed(self) -> bool:
        """Check if Docker is installed"""
        try:
            subprocess.run(['docker', '--version'], capture_output=True, check=True)
            return True
        except:
            return False
    
    def start_services(self) -> bool:
        """Start Docker services"""
        try:
            if not self.docker_script.exists():
                logger.error(f"Docker script not found at {self.docker_script}")
                return False
            
            result = subprocess.run(
                [str(self.docker_script), 'start'],
                capture_output=True, text=True
            )
            
            if result.returncode == 0:
                logger.info("Docker services started successfully")
                # Reinitialize DB pool after starting services
                time.sleep(5)  # Give services time to start
                self._init_db_pool()
                return True
            else:
                logger.error(f"Failed to start services: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error starting Docker services: {e}")
            return False
    
    def stop_services(self) -> bool:
        """Stop Docker services"""
        try:
            result = subprocess.run(
                [str(self.docker_script), 'stop'],
                capture_output=True, text=True
            )
            
            if result.returncode == 0:
                logger.info("Docker services stopped successfully")
                # Close DB pool
                if self.db_pool:
                    self.db_pool.closeall()
                    self.db_pool = None
                return True
            else:
                logger.error(f"Failed to stop services: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error stopping Docker services: {e}")
            return False
    
    def get_db_connection(self):
        """Get a database connection from the pool"""
        if not self.db_pool:
            self._init_db_pool()
        
        if self.db_pool:
            try:
                return self.db_pool.getconn()
            except Exception as e:
                logger.error(f"Error getting DB connection: {e}")
                return None
        return None
    
    def return_db_connection(self, conn):
        """Return a database connection to the pool"""
        if self.db_pool and conn:
            self.db_pool.putconn(conn)
    
    def test_postgresql_connection(self) -> bool:
        """Test PostgreSQL connection"""
        conn = self.get_db_connection()
        if conn:
            try:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    result = cursor.fetchone()
                    self.return_db_connection(conn)
                    return result[0] == 1
            except Exception as e:
                logger.error(f"PostgreSQL connection test failed: {e}")
                self.return_db_connection(conn)
        return False
    
    def test_searxng_connection(self) -> bool:
        """Test SearXNG connection"""
        try:
            response = requests.get(f"{self.searxng_url}/healthz", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def execute_query(self, query: str, params: Optional[tuple] = None) -> Optional[List[tuple]]:
        """Execute a SELECT query and return results"""
        conn = self.get_db_connection()
        if not conn:
            return None
        
        try:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                results = cursor.fetchall()
                self.return_db_connection(conn)
                return results
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            self.return_db_connection(conn)
            return None
    
    def execute_update(self, query: str, params: Optional[tuple] = None) -> bool:
        """Execute an INSERT/UPDATE/DELETE query"""
        conn = self.get_db_connection()
        if not conn:
            return False
        
        try:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                conn.commit()
                self.return_db_connection(conn)
                return True
        except Exception as e:
            logger.error(f"Update execution failed: {e}")
            conn.rollback()
            self.return_db_connection(conn)
            return False
    
    def search_with_searxng(self, query: str, engines: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
        """Search using SearXNG"""
        try:
            params = {
                'q': query,
                'format': 'json',
                'safesearch': 0
            }
            
            if engines:
                params['engines'] = ','.join(engines)
            
            response = requests.get(
                f"{self.searxng_url}/search",
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"SearXNG search failed with status {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"SearXNG search error: {e}")
            return None
    
    def get_service_info(self) -> Dict[str, Any]:
        """Get information about Docker services"""
        status = self.check_services_status()
        
        info = {
            'docker_installed': status['docker'],
            'services': {
                'postgresql': {
                    'running': status['postgresql'],
                    'connection_test': self.test_postgresql_connection() if status['postgresql'] else False,
                    'config': {
                        'host': self.db_config['host'],
                        'port': self.db_config['port'],
                        'database': self.db_config['database']
                    }
                },
                'searxng': {
                    'running': status['searxng'],
                    'connection_test': self.test_searxng_connection() if status['searxng'] else False,
                    'url': self.searxng_url
                }
            }
        }
        
        return info

# Global instance
docker_services = DockerServicesManager()