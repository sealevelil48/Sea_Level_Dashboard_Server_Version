# Redis Installation Script for Windows
# Run this in PowerShell as Administrator

Write-Host "Installing Redis for Sea Level Dashboard..." -ForegroundColor Cyan

# Method 1: Try Chocolatey
try {
    choco --version | Out-Null
    Write-Host "Installing Redis via Chocolatey..." -ForegroundColor Yellow
    choco install redis-64 -y
    Write-Host "Starting Redis service..." -ForegroundColor Yellow
    redis-server --maxmemory 512mb --maxmemory-policy allkeys-lru
} catch {
    Write-Host "Chocolatey not found. Manual installation required." -ForegroundColor Red
    Write-Host ""
    Write-Host "MANUAL INSTALLATION STEPS:" -ForegroundColor Yellow
    Write-Host "1. Download Redis from: https://github.com/microsoftarchive/redis/releases" -ForegroundColor White
    Write-Host "2. Download: Redis-x64-3.0.504.msi" -ForegroundColor White
    Write-Host "3. Install and start Redis service" -ForegroundColor White
    Write-Host "4. Or use WSL: wsl --install then 'sudo apt install redis-server'" -ForegroundColor White
    Write-Host ""
    Write-Host "ALTERNATIVE - Use Redis Cloud (Free):" -ForegroundColor Green
    Write-Host "1. Visit: https://redis.com/try-free/" -ForegroundColor White
    Write-Host "2. Create free account (30MB free)" -ForegroundColor White
    Write-Host "3. Get connection string and update .env file" -ForegroundColor White
}

Write-Host ""
Write-Host "After Redis is running, restart your backend to enable caching!" -ForegroundColor Green