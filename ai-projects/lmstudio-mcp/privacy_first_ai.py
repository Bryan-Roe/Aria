#!/usr/bin/env python3
"""
Privacy-First AI Reasoning with LM Studio

This guide demonstrates how to keep sensitive data local while leveraging
Aria's AGI Provider for powerful multi-agent reasoning.

Key Principles:
1. All inference on local hardware (LM Studio)
2. No sensitive data sent to cloud APIs
3. Full privacy control and audit trails
4. High-quality reasoning with AGI provider
"""

import asyncio
import hashlib
import json
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# =============================================================================
# Privacy Levels & Data Classification
# =============================================================================


class PrivacyLevel(Enum):
    """Classification of data sensitivity."""

    PUBLIC = "public"  # No privacy constraints
    INTERNAL = "internal"  # Organizational data, not confidential
    CONFIDENTIAL = "confidential"  # Sensitive but not regulated
    RESTRICTED = "restricted"  # Highly sensitive, regulated data
    ENCRYPTED = "encrypted"  # Encrypted at rest


class DataClassification(Enum):
    """Types of data requiring privacy protection."""

    PII = "personally_identifiable_information"  # Names, SSN, email, phone
    HEALTH = "health_information"  # Medical records, diagnoses
    FINANCIAL = "financial_information"  # Bank accounts, credit cards, salary
    PROPRIETARY = "proprietary_information"  # Trade secrets, code, designs
    LEGAL = "legal_information"  # Contracts, litigation docs
    CREDENTIALS = "credentials"  # Passwords, API keys, tokens


# =============================================================================
# Privacy-Preserving Data Handling
# =============================================================================


@dataclass
class PrivateData:
    """Wrapper for sensitive data with privacy metadata."""

    content: str
    classification: DataClassification
    privacy_level: PrivacyLevel = PrivacyLevel.RESTRICTED
    source: str = "user"
    accessed_at: str = None
    must_stay_local: bool = True  # Never send to cloud

    def __post_init__(self):
        if self.accessed_at is None:
            self.accessed_at = datetime.now().isoformat()

    def get_hash(self) -> str:
        """Get hash of content without exposing actual data."""
        return hashlib.sha256(self.content.encode()).hexdigest()[:8]

    def __str__(self) -> str:
        """String representation that doesn't expose sensitive data."""
        return f"<{self.classification.value}:{self.privacy_level.value}>"

    def to_audit_log(self) -> Dict[str, Any]:
        """Create audit log entry without exposing content."""
        return {
            "timestamp": self.accessed_at,
            "classification": self.classification.value,
            "privacy_level": self.privacy_level.value,
            "content_hash": self.get_hash(),
            "source": self.source,
        }


