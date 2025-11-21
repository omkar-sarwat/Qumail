-- =====================================================
-- QuMail Secure Email System - MySQL Database Setup  
-- =====================================================
-- Created: November 9, 2025
-- Version: 1.0
-- Description: Complete MySQL database schema for QuMail quantum encryption system
-- Features: Users, OAuth, Emails, Attachments, Key Management, Audit Logging
-- =====================================================

-- Drop database if exists and create fresh
DROP DATABASE IF EXISTS qumail_secure;
CREATE DATABASE qumail_secure 
    CHARACTER SET utf8mb4 
    COLLATE utf8mb4_unicode_ci;

USE qumail_secure;

-- =====================================================
-- USER MANAGEMENT TABLES
-- =====================================================

-- Users table for authentication and profile management
CREATE TABLE users (
    id VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
    email VARCHAR(255) NOT NULL UNIQUE,
    display_name VARCHAR(255),
    
    -- OAuth token storage (encrypted)
    oauth_access_token TEXT,
    oauth_refresh_token TEXT, 
    oauth_token_expiry TIMESTAMP NULL,
    
    -- Cryptographic keys for different encryption levels
    rsa_public_key_pem TEXT,
    rsa_private_key_pem TEXT,
    kyber_public_key LONGBLOB,
    kyber_private_key LONGBLOB,
    dilithium_public_key LONGBLOB,
    dilithium_private_key LONGBLOB,
    
    -- Session management
    session_token VARCHAR(512),
    session_expires_at TIMESTAMP NULL,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- User status
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    failed_login_attempts INT DEFAULT 0,
    locked_until TIMESTAMP NULL,
    
    INDEX idx_users_email (email),
    INDEX idx_users_active (is_active),
    INDEX idx_users_session (session_token),
    INDEX idx_users_created (created_at)
) ENGINE=InnoDB;

-- OAuth tokens table for Gmail integration
CREATE TABLE oauth_tokens (
    id VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
    user_id VARCHAR(36) NOT NULL,
    user_email VARCHAR(255) NOT NULL,
    
    -- Encrypted token storage
    encrypted_access_token TEXT NOT NULL,
    encrypted_refresh_token TEXT,
    token_type VARCHAR(50) DEFAULT 'Bearer',
    expires_at TIMESTAMP NULL,
    
    -- OAuth metadata
    scopes JSON,  -- Array of granted scopes
    grant_type VARCHAR(100),
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    last_refreshed_at TIMESTAMP NULL,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_oauth_user (user_id),
    INDEX idx_oauth_email (user_email),
    INDEX idx_oauth_expires (expires_at)
) ENGINE=InnoDB;

-- =====================================================
-- EMAIL SYSTEM TABLES
-- =====================================================

-- Emails table for encrypted message storage
CREATE TABLE emails (
    id VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
    flow_id VARCHAR(255) NOT NULL UNIQUE,
    user_id VARCHAR(36) NOT NULL,
    
    -- Email addresses
    sender_email VARCHAR(255) NOT NULL,
    receiver_email VARCHAR(255) NOT NULL,
    cc_emails JSON,  -- Array of CC recipients
    bcc_emails JSON, -- Array of BCC recipients
    
    -- Email content (encrypted)
    subject TEXT,
    body_encrypted LONGTEXT,  -- Base64 encoded encrypted content
    body_plaintext LONGTEXT,  -- For testing/debug only
    
    -- Encryption metadata
    encryption_key_id VARCHAR(255),
    encryption_algorithm VARCHAR(100),
    encryption_iv TEXT,  -- Initialization vector for AES
    encryption_auth_tag TEXT,  -- Authentication tag for GCM
    encryption_nonce TEXT,  -- Nonce for other algorithms
    encryption_metadata JSON,  -- Additional encryption parameters
    
    -- Security and classification
    security_level INT NOT NULL,  -- 1=OTP, 2=AES, 3=PQC, 4=RSA
    direction ENUM('SENT', 'RECEIVED') NOT NULL,
    
    -- Gmail integration
    gmail_message_id VARCHAR(255),
    gmail_thread_id VARCHAR(255),
    gmail_labels JSON,  -- Array of Gmail labels
    
    -- Email status
    is_read BOOLEAN DEFAULT FALSE,
    is_starred BOOLEAN DEFAULT FALSE,
    is_archived BOOLEAN DEFAULT FALSE,
    is_deleted BOOLEAN DEFAULT FALSE,
    is_suspicious BOOLEAN DEFAULT FALSE,
    
    -- Timestamps
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    read_at TIMESTAMP NULL,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (sender_email) REFERENCES users(email) ON DELETE RESTRICT,
    FOREIGN KEY (receiver_email) REFERENCES users(email) ON DELETE RESTRICT,
    
    INDEX idx_emails_flow (flow_id),
    INDEX idx_emails_user (user_id),
    INDEX idx_emails_sender (sender_email),
    INDEX idx_emails_receiver (receiver_email),
    INDEX idx_emails_security (security_level),
    INDEX idx_emails_direction (direction),
    INDEX idx_emails_timestamp (timestamp),
    INDEX idx_emails_read (is_read),
    INDEX idx_emails_gmail (gmail_message_id),
    INDEX idx_emails_key (encryption_key_id)
) ENGINE=InnoDB;

