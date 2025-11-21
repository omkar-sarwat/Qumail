# Test script for deployed KME services
Write-Host "=== Testing Deployed KME Services ===" -ForegroundColor Cyan

# URLs
$KME1_URL = "https://qumail-kme1-brzq.onrender.com"
$KME2_URL = "https://qumail-kme2-brzq.onrender.com"
$SAE1_ID = "25840139-0dd4-49ae-ba1e-b86731601803"
$SAE2_ID = "c565d5aa-8670-4446-8471-b0e53e315d2a"

Write-Host "`n1. Checking KME1 Status..." -ForegroundColor Yellow
$kme1Status = curl.exe -s -X GET "$KME1_URL/api/v1/kme/status" | ConvertFrom-Json
Write-Host "KME1 ID: $($kme1Status.KME_ID)" -ForegroundColor Green
Write-Host "Role: $($kme1Status.role)" -ForegroundColor Green
Write-Host "Pool Size: $($kme1Status.shared_pool.pool_size)" -ForegroundColor Green
Write-Host "Reserved Keys: $($kme1Status.shared_pool.reserved_keys)" -ForegroundColor Green

Write-Host "`n2. Checking KME2 Status..." -ForegroundColor Yellow
$kme2Status = curl.exe -s -X GET "$KME2_URL/api/v1/kme/status" | ConvertFrom-Json
Write-Host "KME2 ID: $($kme2Status.KME_ID)" -ForegroundColor Green
Write-Host "Role: $($kme2Status.role)" -ForegroundColor Green
Write-Host "Can reach KME1: $($kme2Status.shared_pool -ne $null)" -ForegroundColor Green

Write-Host "`n3. Testing enc_keys on KME1..." -ForegroundColor Yellow
$encResponse = curl.exe -s -X POST "$KME1_URL/api/v1/keys/$SAE2_ID/enc_keys" `
    -H "Content-Type: application/json" `
    -d '{"number":1,"size":256}' | ConvertFrom-Json

if ($encResponse.keys) {
    $keyId = $encResponse.keys[0].key_ID
    $keyData = $encResponse.keys[0].key
    Write-Host "✓ Got encryption key" -ForegroundColor Green
    Write-Host "  Key ID: $keyId" -ForegroundColor Cyan
    Write-Host "  Key Data: $($keyData.Substring(0, [Math]::Min(20, $keyData.Length)))..." -ForegroundColor Cyan
    
    Write-Host "`n4. Checking pool status after enc_keys..." -ForegroundColor Yellow
    $kme1Status2 = curl.exe -s -X GET "$KME1_URL/api/v1/kme/status" | ConvertFrom-Json
    Write-Host "Reserved Keys: $($kme1Status2.shared_pool.reserved_keys)" -ForegroundColor Green
    Write-Host "Pool Size: $($kme1Status2.shared_pool.pool_size)" -ForegroundColor Green
    
    Write-Host "`n5. Testing internal get_reserved_key endpoint on KME1..." -ForegroundColor Yellow
    $jsonPayload = @"
{"key_id":"$keyId","kme_id":"2","remove":false}
"@
    $reservedResponse = curl.exe -s -X POST "$KME1_URL/api/v1/internal/get_reserved_key" `
        -H "Content-Type: application/json" `
        -d $jsonPayload
    Write-Host "Response: $reservedResponse" -ForegroundColor Cyan
    
    Write-Host "`n6. Testing dec_keys on KME2..." -ForegroundColor Yellow
    $jsonPayload2 = @"
{"key_IDs":[{"key_ID":"$keyId"}]}
"@
    $decResponse = curl.exe -s -X POST "$KME2_URL/api/v1/keys/$SAE1_ID/dec_keys" `
        -H "Content-Type: application/json" `
        -d $jsonPayload2
    Write-Host "Response: $decResponse" -ForegroundColor Cyan
    
    if ($decResponse -like "*$keyId*") {
        Write-Host "`n✓ SUCCESS: KME2 successfully retrieved key from KME1!" -ForegroundColor Green
    } else {
        Write-Host "`n✗ FAILED: KME2 could not retrieve key from KME1" -ForegroundColor Red
        Write-Host "Error: $decResponse" -ForegroundColor Red
    }
} else {
    Write-Host "✗ Failed to get encryption key" -ForegroundColor Red
    Write-Host "Response: $encResponse" -ForegroundColor Red
}

Write-Host "`n=== Test Complete ===" -ForegroundColor Cyan
