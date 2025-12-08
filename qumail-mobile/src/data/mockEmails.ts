import { Email } from '../types';

// Mock emails - Indian Data Scientists with Quantum Secure Email
export const mockEmails: Email[] = [
  {
    id: '1',
    threadId: 't1',
    from: {
      name: 'Dr. Priya Sharma',
      email: 'priya.sharma@isro.gov.in',
    },
    to: [{ name: 'Me', email: 'me@qumail.app' }],
    subject: 'Quantum Key Distribution Research',
    snippet: 'Namaste! I would like to discuss our upcoming quantum cryptography research collaboration with ISRO.',
    body: 'Namaste!\n\nI would like to discuss our upcoming quantum cryptography research collaboration with ISRO. The satellite-based QKD experiments are showing promising results.\n\nDate: 15.12.2024\nTime: 14:00 IST\n\nBest regards,\nDr. Priya Sharma\nSenior Data Scientist, ISRO',
    date: new Date().toISOString(),
    timestamp: Date.now(),
    isRead: false,
    isStarred: true,
    labels: ['INBOX'],
    hasAttachments: false,
    isEncrypted: true,
    encryptionLevel: 1,
    tags: [
      { label: 'Level 1 - OTP', color: 'green' }
    ]
  },
  {
    id: '2',
    threadId: 't2',
    from: {
      name: 'Amit Patel',
      email: 'amit.patel@drdo.gov.in',
    },
    to: [{ name: 'Me', email: 'me@qumail.app' }],
    subject: 'RE: Secure Communication Protocol',
    snippet: 'The AES-256 implementation with quantum keys has been tested successfully. Attaching the report.',
    body: 'The AES-256 implementation with quantum keys has been tested successfully. Attaching the detailed security audit report.\n\nBest regards,\nAmit Patel\nLead Data Scientist, DRDO',
    date: new Date(Date.now() - 3600000).toISOString(),
    timestamp: Date.now() - 3600000,
    isRead: true,
    isStarred: false,
    labels: ['INBOX'],
    hasAttachments: true,
    isEncrypted: true,
    encryptionLevel: 2,
    tags: [
      { label: 'Level 2 - AES', color: 'blue' }
    ]
  },
  {
    id: '3',
    threadId: 't3',
    from: {
      name: 'Neha Gupta',
      email: 'neha.gupta@cdac.in',
    },
    to: [{ name: 'Me', email: 'me@qumail.app' }],
    subject: 'Post-Quantum Cryptography Workshop',
    snippet: 'Invitation to the PQC workshop at C-DAC Pune. Kyber and Dilithium algorithms will be discussed.',
    body: 'Dear Colleague,\n\nYou are invited to the Post-Quantum Cryptography workshop at C-DAC Pune.\n\nTopics: Kyber1024, Dilithium5 algorithms\nDate: 20.12.2024\nVenue: C-DAC Pune\n\nNeha Gupta\nPrincipal Data Scientist, C-DAC',
    date: new Date(Date.now() - 86400000).toISOString(),
    timestamp: Date.now() - 86400000,
    isRead: true,
    isStarred: false,
    labels: ['INBOX'],
    hasAttachments: false,
    isEncrypted: true,
    encryptionLevel: 3,
    tags: [
      { label: 'Level 3 - PQC', color: 'purple' }
    ]
  },
  {
    id: '4',
    threadId: 't4',
    from: {
      name: 'Rajesh Kumar',
      email: 'rajesh.kumar@nic.in',
    },
    to: [{ name: 'Me', email: 'me@qumail.app' }],
    subject: 'RSA-4096 Hybrid Encryption Test',
    snippet: 'The hybrid RSA + quantum key implementation is ready for government deployment.',
    body: 'Namaste!\n\nThe hybrid RSA-4096 + quantum key implementation is ready for government deployment. Security audit passed with all parameters.\n\nPlease review and approve.\n\nRajesh Kumar\nChief Data Scientist, NIC',
    date: new Date(Date.now() - 172800000).toISOString(),
    timestamp: Date.now() - 172800000,
    isRead: true,
    isStarred: false,
    labels: ['INBOX'],
    hasAttachments: false,
    isEncrypted: true,
    encryptionLevel: 4,
    tags: [
      { label: 'Level 4 - RSA', color: 'orange' }
    ]
  },
  {
    id: '5',
    threadId: 't5',
    from: {
      name: 'Kavitha Menon',
      email: 'kavitha.menon@iitb.ac.in',
    },
    to: [{ name: 'Me', email: 'me@qumail.app' }],
    subject: 'Quantum Computing Seminar',
    snippet: 'Join us for the quantum computing seminar at IIT Bombay. Topics include quantum ML and cryptography.',
    body: 'Dear Researcher,\n\nJoin us for the quantum computing seminar at IIT Bombay.\n\nTopics:\n- Quantum Machine Learning\n- Quantum Cryptography\n- Post-Quantum Security\n\nDr. Kavitha Menon\nAssociate Professor & Data Scientist, IIT Bombay',
    date: new Date(Date.now() - 259200000).toISOString(),
    timestamp: Date.now() - 259200000,
    isRead: false,
    isStarred: false,
    labels: ['INBOX'],
    hasAttachments: false,
    isEncrypted: true,
    encryptionLevel: 2,
    tags: [
      { label: 'Level 2 - AES', color: 'blue' }
    ]
  },
];

export const mockSentEmails: Email[] = [];

export const mockDrafts: Email[] = [];