-- Email attachments table
CREATE TABLE attachments (
    id VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
    email_id VARCHAR(36) NOT NULL,
    
    -- File information
    filename VARCHAR(255) NOT NULL,
    content_type VARCHAR(100),
    file_size BIGINT,
    
    -- Encrypted file data
    file_data_encrypted LONGBLOB,
    encryption_key_id VARCHAR(255),
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (email_id) REFERENCES emails(id) ON DELETE CASCADE,
    INDEX idx_attachments_email (email_id),
    INDEX idx_attachments_filename (filename)
) ENGINE=InnoDB;

-- =====================================================
-- QUANTUM KEY MANAGEMENT TABLES
-- =====================================================

-- Quantum key storage and management
CREATE TABLE quantum_keys (
    id VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
    
    -- Key identifiers from KME servers
    kme1_key_id VARCHAR(255) NOT NULL,
    kme2_key_id VARCHAR(255) NOT NULL,
    
    -- Actual key material (encrypted at rest)
    kme1_key_material LONGBLOB NOT NULL,
    kme2_key_material LONGBLOB NOT NULL,
    
    -- Key properties
    key_size_bits INT NOT NULL,
    algorithm VARCHAR(50) DEFAULT 'OTP-QKD',
    
    -- Key lifecycle
    state ENUM('GENERATED', 'STORED', 'RESERVED', 'CONSUMED', 'EXPIRED') DEFAULT 'GENERATED',
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reserved_at TIMESTAMP NULL,
    consumed_at TIMESTAMP NULL,
    expires_at TIMESTAMP NULL,
    
    -- Usage tracking
    reserved_by_user_id VARCHAR(36),
    consumed_by_flow_id VARCHAR(255),
    
    -- Pool management
    pool_id VARCHAR(100) DEFAULT 'shared_pool',
    priority INT DEFAULT 0,
    
    FOREIGN KEY (reserved_by_user_id) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_quantum_keys_state (state),
    INDEX idx_quantum_keys_pool (pool_id),
    INDEX idx_quantum_keys_generated (generated_at),
    INDEX idx_quantum_keys_flow (consumed_by_flow_id),
    INDEX idx_quantum_keys_kme1 (kme1_key_id),
    INDEX idx_quantum_keys_kme2 (kme2_key_id)
) ENGINE=InnoDB;

-- Key usage tracking for emails
CREATE TABLE key_usage (
    id VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
    email_id VARCHAR(36) NOT NULL,
    quantum_key_id VARCHAR(36),
    
    -- Usage details
    operation_type ENUM('ENCRYPT', 'DECRYPT') NOT NULL,
    key_type VARCHAR(50),  -- 'quantum', 'rsa', 'aes', 'pqc'
    algorithm VARCHAR(100),
    
    -- Timestamps
    used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (email_id) REFERENCES emails(id) ON DELETE CASCADE,
    FOREIGN KEY (quantum_key_id) REFERENCES quantum_keys(id) ON DELETE SET NULL,
    INDEX idx_key_usage_email (email_id),
    INDEX idx_key_usage_key (quantum_key_id),
    INDEX idx_key_usage_operation (operation_type)
) ENGINE=InnoDB;

