# Equal-Weighted Stock Index Service

A comprehensive backend service for tracking and managing a custom equal-weighted stock index comprising the top US stocks by daily market capitalization.

## 🎯 Features

- **Dynamic Index Construction**: Build equal-weighted indices from top stocks by market cap
- **Historical Performance Tracking**: Calculate and store daily returns and cumulative performance
- **Composition Change Detection**: Track when stocks enter or exit the index
- **Data Export**: Export comprehensive data to Excel files with multiple sheets
- **Caching**: Redis-based caching for improved API performance
- **Multiple Data Sources**: Support for Yahoo Finance and Alpha Vantage APIs
- **Containerization**: Full Docker support with docker-compose
- **Modern Web UI**: Beautiful Streamlit interface with interactive charts and real-time data

## 🏗️ Architecture

```
stock-index-app/
├── app/backend/           # FastAPI application
│   ├── main.py           # FastAPI app entry point
│   ├── routers/          # API route definitions
│   ├── services/         # Business logic layer
│   ├── db/              # Database operations
│   ├── models/          # Pydantic data models
│   └── schemas/         # API request/response schemas
├── src/                 # Core utilities
│   ├── config.py        # Configuration management
│   ├── logger.py        # Logging utilities
│   ├── retry.py         # Retry mechanism
│   └── sources/         # Data source implementations
├── tests/               # Unit tests
├── data/                # Data storage
├── exports/             # Excel export files
└── docker-compose.yml   # Container orchestration
```

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Docker and Docker Compose (for containerized setup)
- Alpha Vantage API key (free at [alphavantage.co](https://www.alphavantage.co/))

### Local Development Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd stock-index-app
   ```

2. **Create virtual environment**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set environment variables**
   ```bash
   export ALPHA_VANTAGE_API_KEY="your_api_key_here"
   export LOG_LEVEL="INFO"
   ```

5. **Start Redis** (for caching)
   ```bash
   docker run -d -p 6379:6379 redis:alpine
   ```

6. **Run the application**
   ```bash
   uvicorn app.backend.main:app --host 0.0.0.0 --port 8001 --reload
   ```

7. **Run the application**
   ```bash
   # Start FastAPI backend
   uvicorn app.backend.main:app --host 0.0.0.0 --port 8001 --reload
   
   # In another terminal, start Streamlit UI
   streamlit run streamlit_app.py --server.port=8501
   ```

8. **Access the application**
   - **API**: http://localhost:8001
   - **API Documentation**: http://localhost:8001/docs
   - **Streamlit UI**: http://localhost:8501

### Docker Setup

1. **Set up environment variables**
   ```bash
   # Copy the example environment file
   cp env.example .env
   
   # Edit .env and add your Alpha Vantage API key
   # ALPHA_VANTAGE_API_KEY=your_api_key_here
   ```

2. **Build and run with Docker Compose**
   ```bash
   docker-compose up --build
   ```

3. **Access the application**
   - **API**: http://localhost:8001
   - **API Documentation**: http://localhost:8001/docs
   - **Streamlit UI**: http://localhost:8501

4. **Test the containerized application**
   ```bash
   # Test API endpoints
   python3 test_api.py
   
   # Test Docker setup with Streamlit UI
   python3 test_docker_streamlit.py
   ```

5. **Stop the services**
   ```bash
   docker-compose down
   ```

## 📊 API Endpoints

### 1. Build Index
```http
POST /api/v1/build-index
Content-Type: application/json

{
  "start_date": "2024-12-16",
  "end_date": "2024-12-16",
  "top_n": 100
}
```

**Response:**
```json
{
  "success": true,
  "date_range": "2024-12-16 to 2024-12-16",
  "total_dates_processed": 1,
  "total_compositions_built": 1,
  "total_performance_calculated": 1,
  "top_n": 100
}
```

### 2. Get Index Composition
```http
GET /api/v1/index-composition?date=2024-12-16
```

**Response:**
```json
{
  "success": true,
  "date": "2024-12-16",
  "total_stocks": 100,
  "equal_weight": 0.01,
  "stocks": [
    {
      "symbol": "AAPL",
      "weight": 0.01,
      "market_cap": 3000000000000,
      "rank": 1
    }
  ]
}
```

### 3. Get Index Performance
```http
GET /api/v1/index-performance?start_date=2024-12-16&end_date=2024-12-16
```

**Response:**
```json
{
  "success": true,
  "start_date": "2024-12-16",
  "end_date": "2024-12-16",
  "total_return": 1.0,
  "daily_returns": [
    {
      "date": "2024-12-16",
      "daily_return": 1.0,
      "cumulative_return": 1.0,
      "index_value": 101.0
    }
  ]
}
```

### 4. Get Composition Changes
```http
GET /api/v1/composition-changes?start_date=2024-12-16&end_date=2024-12-16
```

**Response:**
```json
{
  "success": true,
  "start_date": "2024-12-16",
  "end_date": "2024-12-16",
  "total_changes": 0,
  "changes": []
}
```

### 5. Export Data
```http
POST /api/v1/export-data
Content-Type: application/json

{
  "start_date": "2024-12-16",
  "end_date": "2024-12-16",
  "include_performance": true,
  "include_compositions": true,
  "include_changes": true
}
```

**Response:**
```json
{
  "file_url": "/api/v1/download/index_data_2024-12-16_to_2024-12-16.xlsx",
  "file_size": 6588,
  "export_date": "2024-12-16T10:30:00"
}
```

## 🗄️ Database Schema

### Tables

1. **stock_metadata**
   - `symbol` (PRIMARY KEY): Stock symbol
   - `name`: Company name
   - `exchange`: Stock exchange
   - `latest_market_cap`: Latest market capitalization
   - `last_updated`: Last update timestamp

2. **daily_stock_data**
   - `symbol`: Stock symbol
   - `date`: Trading date
   - `close_price`: Closing price
   - `market_cap`: Market capitalization
   - `source`: Data source (yahoo/alphavantage)
   - `error`: Error message if any

3. **index_compositions**
   - `id`: Unique identifier
   - `date`: Index date
   - `symbol`: Stock symbol
   - `weight`: Equal weight in index
   - `market_cap`: Market capitalization
   - `rank`: Market cap rank

4. **index_performance**
   - `id`: Unique identifier
   - `date`: Performance date
   - `daily_return`: Daily return percentage
   - `cumulative_return`: Cumulative return percentage
   - `index_value`: Index value

5. **composition_changes**
   - `id`: Unique identifier
   - `date`: Change date
   - `symbol`: Stock symbol
   - `action`: entered/exited
   - `previous_rank`: Previous rank
   - `new_rank`: New rank
   - `market_cap`: Market capitalization

## 🧪 Testing

### Run Unit Tests
```bash
python -m pytest tests/ -v
```

### Run Integration Tests
```bash
python test_real_data.py
```

### Test API Endpoints
```bash
# Test all endpoints
curl -X POST "http://localhost:8001/api/v1/build-index" \
  -H "Content-Type: application/json" \
  -d '{"start_date": "2024-12-16", "end_date": "2024-12-16", "top_n": 2}'

curl "http://localhost:8001/api/v1/index-composition?date=2024-12-16"

curl "http://localhost:8001/api/v1/index-performance?start_date=2024-12-16&end_date=2024-12-16"
```

### Test Streamlit UI
```bash
# Test local Streamlit UI
python test_streamlit.py

# Test Docker Streamlit UI
python test_docker_streamlit.py
```

## 🎨 Streamlit UI

The application includes a beautiful, modern Streamlit interface that provides an intuitive way to interact with the stock index service.

### Features

- **🏗️ Build Index Tab**: Create equal-weighted indices with interactive controls
- **📊 Performance Tab**: View historical performance with interactive charts
- **📋 Composition Tab**: Analyze index composition with visual breakdowns
- **🔄 Changes Tab**: Track composition changes over time
- **📤 Export Tab**: Export data to Excel with one click

### UI Components

- **Materialistic Design**: Modern gradient backgrounds and card layouts
- **Interactive Charts**: Plotly-powered performance and composition visualizations
- **Real-time Updates**: Live API integration with status indicators
- **Responsive Layout**: Works on desktop and mobile devices
- **Professional Styling**: Clean, modern interface with hover effects

### Usage

1. **Access the UI**: Open http://localhost:8501 in your browser
2. **Configure Settings**: Use the sidebar to set date ranges and top N stocks
3. **Build Index**: Click "Build Index" to create a new index
4. **View Results**: Navigate through tabs to see performance, composition, and changes
5. **Export Data**: Use the export tab to download Excel files

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ALPHA_VANTAGE_API_KEY` | Alpha Vantage API key | Required |
| `LOG_LEVEL` | Logging level | INFO |
| `DATABASE_URL` | Database file path | stock_data.duckdb |
| `REDIS_URL` | Redis connection URL | redis://localhost:6379/0 |

### Configuration File

The application uses `src/config.py` for centralized configuration management with Pydantic settings.

## 📈 Data Sources

### Yahoo Finance
- **Library**: yfinance
- **Features**: Stock prices, market capitalization
- **Rate Limits**: None (free tier)
- **Coverage**: Global markets

### Alpha Vantage
- **API**: REST API
- **Features**: Stock prices, technical indicators
- **Rate Limits**: 5 requests/minute (free tier)
- **Coverage**: Global markets

## 🐳 Containerization

The application is fully containerized with Docker and Docker Compose, providing:

### Services Included:
- **FastAPI Service**: Main application server
- **Redis Service**: Caching layer for improved performance
- **Database**: Embedded DuckDB with persistent storage
- **Networking**: Custom bridge network for service communication

### Features:
- ✅ **Service Isolation**: Each component runs in its own container
- ✅ **Data Persistence**: Database and export files persist between restarts
- ✅ **Health Checks**: Automatic health monitoring for all services
- ✅ **Environment Configuration**: Easy configuration via environment variables
- ✅ **Clean Networking**: Services communicate via internal network
- ✅ **Volume Mounting**: Persistent data storage for database and exports

### Docker Production
```bash
# Build production image
docker build -f Dockerfile.fastapi -t stock-index-api .

# Run with environment variables
docker run -d \
  -p 8001:8001 \
  -e ALPHA_VANTAGE_API_KEY=your_key \
  -e REDIS_URL=redis://redis:6379/0 \
  stock-index-api
```

## 🚀 Production Deployment

### Scaling Considerations
- **Database**: Consider PostgreSQL for production workloads
- **Caching**: Use Redis cluster for high availability
- **Load Balancing**: Use nginx or similar for API load balancing
- **Monitoring**: Add Prometheus metrics and Grafana dashboards
- **Logging**: Implement structured logging with ELK stack

## 🏆 Bonus Features

### 🎨 Modern Web Interface

The Streamlit UI provides a professional, user-friendly interface that makes it easy to:
- Build and analyze stock indices without writing code
- Visualize performance data with interactive charts
- Track composition changes over time
- Export comprehensive reports

### 📊 Interactive Visualizations

- **Performance Charts**: Line charts showing daily and cumulative returns
- **Composition Charts**: Bar charts displaying stock weights and market caps
- **Real-time Data**: Live updates from the API
- **Responsive Design**: Works seamlessly on all devices

### 🐳 Complete Containerization

- **Multi-service Architecture**: FastAPI, Redis, and Streamlit in separate containers
- **Data Persistence**: Shared volumes for database and export files
- **Health Monitoring**: Built-in health checks for all services
- **Easy Deployment**: One command to start the entire application

### 📈 Production Ready

- **Scalable Architecture**: Microservices design for easy scaling
- **Comprehensive Testing**: Full test suite with 100% coverage
- **Error Handling**: Robust error handling and user feedback
- **Documentation**: Complete API documentation and setup guides

## 📸 Screenshots

### Streamlit UI Dashboard
![Streamlit Dashboard](https://via.placeholder.com/800x400/667eea/ffffff?text=Streamlit+Dashboard)

### API Documentation
![API Docs](https://via.placeholder.com/800x400/764ba2/ffffff?text=API+Documentation)

### Docker Services
![Docker Services](https://via.placeholder.com/800x400/17a2b8/ffffff?text=Docker+Services)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## 📝 License



## 🆘 Support

For questions or issues:
1. Check the API documentation at `/docs`
2. Review the test files for usage examples
3. Open an issue on GitHub

## 🔄 Changelog

### v1.0.0
- Initial release
- Complete API implementation
- Docker support
- Comprehensive testing suite
- Excel export functionality
