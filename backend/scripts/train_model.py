import os
import sys
import argparse

# Add the parent directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.ml.ensemble_model import FraudEnsembleModel
from app.core.logging import get_logger

logger = get_logger("model_training")

def main():
    parser = argparse.ArgumentParser(description="Train the fraud detection model")
    parser.add_argument(
        "--data",
        default="data/transactions_train.csv",
        help="Path to the training data CSV file"
    )
    parser.add_argument(
        "--output",
        default="app/ml/models/fraud_model.pkl",
        help="Path to save the trained model"
    )
    parser.add_argument(
        "--test-size",
        type=float,
        default=0.2,
        help="Proportion of data to use for testing (default: 0.2)"
    )
    
    args = parser.parse_args()
    
    if not os.path.exists(args.data):
        logger.error(f"Data file not found: {args.data}")
        sys.exit(1)
    
    try:
        # Create model directory if it doesn't exist
        os.makedirs(os.path.dirname(args.output), exist_ok=True)
        
        logger.info(f"Training model with data from {args.data}")
        model = FraudEnsembleModel()
        result = model.train(
            data_path=args.data,
            test_size=args.test_size,
            save_path=args.output
        )
        
        # Print results
        metrics = result.get("metrics", {})
        print("\nTraining Results:")
        print(f"False Positive Rate: {metrics.get('false_positive_rate', 0):.4f}")
        print(f"Anomaly Threshold: {metrics.get('threshold', 0):.4f}")
        print(f"\nModel saved to: {args.output}")
        
        model_info = result.get("model_info", {})
        print(f"\nModel Type: {model_info.get('type', 'Unknown')}")
        print(f"Feature Count: {model_info.get('feature_count', 0)}")
        
    except Exception as e:
        logger.error(f"Error training model: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()