-- =====================================================
-- SYSTEM MONITORING TABLES  
-- =====================================================

-- KME server status monitoring
CREATE TABLE kme_server_status (
    id VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
    server_name VARCHAR(100) NOT NULL,  -- 'KME1', 'KME2'
    server_url VARCHAR(255) NOT NULL,
    port INT NOT NULL,
    
    -- Status information
    is_online BOOLEAN DEFAULT FALSE,
    last_successful_request TIMESTAMP NULL,
    last_failed_request TIMESTAMP NULL,
    consecutive_failures INT DEFAULT 0,
    
    -- Performance metrics
    avg_response_time_ms INT,
    total_requests INT DEFAULT 0,
    successful_requests INT DEFAULT 0,
    failed_requests INT DEFAULT 0,
    
    -- Key statistics
    keys_generated_today INT DEFAULT 0,
    keys_consumed_today INT DEFAULT 0,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    UNIQUE KEY uk_kme_server (server_name),
    INDEX idx_kme_status (is_online),
    INDEX idx_kme_updated (updated_at)
) ENGINE=InnoDB;

-- System health monitoring
CREATE TABLE system_health (
    id VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
    component VARCHAR(100) NOT NULL,  -- 'backend', 'frontend', 'kme1', 'kme2'
    
    -- Health status
    status ENUM('HEALTHY', 'WARNING', 'CRITICAL', 'DOWN') DEFAULT 'HEALTHY',
    message TEXT,
    
    -- Metrics
    cpu_usage_percent DECIMAL(5,2),
    memory_usage_percent DECIMAL(5,2),
    disk_usage_percent DECIMAL(5,2),
    
    -- Timestamps
    checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_health_component (component),
    INDEX idx_health_status (status),
    INDEX idx_health_checked (checked_at)
) ENGINE=InnoDB;

-- =====================================================
-- SECURITY AND AUDIT TABLES
-- =====================================================

-- Security audit log for all security events
CREATE TABLE security_audit_log (
    id VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
    user_id VARCHAR(36),
    user_email VARCHAR(255),
    
    -- Event information
    event_type VARCHAR(100) NOT NULL,  -- 'LOGIN', 'LOGOUT', 'ENCRYPT', 'DECRYPT', 'OAUTH', 'SUSPICIOUS'
    event_category ENUM('AUTH', 'ENCRYPTION', 'ACCESS', 'SYSTEM', 'SECURITY') NOT NULL,
    severity ENUM('INFO', 'WARNING', 'ERROR', 'CRITICAL') DEFAULT 'INFO',
    
    -- Event details
    description TEXT,
    ip_address VARCHAR(45),  -- IPv6 compatible
    user_agent TEXT,
    endpoint VARCHAR(255),
    method VARCHAR(10),
    
    -- Additional context
    metadata JSON,  -- Flexible field for event-specific data
    flow_id VARCHAR(255),  -- Link to email flow if applicable
    
    -- Risk assessment
    risk_score INT DEFAULT 0,  -- 0-100 risk score
    is_suspicious BOOLEAN DEFAULT FALSE,
    
    -- Timestamps
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_audit_user (user_id),
    INDEX idx_audit_type (event_type),
    INDEX idx_audit_category (event_category),
    INDEX idx_audit_severity (severity),
    INDEX idx_audit_timestamp (timestamp),
    INDEX idx_audit_suspicious (is_suspicious),
    INDEX idx_audit_flow (flow_id)
) ENGINE=InnoDB;

