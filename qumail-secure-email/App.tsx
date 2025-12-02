import React, { useState, useEffect, useCallback, useMemo } from 'react';
import Header from './components/Header';
import Sidebar from './components/Sidebar';
import EmailList from './components/EmailList';
import EmailDetail from './components/EmailDetail';
import ComposeModal from './components/ComposeModal';
import SplashScreen from './components/SplashScreen';
import Dashboard from './components/Dashboard';
import { FALLBACK_USER } from './constants';
import { Email, SecurityLevel, User } from './types';
import {
  fetchCurrentUser,
  fetchEmails,
  fetchEmailDetail,
  decryptEmail,
  sendEmail,
} from './lib/api';
import { applyDecryption, mapSummaryToEmail, mergeDetail } from './lib/emailMapper';

type MailFolder = Email['folder'];

const FOLDER_LABELS: Record<MailFolder, string> = {
  inbox: 'Inbox',
  sent: 'Sent',
  drafts: 'Drafts',
  trash: 'Trash',
};

const SECURITY_LEVEL_TO_ID: Record<SecurityLevel, number> = {
  [SecurityLevel.LEVEL_1]: 1,
  [SecurityLevel.LEVEL_2]: 2,
  [SecurityLevel.LEVEL_3]: 3,
  [SecurityLevel.LEVEL_4]: 4,
};