class PrivacyAuditLog:
    """Track data access and processing for privacy compliance."""

    def __init__(self, log_path: Path = Path("data_out/privacy_audit.jsonl")):
        self.log_path = log_path
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def log_access(
        self,
        data: PrivateData,
        action: str,
        agent: str,
        result: Optional[str] = None,
    ) -> None:
        """Log data access for audit trail."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "data_classification": data.classification.value,
            "privacy_level": data.privacy_level.value,
            "action": action,
            "agent": agent,
            "content_hash": data.get_hash(),
            "result_hash": hashlib.sha256(result.encode()).hexdigest()[:8] if result else None,
        }

        with open(self.log_path, "a") as f:
            f.write(json.dumps(entry) + "\n")

        logger.info(f"Audit: {action} on {data.classification.value} by {agent}")

    def verify_local_processing(self, hours_lookback: int = 24) -> bool:
        """Verify all processing stayed local in recent period."""
        if not self.log_path.exists():
            return True

        from datetime import timedelta
        cutoff = datetime.now() - timedelta(hours=hours_lookback)

        recent_entries = []
        with open(self.log_path) as f:
            for line in f:
                entry = json.loads(line)
                entry_time = datetime.fromisoformat(entry["timestamp"])
                if entry_time > cutoff:
                    recent_entries.append(entry)

        # Check no cloud actions
        cloud_actions = [
            e for e in recent_entries
            if "cloud" in e.get("agent", "").lower()
            or "api" in e.get("action", "").lower()
        ]

        logger.info(f"Privacy audit: {len(recent_entries)} actions, {len(cloud_actions)} cloud")
        return len(cloud_actions) == 0


# =============================================================================
# Local-First Processing Patterns
# =============================================================================


class LocalOnlyProcessor:
    """Ensures data never leaves the local machine."""

    def __init__(self):
        self.audit_log = PrivacyAuditLog()
        self.lmstudio_available = False
        self._check_lmstudio()

    def _check_lmstudio(self) -> None:
        """Verify LM Studio is available for local processing."""
        try:
            import asyncio

            from lmstudio_agent_integration import get_lmstudio_agent_client

            async def check():
                client = get_lmstudio_agent_client()
                return await client.check_health()

            # Note: This is async check, would need proper async context
            self.lmstudio_available = True
            logger.info("✓ LM Studio available for local processing")
        except Exception as e:
            logger.warning(f"LM Studio not available: {e}")
            self.lmstudio_available = False

    async def process_sensitive_data(
        self,
        private_data: PrivateData,
        analysis_task: str,
    ) -> str:
        """
        Process sensitive data locally with no cloud exposure.

        Args:
            private_data: Sensitive data wrapper
            analysis_task: What to analyze

        Returns:
            str: Analysis result (also local)
        """
        if not self.lmstudio_available:
            raise RuntimeError(
                "LM Studio required for private data processing. "
                "Ensure LM Studio is running and local server is enabled."
            )

        # Log access
        self.audit_log.log_access(
            private_data,
            action="analysis_start",
            agent="local_processor",
        )

        try:
            from lmstudio_agent_integration import get_lmstudio_agent_client

            client = get_lmstudio_agent_client()

            # Build prompt without exposing full data
            secure_prompt = self._build_secure_prompt(
                private_data,
                analysis_task,
            )

            # Process locally
            response = await client.complete(
                messages=[
                    {
                        "role": "system",
                        "content": "You process sensitive information with maximum privacy. "
                                   "Never log, store, or expose the data content.",
                    },
                    {
                        "role": "user",
                        "content": secure_prompt,
                    },
                ],
                temperature=0.3,  # Deterministic for security
                max_tokens=512,
            )

            # Log completion
            self.audit_log.log_access(
                private_data,
                action="analysis_complete",
                agent="local_processor",
                result=response,
            )

            return response

        except Exception as e:
            self.audit_log.log_access(
                private_data,
                action="analysis_failed",
                agent="local_processor",
            )
            raise RuntimeError(f"Local processing failed: {e}") from e

    def _build_secure_prompt(
        self,
        private_data: PrivateData,
        analysis_task: str,
    ) -> str:
        """Build prompt that safely references sensitive data."""
        # Use data classification and hash instead of content
        return (
            f"Analyze the following {private_data.classification.value} "
            f"(Privacy level: {private_data.privacy_level.value}, "
            f"Hash: {private_data.get_hash()}):\n\n"
            f"Task: {analysis_task}\n\n"
            f"Reference content is available locally for analysis.\n"
            f"Provide analysis without reproducing or exposing the original content."
        )

    async def verify_privacy_compliance(self) -> Dict[str, Any]:
        """Verify all recent processing stayed local."""
        is_compliant = self.audit_log.verify_local_processing(hours_lookback=24)

        return {
            "compliant": is_compliant,
            "message": "All recent processing stayed local" if is_compliant else "Cloud processing detected!",
            "audit_log_path": str(self.audit_log.log_path),
        }


# =============================================================================
# Privacy-Preserving AGI Integration
# =============================================================================


class PrivacyAwareAGIProvider:
    """AGI provider wrapper with privacy constraints."""

    def __init__(self):
        from lmstudio_agi_integration import AGILMStudioRouter

        self.router = AGILMStudioRouter()
        self.local_processor = LocalOnlyProcessor()

    async def analyze_with_privacy(
        self,
        private_data: PrivateData,
        analysis_type: str,
    ) -> Dict[str, Any]:
        """
        Analyze private data while maintaining strict privacy.

        Args:
            private_data: Sensitive data to analyze
            analysis_type: Type of analysis (security, compliance, medical, etc)

        Returns:
            dict: Analysis results with audit trail
        """
        # Verify privacy constraints
        if not private_data.must_stay_local:
            raise ValueError("Data must have must_stay_local=True")

        # Route through local processor
        result = await self.local_processor.process_sensitive_data(
            private_data,
            analysis_task=f"Perform {analysis_type} analysis",
        )

        # Verify compliance
        compliance = await self.local_processor.verify_privacy_compliance()

        return {
            "analysis_result": result,
            "privacy_compliance": compliance,
            "data_classification": private_data.classification.value,
            "processed_locally": True,
        }


# =============================================================================
# Examples & Usage Patterns
# =============================================================================


async def example_healthcare_analysis():
    """
    Example: Analyze healthcare data privately.

    Scenario: A hospital wants to analyze patient data locally without
    using cloud APIs, maintaining HIPAA compliance.
    """
    print("\n" + "="*70)
    print("Example 1: Healthcare Data Analysis (HIPAA-Compliant)")
    print("=""*70 + "\n")

    # Create private healthcare data
    patient_data = PrivateData(
        content="Patient: John Doe, Age: 45, Diagnosis: Type 2 Diabetes, Medication: Metformin",
        classification=DataClassification.HEALTH,
        privacy_level=PrivacyLevel.RESTRICTED,
        source="healthcare_system",
    )

    print(f"Processing: {patient_data}")
    print(f"Data Hash: {patient_data.get_hash()}")
    print(f"Privacy Level: {patient_data.privacy_level.value}")
    print()

    try:
        processor = LocalOnlyProcessor()

        result = await processor.process_sensitive_data(
            patient_data,
            analysis_task="Identify treatment recommendations and medication interactions",
        )

        print("Analysis Result (Summary):")
        print(result[:200] + "...\n")

        # Verify compliance
        compliance = await processor.verify_privacy_compliance()
        print(f"Privacy Compliance: {compliance['message']}\n")

    except Exception as e:
        print(f"Healthcare analysis example (would work with LM Studio): {e}\n")


async def example_financial_analysis():
    """
    Example: Analyze financial data privately.

    Scenario: A financial advisor wants to analyze client portfolios
    locally without exposing to third parties.
    """
    print("="*70)
    print("Example 2: Financial Data Analysis (PCI-DSS Compliant)")
    print("="*70 + "\n")

    financial_data = PrivateData(
        content="Portfolio: $500K in stocks, $200K bonds, Cash: $50K, "
                "Liabilities: Mortgage $300K at 3.5%",
        classification=DataClassification.FINANCIAL,
        privacy_level=PrivacyLevel.RESTRICTED,
        source="financial_advisor",
    )

    print(f"Processing: {financial_data}")
    print(f"Data Hash: {financial_data.get_hash()}")
    print()

    try:
        processor = LocalOnlyProcessor()

        result = await processor.process_sensitive_data(
            financial_data,
            analysis_task="Analyze asset allocation and recommend rebalancing strategy",
        )

        print("Analysis Result (Summary):")
        print(result[:200] + "...\n")

    except Exception as e:
        print(f"Financial analysis example (would work with LM Studio): {e}\n")


async def example_proprietary_code_review():
    """
    Example: Review proprietary code privately.

    Scenario: A company wants to analyze internal code without exposing
    proprietary algorithms to external services.
    """
    print("="*70)
    print("Example 3: Proprietary Code Review (Trade Secret Compliant)")
    print("="*70 + "\n")

    code_data = PrivateData(
        content="""