-- Security incidents tracking
CREATE TABLE security_incidents (
    id VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
    
    -- Incident classification
    incident_type VARCHAR(100) NOT NULL,
    severity ENUM('LOW', 'MEDIUM', 'HIGH', 'CRITICAL') NOT NULL,
    status ENUM('OPEN', 'INVESTIGATING', 'RESOLVED', 'FALSE_POSITIVE') DEFAULT 'OPEN',
    
    -- Incident details
    title VARCHAR(255) NOT NULL,
    description TEXT,
    affected_user_id VARCHAR(36),
    affected_email VARCHAR(255),
    
    -- Analysis
    root_cause TEXT,
    resolution TEXT,
    preventive_measures TEXT,
    
    -- Timestamps
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (affected_user_id) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_incidents_type (incident_type),
    INDEX idx_incidents_severity (severity),
    INDEX idx_incidents_status (status),
    INDEX idx_incidents_detected (detected_at)
) ENGINE=InnoDB;

-- =====================================================
-- CONFIGURATION AND SETTINGS TABLES
-- =====================================================

-- System configuration table
CREATE TABLE system_config (
    id VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
    config_key VARCHAR(100) NOT NULL UNIQUE,
    config_value TEXT,
    config_type ENUM('STRING', 'INTEGER', 'BOOLEAN', 'JSON') DEFAULT 'STRING',
    description TEXT,
    is_sensitive BOOLEAN DEFAULT FALSE,  -- For passwords, keys, etc.
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_config_key (config_key)
) ENGINE=InnoDB;

-- User preferences and settings
CREATE TABLE user_preferences (
    id VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
    user_id VARCHAR(36) NOT NULL,
    
    -- Email preferences
    default_security_level INT DEFAULT 2,
    auto_encrypt BOOLEAN DEFAULT TRUE,
    show_encryption_details BOOLEAN DEFAULT TRUE,
    
    -- UI preferences
    theme VARCHAR(50) DEFAULT 'light',
    language VARCHAR(10) DEFAULT 'en',
    timezone VARCHAR(50) DEFAULT 'UTC',
    
    -- Security preferences
    require_2fa BOOLEAN DEFAULT FALSE,
    session_timeout_minutes INT DEFAULT 480,  -- 8 hours
    auto_logout BOOLEAN DEFAULT TRUE,
    
    -- Notification preferences
    email_notifications BOOLEAN DEFAULT TRUE,
    security_alerts BOOLEAN DEFAULT TRUE,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY uk_user_preferences (user_id)
) ENGINE=InnoDB;

-- =====================================================
-- DATA SEEDING AND INITIAL CONFIGURATION
-- =====================================================

-- Insert default system configuration
INSERT INTO system_config (config_key, config_value, config_type, description) VALUES
('app_version', '1.0.0', 'STRING', 'Current application version'),
('max_email_size_mb', '25', 'INTEGER', 'Maximum email size in MB'),
('session_timeout_hours', '8', 'INTEGER', 'Default session timeout in hours'),
('max_failed_login_attempts', '5', 'INTEGER', 'Maximum failed login attempts before lockout'),
('account_lockout_minutes', '30', 'INTEGER', 'Account lockout duration in minutes'),
('key_pool_min_size', '100', 'INTEGER', 'Minimum quantum keys to maintain in pool'),
('key_pool_max_size', '1000', 'INTEGER', 'Maximum quantum keys in pool'),
('key_expiry_hours', '24', 'INTEGER', 'Hours after which unused keys expire'),
('encryption_default_level', '2', 'INTEGER', 'Default encryption level (1-4)'),
('audit_log_retention_days', '90', 'INTEGER', 'Days to retain audit logs'),
('backup_enabled', 'true', 'BOOLEAN', 'Enable automatic database backups'),
('debug_mode', 'false', 'BOOLEAN', 'Enable debug logging and features'),
('kme1_url', 'http://localhost:8010', 'STRING', 'KME1 server URL'),
('kme2_url', 'http://localhost:8020', 'STRING', 'KME2 server URL'),
('gmail_api_enabled', 'true', 'BOOLEAN', 'Enable Gmail API integration');

-- Insert initial KME server status records
INSERT INTO kme_server_status (server_name, server_url, port, is_online) VALUES
('KME1', 'http://localhost:8010', 8010, FALSE),
('KME2', 'http://localhost:8020', 8020, FALSE);

