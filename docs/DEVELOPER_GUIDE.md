# 🛠️ Developer Guide
## Real Estate Command Center Development Documentation

### Table of Contents
1. [Development Environment Setup](#development-environment-setup)
2. [Architecture Overview](#architecture-overview)
3. [Code Organization](#code-organization)
4. [Adding New Features](#adding-new-features)
5. [API Integration](#api-integration)
6. [Testing Guidelines](#testing-guidelines)
7. [Deployment](#deployment)

---

## Development Environment Setup

### Prerequisites
- **Ubuntu/Debian Linux** development environment
- **Python 3.11+** with development headers
- **Git** for version control
- **Code Editor**: VSCode, PyCharm, or similar with Python support

### Development Dependencies

#### Install Development Tools
```bash
# Core development tools
sudo apt install -y \
  git \
  python3-dev \
  python3-pip \
  python3-venv \
  build-essential

# Qt development tools
sudo apt install -y \
  qt6-base-dev \
  qt6-tools-dev \
  qt6-tools-dev-tools

# Documentation tools
sudo apt install -y \
  python3-sphinx \
  python3-sphinx-rtd-theme
```

#### IDE Configuration

**VSCode Extensions**:
```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.pylint",
    "ms-python.black-formatter",
    "ms-python.mypy-type-checker",
    "redhat.vscode-xml",
    "ms-vscode.vscode-json"
  ]
}
```

**PyCharm Setup**:
- Configure Python interpreter: `/usr/bin/python3`
- Enable PEP 8 code style
- Set up Qt Designer integration

### Code Style and Standards

#### Python Standards
- **PEP 8**: Python code style guide
- **Type Hints**: Use type annotations for all public APIs
- **Docstrings**: Google-style docstrings for all modules, classes, and functions
- **Black**: Code formatting (line length: 88 characters)

#### Qt/PySide6 Conventions
- **Naming**: Use camelCase for Qt-related methods, snake_case for Python
- **Signals**: Use descriptive signal names with past tense (`item_selected`, `data_changed`)
- **Slots**: Prefix slot methods with `on_` or `handle_`
- **Resources**: Use Qt resource system for icons and assets

---

## Architecture Overview

### Application Structure

```
real-estate-command-center/
├── desktop/                     # Main application
│   ├── src/
│   │   ├── main.py             # Application entry point
│   │   ├── core/               # Business logic and utilities
│   │   │   ├── colonel_client.py    # API client interface
│   │   │   ├── plasma_integration.py # KDE integration
│   │   │   └── cma_reports.py       # Report generation engine
│   │   └── ui/                 # User interface components
│   │       ├── main_window.py       # Main application window
│   │       ├── cma_tab.py          # CMA workflow interface
│   │       ├── photo_manager.py    # Photo management widget
│   │       ├── map_widget.py       # Interactive mapping
│   │       └── ...                 # Other UI components
│   ├── resources/              # Assets (icons, themes, etc.)
│   ├── settings.json           # User configuration
│   └── cma_photos/            # Photo storage
├── docs/                      # Documentation
├── tests/                     # Test suites
└── scripts/                   # Utility scripts
```

### Design Patterns

#### Model-View-Controller (MVC)
- **Models**: Data structures in `core/` modules
- **Views**: UI components in `ui/` modules
- **Controllers**: Main window and tab controllers coordinate between models and views

#### Observer Pattern
- **Qt Signals/Slots**: Primary communication mechanism
- **Custom Signals**: For cross-component communication
- **Event Handling**: Standard Qt event system

#### Factory Pattern
- **Widget Creation**: Factories for complex UI components
- **Report Generation**: Factory for different report types
- **Data Sources**: Factory for different API integrations

### Threading Model

#### Main Thread
- **UI Operations**: All Qt widgets and painting
- **User Interaction**: Event handling and responses
- **Light Processing**: Quick data operations

#### Background Threads
- **Network Operations**: API calls, geocoding, map tile loading
- **File I/O**: Photo processing, report generation
- **Heavy Computation**: Chart generation, data analysis

---

## Code Organization

### Core Modules

#### `core/colonel_client.py`
**Purpose**: Abstract API client interface

```python
class ColonelClient:
    """Abstract interface for backend API communication."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
    
    def ping(self) -> bool:
        """Test API connectivity."""
        pass
    
    def search_properties(self, criteria: Dict) -> List[Property]:
        """Search MLS for properties matching criteria."""
        pass
```

**Extension Points**:
- Add MLS provider implementations
- Implement authentication mechanisms
- Add caching and retry logic

#### `core/cma_reports.py`
**Purpose**: Professional report generation

```python
class CMAChartGenerator:
    """Generate professional charts for CMA reports."""
    
    def create_price_trend_chart(self, data: List[Dict]) -> str:
        """Create price trend visualization."""
        pass

class CMAPDFGenerator:
    """Generate professional PDF reports."""
    
    def generate_cma_report(self, cma_data: Dict, output_path: str) -> str:
        """Create complete PDF report."""
        pass
```

### UI Components

#### Base Widget Pattern
```python
class BaseTabWidget(QWidget):
    """Base class for all tab widgets."""
    
    # Standard signals
    data_changed = Signal()
    refresh_requested = Signal()
    
    def __init__(self, colonel_client, parent=None):
        super().__init__(parent)
        self.colonel_client = colonel_client
        self.init_ui()
        self.setup_signals()
    
    def init_ui(self):
        """Initialize UI components."""
        raise NotImplementedError
    
    def setup_signals(self):
        """Connect signals and slots."""
        pass
    
    def load_data(self):
        """Load/refresh data from backend."""
        pass
```

#### Custom Widgets
- **PhotoManagerWidget**: Drag-and-drop photo handling
- **PropertyMapWidget**: Interactive mapping with Folium
- **CMATab**: Multi-step wizard workflow

### Data Models

#### Property Data Structure
```python
@dataclass
class Property:
    """Represents a real estate property."""
    address: str
    property_type: str
    bedrooms: int
    bathrooms: float
    sqft: int
    lot_size: float
    year_built: int
    features: List[str]
    photos: List[str]
    location: Optional[Tuple[float, float]] = None
```

#### CMA Data Structure
```python
@dataclass
class CMAData:
    """Complete CMA analysis data."""
    subject_property: Property
    comparables: List[Property]
    analysis_date: datetime
    value_estimates: Dict[str, int]
    market_analysis: str
    photos: List[Dict]
    map_data: Dict
```

---

## Adding New Features

### Creating a New Tab

#### 1. Create Tab Class
```python
# ui/new_feature_tab.py
from ui.base_tab import BaseTabWidget

class NewFeatureTab(BaseTabWidget):
    """New feature implementation."""
    
    def init_ui(self):
        layout = QVBoxLayout()
        # Add UI components
        self.setLayout(layout)
    
    def load_data(self):
        # Implement data loading
        pass
```

#### 2. Register in Main Window
```python
# ui/main_window.py
from ui.new_feature_tab import NewFeatureTab

class MainWindow(QMainWindow):
    def __init__(self, colonel_client, theme, config_path, parent=None):
        # ... existing code ...
        
        # Add new tab
        self.new_feature_tab = NewFeatureTab(self.colonel_client)
        self.tabs.addTab(self.new_feature_tab, 'New Feature')
```

#### 3. Add to Refresh Cycle
```python
def refresh_all(self):
    for tab in (self.leads_tab, self.marketing_tab, self.cma_tab, 
                self.new_feature_tab, self.database_tab):
        if hasattr(tab, 'load_data'):
            tab.load_data()
```

### Extending CMA Functionality

#### Adding New Chart Types
```python
# core/cma_reports.py
class CMAChartGenerator:
    def create_new_chart_type(self, data: List[Dict], save_path: str = None) -> str:
        """Create a new type of chart."""
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Chart implementation
        # ...
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            plt.close()
            return save_path
        else:
            # Return base64 for embedding
            buffer = BytesIO()
            plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.getvalue()).decode()
            plt.close()
            return f"data:image/png;base64,{image_base64}"
```

#### Adding New Report Sections
```python
# core/cma_reports.py
class CMAPDFGenerator:
    def _create_new_section(self, cma_data: Dict) -> List:
        """Create a new report section."""
        content = []
        content.append(Paragraph("NEW SECTION", self.styles['SectionHeader']))
        
        # Add section content
        # ...
        
        return content
```

### Custom Widgets

#### Widget Development Template
```python
class CustomWidget(QWidget):
    """Template for custom widget development."""
    
    # Define custom signals
    value_changed = Signal(object)
    action_requested = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.setup_signals()
    
    def init_ui(self):
        """Initialize user interface."""
        layout = QVBoxLayout()
        # Add components
        self.setLayout(layout)
    
    def setup_signals(self):
        """Connect internal signals."""
        pass
    
    def set_data(self, data):
        """Update widget with new data."""
        pass
    
    def get_data(self):
        """Retrieve current widget data."""
        pass
```

---

## API Integration

### Backend Interface Design

#### RESTful API Client
```python
class RESTColonelClient(ColonelClient):
    """REST API implementation."""
    
    def __init__(self, base_url: str, api_key: str = None):
        super().__init__(base_url)
        self.api_key = api_key
        self.session = requests.Session()
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make authenticated API request."""
        headers = kwargs.get('headers', {})
        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'
        
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        return self.session.request(method, url, headers=headers, **kwargs)
    
    def search_properties(self, criteria: Dict) -> List[Property]:
        """Search for properties via API."""
        response = self._make_request('POST', '/api/properties/search', json=criteria)
        response.raise_for_status()
        
        properties = []
        for item in response.json()['results']:
            properties.append(Property(**item))
        
        return properties
```

#### MLS Integration
```python
class MLSClient(ColonelClient):
    """MLS API integration."""
    
    def __init__(self, mls_provider: str, credentials: Dict):
        self.provider = mls_provider
        self.credentials = credentials
        # Initialize provider-specific client
    
    def search_comparables(self, 
                          location: Tuple[float, float], 
                          radius_miles: float,
                          criteria: Dict) -> List[Property]:
        """Search MLS for comparable properties."""
        # Provider-specific implementation
        pass
```

### External Service Integration

#### Geocoding Services
```python
class GeocodingService:
    """Abstract geocoding interface."""
    
    def geocode(self, address: str) -> Optional[Tuple[float, float]]:
        """Convert address to coordinates."""
        raise NotImplementedError
    
    def reverse_geocode(self, lat: float, lng: float) -> Optional[str]:
        """Convert coordinates to address."""
        raise NotImplementedError

class GoogleGeocodingService(GeocodingService):
    """Google Maps geocoding implementation."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    def geocode(self, address: str) -> Optional[Tuple[float, float]]:
        # Google Maps API implementation
        pass
```

### Asynchronous Operations

#### Background Task Manager
```python
class TaskManager(QObject):
    """Manage background tasks and threading."""
    
    task_completed = Signal(str, object)  # task_id, result
    task_failed = Signal(str, str)        # task_id, error
    
    def __init__(self):
        super().__init__()
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.active_tasks = {}
    
    def submit_task(self, task_id: str, func, *args, **kwargs):
        """Submit a task for background execution."""
        future = self.executor.submit(func, *args, **kwargs)
        self.active_tasks[task_id] = future
        
        # Handle completion
        future.add_done_callback(lambda f: self._task_done(task_id, f))
    
    def _task_done(self, task_id: str, future):
        """Handle task completion."""
        try:
            result = future.result()
            self.task_completed.emit(task_id, result)
        except Exception as e:
            self.task_failed.emit(task_id, str(e))
        finally:
            self.active_tasks.pop(task_id, None)
```

---

## Testing Guidelines

### Test Structure

```
tests/
├── unit/                    # Unit tests
│   ├── test_core/
│   │   ├── test_colonel_client.py
│   │   └── test_cma_reports.py
│   └── test_ui/
│       ├── test_main_window.py
│       └── test_cma_tab.py
├── integration/             # Integration tests
│   ├── test_api_integration.py
│   └── test_workflow.py
├── fixtures/               # Test data
│   ├── sample_properties.json
│   └── test_images/
└── conftest.py             # Pytest configuration
```

### Unit Testing

#### Testing Qt Widgets
```python
import pytest
from PySide6.QtWidgets import QApplication
from ui.cma_tab import CMATab

@pytest.fixture
def qt_app():
    """Fixture for Qt application."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app

@pytest.fixture
def mock_colonel_client():
    """Mock API client for testing."""
    class MockClient:
        def ping(self):
            return True
        
        def search_properties(self, criteria):
            return []
    
    return MockClient()

def test_cma_tab_initialization(qt_app, mock_colonel_client):
    """Test CMA tab initialization."""
    tab = CMATab(mock_colonel_client)
    assert tab.cma_tabs.count() == 5
    assert tab.address_edit is not None
```

#### Testing Business Logic
```python
# tests/unit/test_core/test_cma_reports.py
import pytest
from core.cma_reports import CMAChartGenerator

def test_price_trend_chart_generation():
    """Test price trend chart generation."""
    generator = CMAChartGenerator()
    
    sample_data = [
        {'date': '2024-01-01', 'price': 450000},
        {'date': '2024-02-01', 'price': 455000},
        {'date': '2024-03-01', 'price': 460000},
    ]
    
    result = generator.create_price_trend_chart(sample_data)
    assert result.startswith('data:image/png;base64,')
```

### Integration Testing

#### API Integration Tests
```python
# tests/integration/test_api_integration.py
import pytest
from core.colonel_client import ColonelClient

@pytest.mark.integration
def test_api_connectivity():
    """Test real API connectivity."""
    client = ColonelClient("http://localhost:8000")
    result = client.ping()
    assert result is True

@pytest.mark.slow
def test_property_search():
    """Test property search functionality."""
    client = ColonelClient("http://localhost:8000")
    criteria = {'location': 'San Francisco, CA', 'radius': 1.0}
    results = client.search_properties(criteria)
    assert isinstance(results, list)
```

#### Workflow Testing
```python
# tests/integration/test_workflow.py
def test_complete_cma_workflow(qt_app, mock_colonel_client):
    """Test complete CMA creation workflow."""
    from ui.main_window import MainWindow
    
    window = MainWindow(mock_colonel_client, 'dark_amber.xml', 'test_settings.json')
    
    # Navigate to CMA tab
    cma_tab = window.cma_tab
    
    # Fill in property details
    cma_tab.address_edit.setText("123 Test St, Test City, CA")
    cma_tab.bedrooms_spin.setValue(3)
    cma_tab.bathrooms_spin.setValue(2)
    
    # Test form data collection
    data = cma_tab.collect_form_data()
    assert data['bedrooms'] == 3
    assert data['bathrooms'] == 2
```

### Running Tests

#### Pytest Configuration
```python
# conftest.py
import pytest
import os
import sys

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'desktop', 'src'))

def pytest_addoption(parser):
    parser.addoption("--run-slow", action="store_true", 
                     default=False, help="run slow tests")
    parser.addoption("--run-integration", action="store_true",
                     default=False, help="run integration tests")

def pytest_configure(config):
    config.addinivalue_line("markers", "slow: marks tests as slow")
    config.addinivalue_line("markers", "integration: marks tests as integration")

def pytest_collection_modifyitems(config, items):
    if not config.getoption("--run-slow"):
        skip_slow = pytest.mark.skip(reason="need --run-slow option to run")
        for item in items:
            if "slow" in item.keywords:
                item.add_marker(skip_slow)
    
    if not config.getoption("--run-integration"):
        skip_integration = pytest.mark.skip(reason="need --run-integration option to run")
        for item in items:
            if "integration" in item.keywords:
                item.add_marker(skip_integration)
```

#### Test Commands
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test categories
pytest -m "not slow"                # Skip slow tests
pytest -m integration --run-integration  # Run integration tests
pytest tests/unit/                  # Run only unit tests

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/unit/test_core/test_cma_reports.py -v
```

---

## Deployment

### Packaging

#### Creating Distribution Package
```bash
# Create distribution directory
mkdir -p dist/real-estate-command-center

# Copy application files
cp -r desktop/src dist/real-estate-command-center/
cp -r desktop/resources dist/real-estate-command-center/ 2>/dev/null || true
cp README.md dist/real-estate-command-center/
cp docs/INSTALLATION.md dist/real-estate-command-center/

# Create launcher script
cat > dist/real-estate-command-center/launch.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
/usr/bin/python3 src/main.py
EOF
chmod +x dist/real-estate-command-center/launch.sh

# Create archive
cd dist
tar czf real-estate-command-center.tar.gz real-estate-command-center/
```

#### Debian Package Creation
```bash
# Create package structure
mkdir -p package/real-estate-command-center/DEBIAN
mkdir -p package/real-estate-command-center/opt/real-estate-command-center
mkdir -p package/real-estate-command-center/usr/share/applications

# Control file
cat > package/real-estate-command-center/DEBIAN/control << EOF
Package: real-estate-command-center
Version: 1.0.0
Section: office
Priority: optional
Architecture: all
Depends: python3-pyside6.qtcore, python3-pyside6.qtgui, python3-pyside6.qtwidgets, python3-matplotlib, python3-reportlab, python3-folium
Maintainer: Developer <dev@example.com>
Description: Professional Real Estate CMA Platform
 A comprehensive real estate management platform with industry-leading
 Comparative Market Analysis capabilities.
EOF

# Copy files
cp -r desktop/src package/real-estate-command-center/opt/real-estate-command-center/

# Desktop entry
cat > package/real-estate-command-center/usr/share/applications/real-estate-command-center.desktop << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Real Estate Command Center
Comment=Professional CMA and Property Management Platform
Exec=/usr/bin/python3 /opt/real-estate-command-center/src/main.py
Icon=applications-office
Terminal=false
Categories=Office;Finance;
EOF

# Build package
dpkg-deb --build package/real-estate-command-center
```

### Docker Deployment (Future)

#### Dockerfile
```dockerfile
FROM ubuntu:22.04

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pyside6.qtcore \
    python3-pyside6.qtgui \
    python3-pyside6.qtwidgets \
    python3-matplotlib \
    python3-reportlab \
    python3-folium \
    && rm -rf /var/lib/apt/lists/*

# Copy application
COPY desktop/src /app/
WORKDIR /app

# Create non-root user
RUN useradd -m -u 1000 realtor
USER realtor

# Entry point
CMD ["python3", "main.py"]
```

### Continuous Integration

#### GitHub Actions Workflow
```yaml
# .github/workflows/test.yml
name: Test Application

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Install system dependencies
      run: |
        sudo apt-get update
        sudo apt-get install -y \
          python3-pyside6.qtcore \
          python3-pyside6.qtgui \
          python3-pyside6.qtwidgets \
          python3-matplotlib \
          python3-reportlab \
          python3-folium \
          python3-pytest \
          python3-pytest-cov \
          xvfb
    
    - name: Run tests
      run: |
        cd desktop
        xvfb-run -a python3 -m pytest tests/ --cov=src
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

---

## Contributing Guidelines

### Code Contribution Process

1. **Fork Repository**: Create personal fork
2. **Create Branch**: Feature branch from main
3. **Implement Changes**: Follow coding standards
4. **Add Tests**: Ensure test coverage
5. **Update Documentation**: Keep docs current
6. **Submit PR**: Pull request with clear description

### Code Review Standards

- **Functionality**: Feature works as designed
- **Testing**: Adequate test coverage
- **Documentation**: Code is well-documented
- **Standards**: Follows project conventions
- **Performance**: No significant performance regression

---

*Developer Guide - Last updated: 2025-06-26*