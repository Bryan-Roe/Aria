# Pre-commit hook - Run fast tests before allowing commit
#
# Installation:
#   git config core.hooksPath .githooks
#
# To bypass (for emergency commits):
#   git commit --no-verify

Write-Host "🧪 Running pre-commit tests..." -ForegroundColor Cyan

# Run fast unit tests only (skip slow/integration)
python scripts/test_runner.py --unit --verbose 0

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Tests passed - proceeding with commit" -ForegroundColor Green
    exit 0
} else {
    Write-Host "❌ Tests failed - commit blocked" -ForegroundColor Red
    Write-Host ""
    Write-Host "To fix:"
    Write-Host "  1. Review test failures above"
    Write-Host "  2. Fix the issues and try again"
    Write-Host "  3. Or bypass with: git commit --no-verify (not recommended)"
    exit 1
}
