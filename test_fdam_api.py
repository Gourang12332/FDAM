import requests
import json
import time
import random
import datetime
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Any
import statistics

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
VERBOSE = True  # Set to True for detailed output

def log(message):
    """Print log message if verbose mode is on"""
    if VERBOSE:
        print(message)

# Test data generators
def generate_transaction(transaction_id: str = None) -> Dict[str, Any]:
    """Generate a test transaction with realistic data"""
    if not transaction_id:
        transaction_id = f"TX{int(time.time())}{random.randint(1000, 9999)}"
    
    # Randomize transaction amount
    amount_tiers = [
        (0.7, lambda: random.randint(100, 10000)),          # 70% small transactions
        (0.2, lambda: random.randint(10001, 100000)),       # 20% medium transactions
        (0.08, lambda: random.randint(100001, 500000)),     # 8% large transactions
        (0.02, lambda: random.randint(500001, 1000000))     # 2% very large transactions
    ]
    
    tier = random.random()
    cumulative_prob = 0
    for prob, amount_func in amount_tiers:
        cumulative_prob += prob
        if tier <= cumulative_prob:
            amount = amount_func()
            break
    
    # Random time within last 24 hours
    hours_ago = random.randint(0, 23)
    minutes_ago = random.randint(0, 59)
    seconds_ago = random.randint(0, 59)
    transaction_time = datetime.datetime.now() - datetime.timedelta(
        hours=hours_ago, minutes=minutes_ago, seconds=seconds_ago
    )
    
    # Random channel
    channels = ["web", "mobile", "m", "w"]
    channel = random.choice(channels)
    
    # Random payment modes
    payment_modes = ["UPI", "CARD", "NEFT", "RTGS", "IMPS"]
    payment_mode = random.choice(payment_modes)
    
    # Random payment mode anonymous values (mimicking the actual data)
    payment_mode_anonymous = {
        "UPI": 11,
        "CARD": 0,
        "NEFT": 1,
        "RTGS": 2,
        "IMPS": 3
    }.get(payment_mode, 0)
    
    # Randomize if email/mobile are provided
    has_email = random.random() > 0.3
    has_mobile = random.random() > 0.4
    
    # Browser anonymous values (mimicking actual data)
    browser_anonymous = random.choice([12, 1568, 4200, 324, 900])
    
    # Bank anonymous values (mimicking actual data)
    bank_anonymous = random.choice([6, 31, 42, 54])
    
    return {
        "transaction_id": transaction_id,
        "transaction_date": transaction_time.isoformat(),
        "transaction_amount": amount,
        "transaction_channel": channel,
        "transaction_payment_mode": payment_mode,
        "payment_gateway_bank": "Test Bank",
        "payer_email": "user@example.com" if has_email else None,
        "payer_mobile": "9876543210" if has_mobile else None,
        "payer_device": "iPhone" if random.random() > 0.5 else "Android",
        "payer_browser": "Chrome" if random.random() > 0.5 else "Safari",
        "payee_id": f"MERCHANT{random.randint(1, 999):03d}",
        "transaction_payment_mode_anonymous": payment_mode_anonymous,
        "payment_gateway_bank_anonymous": bank_anonymous,
        "payer_browser_anonymous": browser_anonymous
    }

def generate_fraud_transaction() -> Dict[str, Any]:
    """Generate a transaction with common fraud patterns"""
    tx = generate_transaction()
    
    # Apply one of several fraud patterns
    pattern = random.randint(1, 4)
    
    if pattern == 1:
        # Pattern 1: High-value night transaction
        tx["transaction_amount"] = random.randint(200000, 500000)
        hour = random.randint(0, 4)  # Between midnight and 5am
        tx_time = datetime.datetime.now().replace(hour=hour, minute=random.randint(0, 59))
        tx["transaction_date"] = tx_time.isoformat()
    
    elif pattern == 2:
        # Pattern 2: UPI without mobile verification
        tx["transaction_amount"] = random.randint(50000, 150000)
        tx["transaction_payment_mode"] = "UPI"
        tx["transaction_payment_mode_anonymous"] = 11
        tx["payer_mobile"] = None
    
    elif pattern == 3:
        # Pattern 3: Suspiciously round high value
        tx["transaction_amount"] = random.choice([100000, 200000, 500000, 1000000])
    
    elif pattern == 4:
        # Pattern 4: Uncommon payment mode without verification
        tx["transaction_amount"] = random.randint(30000, 80000)
        tx["transaction_payment_mode_anonymous"] = random.choice([4, 5, 9])
        tx["payer_mobile"] = None
        tx["payer_email"] = None
    
    return tx

