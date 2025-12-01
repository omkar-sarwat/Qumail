# PROMPT: Build Secure Email Client - React Electron Desktop Application

---

## TECHNICAL STACK REQUIREMENTS
- **Frontend Framework:** React.js
- **Desktop Platform:** Electron
- **Local Storage:** SQLite
- **Cloud Database:** MongoDB
- **Email Protocol:** IMAP for fetching, SMTP for sending
- **Architecture Pattern:** Local-first with cloud synchronization

---

## DATABASE ARCHITECTURE

### LOCAL DATABASE (Primary Data Source)
Store all email data on the user's device for instant access and complete offline functionality:

**Required Data:**
- Complete email headers
- Email body content: both encrypted and decrypted versions
- Email metadata: folder location, read/unread status, starred status, labels
- Decryption status: boolean flag indicating if email has been decrypted
- Security information: encryption level, key ID,flow id and other things 
- Attachments: file metadata and local file paths
- Sync status: tracking which items have been synced to cloud
- User preferences and application settings

**Functionality:**
- Must work completely offline
- Provides instant email display without network calls
- Primary source for all UI rendering
- Persists across application restarts

### MONGODB (Cloud Backup & Sync)
Store email data for cross-device synchronization and backup:

### What to Store in MongoDB (After Decryption):

**Complete Decrypted Email Content:**
- Full HTML structure with all inline CSS and styling
- Complete email header section:
  - Sender name and email with avatar/icon
  - Recipient information
  - Subject line with exact formatting
  - Date and time with exact format (e.g., "Nov 17, 2025" at "05:42 am")
- Security information panel with exact layout:
  - "Secure Connection Established" banner with styling
  - Encryption protocol details 
  - Key ID display 
  - Security Verification section with exact layout
  - Encryption Protocol badge with icon and text
  - Encryption level indicator
  - Additional technical details 
  - Digital Signature section with verification status
  - Certificate details with green verified indicator
  - Issuer information
  - Verification tracking ID 
- Complete email body with all formatting:
  - All text with exact fonts, sizes, colors
  - All spacing and padding
  - Background colors and borders
  - Links and clickable elements
  - Any embedded content
- Action buttons section:
  - Reply button with icon
  - Forward button with icon
  - Exact styling and layout
- All color schemes (blues, greens, grays)
- All icons and badges
- Complete responsive layout structure

**Storage Format:**
Store the complete rendered HTML/CSS exactly as user sees it after decryption, preserving every visual detail from the reference image.

---

## CRITICAL FEATURE: ONE-TIME DECRYPTION WITH CROSS-DEVICE ACCESS

### The Challenge:
Emails are encrypted with **one-time decryption keys**. Once a key is used to decrypt an email, it is consumed and destroyed. The email can NEVER be decrypted again using that key. This creates a problem for multi-device access.

### The Solution: Store Complete Decrypted Content with OAuth Authentication

#### Step-by-Step Process:

**INITIAL STATE (Encrypted Email):**
- User receives encrypted email
- Email stored in local database as encrypted
- Email synced to MongoDB as encrypted
- Decrypt button is visible in UI
- Flag: `globally_decrypted = false`

**USER CLICKS DECRYPT (First Time, Any Device):**
1. Use one-time decryption key to decrypt email
2. One-time key is now consumed/destroyed forever
3. Save complete decrypted content to local database **exactly as shown** with:
   - Complete HTML structure with all CSS styling
   - All formatting (colors, fonts, spacing, layouts)
   - Security information panel (encryption protocol, key ID, certificate details)
   - All visual badges and indicators
   - Complete email header (sender, recipient, subject, date)
   - All embedded images and content
4. Upload the **exact same decrypted content** to MongoDB (complete HTML/formatting)
5. Store security verification details in MongoDB
6. Set flag in MongoDB: `globally_decrypted = true`
7. Hide decrypt button permanently (globally, not just locally)
8. Display decrypted email exactly as shown in image

