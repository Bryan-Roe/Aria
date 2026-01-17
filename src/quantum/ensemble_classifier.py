#!/usr/bin/env python
"""
Ensemble Classifier combining top 5 quantum ML models
Uses weighted voting based on individual model accuracies
"""
import os
import sys
import numpy as np
import torch
import pickle
from pathlib import Path
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA

sys.path.insert(0, os.path.dirname(__file__))
from src.hybrid_qnn import HybridQNN

class QuantumEnsemble:
    """
    Ensemble of top 5 quantum ML models with weighted voting
    """
    
    def __init__(self):
        self.models = {}
        self.scalers = {}
        self.pcas = {}
        self.weights = {}
        self.model_info = {
            'banknote': {'accuracy': 100.0, 'features': 4, 'classes': 2},
            'wine_quality': {'accuracy': 98.69, 'features': 11, 'classes': 7},
            'ionosphere': {'accuracy': 91.43, 'features': 34, 'classes': 2},
            'heart_disease': {'accuracy': 90.16, 'features': 13, 'classes': 2},
            'iris': {'accuracy': 90.00, 'features': 4, 'classes': 3},
        }
        self.loaded = False
    
    def load_models(self, models_dir='results'):
        """Load all ensemble models"""
        print("🔄 Loading ensemble models...")
        
        for model_name, info in self.model_info.items():
            try:
                # Load model
                model_path = f'{models_dir}/custom_model__{model_name}.pt'
                if not os.path.exists(model_path):
                    model_path = f'{models_dir}/custom_model.pt'
                
                checkpoint = torch.load(model_path)
                
                # Infer output dim from model info
                output_dim = info['classes']
                
                model = HybridQNN(
                    input_dim=16,
                    hidden_dim=16,
                    n_qubits=4,
                    n_quantum_layers=2,
                    output_dim=output_dim
                )
                model.load_state_dict(checkpoint)
                model.eval()
                self.models[model_name] = model
                
                # Load scaler
                scaler_path = f'{models_dir}/custom_scaler__{model_name}.pkl'
                if os.path.exists(scaler_path):
                    with open(scaler_path, 'rb') as f:
                        self.scalers[model_name] = pickle.load(f)
                
                # Load PCA if exists
                pca_path = f'{models_dir}/custom_pca__{model_name}.pkl'
                if os.path.exists(pca_path):
                    with open(pca_path, 'rb') as f:
                        self.pcas[model_name] = pickle.load(f)
                
                # Weight by accuracy
                self.weights[model_name] = info['accuracy'] / 100.0
                
                print(f"   ✅ {model_name}: {info['accuracy']}% (weight: {self.weights[model_name]:.3f})")
                
            except Exception as e:
                print(f"   ⚠️  {model_name}: {str(e)[:60]}")
        
        self.loaded = len(self.models) > 0
        print(f"\n✅ Loaded {len(self.models)}/5 models")
        return self.loaded
    
    def predict_single_model(self, model_name, features):
        """Get prediction from a single model"""
        if model_name not in self.models:
            return None
        
        # Preprocess
        X = np.array(features).reshape(1, -1)
        
        if model_name in self.scalers:
            X = self.scalers[model_name].transform(X)
        
        if model_name in self.pcas:
            X = self.pcas[model_name].transform(X)
        
        # Predict
        X_tensor = torch.FloatTensor(X)
        with torch.no_grad():
            output = self.models[model_name](X_tensor)
            probabilities = torch.softmax(output, dim=1).numpy()[0]
            prediction = int(torch.argmax(output, dim=1).item())
        
        return {
            'prediction': prediction,
            'probabilities': probabilities,
            'confidence': float(probabilities[prediction])
        }
    
    def predict_ensemble(self, features_dict):
        """
        Ensemble prediction using weighted voting
        
        Args:
            features_dict: Dict mapping model names to their feature arrays
                          e.g., {'banknote': [0.5, -1.2, 0.3, 0.1], ...}
        
        Returns:
            Dict with ensemble prediction and individual model votes
        """
        if not self.loaded:
            raise RuntimeError("Models not loaded. Call load_models() first.")
        
        votes = {}
        weighted_scores = {}
        
        # Collect predictions from each model
        for model_name, features in features_dict.items():
            if model_name not in self.models:
                continue
            
            result = self.predict_single_model(model_name, features)
            if result:
                votes[model_name] = result
                
                # Weighted vote contribution
                weight = self.weights[model_name]
                for class_idx, prob in enumerate(result['probabilities']):
                    if class_idx not in weighted_scores:
                        weighted_scores[class_idx] = 0.0
                    weighted_scores[class_idx] += prob * weight
        
        # Normalize weighted scores
        total_weight = sum(self.weights[m] for m in votes.keys())
        for class_idx in weighted_scores:
            weighted_scores[class_idx] /= total_weight
        
        # Final prediction
        final_prediction = max(weighted_scores.items(), key=lambda x: x[1])[0]
        final_confidence = weighted_scores[final_prediction]
        
        return {
            'ensemble_prediction': int(final_prediction),
            'ensemble_confidence': float(final_confidence),
            'weighted_scores': {int(k): float(v) for k, v in weighted_scores.items()},
            'individual_votes': votes,
            'models_used': len(votes),
            'total_weight': float(total_weight)
        }
    
    def predict_compatible(self, features, model_type='binary'):
        """
        Predict using models compatible with the input features
        
        Args:
            features: Feature array
            model_type: 'binary' or 'multiclass'
        
        Returns:
            Ensemble prediction from compatible models
        """
        n_features = len(features)
        
        # Select compatible models
        compatible = {}
        for name, info in self.model_info.items():
            if name in self.models:
                if model_type == 'binary' and info['classes'] == 2:
                    compatible[name] = features[:info['features']] if n_features >= info['features'] else None
                elif model_type == 'multiclass' and info['classes'] > 2:
                    compatible[name] = features[:info['features']] if n_features >= info['features'] else None
        
        # Remove None values
        compatible = {k: v for k, v in compatible.items() if v is not None}
        
        if not compatible:
            raise ValueError(f"No compatible models found for {model_type} with {n_features} features")
        
        return self.predict_ensemble(compatible)
    
    def get_model_info(self):
        """Return information about loaded models"""
        return {
            'loaded_models': list(self.models.keys()),
            'total_models': len(self.models),
            'model_accuracies': {name: info['accuracy'] for name, info in self.model_info.items()},
            'weights': self.weights,
            'average_accuracy': sum(info['accuracy'] for name, info in self.model_info.items() if name in self.models) / len(self.models),
            'ensemble_method': 'Weighted Voting (Accuracy-based)',
            'status': 'loaded' if self.loaded else 'not_loaded'
        }


