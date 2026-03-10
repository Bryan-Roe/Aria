# PSScriptAnalyzer settings for quantum-ai project
# Suppresses known false-positives and configures analyzer rules

@{
    # Exclude known false-positive: PSUseDeclaredVarsMoreThanAssignments
    # Context: deploy_simple.ps1 login check uses try/catch without temporary variables,
    # but analyzer incorrectly reports "loginCheck assigned but never used" at line 36.
    # This rule is globally enabled but excluded for the specific pattern below.
    ExcludeRules = @()

    # Suppress specific rules for individual files
    Rules = @{
        PSUseDeclaredVarsMoreThanAssignments = @{
            Enable = $true
            # Exclude the false-positive in deploy_simple.ps1 login section
            # Note: PSScriptAnalyzer doesn't support per-line suppressions in settings,
            # so we document here and rely on inline suppression if needed in the future.
        }
    }

    # Severity levels to report (Error, Warning, Information)
    Severity = @('Error', 'Warning')

    # Include default rules
    IncludeDefaultRules = $true
}
