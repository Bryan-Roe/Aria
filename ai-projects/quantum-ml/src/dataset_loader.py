"""
Shared dataset loading utilities for quantum AI experiments.
Consolidates duplicated dataset loading code from multiple files.
"""

from pathlib import Path
from typing import List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler


def load_dataset(
    name: str, base_path: Optional[Path] = None, return_feature_names: bool = False
) -> Tuple[np.ndarray, np.ndarray, Optional[List[str]]]:
    """
    Load a preset dataset from the datasets/quantum directory.

    Args:
        name: Dataset name (e.g., 'ionosphere', 'sonar', 'heart', 'banknote')
        base_path: Optional override for the datasets directory
        return_feature_names: If True, returns feature column names

    Returns:
        X: Feature matrix (numpy array)
        y: Labels (numpy array, 0-indexed integers)
        feature_names: Optional list of feature names (if return_feature_names=True)
    """
    if base_path is None:
        base_path = Path(__file__).parent.parent.parent / "datasets" / "quantum"

    # Map dataset names to file paths
    datasets_map = {
        "ionosphere": base_path / "ionosphere.csv",
        "sonar": base_path / "sonar.csv",
        "heart": base_path / "heart_disease.csv",
        "heart_disease": base_path / "heart_disease.csv",
        "banknote": base_path / "banknote.csv",
    }

    if name not in datasets_map:
        raise ValueError(
            f"Unknown dataset: {name}. Available: {list(datasets_map.keys())}"
        )

    path = datasets_map[name]
    if not path.exists():
        raise FileNotFoundError(f"Dataset file not found: {path}")

    # Load the CSV file
    df = pd.read_csv(path, header=None, na_values=["?", "NA", ""])

    # Separate features and labels
    X = df.iloc[:, :-1]
    y = df.iloc[:, -1]

    # Handle missing values
    if X.isnull().any().any():
        imputer = SimpleImputer(strategy="median")
        X = pd.DataFrame(imputer.fit_transform(X), columns=X.columns)

    # Store feature names before converting to numpy
    feature_names = list(X.columns)

    # Convert features to numpy
    X_values = X.values

    # Process labels
    if name in ["heart", "heart_disease"]:
        # Heart disease: labels > 0 indicate disease presence
        y = (y > 0).astype(int).values
    elif not pd.api.types.is_numeric_dtype(y):
        # Non-numeric labels: factorize to 0..K-1
        vals, _ = pd.factorize(y.astype(str))
        y = vals
    else:
        # Numeric labels: ensure 0-indexed integers
        y = y.astype(int).values
        unique_labels = np.unique(y)

        # If binary and not already {0, 1}, remap to {0, 1}
        if len(unique_labels) == 2 and set(unique_labels) != {0, 1}:
            mapping = {unique_labels.min(): 0, unique_labels.max(): 1}
            y = np.array([mapping[v] for v in y])

    if return_feature_names:
        return X_values, y, feature_names
    else:
        return X_values, y, None


def preprocess_for_qubits(
    X_train: np.ndarray, X_val: np.ndarray, n_qubits: int
) -> Tuple[np.ndarray, np.ndarray, Optional["StandardScaler"], Optional["PCA"]]:
    """
    Preprocess data to match the number of qubits.

    Handles both dimensionality reduction (via PCA) and padding with zeros
    to ensure feature dimension matches n_qubits.

    Args:
        X_train: Training features
        X_val: Validation features
        n_qubits: Number of qubits (target dimension)

    Returns:
        X_train_processed: Processed training features
        X_val_processed: Processed validation features
        scaler: StandardScaler used (or None if not needed)
        pca: PCA transformer used (or None if not needed)
    """
    from sklearn.decomposition import PCA
    from sklearn.preprocessing import StandardScaler

    # Standardize features
    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    X_val = scaler.transform(X_val)

    n_features = X_train.shape[1]
    pca = None

    if n_features < n_qubits:
        # Pad with zeros if we have fewer features than qubits
        pad_width = n_qubits - n_features
        X_train = np.pad(X_train, ((0, 0), (0, pad_width)))
        X_val = np.pad(X_val, ((0, 0), (0, pad_width)))
    elif n_features > n_qubits:
        # Use PCA to reduce dimensions
        pca = PCA(n_components=n_qubits, random_state=42)
        X_train = pca.fit_transform(X_train)
        X_val = pca.transform(X_val)

    return X_train, X_val, scaler, pca
