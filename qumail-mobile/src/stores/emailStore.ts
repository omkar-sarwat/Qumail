import { create } from 'zustand';
import { Email, MailboxType } from '../types';
import { mockEmails, mockSentEmails, mockDrafts } from '../data/mockEmails';
import { useAuthStore } from './authStore';

interface EmailStore {
  emails: Email[];
  sentEmails: Email[];
  drafts: Email[];
  currentMailbox: MailboxType;
  selectedEmail: Email | null;
  isLoading: boolean;
  searchQuery: string;
  error: string | null;
  
  // Actions
  setCurrentMailbox: (mailbox: MailboxType) => void;
  setSelectedEmail: (email: Email | null) => void;
  setSearchQuery: (query: string) => void;
  markAsRead: (emailId: string) => void;
  toggleStar: (emailId: string) => void;
  deleteEmail: (emailId: string) => void;
  archiveEmail: (emailId: string) => void;
  decryptEmail: (emailId: string) => Promise<void>;
  sendEmail: (to: string, subject: string, body: string, encryptionLevel?: number) => Promise<void>;
  refreshEmails: () => Promise<void>;
  getFilteredEmails: () => Email[];
  getUnreadCount: () => number;
  clearError: () => void;
}

export const useEmailStore = create<EmailStore>((set, get) => ({
  emails: mockEmails,
  sentEmails: mockSentEmails,
  drafts: mockDrafts,
  currentMailbox: 'inbox',
  selectedEmail: null,
  isLoading: false,
  searchQuery: '',
  error: null,
  
  setCurrentMailbox: (mailbox: MailboxType) => {
    set({ currentMailbox: mailbox, selectedEmail: null });
  },
  
  setSelectedEmail: (email: Email | null) => {
    set({ selectedEmail: email });
    if (email && !email.isRead) {
      get().markAsRead(email.id);
    }
  },
  
  setSearchQuery: (query: string) => {
    set({ searchQuery: query });
  },
  
  markAsRead: (emailId: string) => {
    set((state) => ({
      emails: state.emails.map((email) =>
        email.id === emailId ? { ...email, isRead: true } : email
      ),
    }));
  },
  
  toggleStar: (emailId: string) => {
    set((state) => ({
      emails: state.emails.map((email) =>
        email.id === emailId ? { ...email, isStarred: !email.isStarred } : email
      ),
    }));
  },
  
  deleteEmail: (emailId: string) => {
    set((state) => ({
      emails: state.emails.filter((email) => email.id !== emailId),
      selectedEmail: state.selectedEmail?.id === emailId ? null : state.selectedEmail,
    }));
  },

  archiveEmail: (emailId: string) => {
    set((state) => ({
      emails: state.emails.filter((email) => email.id !== emailId),
      selectedEmail: state.selectedEmail?.id === emailId ? null : state.selectedEmail,
    }));
  },
  
  decryptEmail: async (emailId: string) => {
    const { emails, selectedEmail } = get();
    const email = emails.find(e => e.id === emailId) || selectedEmail;
    
    if (!email) return;

    set({ isLoading: true, error: null });

    // Simulate decryption with animation delay
    await new Promise((resolve) => setTimeout(resolve, 1500));
    
    // Sample decrypted content based on encryption level
    const decryptedMessages: Record<number, string> = {
      1: `🔓 DECRYPTED (OTP Level 1)\n\n${email.body}\n\n---\n✓ One-Time Pad encryption verified\n✓ Quantum key consumed`,
      2: `🔓 DECRYPTED (AES-256 Level 2)\n\n${email.body}\n\n---\n✓ AES-256-GCM decryption successful\n✓ Authentication tag verified`,
      3: `🔓 DECRYPTED (PQC Level 3)\n\n${email.body}\n\n---\n✓ Kyber1024 key decapsulated\n✓ Dilithium5 signature verified`,
      4: `🔓 DECRYPTED (Quantum Level 4)\n\n${email.body}\n\n---\n✓ RSA-4096 key unwrapped\n✓ Quantum-enhanced security verified`,
    };
    
    const decryptedBody = email.encryptionLevel 
      ? decryptedMessages[email.encryptionLevel] || email.body
      : email.body;
    
    set((state) => ({
      emails: state.emails.map((e) =>
        e.id === emailId
          ? { ...e, isDecrypted: true, decryptedBody }
          : e
      ),
      selectedEmail:
        state.selectedEmail?.id === emailId
          ? { ...state.selectedEmail, isDecrypted: true, decryptedBody }
          : state.selectedEmail,
      isLoading: false,
    }));
  },
  
  sendEmail: async (to: string, subject: string, body: string, encryptionLevel?: number) => {
    set({ isLoading: true, error: null });
    
    // Simulate sending with encryption
    await new Promise((resolve) => setTimeout(resolve, 1200));
    
    const user = useAuthStore.getState().user;
    const newEmail: Email = {
      id: `s${Date.now()}`,
      threadId: `thread${Date.now()}`,
      from: {
        name: user?.name || 'You',
        email: user?.email || 'you@qumail.app',
      },
      to: [{ name: to.split('@')[0], email: to }],
      subject,
      snippet: body.substring(0, 100),
      body,
      date: new Date().toISOString(),
      timestamp: Date.now(),
      isRead: true,
      isStarred: false,
      labels: ['SENT'],
      hasAttachments: false,
      isEncrypted: !!encryptionLevel,
      encryptionLevel: encryptionLevel as 1 | 2 | 3 | 4 | undefined,
    };
    
    set((state) => ({
      sentEmails: [newEmail, ...state.sentEmails],
      isLoading: false,
    }));
  },

  refreshEmails: async () => {
    set({ isLoading: true });
    
    // Simulate refresh delay
    await new Promise((resolve) => setTimeout(resolve, 800));
    
    set({ isLoading: false });
  },
  
  getFilteredEmails: () => {
    const { emails, sentEmails, drafts, currentMailbox, searchQuery } = get();
    
    let filtered: Email[] = [];
    
    switch (currentMailbox) {
      case 'inbox':
        filtered = emails.filter(e => e.labels.includes('INBOX'));
        break;
      case 'sent':
        filtered = sentEmails;
        break;
      case 'drafts':
        filtered = drafts;
        break;
      case 'starred':
        filtered = [...emails, ...sentEmails].filter(e => e.isStarred);
        break;
      case 'archive':
        filtered = emails.filter(e => e.labels.includes('ARCHIVE'));
        break;
      case 'trash':
        filtered = emails.filter(e => e.labels.includes('TRASH'));
        break;
      case 'spam':
        filtered = emails.filter(e => e.labels.includes('SPAM'));
        break;
      default:
        filtered = emails;
    }
    
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(
        (email) =>
          email.subject.toLowerCase().includes(query) ||
          email.from.name.toLowerCase().includes(query) ||
          email.from.email.toLowerCase().includes(query) ||
          email.snippet.toLowerCase().includes(query)
      );
    }
    
    return filtered.sort((a, b) => b.timestamp - a.timestamp);
  },
  
  getUnreadCount: () => {
    const { emails } = get();
    return emails.filter((email) => !email.isRead && email.labels.includes('INBOX')).length;
  },
  
  clearError: () => set({ error: null }),
}));
