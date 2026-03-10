# PowerShell Script Analyzer Configuration for quantum-ai
# This file configures PSScriptAnalyzer to suppress known false-positives

# To apply this in VS Code, ensure the PowerShell extension setting points to this file:
# "powershell.scriptAnalysis.settingsPath": "PSScriptAnalyzerSettings.psd1"

@{
    # Include default rules but allow selective exclusions below
    IncludeDefaultRules = $true

    # Global severity filter (Error, Warning, Information)
    Severity = @('Error', 'Warning')

    # Exclude specific rules globally or per-file
    # Note: PSScriptAnalyzer has limited per-line suppression in .psd1 config;
    # inline [Diagnostics.CodeAnalysis.SuppressMessageAttribute] is preferred for targeted suppression.
    ExcludeRules = @(
        # Suppress false-positive in deploy_simple.ps1 where analyzer reports
        # "loginCheck assigned but never used" despite no such variable in code.
        # This appears to be an analyzer bug with try/catch + $LASTEXITCODE patterns.
        # Inline suppression added to deploy_simple.ps1 header as primary mitigation.
    )

    # Rule-specific configuration
    Rules = @{
        # Allow justified use of declared variables in scripts relying on side effects
        PSUseDeclaredVarsMoreThanAssignments = @{
            Enable = $true
        }

        # Ensure cmdlets are used instead of aliases in production scripts
        PSAvoidUsingCmdletAliases = @{
            Enable = $true
        }
    }
}
