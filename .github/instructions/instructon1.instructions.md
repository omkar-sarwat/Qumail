---
applyTo: '**'
---
# Requirements Document: QuMail Encryption System Integration Fix

## Introduction

This document outlines the requirements for fixing and properly integrating the QuMail secure email encryption system. The system uses quantum key distribution (QKD) via the Next Door Key Simulator (ETSI QKD 014 standard) to provide four levels of encryption security. The goal is to ensure all encryption levels work correctly with proper API routing, KME integration, Google OAuth authentication, and end-to-end encrypted email flow.

## Requirements

### Requirement 1: Fix Encryption Service Integration

**User Story:** As a developer, I want all four encryption levels to work correctly with the Next Door Key Simulator, so that users can send and receive encrypted emails with real quantum keys.

#### Acceptance Criteria

1. WHEN Level 1 (OTP) encryption is requested THEN the system SHALL retrieve quantum keys from KME servers via ETSI QKD 014 API
2. WHEN Level 2 (AES-256-GCM) encryption is requested THEN the system SHALL use quantum-enhanced AES encryption with keys from both KME servers
3. WHEN Level 3 (PQC) encryption is requested THEN the system SHALL use post-quantum cryptography (Kyber1024 + Dilithium5) with optional quantum enhancement
4. WHEN Level 4 (RSA-4096) encryption is requested THEN the system SHALL use hybrid RSA + AES encryption with optional quantum enhancement
5. WHEN any encryption level is used THEN the system SHALL properly store encryption metadata for decryption
6. WHEN decryption is requested THEN the system SHALL retrieve the correct keys and decrypt the content successfully
7. WHEN encryption or decryption fails THEN the system SHALL provide clear error messages and log the failure

### Requirement 2: Fix API Routes and Backend Integration

**User Story:** As a backend developer, I want all API routes to be properly configured and connected to encryption services, so that the frontend can successfully encrypt and decrypt emails.

#### Acceptance Criteria

1. WHEN the backend starts THEN all encryption API routes SHALL be registered and accessible
2. WHEN `/api/v1/encryption/encrypt` is called THEN it SHALL accept security level (1-4) and content parameters
3. WHEN `/api/v1/encryption/decrypt` is called THEN it SHALL accept encrypted content and metadata parameters
4. WHEN `/api/v1/messages/send` is called with quantum encryption THEN it SHALL encrypt the email body before sending via Gmail API
5. WHEN `/api/v1/messages/{id}` is called THEN it SHALL return encrypted content without auto-decrypting
6. WHEN `/api/v1/messages/{id}/decrypt` is called THEN it SHALL decrypt and return the plaintext content
7. WHEN API errors occur THEN the system SHALL return proper HTTP status codes (400, 401, 500) with error details

### Requirement 3: Fix KME Client and Shared Pool Architecture

**User Story:** As a system administrator, I want a simple shared pool architecture where KM1 generates keys and KM2 retrieves from the same pool, so that quantum keys can be easily shared between encryption and decryption.

#### Acceptance Criteria

1. WHEN the backend initializes THEN it SHALL establish connections to KME1 (port 8010) and KME2 (port 8020)
2. WHEN KM1 generates keys THEN it SHALL store them in a common shared pool (in-memory)
3. WHEN KM2 needs keys THEN it SHALL retrieve them from the same shared pool
4. WHEN requesting encryption keys THEN the system SHALL get keys from KM1's shared pool
5. WHEN requesting decryption keys THEN the system SHALL get the same keys from KM2's shared pool
6. WHEN keys are used THEN they SHALL be marked as consumed in-memory (no database storage)
7. WHEN the shared key pool is low THEN the system SHALL log warnings about key availability
8. WHEN KME servers are unavailable THEN the system SHALL handle errors gracefully and log the issue

### Requirement 4: Integrate Google OAuth Authentication

**User Story:** As a user, I want to authenticate with my Google account, so that I can access my Gmail and send/receive encrypted emails through QuMail.

#### Acceptance Criteria

