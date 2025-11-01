# Cache Performance Test Script
Write-Host "`n=== REDIS CACHE PERFORMANCE TEST ===" -ForegroundColor Cyan

$apiUrl = "http://localhost:30886/api/data?station=Haifa&limit=1000"

Write-Host "`n[1/3] Testing first request (should be CACHE MISS)..." -ForegroundColor Yellow
$result1 = Measure-Command { 
    try {
        $response1 = Invoke-WebRequest -Uri $apiUrl -Headers @{"Accept"="application/json"}
        $cache1 = $response1.Headers["X-Cache"]
        $time1 = $response1.Headers["X-Response-Time"]
        Write-Host "✅ Response Time: $time1" -ForegroundColor White
        Write-Host "✅ Cache Status: $cache1" -ForegroundColor White
    } catch {
        Write-Host "❌ Request failed: $($_.Exception.Message)" -ForegroundColor Red
        return
    }
}
Write-Host "Total Time: $($result1.TotalMilliseconds)ms" -ForegroundColor Cyan

Start-Sleep -Seconds 1

Write-Host "`n[2/3] Testing second request (should be CACHE HIT if Redis running)..." -ForegroundColor Yellow
$result2 = Measure-Command { 
    try {
        $response2 = Invoke-WebRequest -Uri $apiUrl -Headers @{"Accept"="application/json"}
        $cache2 = $response2.Headers["X-Cache"]
        $time2 = $response2.Headers["X-Response-Time"]
        Write-Host "✅ Response Time: $time2" -ForegroundColor White
        Write-Host "✅ Cache Status: $cache2" -ForegroundColor White
    } catch {
        Write-Host "❌ Request failed: $($_.Exception.Message)" -ForegroundColor Red
        return
    }
}
Write-Host "Total Time: $($result2.TotalMilliseconds)ms" -ForegroundColor Cyan

Write-Host "`n[3/3] Performance Analysis:" -ForegroundColor Magenta
if ($result2.TotalMilliseconds -lt $result1.TotalMilliseconds) {
    $improvement = [math]::Round((1 - ($result2.TotalMilliseconds / $result1.TotalMilliseconds)) * 100, 1)
    Write-Host "🚀 Cache Improvement: $improvement% faster" -ForegroundColor Green
    
    if ($improvement -gt 80) {
        Write-Host "🎉 EXCELLENT! Redis caching is working perfectly!" -ForegroundColor Green
    } elseif ($improvement -gt 30) {
        Write-Host "✅ GOOD! Some caching benefit detected" -ForegroundColor Yellow
    } else {
        Write-Host "⚠️  Minimal improvement - Redis may not be running" -ForegroundColor Yellow
    }
} else {
    Write-Host "⚠️  No cache improvement detected" -ForegroundColor Yellow
    Write-Host "   This is normal if Redis is not installed/running" -ForegroundColor Gray
}

Write-Host "`n=== REDIS STATUS CHECK ===" -ForegroundColor Cyan
try {
    $healthResponse = Invoke-WebRequest -Uri "http://localhost:30886/api/health" | ConvertFrom-Json
    if ($healthResponse.cache) {
        Write-Host "✅ Cache Status: $($healthResponse.cache)" -ForegroundColor Green
    } else {
        Write-Host "⚠️  No cache information in health endpoint" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ Could not check health endpoint" -ForegroundColor Red
}

Write-Host "`n=== NEXT STEPS ===" -ForegroundColor Yellow
Write-Host "If Redis is not running:" -ForegroundColor White
Write-Host "1. Run: .\install_redis.ps1 (as Administrator)" -ForegroundColor Gray
Write-Host "2. Or install manually from: https://redis.io/download" -ForegroundColor Gray
Write-Host "3. Restart backend after Redis is running" -ForegroundColor Gray
Write-Host "`nIf Redis is running, you should see 80-95% improvement!" -ForegroundColor Green