-- =====================================================
-- DATABASE VIEWS FOR COMMON QUERIES
-- =====================================================

-- View for email summary with encryption details
CREATE VIEW v_email_summary AS
SELECT 
    e.id,
    e.flow_id,
    e.sender_email,
    e.receiver_email,
    e.subject,
    e.security_level,
    CASE e.security_level
        WHEN 1 THEN 'Quantum OTP'
        WHEN 2 THEN 'Quantum AES'
        WHEN 3 THEN 'Post-Quantum'
        WHEN 4 THEN 'RSA-4096'
        ELSE 'Unknown'
    END as security_level_name,
    e.direction,
    e.is_read,
    e.is_starred,
    e.timestamp,
    u.display_name as sender_name,
    COUNT(a.id) as attachment_count
FROM emails e
LEFT JOIN users u ON e.sender_email = u.email
LEFT JOIN attachments a ON e.id = a.email_id
GROUP BY e.id, e.flow_id, e.sender_email, e.receiver_email, e.subject, 
         e.security_level, e.direction, e.is_read, e.is_starred, 
         e.timestamp, u.display_name;

-- View for quantum key pool status
CREATE VIEW v_key_pool_status AS
SELECT 
    state,
    COUNT(*) as key_count,
    AVG(key_size_bits) as avg_key_size,
    MIN(generated_at) as oldest_key,
    MAX(generated_at) as newest_key
FROM quantum_keys
GROUP BY state;

-- View for user activity summary
CREATE VIEW v_user_activity AS
SELECT 
    u.id,
    u.email,
    u.display_name,
    u.last_login,
    COUNT(DISTINCT e.id) as total_emails,
    COUNT(DISTINCT CASE WHEN e.direction = 'SENT' THEN e.id END) as sent_emails,
    COUNT(DISTINCT CASE WHEN e.direction = 'RECEIVED' THEN e.id END) as received_emails,
    COUNT(DISTINCT sal.id) as security_events,
    u.created_at
FROM users u
LEFT JOIN emails e ON u.id = e.user_id
LEFT JOIN security_audit_log sal ON u.id = sal.user_id
GROUP BY u.id, u.email, u.display_name, u.last_login, u.created_at;

-- =====================================================
-- STORED PROCEDURES FOR COMMON OPERATIONS
-- =====================================================

DELIMITER //

-- Procedure to clean up expired quantum keys
CREATE PROCEDURE CleanupExpiredKeys()
BEGIN
    DECLARE affected_rows INT DEFAULT 0;
    
    -- Delete expired keys
    DELETE FROM quantum_keys 
    WHERE state = 'EXPIRED' 
       OR (expires_at IS NOT NULL AND expires_at < NOW());
    
    SET affected_rows = ROW_COUNT();
    
    -- Log the cleanup
    INSERT INTO security_audit_log (event_type, event_category, description, metadata)
    VALUES ('KEY_CLEANUP', 'SYSTEM', 'Expired quantum keys cleaned up', 
            JSON_OBJECT('deleted_keys', affected_rows));
    
    SELECT affected_rows as deleted_keys;
END//

-- Procedure to get user email statistics
CREATE PROCEDURE GetUserEmailStats(IN user_email VARCHAR(255))
BEGIN
    SELECT 
        u.email,
        u.display_name,
        COUNT(e.id) as total_emails,
        COUNT(CASE WHEN e.direction = 'SENT' THEN 1 END) as sent_count,
        COUNT(CASE WHEN e.direction = 'RECEIVED' THEN 1 END) as received_count,
        COUNT(CASE WHEN e.security_level = 1 THEN 1 END) as level1_count,
        COUNT(CASE WHEN e.security_level = 2 THEN 1 END) as level2_count,
        COUNT(CASE WHEN e.security_level = 3 THEN 1 END) as level3_count,
        COUNT(CASE WHEN e.security_level = 4 THEN 1 END) as level4_count,
        MAX(e.timestamp) as last_email_date
    FROM users u
    LEFT JOIN emails e ON u.id = e.user_id
    WHERE u.email = user_email
    GROUP BY u.id, u.email, u.display_name;