1. WHEN a user visits the frontend THEN they SHALL see a "Sign in with Google" button
2. WHEN the user clicks "Sign in with Google" THEN they SHALL be redirected to Google OAuth consent screen
3. WHEN the user grants permissions THEN the system SHALL receive an authorization code
4. WHEN the authorization code is received THEN the backend SHALL exchange it for access and refresh tokens
5. WHEN tokens are obtained THEN the system SHALL store them securely in the database
6. WHEN tokens expire THEN the system SHALL automatically refresh them using the refresh token
7. WHEN API requests are made THEN the system SHALL include valid OAuth tokens in Gmail API calls
8. WHEN a user logs out THEN the system SHALL revoke tokens and clear the session

### Requirement 5: Implement End-to-End Encrypted Email Flow

**User Story:** As a user, I want to send encrypted emails that only the recipient can decrypt in QuMail, so that my communications remain private and secure.

#### Acceptance Criteria

1. WHEN composing an email THEN the user SHALL be able to select a security level (1-4)
2. WHEN the user clicks "Send" THEN the email body SHALL be encrypted with the selected security level
3. WHEN encryption completes THEN the encrypted content SHALL be sent via Gmail API
4. WHEN the email is stored in Gmail THEN it SHALL contain only encrypted ciphertext (no plaintext)
5. WHEN the recipient opens the email in Gmail web THEN they SHALL see encrypted gibberish
6. WHEN the recipient opens the email in QuMail THEN they SHALL see a "Decrypt" button
7. WHEN the recipient clicks "Decrypt" THEN the system SHALL decrypt and display the original message
8. WHEN decryption fails THEN the system SHALL show an error message explaining the issue

### Requirement 6: Use In-Memory Storage for Keys and Metadata

**User Story:** As a backend developer, I want quantum keys and encryption metadata stored in-memory only (not in database), so that the system is faster and more secure.

#### Acceptance Criteria

1. WHEN keys are generated THEN they SHALL be stored in-memory only (no database writes for keys)
2. WHEN encryption metadata is created THEN it SHALL be stored in-memory cache (not database)
3. WHEN storing metadata THEN it SHALL include: key_id, security_level, algorithm, nonce/IV, auth_tag, flow_id
4. WHEN retrieving an email THEN the system SHALL fetch encryption metadata from in-memory cache
5. WHEN decrypting THEN the system SHALL use in-memory metadata to retrieve the correct keys
6. WHEN keys are consumed THEN they SHALL be marked as used in-memory
7. WHEN the backend restarts THEN the key pool and metadata cache SHALL be regenerated fresh

### Requirement 7: Start and Test Complete System

**User Story:** As a developer, I want a simple way to start all services and verify the system works, so that I can quickly test the encryption flow.

#### Acceptance Criteria

1. WHEN running the start script THEN it SHALL start KME1, KME2, backend, and frontend in correct order
2. WHEN all services start THEN they SHALL be accessible on their respective ports
3. WHEN running the test script THEN it SHALL verify all four encryption levels work
4. WHEN tests pass THEN the system SHALL log success messages with encryption details
5. WHEN tests fail THEN the system SHALL log clear error messages indicating what failed
6. WHEN the system is running THEN the frontend SHALL be accessible at http://localhost:5173
7. WHEN the system is running THEN the backend SHALL be accessible at http://localhost:8000

### Requirement 8: Terminal Logging for Encryption Operations

**User Story:** As a developer, I want detailed encryption logs displayed in the terminal in real-time, so that I can see exactly what's happening during encryption/decryption.

#### Acceptance Criteria

1. WHEN encryption starts THEN the system SHALL print detailed logs to terminal with security level, user, and content size
2. WHEN keys are retrieved from shared pool THEN the system SHALL print key IDs, sizes, and pool status to terminal
3. WHEN encryption completes THEN the system SHALL print success message with algorithm details to terminal
4. WHEN decryption starts THEN the system SHALL print flow ID and metadata to terminal
5. WHEN decryption completes THEN the system SHALL print success and verification status to terminal
6. WHEN errors occur THEN the system SHALL print detailed error messages to terminal
7. WHEN keys are generated/consumed THEN the system SHALL print shared pool statistics to terminal (available keys, used keys)
8. WHEN the log level is INFO THEN all encryption operations SHALL be visible in terminal output
