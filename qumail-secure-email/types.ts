import React from 'react';

export enum SecurityLevel {
  LEVEL_1 = 'Quantum Secure (Level 1)',
  LEVEL_2 = 'Quantum-Aided AES (Level 2)',
  LEVEL_3 = 'Post-Quantum (Level 3)',
  LEVEL_4 = 'Standard (Level 4)',
}

export interface EmailAttachment {
  id: string;
  filename: string;
  mimeType?: string;
  size?: number;
  content?: string;
}

export interface Email {
  id: string;
  senderName: string;
  senderEmail: string;
  senderAvatar: string; // URL or initials
  subject: string;
  snippet: string;
  content: string | React.ReactNode;
  bodyHtml?: string;
  attachments?: EmailAttachment[];
  timestamp: string; // Display time
  fullDate: string;
  tags: string[];
  isUnread: boolean;
  isStarred: boolean; // New property
  securityLevel: SecurityLevel;
  isEncrypted: boolean; // If true, requires decryption to view body
  folder: 'inbox' | 'sent' | 'drafts' | 'trash';
  isFlagged?: boolean;
  securityDetails?: {
    flowId: string;
    signatureVerified: boolean;
  };
  flowId?: string;
  gmailMessageId?: string;
  requiresDecryption?: boolean;
  decryptEndpoint?: string;
}

export interface User {
  name: string;
  email: string;
  avatar: string;
  accountType: string;
}

export interface Folder {
  id: string;
  name: string;
  icon: any; // Using Lucide icons
  count?: number;
}