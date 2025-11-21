# QuMail Optimized KM Client Implementation

This document outlines the implementation of the optimized Quantum Key Management (KM) client for the QuMail secure email system. The optimized client addresses issues with real KM servers by implementing connection pooling, retry logic, and improved error handling.

## Overview

The QuMail secure email system uses Quantum Key Distribution (QKD) to enhance encryption security. It interfaces with two Quantum Key Management Entities (KMEs):
- KM1 (Alice) running on localhost:13000
- KM2 (Bob) running on localhost:14000

Previously, the system was encountering 504 Gateway Timeout errors when connecting to real KM servers, which led to the use of mock KM servers. This implementation replaces the mock servers with an optimized KM client that can reliably connect to real KM servers.

## Implementation Details

### 1. Optimized KM Client

The `OptimizedKMClient` class in `app/services/optimized_km_client.py` implements the following features:

- **Connection Pooling**: Uses `aiohttp.ClientSession` with connection pooling to maintain persistent connections to KM servers
- **Retry Logic**: Automatically retries failed requests with exponential backoff
- **Timeout Handling**: Configurable timeouts for KM server requests
- **Key Cache**: Background task to pre-populate and maintain a cache of quantum keys
- **Error Handling**: Improved error handling and logging for KM server interactions

### 2. Integration with Encryption Levels

All four encryption levels have been updated to use the optimized KM client:

- **Level 1 (OTP)**: One-time pad using quantum keys from KM servers
- **Level 2 (AES)**: Quantum-enhanced AES-256-GCM encryption
- **Level 3 (PQC)**: Post-quantum cryptography with optional quantum enhancement
- **Level 4 (RSA)**: RSA-4096 + AES-256-GCM with optional quantum enhancement

### 3. Global KM Client Initialization

KM clients are initialized as global singletons in `app/services/km_client_init.py` and are available throughout the application. The application's lifespan manager initializes the clients during startup.

## Configuration

The optimized KM client can be configured with the following parameters:

- `retry_attempts`: Number of retry attempts for failed requests (default: 3)
- `retry_delay`: Initial delay between retries in seconds (default: 1)
- `timeout`: Request timeout in seconds (default: 10)
- `pool_connections`: Number of connections to keep in the pool (default: 5)
- `pool_maxsize`: Maximum number of connections in the pool (default: 10)

## Key Features

1. **Resilient Connections**: Retries failed requests with exponential backoff
2. **Efficient Resource Usage**: Maintains connection pool to reduce connection overhead
3. **Background Key Caching**: Prefetches keys to ensure availability when needed
4. **Configurable**: Easily tune performance parameters for specific environments
5. **Comprehensive Logging**: Detailed logging for troubleshooting

## Testing

The following test scripts are included to verify the functionality of the optimized KM client:

- `test_real_km_optimized.py`: Basic tests for the optimized KM client
- `test_optimized_km_all_levels.py`: Tests all encryption levels with the optimized client

## Usage

The optimized KM clients are initialized during application startup and are available throughout the application. Use the following functions to access the clients:

```python
from app.services.km_client_init import get_optimized_km_clients

# Get the optimized KM clients
km1_client, km2_client = get_optimized_km_clients()

# Use the clients
status = await km1_client.check_key_status(1)
keys = await km1_client.request_enc_keys(1, number=1, size=256)
```

## Benefits

1. **Improved Reliability**: Retry mechanism ensures requests are more likely to succeed
2. **Better Performance**: Connection pooling reduces connection overhead
3. **Enhanced Security**: Real QKD keys provide true quantum security instead of mock keys
4. **Scalability**: Configurable parameters allow tuning for different load scenarios
5. **Maintainability**: Centralized KM client logic for easier updates and troubleshooting

## Future Enhancements

1. Implement circuit breaker pattern for better failure handling
2. Add metrics collection for KM server interactions
3. Implement adaptive retry strategy based on server performance
4. Add support for multiple KM servers for redundancy
5. Implement key rotation and expiration policies