**USER LOGS INTO DIFFERENT DEVICE:**
1. User enters email/username and password
2. Opens Google Authenticator app on phone
3. Enters current 6-digit verification code
4. System verifies and authenticates user
5. Fetch emails from MongoDB
6. Check `globally_decrypted` flag for each email
7. For decrypted emails: Download complete decrypted content from MongoDB
8. Save to new device's local database with exact formatting
9. Display email exactly as it appears - complete with all styling and security info
10. No decrypt button shown (email already decrypted globally)

**SUBSEQUENT ACCESS (Any Device):**
- Email loads from local database instantly
- Displays exactly as shown in reference image
- All formatting, colors, security badges preserved
- No decrypt button visible
- Works offline after initial sync

### Authentication Model:

**Two-Factor Authentication (2FA) with TOTP (Time-Based One-Time Password):**
- User sets up 2FA during initial registration
- Generate QR code for user to scan with Google Authenticator app (or similar: Authy, Microsoft Authenticator)
- User scans QR code with their authenticator app
- App generates 6-digit codes that refresh every 30 seconds
- No internet required for code generation (time-based algorithm)

**Login Process:**
1. User enters email/username and password
2. System prompts for 6-digit verification code
3. User opens Google Authenticator app on their phone
4. App shows 6-digit code (refreshes every 30 seconds)
5. User enters the code in application
6. System verifies code matches server-side generation
7. If valid, user is authenticated and granted access
8. OAuth token issued for session management

**Cross-Device Login:**
- User installs app on new device
- Enters email/username and password
- Opens Google Authenticator app on phone
- Enters current 6-digit code from authenticator
- Gets access to all decrypted emails from MongoDB
- Same authenticator app works for all devices

**Security Benefits:**
- Two-factor security (password + authenticator code)
- Codes expire every 30 seconds
- Works offline (time-based algorithm)
- Same authenticator app for all user's devices
- No SMS required (more secure than SMS-based 2FA)
- Standard TOTP protocol (RFC 6238)

**Backup Codes:**
- Generate 10 backup codes during setup
- User saves these securely
- Can use if phone is lost/stolen
- Each backup code single-use only

**No Additional Password Layer:**
- No master password encryption needed
- Decrypted content stored in MongoDB as-is (complete HTML/formatting)
- Protected by standard login password + TOTP 2FA
- User's account security = application security
- MongoDB access requires valid authentication token

---

## OFFLINE-FIRST FUNCTIONALITY

### When Application is OFFLINE:

**Must Work Completely:**
- Display all previously synced emails from local database
- Open and read any email instantly
- Decrypt encrypted emails (if not yet decrypted globally)
- Mark emails as read/unread
- Star/unstar emails
- Move emails between folders
- Apply labels
- Search through all local emails
- View attachments stored locally
- Compose and queue emails for sending

**Local Operations Queue:**
- Track all changes made offline
- Store in local queue for later sync
- Include: read status changes, folder moves, label applications, starred status

### When Application is ONLINE:

**Automatic Sync Process:**
1. Detect internet connection
2. Fetch new emails from email server via IMAP
3. Save new emails to local database immediately
4. Sync new encrypted emails to MongoDB
5. Download any globally-decrypted emails from MongoDB
6. Decrypt with user master password and save locally
7. Upload queued local changes to MongoDB
8. Sync read/unread status, folders, labels bidirectionally
9. Update sync timestamps
10. Continue background sync at intervals

**Background Synchronization:**
- Non-blocking: user can continue using app during sync
- Progress indicators for user feedback
- Error handling with retry logic
- Conflict resolution (timestamp-based or last-write-wins)

---

## USER INTERFACE REQUIREMENTS

### Email List View:
- Display all emails in current folder
- Show: sender name, subject line, preview snippet, date/time
- Visual indicators: read/unread status, starred, has attachments, encryption status
- Encryption badge: icon indicating if email is encrypted
- Smooth scrolling with virtual scrolling for large lists
- Search functionality across all local emails
- Folder navigation sidebar
- Sync status indicator (syncing/synced/offline)