def test_ensemble():
    """Test the ensemble classifier"""
    print("="*70)
    print("🧪 Testing Quantum Ensemble Classifier")
    print("="*70)
    
    ensemble = QuantumEnsemble()
    
    if not ensemble.load_models():
        print("❌ Failed to load models")
        return
    
    print("\n📊 Ensemble Info:")
    info = ensemble.get_model_info()
    print(f"   Models Loaded: {info['total_models']}")
    print(f"   Average Accuracy: {info['average_accuracy']:.2f}%")
    print(f"   Method: {info['ensemble_method']}")
    
    # Test with banknote features (authentic example)
    print("\n🧪 Test Case 1: Banknote Authentication")
    print("   Features: [3.6216, 8.6661, -2.8073, -0.44699]")
    
    try:
        result = ensemble.predict_compatible([3.6216, 8.6661, -2.8073, -0.44699], model_type='binary')
        print(f"   Prediction: {'Authentic' if result['ensemble_prediction'] == 0 else 'Fraudulent'}")
        print(f"   Confidence: {result['ensemble_confidence']*100:.2f}%")
        print(f"   Models Used: {result['models_used']}")
    except Exception as e:
        print(f"   Error: {str(e)}")
    
    print("\n✅ Ensemble test complete")
    print("="*70)

if __name__ == '__main__':
    os.chdir('/workspaces/AI/quantum-ai')
    test_ensemble()
