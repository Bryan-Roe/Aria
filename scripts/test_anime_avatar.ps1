# Test Anime Avatar Interactive Script
# Demonstrates the anime persona with various questions

$modelPath = "deployed_models\anime_avatar_v2_20251126_000131\lora_adapter"

Write-Host "`n╔════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   🌸 Anime Avatar Test Suite 🌸          ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════╝`n" -ForegroundColor Cyan

# Test 1: Introduction
Write-Host "📝 Test 1: Introduction" -ForegroundColor Yellow
Write-Host "Question: Hello Aria! Tell me about yourself!`n" -ForegroundColor Gray
python .\talk-to-ai\src\chat_cli.py --provider lora --model $modelPath --once "Hello Aria! Tell me about yourself!" 2>$null
Write-Host "`n" -NoNewline

Start-Sleep -Seconds 2

# Test 2: Technical Help
Write-Host "`n📝 Test 2: Technical Explanation" -ForegroundColor Yellow
Write-Host "Question: Can you explain what APIs are?`n" -ForegroundColor Gray
python .\talk-to-ai\src\chat_cli.py --provider lora --model $modelPath --once "Aria, can you explain what APIs are in simple terms?" 2>$null
Write-Host "`n" -NoNewline

Start-Sleep -Seconds 2

# Test 3: Emotional Support
Write-Host "`n📝 Test 3: Emotional Support" -ForegroundColor Yellow
Write-Host "Question: I'm feeling discouraged about learning to code...`n" -ForegroundColor Gray
python .\talk-to-ai\src\chat_cli.py --provider lora --model $modelPath --once "Aria-chan, I'm feeling discouraged about learning to code. Can you motivate me?" 2>$null
Write-Host "`n" -NoNewline

Start-Sleep -Seconds 2

# Test 4: Debugging Help
Write-Host "`n📝 Test 4: Debugging Mindset" -ForegroundColor Yellow
Write-Host "Question: What's a good approach to debugging code?`n" -ForegroundColor Gray
python .\talk-to-ai\src\chat_cli.py --provider lora --model $modelPath --once "Aria, what's your advice for debugging tricky code issues?" 2>$null

Write-Host "`n`n╔════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║   ✨ Test Suite Complete! ✨             ║" -ForegroundColor Green
Write-Host "╚════════════════════════════════════════════╝`n" -ForegroundColor Green

Write-Host "🎯 Next Steps:" -ForegroundColor Cyan
Write-Host "  • For interactive chat: python .\talk-to-ai\src\chat_cli.py --provider lora --model $modelPath"
Write-Host "  • For web interface: Open http://localhost:7071/api/chat-web (server already running)"
Write-Host "  • Deploy to Azure: Follow AZURE_DEPLOYMENT_ANIME_AVATAR.md`n"
