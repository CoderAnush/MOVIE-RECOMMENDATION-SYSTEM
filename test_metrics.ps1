# PowerShell Script to Test Metrics
# Save as: test_metrics.ps1
# Run as: .\test_metrics.ps1

Write-Host "🚀 Testing Metrics API..." -ForegroundColor Cyan

# Make a recommendation request using /recommend/enhanced endpoint
$body = @{
    user_preferences = @{
        action = 8
        comedy = 7
        romance = 6
        thriller = 7
        drama = 8
        horror = 5
        sci_fi = 8
        fantasy = 7
        adventure = 8
    }
    num_recommendations = 5
} | ConvertTo-Json -Depth 3

Write-Host "`n📤 Sending request to /recommend/enhanced on port 3000..." -ForegroundColor Yellow

try {
    $response = Invoke-WebRequest `
        -Uri "http://localhost:3000/recommend/enhanced" `
        -Method POST `
        -Headers @{"Content-Type"="application/json"} `
        -Body $body `
        -UseBasicParsing

    $data = $response.Content | ConvertFrom-Json
    
    Write-Host "`n✅ Response received!" -ForegroundColor Green
    Write-Host "`n📊 Total recommendations: $($data.total_movies)" -ForegroundColor Cyan
    Write-Host "⏱️  Processing time: $($data.processing_time_ms)ms" -ForegroundColor Cyan
    Write-Host "⭐ Average rating: $($data.average_rating)" -ForegroundColor Cyan
    
    Write-Host "`n🎬 First recommendation:" -ForegroundColor Yellow
    if ($data.recommendations -and $data.recommendations.Count -gt 0) {
        $rec = $data.recommendations[0]
        Write-Host "  Title: $($rec.title)"
        Write-Host "  Score: $($rec.score)"
        Write-Host "  Recommendation: $($rec.reason)"
    }
    
} catch {
    Write-Host "`n❌ Error: $_" -ForegroundColor Red
}

Write-Host "`n🔍 Check the API console (Terminal 1) to see formatted metrics display!" -ForegroundColor Yellow
