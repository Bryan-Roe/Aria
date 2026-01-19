"""
Dataset Quality Validator
Validates dataset integrity, quality, and compliance with training requirements
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import pandas as pd
import numpy as np
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatasetValidator:
    """Validates dataset quality and integrity"""
    
    def __init__(self):
        self.datasets_dir = Path("datasets")
        self.validation_report = {
            "timestamp": datetime.now().isoformat(),
            "total_datasets": 0,
            "valid_datasets": 0,
            "failed_datasets": 0,
            "issues": [],
            "quality_scores": {}
        }
    
    def validate_csv_dataset(self, filepath: Path) -> Tuple[bool, Dict, float]:
        """Validate a CSV dataset"""
        issues = []
        quality_score = 100.0
        
        try:
            df = pd.read_csv(filepath)
            
            # Check 1: Minimum rows
            if len(df) < 10:
                issues.append(f"Too few samples: {len(df)} < 10")
                quality_score -= 30
            
            # Check 2: Minimum columns
            if len(df.columns) < 2:
                issues.append(f"Too few features: {len(df.columns)} < 2")
                quality_score -= 20
            
            # Check 3: Missing values
            missing_ratio = df.isnull().sum().sum() / (len(df) * len(df.columns))
            if missing_ratio > 0.5:
                issues.append(f"Too many missing values: {missing_ratio:.1%}")
                quality_score -= 30
            elif missing_ratio > 0.2:
                issues.append(f"High missing values: {missing_ratio:.1%}")
                quality_score -= 15
            
            # Check 4: Data types
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) == 0:
                issues.append("No numeric columns found")
                quality_score -= 25
            
            # Check 5: Duplicate rows
            dup_ratio = df.duplicated().sum() / len(df)
            if dup_ratio > 0.5:
                issues.append(f"Too many duplicates: {dup_ratio:.1%}")
                quality_score -= 20
            elif dup_ratio > 0.2:
                issues.append(f"High duplicates: {dup_ratio:.1%}")
                quality_score -= 10
            
            # Check 6: Column names
            if df.columns.duplicated().any():
                issues.append("Duplicate column names")
                quality_score -= 15
            
            # Check 7: Data variance
            if len(numeric_cols) > 0:
                zero_var_cols = [col for col in numeric_cols if df[col].std() == 0]
                if zero_var_cols:
                    issues.append(f"Zero variance columns: {len(zero_var_cols)}")
                    quality_score -= 10
            
            # Metadata
            metadata = {
                "samples": len(df),
                "features": len(df.columns),
                "numeric_features": len(numeric_cols),
                "missing_ratio": missing_ratio,
                "duplicate_ratio": dup_ratio,
                "memory_mb": df.memory_usage(deep=True).sum() / 1024 / 1024
            }
            
            is_valid = quality_score >= 50 and len(df) >= 10
            
            return is_valid, {"issues": issues, "metadata": metadata}, quality_score
            
        except Exception as e:
            return False, {"issues": [f"Error reading file: {str(e)}"]}, 0.0
    
    def validate_jsonl_dataset(self, filepath: Path) -> Tuple[bool, Dict, float]:
        """Validate a JSONL dataset (chat format)"""
        issues = []
        quality_score = 100.0
        
        try:
            lines = []
            with open(filepath) as f:
                for line in f:
                    if line.strip():
                        lines.append(json.loads(line))
            
            # Check 1: Minimum samples
            if len(lines) < 10:
                issues.append(f"Too few samples: {len(lines)} < 10")
                quality_score -= 30
            
            # Check 2: Format validation
            valid_format = 0
            for item in lines:
                if "messages" in item and isinstance(item["messages"], list):
                    valid_format += 1
            
            format_ratio = valid_format / len(lines) if lines else 0
            if format_ratio < 0.8:
                issues.append(f"Invalid format ratio: {format_ratio:.1%}")
                quality_score -= 40
            elif format_ratio < 0.95:
                issues.append(f"Some format issues: {format_ratio:.1%}")
                quality_score -= 20
            
            # Check 3: Message structure
            role_issues = 0
            empty_content = 0
            
            for item in lines[:100]:  # Sample first 100
                if "messages" in item:
                    for msg in item["messages"]:
                        if "role" not in msg or msg["role"] not in ["user", "assistant", "system"]:
                            role_issues += 1
                        if "content" not in msg or not msg["content"].strip():
                            empty_content += 1
            
            if role_issues > 10:
                issues.append(f"Many invalid roles: {role_issues}")
                quality_score -= 15
            
            if empty_content > 10:
                issues.append(f"Many empty messages: {empty_content}")
                quality_score -= 15
            
            # Metadata
            metadata = {
                "samples": len(lines),
                "valid_format_ratio": format_ratio,
                "file_size_mb": filepath.stat().st_size / 1024 / 1024
            }
            
            is_valid = quality_score >= 50 and len(lines) >= 10
            
            return is_valid, {"issues": issues, "metadata": metadata}, quality_score
            
        except Exception as e:
            return False, {"issues": [f"Error reading file: {str(e)}"]}, 0.0
    
    def validate_directory(self, dirpath: Path, category: str) -> Dict:
        """Validate all datasets in a directory"""
        results = {
            "category": category,
            "path": str(dirpath),
            "files": [],
            "valid_count": 0,
            "invalid_count": 0
        }
        
        if not dirpath.exists():
            logger.warning(f"Directory not found: {dirpath}")
            return results
        
        # Find all dataset files
        csv_files = list(dirpath.glob("*.csv"))
        jsonl_files = list(dirpath.glob("*.jsonl"))
        
        # Also check subdirectories for chat datasets
        if category == "chat":
            for subdir in dirpath.iterdir():
                if subdir.is_dir():
                    jsonl_files.extend(subdir.glob("*.jsonl"))
        
        all_files = csv_files + jsonl_files
        
        logger.info(f"Validating {len(all_files)} files in {category}/")
        
        for filepath in all_files:
            if filepath.suffix == ".csv":
                is_valid, details, score = self.validate_csv_dataset(filepath)
            elif filepath.suffix == ".jsonl":
                is_valid, details, score = self.validate_jsonl_dataset(filepath)
            else:
                continue
            
            result = {
                "filename": filepath.name,
                "path": str(filepath),
                "valid": is_valid,
                "quality_score": score,
                "details": details
            }
            
            results["files"].append(result)
            
            if is_valid:
                results["valid_count"] += 1
            else:
                results["invalid_count"] += 1
                self.validation_report["issues"].append({
                    "file": str(filepath),
                    "issues": details.get("issues", [])
                })
            
            self.validation_report["quality_scores"][str(filepath)] = score
        
        return results
    
    def validate_all(self) -> Dict:
        """Validate all datasets in all categories"""
        logger.info("="*80)
        logger.info("🔍 Starting Comprehensive Dataset Validation")
        logger.info("="*80)
        
        categories = ["quantum", "chat", "vision"]
        all_results = {}
        
        for category in categories:
            dirpath = self.datasets_dir / category
            results = self.validate_directory(dirpath, category)
            all_results[category] = results
            
            self.validation_report["total_datasets"] += len(results["files"])
            self.validation_report["valid_datasets"] += results["valid_count"]
            self.validation_report["failed_datasets"] += results["invalid_count"]
            
            logger.info(f"{category}: {results['valid_count']} valid, {results['invalid_count']} invalid")
        
        # Check massive_quantum
        massive_dir = self.datasets_dir / "massive_quantum"
        if massive_dir.exists():
            results = self.validate_directory(massive_dir, "massive_quantum")
            all_results["massive_quantum"] = results
            
            self.validation_report["total_datasets"] += len(results["files"])
            self.validation_report["valid_datasets"] += results["valid_count"]
            self.validation_report["failed_datasets"] += results["invalid_count"]
            
            logger.info(f"massive_quantum: {results['valid_count']} valid, {results['invalid_count']} invalid")
        
        # Save report
        self.save_report(all_results)
        
        logger.info("="*80)
        logger.info("✅ Validation Complete!")
        logger.info(f"   Total: {self.validation_report['total_datasets']}")
        logger.info(f"   Valid: {self.validation_report['valid_datasets']}")
        logger.info(f"   Invalid: {self.validation_report['failed_datasets']}")
        logger.info(f"   Success Rate: {self.validation_report['valid_datasets']/max(1, self.validation_report['total_datasets'])*100:.1f}%")
        logger.info("="*80)
        
        return all_results
    
    def save_report(self, results: Dict):
        """Save validation report"""
        output_dir = Path("data_out/validation")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Full report
        report_file = output_dir / "validation_report.json"
        full_report = {
            "summary": self.validation_report,
            "details": results
        }
        
        with open(report_file, 'w') as f:
            json.dump(full_report, f, indent=2)
        
        logger.info(f"📄 Report saved to: {report_file}")
        
        # Issues summary
        if self.validation_report["issues"]:
            issues_file = output_dir / "validation_issues.txt"
            with open(issues_file, 'w') as f:
                f.write("Dataset Validation Issues\n")
                f.write("="*80 + "\n\n")
                
                for issue in self.validation_report["issues"]:
                    f.write(f"File: {issue['file']}\n")
                    for problem in issue['issues']:
                        f.write(f"  - {problem}\n")
                    f.write("\n")
            
            logger.info(f"📄 Issues saved to: {issues_file}")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate Dataset Quality")
    parser.add_argument("--category", help="Validate specific category only")
    
    args = parser.parse_args()
    
    validator = DatasetValidator()
    
    if args.category:
        dirpath = Path("datasets") / args.category
        results = validator.validate_directory(dirpath, args.category)
        print(json.dumps(results, indent=2))
    else:
        validator.validate_all()


if __name__ == "__main__":
    main()
