# Self-Learning Chat Quick Start
# Run this to set up and start the self-learning system

# Set preference to display Information messages
$InformationPreference = 'Continue'

Write-Information "`n"
Write-Information ("=" * 70)
Write-Information "SELF-LEARNING CHAT - QUICK START"
Write-Information ("=" * 70)

# Step 1: Check current status
Write-Information "`n[1/4] Checking current status..."
python .\scripts\analyze_learning_progress.py

# Step 2: Generate test data if needed
Write-Information "`n[2/4] Checking conversation data..."
$status = Get-Content "data_out\self_learning\status.json" -ErrorAction SilentlyContinue | ConvertFrom-Json
if ($status -and $status.conversations_since_last_train -lt 20) {
    Write-Information "Generating test conversations..."
    python .\scripts\generate_test_conversations.py
} else {
    Write-Information "Sufficient conversations available"
}

# Step 3: Run training cycle
Write-Information "`n[3/4] Running training cycle..."
Write-Information "This may take 5-10 minutes..."
python .\scripts\self_learning_chat.py --min-conversations 10 --max-samples 64 --epochs 1

# Step 4: Show results
Write-Information "`n[4/4] Training complete! Showing results..."
python .\scripts\analyze_learning_progress.py

Write-Information "`n"
Write-Information ("=" * 70)
Write-Information "QUICK START COMPLETE"
Write-Information ("=" * 70)
Write-Information ""
Write-Information "NEXT STEPS:"
Write-Information "  1. Restart Azure Functions to use new model:"
Write-Information "     Get-Process -Name 'func' | Stop-Process -Force"
Write-Information "     func host start"
Write-Information "  2. Test improved model via chat"
Write-Information "  3. For continuous learning:"
Write-Information "     python .\scripts\self_learning_chat.py --mode continuous"
Write-Information ""
