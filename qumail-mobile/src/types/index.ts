// Email types matching the web app
export interface Email {
  id: string;
  threadId: string;
  from: {
    name: string;
    email: string;
  };
  to: {
    name: string;
    email: string;
  }[];
  subject: string;
  snippet: string;
  body: string;
  date: string;
  timestamp: number;
  isRead: boolean;
  isStarred: boolean;
  labels: string[];
  hasAttachments: boolean;
  attachments?: Attachment[];
  isEncrypted: boolean;
  encryptionLevel?: 1 | 2 | 3 | 4;
  isDecrypted?: boolean;
  decryptedBody?: string;
  tags?: { label: string; color: 'blue' | 'darkBlue' | 'purple' | 'green' | 'orange' }[];
}

export interface Attachment {
  id: string;
  filename: string;
  mimeType: string;
  size: number;
}

export interface User {
  id: string;
  email: string;
  name: string;
  picture?: string;
}

export interface EncryptionLevel {
  level: 1 | 2 | 3 | 4;
  name: string;
  description: string;
  icon: string;
  color: string;
}

export interface ComposeEmail {
  to: string;
  subject: string;
  body: string;
  encryptionLevel: 1 | 2 | 3 | 4;
}

export type MailboxType = 'inbox' | 'sent' | 'drafts' | 'trash' | 'starred' | 'archive' | 'spam';

export interface AuthState {
  isAuthenticated: boolean;
  user: User | null;
  accessToken: string | null;
  isLoading: boolean;
}
