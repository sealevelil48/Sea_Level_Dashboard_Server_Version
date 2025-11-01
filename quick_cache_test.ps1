# Quick Cache Test - Direct API calls
$apiUrl = "http://localhost:30886/api/data?station=Haifa&limit=1000"

Write-Host "=== DIRECT API CACHE TEST ===" -ForegroundColor Cyan

Write-Host "`nFirst request (cache miss):" -ForegroundColor Yellow
$time1 = Measure-Command { 
    $response1 = Invoke-WebRequest -Uri $apiUrl
    $headers1 = $response1.Headers
}
Write-Host "Time: $($time1.TotalMilliseconds)ms" -ForegroundColor White
Write-Host "X-Response-Time: $($headers1['X-Response-Time'])" -ForegroundColor White
Write-Host "X-Cache: $($headers1['X-Cache'])" -ForegroundColor White

Start-Sleep -Seconds 1

Write-Host "`nSecond request (should be cache hit):" -ForegroundColor Yellow
$time2 = Measure-Command { 
    $response2 = Invoke-WebRequest -Uri $apiUrl
    $headers2 = $response2.Headers
}
Write-Host "Time: $($time2.TotalMilliseconds)ms" -ForegroundColor White
Write-Host "X-Response-Time: $($headers2['X-Response-Time'])" -ForegroundColor White
Write-Host "X-Cache: $($headers2['X-Cache'])" -ForegroundColor White

if ($time2.TotalMilliseconds -lt $time1.TotalMilliseconds) {
    $improvement = [math]::Round((1 - ($time2.TotalMilliseconds / $time1.TotalMilliseconds)) * 100, 1)
    Write-Host "`nImprovement: $improvement% faster" -ForegroundColor Green
} else {
    Write-Host "`nNo improvement detected" -ForegroundColor Red
}