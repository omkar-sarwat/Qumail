# QuMail New Compose Email Modal - Complete Documentation

## Overview

The **NewComposeEmailModal** is a fully-featured, modern email composition interface with rich text editing capabilities, quantum encryption levels, and a beautiful UI that matches Gmail's design aesthetic.

## Features

### 🎨 Rich Text Formatting
- **Bold** (Ctrl+B) - Make text bold
- **Italic** (Ctrl+I) - Italicize text  
- **Underline** (Ctrl+U) - Underline text
- **Strikethrough** - Strike through text
- **Bullet Lists** - Create unordered lists
- **Numbered Lists** - Create ordered lists
- **Links** - Insert hyperlinks with custom dialog
- **Code Blocks** - Format code with syntax highlighting

### 🔐 Security Levels
1. **Standard (Level 4)** - Regular encryption without quantum enhancement
2. **Quantum Secure (Level 1)** - One Time Pad with Quantum Keys - Maximum Security
3. **Quantum-Aided AES (Level 2)** - AES encryption with quantum key enhancement
4. **Post-Quantum Cryptography (Level 3)** - Future-proof encryption for post-quantum era

### 📧 Email Features
- **To/Cc/Bcc** - Multiple recipient support with autocomplete
- **Contact Suggestions** - Dropdown with contact avatars and emails
- **Subject Line** - Clean subject input
- **File Attachments** - Drag & drop or browse to attach files
- **Reply Mode** - Automatically populate fields when replying
- **Draft Auto-save** - Saves draft every 30 seconds
- **Character Counter** - Real-time character count

### 💫 UI/UX Features
- **Smooth Animations** - Framer Motion powered transitions
- **Dark Mode Support** - Full dark theme compatibility
- **Responsive Design** - Works on all screen sizes
- **Keyboard Shortcuts** - Standard editor shortcuts (Ctrl+B, Ctrl+I, etc.)
- **Loading States** - Clear feedback during send operations
- **Error Handling** - Toast notifications for all actions
- **Accessibility** - ARIA labels and keyboard navigation

## Installation

### Required Dependencies

```bash
npm install @tiptap/react@^2.1.13 @tiptap/starter-kit@^2.1.13 @tiptap/extension-underline@^2.1.13 @tiptap/extension-link@^2.1.13 framer-motion react-hot-toast lucide-react
```

If you encounter peer dependency issues:

```bash
npm install @tiptap/react@^2.1.13 @tiptap/starter-kit@^2.1.13 @tiptap/extension-underline@^2.1.13 @tiptap/extension-link@^2.1.13 --legacy-peer-deps
```

## Usage

### Basic Usage

```tsx
import React, { useState } from 'react'
import { NewComposeEmailModal, QuantumSendSummary } from './components/compose'

function App() {
  const [isComposeOpen, setIsComposeOpen] = useState(false)

  const handleSend = (summary: QuantumSendSummary) => {
    console.log('Email sent:', summary)
    setIsComposeOpen(false)
    // Refresh inbox or update UI
  }

  return (
    <>
      <button onClick={() => setIsComposeOpen(true)}>
        Compose Email
      </button>

      <NewComposeEmailModal
        isOpen={isComposeOpen}
        onClose={() => setIsComposeOpen(false)}
        onSend={handleSend}
      />
    </>
  )
}
```

### Reply to Email

```tsx
import React, { useState } from 'react'
import { NewComposeEmailModal } from './components/compose'

function EmailViewer({ email }) {
  const [isReplyOpen, setIsReplyOpen] = useState(false)

  return (
    <>
      <button onClick={() => setIsReplyOpen(true)}>
        Reply
      </button>

      <NewComposeEmailModal
        isOpen={isReplyOpen}
        onClose={() => setIsReplyOpen(false)}
        onSend={(summary) => {
          console.log('Reply sent:', summary)
          setIsReplyOpen(false)
        }}
        replyTo={email}
      />
    </>
  )
}
```

### With Custom Security Level

```tsx
<NewComposeEmailModal
  isOpen={isOpen}
  onClose={onClose}
  onSend={onSend}
  // Will pre-select Level 1 (Quantum Secure)
/>
```

## Component Props

### NewComposeEmailModalProps

```typescript
interface NewComposeEmailModalProps {
  /** Controls modal visibility */
  isOpen: boolean
  
  /** Called when user closes the modal */
  onClose: () => void
  
  /** Called after successful email send with summary */
  onSend: (summary: QuantumSendSummary) => void
  
  /** Optional email to reply to - populates fields */
  replyTo?: Email | null
}
```

### QuantumSendSummary

```typescript
interface QuantumSendSummary {
  success: boolean
  message: string
  flowId: string
  gmailMessageId?: string
  gmailThreadId?: string
  encryptionMethod: string
  securityLevel: number
  emailId?: number
  emailUuid?: string
  entropy?: number
  keyId?: string
  encryptedSize?: number
  timestamp?: string
  sentViaGmail: boolean
}
```

### Email Interface

```typescript
interface Email {
  id: string
  from?: string
  to?: string
  subject?: string
  body?: string
  html_body?: string
  plain_body?: string
  timestamp: string
  read?: boolean
  encrypted?: boolean
  securityLevel?: 1 | 2 | 3 | 4
  sender_name?: string
  sender_email?: string
  // ... additional fields
}
```

## Customization

### Add Custom Contacts

Modify the `contacts` array in the component:

```typescript
const contacts: Contact[] = [
  { email: 'alice@example.com', name: 'Alice Johnson' },
  { email: 'bob@example.com', name: 'Bob Smith' },
  // Add your contacts here
]
```