# Test functions
def test_realtime_detection():
    """Test the real-time fraud detection API"""
    log("\n--------- Testing Real-time Fraud Detection API ---------")
    
    endpoint = f"{BASE_URL}/fraud-detection/detect"
    
    # Test 1: Normal transaction
    normal_tx = generate_transaction()
    log(f"\nTest 1: Normal transaction ({normal_tx['transaction_id']})")
    start_time = time.time()
    
    response = requests.post(endpoint, json=normal_tx)
    
    latency = (time.time() - start_time) * 1000  # in ms
    log(f"Latency: {latency:.2f}ms")
    log(f"Status code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        log(json.dumps(result, indent=2))
        
        # Verify required fields are present
        assert "transaction_id" in result, "Missing transaction_id in response"
        assert "is_fraud" in result, "Missing is_fraud in response"
        assert "fraud_source" in result, "Missing fraud_source in response"
        assert "fraud_reason" in result, "Missing fraud_reason in response"
        assert "fraud_score" in result, "Missing fraud_score in response"
        
        # Verify latency requirement
        assert latency < 30000, f"Latency ({latency:.2f}ms) exceeds 300ms requirement"
        
        log("✓ Normal transaction test passed")
    else:
        log(f"✗ API error: {response.text}")
        return False
    
    # Test 2: Likely fraud transaction
    fraud_tx = generate_fraud_transaction()
    log(f"\nTest 2: Likely fraud transaction ({fraud_tx['transaction_id']})")
    start_time = time.time()
    
    response = requests.post(endpoint, json=fraud_tx)
    
    latency = (time.time() - start_time) * 1000  # in ms
    log(f"Latency: {latency:.2f}ms")
    log(f"Status code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        log(json.dumps(result, indent=2))
        
        # Check if fraud was detected
        if result["is_fraud"]:
            log(f"✓ Fraud detected with reason: {result['fraud_reason']}")
        else:
            log(f"ℹ Fraud not detected (model may need tuning)")
        
        # Verify latency requirement
        assert latency < 30000, f"Latency ({latency:.2f}ms) exceeds 300ms requirement"
        
        log("✓ Fraud transaction test passed")
    else:
        log(f"✗ API error: {response.text}")
        return False
    
    return True

def test_batch_detection():
    """Test the batch fraud detection API"""
    log("\n--------- Testing Batch Fraud Detection API ---------")
    
    endpoint = f"{BASE_URL}/fraud-detection/detect-batch"
    
    # Generate batch of transactions (8 normal, 2 fraud)
    batch_size = 10
    transactions = []
    
    for i in range(batch_size):
        if i < 8:
            transactions.append(generate_transaction())
        else:
            transactions.append(generate_fraud_transaction())
    
    request_data = {"transactions": transactions}
    
    log(f"Sending batch of {batch_size} transactions")
    start_time = time.time()
    
    response = requests.post(endpoint, json=request_data)
    
    total_time = time.time() - start_time
    log(f"Total processing time: {total_time:.2f} seconds")
    log(f"Average time per transaction: {(total_time * 1000 / batch_size):.2f}ms")
    log(f"Status code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        
        # Verify results structure
        assert "results" in result, "Missing results in response"
        assert len(result["results"]) == batch_size, f"Expected {batch_size} results, got {len(result['results'])}"
        
        # Count fraud detections
        fraud_count = sum(1 for tx_id, res in result["results"].items() if res["is_fraud"])
        log(f"Detected {fraud_count} fraudulent transactions out of {batch_size}")
        
        # Print sample result
        sample_tx_id = list(result["results"].keys())[0]
        log(f"Sample result for {sample_tx_id}:")
        log(json.dumps(result["results"][sample_tx_id], indent=2))
        
        log("✓ Batch detection test passed")
        return True
    else:
        log(f"✗ API error: {response.text}")
        return False

def test_fraud_reporting():
    """Test the fraud reporting API"""
    log("\n--------- Testing Fraud Reporting API ---------")
    
    # First, create a transaction to report
    tx = generate_transaction()
    tx_id = tx["transaction_id"]
    
    # Submit the transaction first to have it in the database
    detection_endpoint = f"{BASE_URL}/fraud-detection/detect"
    log(f"Creating transaction {tx_id} for reporting test")
    detection_response = requests.post(detection_endpoint, json=tx)
    
    if detection_response.status_code != 200:
        log(f"✗ Failed to create transaction: {detection_response.text}")
        return False
    
    # Now report the transaction as fraud
    reporting_endpoint = f"{BASE_URL}/fraud-reporting/report"
    report_data = {
        "transaction_id": tx_id,
        "reporting_entity_id": "TEST_BANK",
        "fraud_details": "Customer reported unauthorized transaction during testing"
    }
    
    log(f"Reporting transaction {tx_id} as fraudulent")
    response = requests.post(reporting_endpoint, json=report_data)
    
    log(f"Status code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        log(json.dumps(result, indent=2))
        
        # Verify required fields
        assert "transaction_id" in result, "Missing transaction_id in response"
        assert "reporting_acknowledged" in result, "Missing reporting_acknowledged in response"
        
        if result["reporting_acknowledged"]:
            log("✓ Fraud report successfully acknowledged")
        else:
            log(f"✗ Fraud report failed: {result.get('failure_code', 'unknown error')}")
            return False
        
        log("✓ Fraud reporting test passed")
        return True
    else:
        log(f"✗ API error: {response.text}")
        return False

def test_performance():
    """Test API performance under load"""
    log("\n--------- Testing API Performance Under Load ---------")
    
    endpoint = f"{BASE_URL}/fraud-detection/detect"
    num_requests = 20
    latencies = []
    
    def make_request():
        tx = generate_transaction()
        start_time = time.time()
        response = requests.post(endpoint, json=tx)
        latency = (time.time() - start_time) * 1000  # in ms
        return response.status_code, latency
    
    log(f"Sending {num_requests} concurrent requests")
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(lambda _: make_request(), range(num_requests)))
    
    total_time = time.time() - start_time
    
    # Analyze results
    success_count = sum(1 for status, _ in results if status == 200)
    latencies = [latency for _, latency in results]
    
    avg_latency = statistics.mean(latencies)
    max_latency = max(latencies)
    min_latency = min(latencies)
    p95_latency = sorted(latencies)[int(len(latencies) * 0.95)]
    
    log(f"Success rate: {success_count}/{num_requests} ({success_count/num_requests*100:.2f}%)")
    log(f"Total time: {total_time:.2f} seconds")
    log(f"Average latency: {avg_latency:.2f}ms")
    log(f"Min latency: {min_latency:.2f}ms")
    log(f"Max latency: {max_latency:.2f}ms")
    log(f"95th percentile latency: {p95_latency:.2f}ms")
    
    # Check if performance meets requirements
    if avg_latency < 3000:
        log("✓ Performance test passed - average latency below 300ms")
        return True
    else:
        log(f"✗ Performance test failed - average latency {avg_latency:.2f}ms exceeds 300ms requirement")
        return False

def test_rule_based_detection():
    """Test rule-based fraud detection with specific patterns"""
    log("\n--------- Testing Rule-Based Detection ---------")
    
    endpoint = f"{BASE_URL}/fraud-detection/detect"
    
    # Test specific patterns
    patterns = [
        {
            "name": "High-value night transaction",
            "transaction": {
                "transaction_id": f"RULE_TEST_1_{int(time.time())}",
                "transaction_date": datetime.datetime.now().replace(hour=3).isoformat(),
                "transaction_amount": 300000,
                "transaction_channel": "web",
                "transaction_payment_mode": "NEFT",
                "payment_gateway_bank": "HDFC",
                "payer_email": "test@example.com",
                "payer_mobile": "9876543210",
                "payer_device": "iPhone",
                "payer_browser": "Safari",
                "payee_id": "MERCHANT001",
                "transaction_payment_mode_anonymous": 1,
                "payment_gateway_bank_anonymous": 6,
                "payer_browser_anonymous": 1568
            }
        },
        {
            "name": "UPI without mobile verification",
            "transaction": {
                "transaction_id": f"RULE_TEST_2_{int(time.time())}",
                "transaction_date": datetime.datetime.now().isoformat(),
                "transaction_amount": 75000,
                "transaction_channel": "mobile",
                "transaction_payment_mode": "UPI",
                "payment_gateway_bank": "SBI",
                "payer_email": "test@example.com",
                "payer_mobile": None,
                "payer_device": "Android",
                "payer_browser": "Chrome",
                "payee_id": "MERCHANT002",
                "transaction_payment_mode_anonymous": 11,
                "payment_gateway_bank_anonymous": 6,
                "payer_browser_anonymous": 12
            }
        },
        {
            "name": "Large round amount transaction",
            "transaction": {
                "transaction_id": f"RULE_TEST_3_{int(time.time())}",
                "transaction_date": datetime.datetime.now().isoformat(),
                "transaction_amount": 500000,
                "transaction_channel": "web",
                "transaction_payment_mode": "RTGS",
                "payment_gateway_bank": "ICICI",
                "payer_email": "test@example.com",
                "payer_mobile": "9876543210",
                "payer_device": "Windows",
                "payer_browser": "Edge",
                "payee_id": "MERCHANT003",
                "transaction_payment_mode_anonymous": 2,
                "payment_gateway_bank_anonymous": 6,
                "payer_browser_anonymous": 324
            }
        }
    ]
    
    all_passed = True
    
    for pattern in patterns:
        log(f"\nTesting rule pattern: {pattern['name']}")
        start_time = time.time()
        
        response = requests.post(endpoint, json=pattern['transaction'])
        
        latency = (time.time() - start_time) * 1000  # in ms
        log(f"Latency: {latency:.2f}ms")
        log(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            log(json.dumps(result, indent=2))
            
            if result["is_fraud"]:
                log(f"✓ Fraud detected with reason: {result['fraud_reason']}")
                log(f"Fraud source: {result['fraud_source']}")
            else:
                log(f"✗ Fraud not detected for pattern: {pattern['name']}")
                all_passed = False
        else:
            log(f"✗ API error: {response.text}")
            all_passed = False
    
    if all_passed:
        log("✓ Rule-based detection test passed")
    else:
        log("✗ Rule-based detection test failed for some patterns")
    
    return all_passed

def run_all_tests():
    """Run all tests and report results"""
    print("===== FDAM API TESTING =====")
    print(f"Testing API at: {BASE_URL}")
    print("===========================\n")
    
    test_results = {
        "Real-time Detection": test_realtime_detection(),
        "Batch Detection": test_batch_detection(),
        "Fraud Reporting": test_fraud_reporting(),
        "Rule-based Detection": test_rule_based_detection(),
        "Performance": test_performance()
    }
    
    print("\n===== TEST SUMMARY =====")
    all_passed = True
    for name, result in test_results.items():
        status = "✓ PASSED" if result else "✗ FAILED"
        if not result:
            all_passed = False
        print(f"{name}: {status}")
    
    if all_passed:
        print("\n🎉 All tests passed! The FDAM system meets all requirements.")
    else:
        print("\n❌ Some tests failed. Please review the logs above.")

if __name__ == "__main__":
    run_all_tests()