### Single Email View:

**Header Section:**
- Sender information with avatar/icon
- Sender email address
- Recipient email address
- Email subject prominently displayed
- Date and time formatted nicely
- Security badge showing encryption status

**Security Information Panel (Always Visible):**
Display detailed security information:
- "Secure Connection Established" banner or similar
- Encryption protocol name (e.g., "Quantum-Aided AES-256")
- Encryption level indicator (e.g., "Level 2")
- Key ID displayed (e.g., "Key ID: #8842-A")
- Certificate verification status with visual indicator (green checkmark for verified)
- Certificate issuer name
- Verification tracking ID or reference number
- Color-coded badges (green for verified/secure)

**Decrypt Button (Conditional Display):**
- Show ONLY when: email is encrypted AND not yet decrypted globally
- Prominent button placement
- Clear label: "Decrypt Email" or similar
- Single click action
- Disappears permanently after decryption
- Never appears again on any device once email is decrypted

**Email Body Content:**
- Render HTML emails properly with CSS styling
- Support plain text fallback
- Preserve formatting, colors, fonts, layouts
- Display embedded images
- Sanitize content for security (prevent XSS)

**Action Buttons:**
- Reply button
- Reply All button
- Forward button
- Delete button
- Move to folder option
- Label management

**Attachments Section:**
- List all attachments with filenames
- Show file sizes and types
- Download buttons for each attachment
- Preview capability where applicable

---

## EMAIL FETCHING & SYNCHRONIZATION

### Initial Email Fetch:
- Connect to email server via IMAP
- Authenticate user credentials
- Fetch email headers first for quick display
- Download email bodies progressively
- Parse encryption metadata from headers
- Extract security certificates and verification info
- Download attachments (on-demand or automatic based on settings)
- Save everything to local database
- Sync encrypted content to MongoDB

### Periodic Sync (When Online):
- Check for new emails every configurable interval (e.g., 5 minutes)
- Incremental sync: only fetch new or changed emails
- Update local database with new emails
- Upload local changes to MongoDB
- Handle deletions on server
- Sync folder structure changes
- Update read receipts if applicable

### Sync After Offline Period:
- Detect when internet connection is restored
- Immediate sync trigger
- Fetch all emails received during offline period
- Upload all queued actions from offline usage
- Resolve conflicts if same email modified on multiple devices
- Complete bidirectional synchronization
- Notify user of sync completion

---

## DECRYPTION WORKFLOW DETAILS

### Pre-Decryption State:
- Email exists in local database with encrypted body
- `is_decrypted` flag is false in local database
- `globally_decrypted` flag is false in MongoDB
- UI displays encrypted placeholder or notice
- Decrypt button is visible and enabled

### During Decryption:
- User clicks decrypt button
- Show loading indicator
- Retrieve one-time decryption key from secure storage
- Execute decryption algorithm
- Validate decrypted content
- One-time key is consumed/destroyed
- Save complete decrypted content to local database with **exact formatting**:
  - Store complete HTML structure with all CSS
  - Preserve all visual styling (colors, fonts, spacing)
  - Include security verification panel with all badges
  - Store complete email header with exact layout
  - Include all icons, indicators, and visual elements
  - Maintain exact color scheme from reference image
- Upload the **exact same formatted content** to MongoDB
- Update `globally_decrypted` flag in MongoDB to true
- Update local `is_decrypted` flag to true
- Hide decrypt button in UI
- Display decrypted email with complete formatting intact

### Post-Decryption State:
- Email displays normally like any regular email
- No visual indication of previous encryption (except security info panel)
- Decrypt button never appears again
- Content loads instantly from local database
- Works offline
- Accessible from all user's devices

---

## PERFORMANCE REQUIREMENTS

### Speed & Responsiveness:
- Application launch: under 2 seconds
- Email list display: instant from local database
- Email open time: under 500ms from local database
- Search results: under 1 second for thousands of emails
- Smooth 60fps scrolling in email list
- No UI blocking during background operations

