<#
.SYNOPSIS
    Automated threshold tuning based on Application Insights metrics.

.DESCRIPTION
    Analyzes slow query metrics from Application Insights to recommend optimal
    QAI_SQL_SLOW_MS threshold values. Uses P50/P95/P99 percentiles and alert
    frequency to balance sensitivity vs. noise.

.PARAMETER ResourceGroup
    Azure resource group containing the Function App.

.PARAMETER FunctionAppName
    Name of the Azure Function App to analyze.

.PARAMETER DaysBack
    Number of days of historical data to analyze (default: 7).

.PARAMETER TargetAlertsPerDay
    Target number of slow query alerts per day (default: 5).

.PARAMETER Apply
    Automatically apply the recommended threshold to Azure Function App settings.

.PARAMETER OutputFile
    Path to save the analysis report (default: data_out/threshold_analysis.json).

.EXAMPLE
    .\tune_sql_thresholds.ps1 -ResourceGroup "qai-rg" -FunctionAppName "qai-func"

.EXAMPLE
    .\tune_sql_thresholds.ps1 -ResourceGroup "qai-rg" -FunctionAppName "qai-func" -Apply
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$ResourceGroup,

    [Parameter(Mandatory = $true)]
    [string]$FunctionAppName,

    [Parameter(Mandatory = $false)]
    [int]$DaysBack = 7,

    [Parameter(Mandatory = $false)]
    [int]$TargetAlertsPerDay = 5,

    [Parameter(Mandatory = $false)]
    [switch]$Apply,

    [Parameter(Mandatory = $false)]
    [string]$OutputFile
)

$ErrorActionPreference = "Stop"
$ScriptRoot = Split-Path -Parent $PSScriptRoot

if (-not $OutputFile) {
    $OutputFile = Join-Path $ScriptRoot "data_out\threshold_analysis_$(Get-Date -Format 'yyyyMMdd_HHmmss').json"
}

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $colors = @{ "INFO" = "White"; "SUCCESS" = "Green"; "WARNING" = "Yellow"; "ERROR" = "Red" }
    Write-Host "[$Level] $Message" -ForegroundColor $colors[$Level]
}

function Get-ApplicationInsightsId {
    Write-Log "Retrieving Application Insights component ID..."
    
    try {
        $funcApp = az functionapp show --name $FunctionAppName --resource-group $ResourceGroup 2>$null | ConvertFrom-Json
        
        if (-not $funcApp) {
            throw "Function App '$FunctionAppName' not found"
        }
        
        $appInsightsKey = $funcApp.siteConfig.appSettings | Where-Object { $_.name -eq "APPINSIGHTS_INSTRUMENTATIONKEY" } | Select-Object -ExpandProperty value
        
        if (-not $appInsightsKey) {
            throw "Application Insights not configured for Function App"
        }
        
        # Get App Insights component from instrumentation key
        $components = az monitor app-insights component show --resource-group $ResourceGroup 2>$null | ConvertFrom-Json
        
        if ($components -is [array]) {
            $component = $components | Where-Object { $_.instrumentationKey -eq $appInsightsKey } | Select-Object -First 1
        } else {
            $component = $components
        }
        
        if (-not $component) {
            throw "Could not find Application Insights component with instrumentation key"
        }
        
        Write-Log "Found Application Insights: $($component.name)" "SUCCESS"
        return $component.id
    } catch {
        Write-Log "Failed to retrieve Application Insights ID: $_" "ERROR"
        throw
    }
}

