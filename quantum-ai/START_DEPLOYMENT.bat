@echo off
echo ========================================
echo   STARTING AZURE QUANTUM DEPLOYMENT
echo ========================================
echo.
echo Opening fresh PowerShell with Azure CLI...
echo.

start powershell -NoExit -Command "cd 'c:\Users\Bryan\OneDrive\AI\quantum-ai'; Write-Host '========================================' -ForegroundColor Cyan; Write-Host '  AZURE QUANTUM DEPLOYMENT' -ForegroundColor Yellow; Write-Host '========================================' -ForegroundColor Cyan; Write-Host ''; Write-Host 'Verifying Azure CLI...' -ForegroundColor Yellow; az --version | Select-Object -First 3; Write-Host ''; Write-Host '========================================' -ForegroundColor Cyan; Write-Host '  STARTING DEPLOYMENT SCRIPT' -ForegroundColor Yellow; Write-Host '========================================' -ForegroundColor Cyan; Write-Host ''; .\deploy_azure_quantum.ps1"

echo.
echo A new PowerShell window should open with the deployment script running.
echo If not, check if any windows were blocked.
echo.
pause