### Optimization Techniques:
- Database indexing on frequently queried fields
- Virtual scrolling for large email lists
- Lazy loading of email bodies
- Progressive image loading
- Caching strategies for frequently accessed data
- Efficient memory management
- Background workers for heavy processing

### Scalability:
- Handle 100,000+ emails without performance degradation
- Efficient database query optimization
- Pagination for large result sets
- Incremental sync to minimize data transfer

---

## SECURITY REQUIREMENTS

### Data Protection:
- Decrypted content stored in MongoDB with complete formatting
- Protected by password + TOTP 2FA authentication
- Access controlled through two-factor authentication
- Secure connection to email servers (TLS/SSL)
- Certificate validation for encrypted emails
- MongoDB access requires valid authentication token

### Authentication:
- Two-Factor Authentication (2FA) with TOTP
- Compatible with Google Authenticator, Authy, Microsoft Authenticator
- 6-digit codes that refresh every 30 seconds
- Works offline (time-based algorithm)
- Backup codes for account recovery
- Token-based session management
- Automatic token refresh

### Privacy:
- Decrypted content stored in MongoDB with complete formatting as-is
- Protected by password + TOTP 2FA authentication
- One-time decryption keys never stored permanently
- TOTP secrets securely stored (encrypted)
- Session tokens securely managed
- Local database protected by OS-level security

---

## ERROR HANDLING

### Network Errors:
- Graceful degradation when connection lost
- Automatic retry with exponential backoff
- Clear user messaging about offline status
- Queue operations for later sync

### Decryption Errors:
- Handle corrupted encrypted content
- Notify user if decryption fails
- Preserve encrypted content for retry
- Log errors for debugging

### Database Errors:
- Handle quota exceeded scenarios
- Graceful handling of database corruption
- Automatic backup and recovery mechanisms
- User notification with actionable steps

### Sync Conflicts:
- Timestamp-based conflict resolution
- Last-write-wins strategy for simple conflicts
- User notification for important conflicts
- Conflict history tracking

---

## USER EXPERIENCE REQUIREMENTS

### Visual Design:
- Clean, modern interface similar to Gmail
- Consistent color scheme and typography
- Professional appearance
- Responsive layout
- Accessibility compliance (WCAG 2.1 AA)
- Dark mode support (optional but recommended)

### User Feedback:
- Loading indicators for all async operations
- Success/error notifications
- Sync progress indicators
- Tooltips for unclear features
- Keyboard shortcuts for power users

### Onboarding:
- Simple setup wizard
- Account registration with password
- 2FA setup: Generate QR code for Google Authenticator
- User scans QR code with authenticator app
- Test 2FA code verification
- Generate and display backup codes
- Email account connection guide
- Optional import from other email clients
- Quick tour of key features
- Explanation of one-time decryption feature

---

## EXPECTED DELIVERABLES

Build a fully functional React Electron desktop application that:

1. Stores all emails locally in SQLite for offline access with complete formatting
2. Syncs emails to MongoDB including fully decrypted content with exact visual styling
3. Uses TOTP 2FA authentication with Google Authenticator app (6-digit codes, 30-second refresh)
4. Handles one-time decryption keys by storing complete decrypted content in MongoDB
5. Preserves exact email formatting as shown in reference image (HTML, CSS, all visual elements)
6. Shows decrypt button only once globally across all devices
7. Works completely offline with full functionality
8. Syncs automatically when online
9. Provides Gmail-like user experience
10. Displays security information exactly as shown in reference image with all styling
11. Handles multi-device scenarios seamlessly with 2FA authentication
12. Maintains high performance with large email volumes
13. Supports Google Authenticator, Authy, Microsoft Authenticator, or any TOTP-compatible app

**Critical Requirement:** Store decrypted emails in MongoDB with complete HTML/CSS formatting exactly as displayed, preserving all visual elements, colors, badges, icons, and layout shown in the reference image.