END//

-- Procedure to reserve quantum keys for encryption
CREATE PROCEDURE ReserveQuantumKeys(
    IN requested_count INT,
    IN user_id VARCHAR(36),
    IN flow_id VARCHAR(255)
)
BEGIN
    DECLARE available_keys INT DEFAULT 0;
    
    -- Check available keys
    SELECT COUNT(*) INTO available_keys
    FROM quantum_keys 
    WHERE state = 'GENERATED';
    
    IF available_keys >= requested_count THEN
        -- Reserve the keys
        UPDATE quantum_keys 
        SET state = 'RESERVED',
            reserved_at = NOW(),
            reserved_by_user_id = user_id,
            consumed_by_flow_id = flow_id
        WHERE state = 'GENERATED'
        ORDER BY generated_at ASC
        LIMIT requested_count;
        
        -- Return reserved keys
        SELECT id, kme1_key_id, kme2_key_id, key_size_bits
        FROM quantum_keys
        WHERE consumed_by_flow_id = flow_id AND state = 'RESERVED';
    ELSE
        -- Not enough keys available
        SELECT 0 as success, available_keys as available, requested_count as requested;
    END IF;
END//

DELIMITER ;

-- =====================================================
-- TRIGGERS FOR DATA INTEGRITY
-- =====================================================

-- Trigger to update user last_login on OAuth token creation
DELIMITER //
CREATE TRIGGER update_user_last_login 
    AFTER INSERT ON oauth_tokens
    FOR EACH ROW
BEGIN
    UPDATE users 
    SET last_login = NOW() 
    WHERE id = NEW.user_id;
END//
DELIMITER ;

-- Trigger to log email operations
DELIMITER //
CREATE TRIGGER log_email_operations
    AFTER INSERT ON emails
    FOR EACH ROW
BEGIN
    INSERT INTO security_audit_log (
        user_id, event_type, event_category, description, flow_id, metadata
    ) VALUES (
        NEW.user_id,
        CASE NEW.direction 
            WHEN 'SENT' THEN 'EMAIL_SENT'
            WHEN 'RECEIVED' THEN 'EMAIL_RECEIVED'
            ELSE 'EMAIL_CREATED'
        END,
        'ENCRYPTION',
        CONCAT('Email ', NEW.direction, ' with security level ', NEW.security_level),
        NEW.flow_id,
        JSON_OBJECT(
            'security_level', NEW.security_level,
            'direction', NEW.direction,
            'encryption_algorithm', NEW.encryption_algorithm
        )
    );
END//
DELIMITER ;

-- Trigger to mark quantum keys as consumed
DELIMITER //
CREATE TRIGGER mark_keys_consumed
    AFTER INSERT ON key_usage
    FOR EACH ROW
BEGIN
    IF NEW.quantum_key_id IS NOT NULL AND NEW.operation_type = 'ENCRYPT' THEN
        UPDATE quantum_keys 
        SET state = 'CONSUMED', consumed_at = NOW()
        WHERE id = NEW.quantum_key_id;
    END IF;
END//
DELIMITER ;

-- =====================================================
-- INDEXES FOR PERFORMANCE OPTIMIZATION
-- =====================================================

-- Additional composite indexes for complex queries
CREATE INDEX idx_emails_user_direction_time ON emails(user_id, direction, timestamp DESC);
CREATE INDEX idx_emails_security_time ON emails(security_level, timestamp DESC);
CREATE INDEX idx_audit_user_type_time ON security_audit_log(user_id, event_type, timestamp DESC);
CREATE INDEX idx_quantum_keys_state_generated ON quantum_keys(state, generated_at);
CREATE INDEX idx_oauth_tokens_expires ON oauth_tokens(user_id, expires_at);

-- =====================================================
-- INITIAL DATA AND TEST USERS
-- =====================================================

