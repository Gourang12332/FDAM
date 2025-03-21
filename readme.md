# FDAM System: Fraud Detection, Alert, and Monitoring for SabPaisa

![SabPaisa](https://www.sabpaisa.in/wp-content/uploads/2023/07/7.png)

## Overview

FDAM is a comprehensive Fraud Detection, Alert, and Monitoring system developed for SabPaisa's payment gateway during a 24-hour hackathon. The system employs a multi-layered defense strategy combining rule-based detection, anomaly detection, and risk scoring to identify fraudulent transactions in real-time.

## Architecture

The FDAM system features a robust backend architecture with the following components:

```
                                    ┌─────────────────┐
                                    │   API Gateway   │
                                    └────────┬────────┘
                                             │
                                             ▼
┌────────────────┐                 ┌─────────────────┐                 ┌─────────────────┐
│  Rule Engine   │◄────────────────┤  Detection API  │────────────────►│  ML Models      │
│                │                 │                 │                 │                 │
└────────────────┘                 └────────┬────────┘                 └─────────────────┘
                                             │
                     ┌───────────────┬──────┴─────┬────────────────┐
                     ▼               ▼            ▼                ▼
             ┌──────────────┐ ┌────────────┐ ┌─────────┐  ┌─────────────────┐
             │ Fraud        │ │ Reporting  │ │ Analytics│  │ Database       │
             │ Detection    │ │ Service    │ │ Service  │  │ Service        │
             └──────────────┘ └────────────┘ └─────────┘  └─────────────────┘
```

## Technology Stack

### Backend
- **Python 3.11+** with FastAPI framework
- **SQLAlchemy 2.0+** for asynchronous database operations
- **SQLite** (development) / **PostgreSQL** (production)
- **Isolation Forest** for anomaly detection
- **Rule Engine** with JsonLogic for configurable rules
- **Asynchronous Processing** for high performance

### Frontend (made but integration in future)
- Next.js 14+
- shadcn/ui components based on Radix UI
- Tailwind CSS with SabPaisa theming

## Key Features Implemented

### 1. Multi-layered Fraud Detection

Our solution employs three complementary approaches to fraud detection:

- **Rule Engine**: Pattern-based detection with configurable rules
- **Anomaly Detection**: Isolation Forest model to identify unusual transactions
- **Risk Scoring**: Expert-defined risk assessment based on transaction attributes

This layered approach provides robust protection even with extremely imbalanced datasets (0.0065% fraud cases).

### 2. India-specific Fraud Patterns

The system includes specialized rules for Indian payment contexts:

- UPI transaction patterns
- INR-specific amount thresholds
- India banking hours and risk time periods
- Common fraud patterns observed in Indian payment systems

### 3. APIs Implemented

- **Fraud Detection API (Real-time)**
  - Input: Single transaction as JSON
  - Output: Fraud determination with reason and score
  - Latency: <300ms

- **Fraud Detection API (Batch)**
  - Process multiple transactions in parallel
  - Uses the same detection logic as real-time API

- **Fraud Reporting API**
  - Allow reporting of actual fraud occurrences
  - Store fraud reports for analysis

### 4. Analytics and Monitoring

- Database storage of all transactions
- Fraud detection results with explanations
- Support for evaluation metrics calculation

## Installation

### Prerequisites
- Python 3.11+
- pip
- SQLite (for development)

### Setup

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/fdam.git
cd fdam
```

2. **Create a virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Initialize the database**
```bash
python scripts/init_db.py
```

5. **Train the model**
```bash
python scripts/train_model.py --data data/transactions_train.csv --output app/ml/models/fraud_model.pkl
```

6. **Start the server**
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Usage Examples

### Real-time Fraud Detection

```bash
curl -X POST http://localhost:8000/api/v1/fraud-detection/detect \
  -H "Content-Type: application/json" \
  -d '{
    "transaction_id": "TX123456789",
    "transaction_date": "2023-03-21T14:35:12",
    "transaction_amount": 150000,
    "transaction_channel": "web",
    "transaction_payment_mode": "UPI",
    "payment_gateway_bank": "HDFC",
    "payer_email": "user@example.com",
    "payer_mobile": "9876543210",
    "payer_device": "iPhone",
    "payer_browser": "Safari",
    "payee_id": "MERCHANT001",
    "transaction_payment_mode_anonymous": 11,
    "payment_gateway_bank_anonymous": 6,
    "payer_browser_anonymous": 1568
  }'
```

### Report Fraud

```bash
curl -X POST http://localhost:8000/api/v1/fraud-reporting/report \
  -H "Content-Type: application/json" \
  -d '{
    "transaction_id": "TX123456789",
    "reporting_entity_id": "BANK001",
    "fraud_details": "Customer reported unauthorized transaction"
  }'
```

## Performance Considerations

### Latency Optimization

The system is optimized to meet the <300ms latency requirement through:

1. **Asynchronous Processing**
   - FastAPI's async support for non-blocking operations
   - Parallel execution of rule engine and ML model
   - Background tasks for non-critical operations

2. **Caching Strategy**
   - File-based caching for development
   - Configurable for Redis integration

3. **Database Optimization**
   - Proper indexing on frequently queried fields
   - Async database operations
   - Connection pooling

## Challenges and Solutions

### 1. Extreme Class Imbalance

**Challenge**: Only 11 fraud cases out of 172,926 transactions (0.0065%).

**Solution**: 
- Prioritized rule-based detection for high-precision identification
- Used anomaly detection (Isolation Forest) instead of traditional classification
- Implemented direct risk scoring based on domain expertise

### 2. Indian Payment Context

**Challenge**: Need for specialized rules for Indian payment systems.

**Solution**:
- Implemented UPI-specific fraud patterns
- Created rules for INR denominations and round amounts
- Added time-based patterns aligned with Indian banking hours

### 3. Performance Requirements

**Challenge**: Strict <300ms latency requirement.

**Solution**:
- Parallel execution of detection components
- Optimized feature extraction
- Efficient database operations

## Testing

A comprehensive test script is included to validate all API functionality:

```bash
python test_fdam_api.py
```

This tests:
- Real-time detection API
- Batch detection API
- Fraud reporting API
- Performance under load
- Rule-based detection

## Future Improvements

1. **Frontend Integration**
   - Complete the planned Next.js frontend
   - Implement visualization dashboards
   - Add rule configuration UI

2. **Enhanced ML Models**
   - Train with more fraud examples as they become available
   - Implement adaptive thresholds
   - Add online learning capabilities

3. **Production Deployment**
   - Docker containerization
   - Kubernetes orchestration
   - Monitoring and alerting setup

## Conclusion

The FDAM system provides a robust, multi-layered approach to fraud detection optimized for the Indian payment context. Despite the challenges of extreme data imbalance, the system successfully implements all required backend functionality with high performance and accuracy.

While the frontend integration wasn't completed during the hackathon timeframe, the backend APIs provide all necessary capabilities for future frontend development.

---

*Developed for SabPaisa during the 24-hour hackathon*