const App: React.FC = () => {
  const [showSplash, setShowSplash] = useState(true);
  const [isBootstrapping, setIsBootstrapping] = useState(true);
  const [user, setUser] = useState<User>(FALLBACK_USER);
  const [emailsByFolder, setEmailsByFolder] = useState<Record<MailFolder, Email[]>>({
    inbox: [],
    sent: [],
    drafts: [],
    trash: [],
  });
  const [activeFolder, setActiveFolder] = useState<'dashboard' | MailFolder>('inbox');
  const [selectedEmailId, setSelectedEmailId] = useState<string | null>(null);
  const [isComposeOpen, setIsComposeOpen] = useState(false);
  const [isSidebarCompact, setIsSidebarCompact] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loadingEmailId, setLoadingEmailId] = useState<string | null>(null);
  const [decryptingEmailId, setDecryptingEmailId] = useState<string | null>(null);
  const [isFetchingFolder, setIsFetchingFolder] = useState(false);
  const [isSending, setIsSending] = useState(false);

  const ensureList = useCallback((payload: any) => {
    if (!payload) return [];
    if (Array.isArray(payload)) return payload;
    if (Array.isArray(payload.emails)) return payload.emails;
    if (Array.isArray(payload.messages)) return payload.messages;
    if (Array.isArray(payload.data)) return payload.data;
    return [];
  }, []);

  const setFolderEmails = useCallback((folder: MailFolder, next: Email[]) => {
    setEmailsByFolder(prev => ({ ...prev, [folder]: next }));
  }, []);

  const updateEmail = useCallback((folder: MailFolder, updated: Email) => {
    setEmailsByFolder(prev => ({
      ...prev,
      [folder]: (prev[folder] || []).map(email => (email.id === updated.id ? updated : email)),
    }));
  }, []);

  const bootstrap = useCallback(async () => {
    try {
      const [userResponse, inboxResponse] = await Promise.all([
        fetchCurrentUser().catch(() => null),
        fetchEmails('inbox'),
      ]);

      if (userResponse?.user) {
        setUser(userResponse.user);
      } else if (userResponse?.name) {
        setUser(userResponse as User);
      }

      const inboxList = ensureList(inboxResponse).map((summary: any) => mapSummaryToEmail(summary, 'inbox'));
      setFolderEmails('inbox', inboxList);
      setSelectedEmailId(inboxList[0]?.id || null);
      setError(null);
    } catch (err) {
      console.error(err);
      setError((err as Error).message || 'Failed to initialize workspace');
    } finally {
      setIsBootstrapping(false);
    }
  }, [ensureList, setFolderEmails]);

  useEffect(() => {
    bootstrap();
  }, [bootstrap]);

  const loadFolder = useCallback(
    async (folder: MailFolder) => {
      setIsFetchingFolder(true);
      try {
        const response = await fetchEmails(folder);
        const list = ensureList(response).map((summary: any) => mapSummaryToEmail(summary, folder));
        setFolderEmails(folder, list);
        setError(null);
      } catch (err) {
        console.error(err);
        setError((err as Error).message || `Unable to load ${folder}`);
      } finally {
        setIsFetchingFolder(false);
      }
    },
    [ensureList, setFolderEmails]
  );

  useEffect(() => {
    if (activeFolder === 'dashboard') {
      return;
    }
    loadFolder(activeFolder);
  }, [activeFolder, loadFolder]);

  useEffect(() => {
    if (activeFolder === 'dashboard') {
      setSelectedEmailId(null);
      return;
    }
    const currentFolderEmails = emailsByFolder[activeFolder];
    if (!currentFolderEmails?.length) {
      setSelectedEmailId(null);
      return;
    }
    if (!selectedEmailId || !currentFolderEmails.some(email => email.id === selectedEmailId)) {
      setSelectedEmailId(currentFolderEmails[0].id);
    }
  }, [activeFolder, emailsByFolder, selectedEmailId]);

  const activeEmails = useMemo(() => {
    if (activeFolder === 'dashboard') {
      return [];
    }
    return emailsByFolder[activeFolder] || [];
  }, [activeFolder, emailsByFolder]);

  const selectedEmail = useMemo(() => {
    if (!selectedEmailId) return null;
    if (activeFolder === 'dashboard') return null;
    return activeEmails.find(email => email.id === selectedEmailId) || null;
  }, [activeEmails, activeFolder, selectedEmailId]);

  useEffect(() => {
    if (!selectedEmail || selectedEmail.content) {
      return;
    }
    setLoadingEmailId(selectedEmail.id);
    fetchEmailDetail(selectedEmail.id)
      .then(detail => {
        const merged = mergeDetail(selectedEmail, detail);
        updateEmail(selectedEmail.folder, merged);
      })
      .catch(err => {
        console.error(err);
        setError((err as Error).message || 'Failed to load email');
      })
      .finally(() => {
        setLoadingEmailId(null);
      });
  }, [selectedEmail, updateEmail]);

  useEffect(() => {
    if (!selectedEmail || !selectedEmail.isUnread) {
      return;
    }
    updateEmail(selectedEmail.folder, { ...selectedEmail, isUnread: false });
  }, [selectedEmail, updateEmail]);

  const toggleStar = (id: string) => {
    if (activeFolder === 'dashboard') return;
    setEmailsByFolder(prev => ({
      ...prev,
      [activeFolder]: (prev[activeFolder] || []).map(email =>
        email.id === id ? { ...email, isStarred: !email.isStarred } : email
      ),
    }));
  };

  const handleDecrypt = async () => {
    if (!selectedEmail || decryptingEmailId) return;
    setDecryptingEmailId(selectedEmail.id);
    try {
      const result = await decryptEmail(selectedEmail.id);
      const decrypted = applyDecryption(selectedEmail, result);
      updateEmail(selectedEmail.folder, decrypted);
      setError(null);
    } catch (err) {
      console.error(err);
      setError((err as Error).message || 'Decryption failed');
    } finally {
      setDecryptingEmailId(null);
    }
  };

  const handleSendEmail = async (data: { to: string; subject: string; content: string; securityLevel: SecurityLevel }) => {
    setIsSending(true);
    try {
      const formData = new FormData();
      formData.append('to', data.to);
      formData.append('subject', data.subject);
      formData.append('body', data.content);
      formData.append('security_level', String(SECURITY_LEVEL_TO_ID[data.securityLevel] || 4));

      await sendEmail(formData);
      setIsComposeOpen(false);
      setActiveFolder('sent');
      await loadFolder('sent');
      setError(null);
    } catch (err) {
      console.error(err);
      setError((err as Error).message || 'Failed to send email');
    } finally {
      setIsSending(false);
    }
  };

  const handleMoveEmail = (id: string, targetFolder: 'trash' | 'archive') => {
    if (activeFolder === 'dashboard') return;
    if (targetFolder === 'archive') {
      setEmailsByFolder(prev => ({
        ...prev,
        [activeFolder]: (prev[activeFolder] || []).filter(email => email.id !== id),
      }));
      return;
    }

    setEmailsByFolder(prev => {
      const currentFolderEmails = prev[activeFolder] || [];
      const movedEmail = currentFolderEmails.find(email => email.id === id);
      if (!movedEmail) return prev;
      return {
        ...prev,
        [activeFolder]: currentFolderEmails.filter(email => email.id !== id),
        [targetFolder]: [
          {
            ...movedEmail,
            folder: targetFolder,
          },
          ...(prev[targetFolder] || []),
        ],
      };
    });

    if (selectedEmailId === id) {
      setSelectedEmailId(null);
    }
  };

  const folderCounts = useMemo(
    () => ({
      inbox: (emailsByFolder.inbox || []).filter(email => email.isUnread).length,
      drafts: emailsByFolder.drafts?.length || 0,
      trash: emailsByFolder.trash?.length || 0,
    }),
    [emailsByFolder]
  );

  const isCurrentEmailDecrypted = selectedEmail ? !selectedEmail.requiresDecryption : true;
  const isDecrypting = decryptingEmailId === selectedEmail?.id;
  const isEmailLoading = loadingEmailId === selectedEmail?.id;

  const showContent = !showSplash && !isBootstrapping;

  return (
    <>
      {showSplash && <SplashScreen onFinish={() => setShowSplash(false)} />}
      
      <div className={`flex flex-col h-screen bg-gray-50 transition-opacity duration-1000 ${showContent ? 'opacity-100' : 'opacity-0'}`}>
        <Header user={user} onToggleSidebar={() => setIsSidebarCompact(!isSidebarCompact)} />
        
        {error && (
          <div className="mx-6 mt-3 px-4 py-2 bg-red-50 border border-red-100 text-red-700 text-sm rounded-xl shadow-sm">
            {error}
          </div>
        )}

        <div className="flex flex-1 overflow-hidden bg-gray-50 py-3 pr-3 pl-0 gap-3">
          <Sidebar 
            activeFolder={activeFolder} 
            setActiveFolder={setActiveFolder} 
            onCompose={() => setIsComposeOpen(true)}
            isCompact={isSidebarCompact}
            folderCounts={folderCounts}
          />
          
          {activeFolder === 'dashboard' ? (
            <Dashboard />
          ) : (
            <>
              <EmailList 
                emails={activeEmails} 
                folderLabel={FOLDER_LABELS[activeFolder as MailFolder] || 'Inbox'}
                selectedId={selectedEmailId} 
                onSelect={setSelectedEmailId} 
                onToggleStar={toggleStar}
                isLoading={isFetchingFolder}
              />

              {selectedEmail ? (
                  <EmailDetail 
                      email={selectedEmail} 
                      isDecrypted={isCurrentEmailDecrypted}
                      isDecrypting={isDecrypting}
                      isLoading={isEmailLoading}
                      onDecrypt={handleDecrypt}
                      onDelete={() => handleMoveEmail(selectedEmail.id, 'trash')}
                      onArchive={() => handleMoveEmail(selectedEmail.id, 'archive')}
                  />
              ) : (
                  <div className="flex-1 flex items-center justify-center rounded-2xl border border-dashed border-gray-200 bg-gray-50/50 text-gray-400">
                      Select an email to read
                  </div>
              )}
            </>
          )}
        </div>

        <ComposeModal 
          isOpen={isComposeOpen} 
          onClose={() => setIsComposeOpen(false)} 
          onSend={handleSendEmail}
          isSending={isSending}
        />
      </div>
    </>
  );
};

export default App;