function Invoke-KustoQuery {
    param(
        [string]$AppInsightsId,
        [string]$Query
    )
    
    try {
        $result = az monitor app-insights query `
            --app $AppInsightsId `
            --analytics-query $Query `
            --output json 2>&1 | ConvertFrom-Json
        
        if ($result.tables -and $result.tables[0].rows) {
            return $result.tables[0].rows
        }
        
        return @()
    } catch {
        Write-Log "Kusto query failed: $_" "ERROR"
        return @()
    }
}

function Get-QueryPercentiles {
    param([string]$AppInsightsId)
    
    Write-Log "Analyzing query execution times (P50/P95/P99)..."
    
    $query = @"
traces
| where timestamp > ago($($DaysBack)d)
| where message has "[sql_engine] slow query"
| extend duration_ms = todouble(extract(@"slow query \((\d+\.\d+) ms", 1, message))
| where isnotnull(duration_ms)
| summarize 
    P50 = percentile(duration_ms, 50),
    P95 = percentile(duration_ms, 95),
    P99 = percentile(duration_ms, 99),
    Count = count()
"@
    
    $rows = Invoke-KustoQuery -AppInsightsId $AppInsightsId -Query $query
    
    if ($rows.Count -eq 0) {
        Write-Log "No slow query data found in last $DaysBack days" "WARNING"
        return $null
    }
    
    $result = @{
        P50 = [math]::Round($rows[0][0], 2)
        P95 = [math]::Round($rows[0][1], 2)
        P99 = [math]::Round($rows[0][2], 2)
        Count = $rows[0][3]
    }
    
    Write-Log "P50: $($result.P50) ms | P95: $($result.P95) ms | P99: $($result.P99) ms | Count: $($result.Count)" "SUCCESS"
    
    return $result
}

function Get-AlertFrequency {
    param([string]$AppInsightsId)
    
    Write-Log "Calculating current alert frequency..."
    
    $query = @"
traces
| where timestamp > ago($($DaysBack)d)
| where message has "[sql_engine] slow query"
| summarize AlertCount = count()
| extend DailyAverage = AlertCount / $DaysBack
"@
    
    $rows = Invoke-KustoQuery -AppInsightsId $AppInsightsId -Query $query
    
    if ($rows.Count -eq 0) {
        return @{ TotalAlerts = 0; DailyAverage = 0 }
    }
    
    $result = @{
        TotalAlerts = $rows[0][0]
        DailyAverage = [math]::Round($rows[0][1], 2)
    }
    
    Write-Log "Alert frequency: $($result.DailyAverage) per day (total: $($result.TotalAlerts) over $DaysBack days)" "SUCCESS"
    
    return $result
}

function Get-CurrentThreshold {
    Write-Log "Retrieving current QAI_SQL_SLOW_MS setting..."
    
    try {
        $settings = az functionapp config appsettings list `
            --name $FunctionAppName `
            --resource-group $ResourceGroup `
            --output json 2>$null | ConvertFrom-Json
        
        $currentSetting = $settings | Where-Object { $_.name -eq "QAI_SQL_SLOW_MS" } | Select-Object -ExpandProperty value
        
        if ($currentSetting) {
            Write-Log "Current QAI_SQL_SLOW_MS: $currentSetting ms" "SUCCESS"
            return [int]$currentSetting
        } else {
            Write-Log "QAI_SQL_SLOW_MS not explicitly set (using environment default)" "WARNING"
            
            # Check environment
            $envSetting = $settings | Where-Object { $_.name -eq "AZURE_FUNCTIONS_ENVIRONMENT" } | Select-Object -ExpandProperty value
            
            $defaultThresholds = @{
                "development" = 100
                "staging" = 300
                "production" = 500
            }
            
            $threshold = $defaultThresholds[$envSetting]
            if ($threshold) {
                Write-Log "Using environment default: $threshold ms (environment: $envSetting)" "INFO"
                return $threshold
            }
            
            Write-Log "Using fallback default: 500 ms" "INFO"
            return 500
        }
    } catch {
        Write-Log "Failed to retrieve current threshold: $_" "ERROR"
        return 500  # Fallback
    }
}

function Calculate-RecommendedThreshold {
    param(
        [hashtable]$Percentiles,
        [hashtable]$AlertFrequency,
        [int]$CurrentThreshold
    )
    
    Write-Log "Calculating recommended threshold..."
    
    if (-not $Percentiles) {
        Write-Log "Insufficient data to recommend threshold" "WARNING"
        return @{
            Recommended = $CurrentThreshold
            Rationale = "No slow query data available - keeping current threshold"
            Confidence = "Low"
        }
    }
    
    # Decision logic
    $recommendation = @{}
    
    if ($AlertFrequency.DailyAverage -gt ($TargetAlertsPerDay * 2)) {
        # Too many alerts - increase threshold
        $newThreshold = [math]::Ceiling($Percentiles.P95 * 1.2)
        $recommendation = @{
            Recommended = $newThreshold
            Rationale = "Alert frequency ($($AlertFrequency.DailyAverage)/day) exceeds target ($TargetAlertsPerDay/day). Raising threshold to P95 * 1.2 to reduce noise."
            Confidence = "High"
        }
    }
    elseif ($AlertFrequency.DailyAverage -lt ($TargetAlertsPerDay * 0.5)) {
        # Too few alerts - decrease threshold if not already aggressive
        if ($CurrentThreshold -gt ($Percentiles.P95 * 1.1)) {
            $newThreshold = [math]::Ceiling($Percentiles.P95 * 1.1)
            $recommendation = @{
                Recommended = $newThreshold
                Rationale = "Alert frequency ($($AlertFrequency.DailyAverage)/day) is below target ($TargetAlertsPerDay/day). Lowering threshold to P95 * 1.1 for earlier detection."
                Confidence = "Medium"
            }
        } else {
            $recommendation = @{
                Recommended = $CurrentThreshold
                Rationale = "Alert frequency is low, but current threshold is already near P95. No change recommended."
                Confidence = "Medium"
            }
        }
    }
    else {
        # Alert frequency is in target range
        $recommendation = @{
            Recommended = $CurrentThreshold
            Rationale = "Alert frequency ($($AlertFrequency.DailyAverage)/day) is within target range ($TargetAlertsPerDay ± 50%). Current threshold is optimal."
            Confidence = "High"
        }
    }
    
    Write-Log "Recommended: $($recommendation.Recommended) ms" "SUCCESS"
    Write-Log "Rationale: $($recommendation.Rationale)" "INFO"
    
    return $recommendation
}