-- Create test user for development (remove in production)
INSERT INTO users (id, email, display_name, is_active, is_verified) VALUES
('test-user-001', 'test@example.com', 'Test User', TRUE, TRUE),
('admin-user-001', 'admin@qumail.com', 'QuMail Administrator', TRUE, TRUE);

-- Create default user preferences for test users
INSERT INTO user_preferences (user_id, default_security_level, auto_encrypt) VALUES
('test-user-001', 2, TRUE),
('admin-user-001', 3, TRUE);

-- =====================================================
-- SECURITY SETTINGS
-- =====================================================

-- Create dedicated database user for the application
CREATE USER IF NOT EXISTS 'qumail_app'@'localhost' IDENTIFIED BY 'QuMail_Secure_2025!';
CREATE USER IF NOT EXISTS 'qumail_app'@'%' IDENTIFIED BY 'QuMail_Secure_2025!';

-- Grant appropriate permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON qumail_secure.* TO 'qumail_app'@'localhost';
GRANT SELECT, INSERT, UPDATE, DELETE ON qumail_secure.* TO 'qumail_app'@'%';
GRANT EXECUTE ON qumail_secure.* TO 'qumail_app'@'localhost';
GRANT EXECUTE ON qumail_secure.* TO 'qumail_app'@'%';

-- Create read-only user for reporting
CREATE USER IF NOT EXISTS 'qumail_readonly'@'localhost' IDENTIFIED BY 'QuMail_ReadOnly_2025!';
GRANT SELECT ON qumail_secure.* TO 'qumail_readonly'@'localhost';

FLUSH PRIVILEGES;

-- =====================================================
-- BACKUP AND MAINTENANCE PROCEDURES
-- =====================================================

-- Create backup procedure
DELIMITER //
CREATE PROCEDURE CreateBackup()
BEGIN
    DECLARE backup_name VARCHAR(255);
    SET backup_name = CONCAT('qumail_backup_', DATE_FORMAT(NOW(), '%Y%m%d_%H%i%s'));
    
    -- Log backup start
    INSERT INTO security_audit_log (event_type, event_category, description)
    VALUES ('BACKUP_START', 'SYSTEM', CONCAT('Database backup started: ', backup_name));
    
    -- Note: Actual backup command would be executed outside MySQL
    -- This is just for logging purposes
    
    SELECT backup_name as backup_file, NOW() as backup_time;
END//
DELIMITER ;

-- =====================================================
-- DATABASE SETUP COMPLETE
-- =====================================================

-- Final status check
SELECT 
    'Database Setup Complete' as status,
    DATABASE() as database_name,
    COUNT(*) as tables_created
FROM information_schema.tables 
WHERE table_schema = DATABASE();

-- Show table summary
SELECT 
    table_name,
    table_rows,
    data_length,
    index_length,
    ROUND((data_length + index_length) / 1024 / 1024, 2) as size_mb
FROM information_schema.tables 
WHERE table_schema = DATABASE()
ORDER BY table_name;

-- =====================================================
-- MAINTENANCE NOTES
-- =====================================================
/*
MAINTENANCE CHECKLIST:

1. REGULAR TASKS:
   - Run CleanupExpiredKeys() daily
   - Monitor quantum key pool levels
   - Check KME server status
   - Review security audit logs

2. WEEKLY TASKS:
   - Analyze user activity patterns
   - Check for security incidents
   - Verify backup integrity
   - Review performance metrics

3. MONTHLY TASKS:
   - Archive old audit logs
   - Update system configuration
   - Review user permissions
   - Optimize database indexes

4. MONITORING QUERIES:
   - SELECT * FROM v_key_pool_status;
   - SELECT * FROM v_user_activity WHERE last_login > DATE_SUB(NOW(), INTERVAL 7 DAY);
   - SELECT * FROM security_incidents WHERE status = 'OPEN';
   - SELECT * FROM kme_server_status WHERE is_online = FALSE;

5. EMERGENCY PROCEDURES:
   - If KME servers fail: Check kme_server_status table
   - If keys depleted: Run key generation process
   - If security breach: Check security_audit_log and security_incidents
   - If performance issues: Analyze slow query log and check indexes
*/