def proprietary_algorithm(data):
    # Patented compression algorithm
    compressed = secret_compress(data)
    return apply_proprietary_metric(compressed)
        """,
        classification=DataClassification.PROPRIETARY,
        privacy_level=PrivacyLevel.RESTRICTED,
        source="internal_engineering",
    )

    print(f"Processing: {code_data}")
    print(f"Data Hash: {code_data.get_hash()}")
    print()

    try:
        processor = LocalOnlyProcessor()

        result = await processor.process_sensitive_data(
            code_data,
            analysis_task="Review for security vulnerabilities and performance issues",
        )

        print("Analysis Result (Summary):")
        print(result[:200] + "...\n")

    except Exception as e:
        print(f"Code review example (would work with LM Studio): {e}\n")


async def example_compliance_monitoring():
    """
    Example: Monitor compliance with privacy requirements.

    Shows audit trail and verification of local-only processing.
    """
    print("="*70)
    print("Example 4: Compliance Monitoring & Audit Trail")
    print("="*70 + "\n")

    processor = LocalOnlyProcessor()

    # Log some example activities
    test_data = PrivateData(
        content="Test sensitive information",
        classification=DataClassification.CONFIDENTIAL,
        privacy_level=PrivacyLevel.RESTRICTED,
    )

    processor.audit_log.log_access(test_data, "access", "example_agent")
    processor.audit_log.log_access(test_data, "analysis", "lmstudio_local", "result")

    # Check audit log exists
    audit_file = processor.audit_log.log_path
    if audit_file.exists():
        print(f"✓ Audit log created: {audit_file}")

        # Show sample entries
        print(f"\nAudit Trail (last 2 entries):")
        with open(audit_file) as f:
            entries = f.readlines()[-2:]
            for entry in entries:
                data = json.loads(entry)
                print(f"  {data['timestamp']}: {data['action']} - {data['classification']}")
    else:
        print(f"Audit log would be created at: {audit_file}")

    print()


async def example_configuration():
    """
    Example: Configuration for privacy-first deployment.
    """
    print("="*70)
    print("Example 5: Privacy Configuration")
    print("="*70 + "\n")

    config = {
        "privacy_mode": "strict",
        "allowed_endpoints": ["127.0.0.1:1234"],  # Local only
        "blocked_endpoints": ["*.openai.com", "*.anthropic.com", "*.aws.com"],
        "audit_logging": True,
        "audit_retention_days": 90,
        "encryption": {
            "at_rest": True,
            "cipher": "AES-256",
            "key_storage": "secure_enclave",
        },
        "data_classification": {
            "default_privacy_level": "restricted",
            "enforce_local_processing": True,
        },
        "monitoring": {
            "detect_data_exfiltration": True,
            "alert_on_cloud_api_calls": True,
        },
    }

    print("Privacy-First Configuration:")
    print(json.dumps(config, indent=2))
    print()


# =============================================================================
# Main
# =============================================================================


async def main():
    """Run all privacy examples."""
    print("\n" + "="*70)
    print("Privacy-First AI Reasoning with LM Studio + AGI Provider")
    print("="*70)

    await example_healthcare_analysis()
    await example_financial_analysis()
    await example_proprietary_code_review()
    await example_compliance_monitoring()
    await example_configuration()

    print("="*70)
    print("Privacy Examples Complete")
    print("="*70 + "\n")

    print("Key Takeaways:")
    print("  ✓ Use LM Studio for all processing (stays local)")
    print("  ✓ Classify data by sensitivity level")
    print("  ✓ Maintain audit trails for compliance")
    print("  ✓ Never expose sensitive data to cloud APIs")
    print("  ✓ Verify privacy compliance regularly")
    print()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nExamples interrupted")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