function Set-AzureThreshold {
    param([int]$Threshold)
    
    Write-Log "Applying new threshold: $Threshold ms" "INFO"
    
    try {
        $result = az functionapp config appsettings set `
            --name $FunctionAppName `
            --resource-group $ResourceGroup `
            --settings "QAI_SQL_SLOW_MS=$Threshold" `
            --output json 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-Log "Threshold applied successfully" "SUCCESS"
            Write-Log "Function App will restart to apply changes" "WARNING"
            return $true
        } else {
            Write-Log "Failed to apply threshold: $result" "ERROR"
            return $false
        }
    } catch {
        Write-Log "Exception applying threshold: $_" "ERROR"
        return $false
    }
}

function Save-AnalysisReport {
    param([hashtable]$Analysis)
    
    $null = New-Item -ItemType Directory -Force -Path (Split-Path $OutputFile -Parent)
    $Analysis | ConvertTo-Json -Depth 5 | Set-Content -Path $OutputFile
    Write-Log "Analysis report saved to: $OutputFile" "SUCCESS"
}

# ========================================
# Main Execution
# ========================================

Write-Log "========================================" "INFO"
Write-Log "SQL Threshold Auto-Tuning" "INFO"
Write-Log "========================================" "INFO"

$analysis = @{
    timestamp = (Get-Date -Format "o")
    functionApp = $FunctionAppName
    resourceGroup = $ResourceGroup
    daysAnalyzed = $DaysBack
    targetAlertsPerDay = $TargetAlertsPerDay
}

try {
    # Step 1: Get Application Insights ID
    $appInsightsId = Get-ApplicationInsightsId
    $analysis.appInsightsId = $appInsightsId
    
    # Step 2: Get current threshold
    $currentThreshold = Get-CurrentThreshold
    $analysis.currentThreshold = $currentThreshold
    
    # Step 3: Analyze percentiles
    $percentiles = Get-QueryPercentiles -AppInsightsId $appInsightsId
    $analysis.percentiles = $percentiles
    
    # Step 4: Analyze alert frequency
    $alertFrequency = Get-AlertFrequency -AppInsightsId $appInsightsId
    $analysis.alertFrequency = $alertFrequency
    
    # Step 5: Calculate recommendation
    $recommendation = Calculate-RecommendedThreshold `
        -Percentiles $percentiles `
        -AlertFrequency $alertFrequency `
        -CurrentThreshold $currentThreshold
    
    $analysis.recommendation = $recommendation
    
    # Step 6: Apply if requested
    if ($Apply) {
        if ($recommendation.Recommended -ne $currentThreshold) {
            $applied = Set-AzureThreshold -Threshold $recommendation.Recommended
            $analysis.applied = $applied
        } else {
            Write-Log "No change needed - skipping apply" "INFO"
            $analysis.applied = $false
        }
    } else {
        Write-Log "Recommendation generated. Use -Apply flag to automatically apply." "INFO"
        $analysis.applied = $false
    }
    
    # Step 7: Save report
    Save-AnalysisReport -Analysis $analysis
    
    Write-Log ""
    Write-Log "========================================" "SUCCESS"
    Write-Log "Analysis Complete" "SUCCESS"
    Write-Log "========================================" "SUCCESS"
    
    exit 0
    
} catch {
    Write-Log "Auto-tuning failed: $_" "ERROR"
    $analysis.error = $_.ToString()
    Save-AnalysisReport -Analysis $analysis
    exit 1
}
