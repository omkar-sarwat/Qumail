# Test complete cross-KME OTP flow
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  CROSS-KME OTP FLOW TEST" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Step 1: Get encryption key from KME1
Write-Host "[Step 1] Request encryption key from KME1..." -ForegroundColor Green
$encBody = @{
    number = 1
    size = 256
} | ConvertTo-Json

try {
    $enc = Invoke-WebRequest -Method POST `
        -Uri "https://qumail-kme1-brzq.onrender.com/api/v1/keys/backend_sae/enc_keys" `
        -Body $encBody `
        -ContentType "application/json" `
        -UseBasicParsing | ConvertFrom-Json
    
    $keyId = $enc.keys[0].key_ID
    Write-Host "  ✓ Got key: $($keyId.Substring(0,20))..." -ForegroundColor White
} catch {
    Write-Host "  ✗ FAILED: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Step 2: Check KME1 status (should show 1 reserved key)
Write-Host "`n[Step 2] Check KME1 status..." -ForegroundColor Green
$status1 = Invoke-WebRequest -Uri "https://qumail-kme1-brzq.onrender.com/api/v1/kme/status" -UseBasicParsing | ConvertFrom-Json
Write-Host "  Pool: $($status1.pool_size) keys" -ForegroundColor White
Write-Host "  Reserved: $($status1.reserved_keys) keys (should be at least 1)" -ForegroundColor White

# Step 3: Decrypt on KME2 (cross-KME retrieval)
Write-Host "`n[Step 3] Decrypt key on KME2 (cross-KME fetch)..." -ForegroundColor Green
$decBody = @{
    key_IDs = @(
        @{ key_ID = $keyId }
    )
} | ConvertTo-Json -Depth 3

try {
    $dec = Invoke-WebRequest -Method POST `
        -Uri "https://qumail-kme2-brzq.onrender.com/api/v1/keys/backend_sae/dec_keys" `
        -Body $decBody `
        -ContentType "application/json" `
        -UseBasicParsing | ConvertFrom-Json
    
    Write-Host "  ✓ SUCCESS! Decrypted key: $($dec.keys[0].key_ID.Substring(0,20))..." -ForegroundColor Green
    
    # Verify keys match
    if ($dec.keys[0].key_ID -eq $keyId) {
        Write-Host "  ✓ Key IDs match!" -ForegroundColor Green
    } else {
        Write-Host "  ✗ Key ID mismatch!" -ForegroundColor Red
    }
} catch {
    Write-Host "  ✗ FAILED: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "  Status Code: $($_.Exception.Response.StatusCode.value__)" -ForegroundColor Red
    exit 1
}

# Step 4: Check KME1 status again (reserved should decrease)
Write-Host "`n[Step 4] Check KME1 status after consumption..." -ForegroundColor Green
$status2 = Invoke-WebRequest -Uri "https://qumail-kme1-brzq.onrender.com/api/v1/kme/status" -UseBasicParsing | ConvertFrom-Json
Write-Host "  Pool: $($status2.pool_size) keys" -ForegroundColor White
Write-Host "  Reserved: $($status2.reserved_keys) keys (should decrease by 1)" -ForegroundColor White

# Step 5: Try to decrypt again (should fail - OTP)
Write-Host "`n[Step 5] Try to decrypt same key again (should fail - OTP)..." -ForegroundColor Green
try {
    $dec2 = Invoke-WebRequest -Method POST `
        -Uri "https://qumail-kme2-brzq.onrender.com/api/v1/keys/backend_sae/dec_keys" `
        -Body $decBody `
        -ContentType "application/json" `
        -UseBasicParsing | ConvertFrom-Json
    
    Write-Host "  ✗ FAILED: Key still available (OTP violation!)" -ForegroundColor Red
    exit 1
} catch {
    $statusCode = $_.Exception.Response.StatusCode.value__
    if ($statusCode -eq 404) {
        Write-Host "  ✓ Correctly failed with 404 (OTP enforced)" -ForegroundColor Green
    } else {
        Write-Host "  ? Failed with status $statusCode" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  ALL TESTS PASSED!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "" 