### Customize Security Levels

Modify the `SECURITY_LEVELS` array:

```typescript
const SECURITY_LEVELS = [
  {
    value: 4,
    name: 'Standard',
    shortName: 'Standard',
    description: 'Regular encryption without quantum enhancement',
    color: 'gray',
    icon: Lock,
    gradient: 'from-gray-500 to-gray-600'
  },
  // Add or modify levels
]
```

### Change Editor Configuration

Modify the Tiptap editor initialization:

```typescript
const editor = useEditor({
  extensions: [
    StarterKit.configure({
      heading: {
        levels: [1, 2, 3, 4, 5, 6] // Enable all heading levels
      }
    }),
    Underline,
    Link,
    // Add more extensions like Image, Table, etc.
  ],
  content: '',
  editorProps: {
    attributes: {
      class: 'your-custom-classes'
    }
  }
})
```

### Styling

The component uses Tailwind CSS classes. To customize:

1. **Colors**: Modify gradient classes like `from-blue-600 to-indigo-600`
2. **Spacing**: Change padding/margin classes like `px-6 py-4`
3. **Border Radius**: Update rounded classes like `rounded-2xl`
4. **Shadows**: Adjust shadow classes like `shadow-2xl`

## API Integration

### Backend Endpoints

The component expects these API endpoints:

#### 1. Check Quantum Keys
```
GET http://localhost:8000/api/v1/quantum/keys/available
Headers: Authorization: Bearer {token}
Response: { available: boolean, count: number }
```

#### 2. Generate Quantum Keys
```
POST http://localhost:8000/api/v1/quantum/key/exchange
Headers: 
  Authorization: Bearer {token}
  Content-Type: application/json
Body: { sender_kme_id: 1, recipient_kme_id: 2 }
```

#### 3. Send Email
```
POST http://localhost:8000/api/v1/emails/send/quantum
Headers:
  Authorization: Bearer {token}
  Content-Type: application/json
Body: {
  to: string,
  subject: string,
  body: string (HTML),
  security_level: 1 | 2 | 3 | 4,
  type: 'quantum',
  cc?: string[],
  bcc?: string[]
}
Response: QuantumSendSummary
```

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| Ctrl+B | Toggle Bold |
| Ctrl+I | Toggle Italic |
| Ctrl+U | Toggle Underline |
| Ctrl+Enter | Send Email (when ready) |
| Escape | Close Modal |

## Advanced Features

### Auto-save Drafts

The component automatically saves drafts every 30 seconds. Customize the interval:

```typescript
// In the component, find this line and change 30000 to your desired milliseconds
const interval = setInterval(saveDraft, 30000) // 30 seconds
```

### Custom Link Dialog

The link insertion uses a custom dialog. You can enhance it:

```typescript
const setLink = () => {
  if (!linkUrl) {
    editor?.chain().focus().unsetLink().run()
    return
  }

  // Add custom validation
  if (!linkUrl.match(/^https?:\/\//)) {
    toast.error('Please enter a valid URL')
    return
  }

  const url = linkUrl.startsWith('http') ? linkUrl : `https://${linkUrl}`
  editor?.chain().focus().extendMarkRange('link').setLink({ href: url }).run()
  setShowLinkDialog(false)
  setLinkUrl('')
}
```

### File Upload Progress

The component supports file attachments. To add upload progress:

```typescript
const handleFileSelect = async (event: React.ChangeEvent<HTMLInputElement>) => {
  const files = Array.from(event.target.files || [])
  
  for (const file of files) {
    const attachment = {
      file,
      id: Math.random().toString(36).substring(7),
      progress: 0
    }
    
    setAttachments(prev => [...prev, attachment])
    
    // Simulate upload with progress
    const interval = setInterval(() => {
      setAttachments(prev => prev.map(a => 
        a.id === attachment.id 
          ? { ...a, progress: Math.min(a.progress + 10, 100) }
          : a
      ))
    }, 100)
  }
}
```

## Troubleshooting

### Editor Not Loading

Ensure Tiptap extensions are installed:
```bash
npm list @tiptap/react @tiptap/starter-kit
```

### Styles Not Applying

Make sure Tailwind CSS is properly configured in your project:
```javascript
// tailwind.config.js
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  // ...
}
```

### Dark Mode Not Working

Ensure your parent component has dark mode class:
```html
<div className="dark">
  <NewComposeEmailModal ... />
</div>
```

### Authentication Errors

The component expects an `authToken` in localStorage:
```typescript
localStorage.setItem('authToken', 'your-jwt-token')
```

## Performance Optimization

### Lazy Loading

Lazy load the composer to reduce initial bundle size:

```typescript
import React, { lazy, Suspense } from 'react'

const NewComposeEmailModal = lazy(() => 
  import('./components/compose/NewComposeEmailModal').then(module => ({
    default: module.NewComposeEmailModal
  }))
)

function App() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <NewComposeEmailModal ... />
    </Suspense>
  )
}
```

### Memoization

Memoize callback functions:

```typescript
import { useCallback } from 'react'

const handleSend = useCallback((summary: QuantumSendSummary) => {
  // Handle send
}, [])
```

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## License

Same as QuMail project license.

## Contributing

To contribute improvements to the composer:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## Support

For issues or questions:
- Open an issue on GitHub
- Contact the QuMail team
- Check the main documentation

## Changelog

### Version 1.0.0 (Current)
- ✨ Initial release with full rich text editing
- 🔐 Four quantum security levels
- 📎 File attachment support
- 🎨 Modern UI with dark mode
- ⚡ Smooth animations and transitions
- 📱 Responsive design
- ♿ Accessibility features
