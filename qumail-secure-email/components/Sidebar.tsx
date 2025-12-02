import React from 'react';
import { 
  Inbox, Send, FileText, Trash2, 
  ShieldCheck, Plus, LayoutDashboard
} from 'lucide-react';

interface SidebarProps {
  activeFolder: string;
  setActiveFolder: (folder: string) => void;
  onCompose: () => void;
  isCompact: boolean;
  folderCounts: {
    inbox: number;
    drafts: number;
    trash: number;
  };
}

const Sidebar: React.FC<SidebarProps> = ({ activeFolder, setActiveFolder, onCompose, isCompact, folderCounts }) => {
  const folders = [
    { id: 'inbox', name: 'Inbox', icon: Inbox, count: folderCounts.inbox },
    { id: 'sent', name: 'Sent', icon: Send, count: undefined },
    { id: 'drafts', name: 'Drafts', icon: FileText, count: folderCounts.drafts },
    { id: 'trash', name: 'Trash', icon: Trash2, count: folderCounts.trash },
  ];

  const managementItems = [
    { 
        id: 'dashboard', 
        name: 'Quantum Dashboard', 
        icon: LayoutDashboard,
        colorClass: "group-hover:text-indigo-600",
    }
  ];

  return (
    <div className={`${isCompact ? 'w-24' : 'w-64'} h-full bg-white border-y border-r border-gray-200 rounded-r-2xl shadow-sm flex flex-col flex-shrink-0 transition-all duration-300 ease-in-out z-20 relative overflow-hidden`}>
      {/* Compose Button */}
      <div className="p-5 flex justify-center">
        <button 
          onClick={onCompose}
          className={`bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl font-medium flex items-center justify-center shadow-sm transition-all duration-200 group relative
            ${isCompact ? 'w-14 h-14 rounded-full' : 'w-48 h-12 gap-2.5'}`}
        >
          {isCompact ? (
             <>
                <Plus size={28} />
                <span className="absolute left-full ml-4 px-2 py-1 bg-gray-800 text-white text-xs rounded opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity whitespace-nowrap z-50">
                    New Message
                </span>
             </>
          ) : (
             <>
                <Plus size={20} />
                <span className="text-sm font-semibold">New Message</span>
             </>
          )}
        </button>
      </div>

      {/* Folders */}
      <div className={`px-3 py-2 ${isCompact ? 'flex flex-col items-center' : ''}`}>
        {!isCompact && <h3 className="px-4 text-[11px] font-bold text-gray-400 uppercase tracking-wider mb-2 animate-in fade-in duration-300">Folders</h3>}
        <div className="space-y-1 w-full">
          {folders.map((folder) => {
            const Icon = folder.icon;
            const isActive = activeFolder === folder.id;
            const showCount = folder.count !== undefined && folder.count > 0;

            return (
              <button
                key={folder.id}
                onClick={() => setActiveFolder(folder.id)}
                className={`w-full flex items-center rounded-lg font-medium transition-colors group relative
                  ${isActive 
                    ? 'bg-indigo-50 text-indigo-700' 
                    : 'text-gray-600 hover:bg-gray-50'
                  }
                  ${isCompact ? 'justify-center py-4' : 'justify-between px-4 py-2.5 text-sm'}
                `}
              >
                <div className={`flex items-center ${isCompact ? '' : 'gap-3'}`}>
                  <Icon size={isCompact ? 24 : 18} strokeWidth={2} className={isActive ? 'text-indigo-600' : 'text-gray-400'} />
                  {!isCompact && <span>{folder.name}</span>}
                </div>
                
                {!isCompact && showCount && (
                  <span className={`text-[11px] px-2 py-0.5 rounded-full ${isActive ? 'bg-indigo-100 text-indigo-700' : 'bg-gray-100 text-gray-600'}`}>
                    {folder.count}
                  </span>
                )}

                {/* Tooltip for Compact Mode */}
                {isCompact && (
                    <span className="absolute left-full ml-4 px-2 py-1 bg-gray-800 text-white text-xs rounded opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity whitespace-nowrap z-50">
                        {folder.name} {showCount && `(${folder.count})`}
                    </span>
                )}
              </button>
            );
          })}
        </div>
      </div>

      {/* Management Section */}
      <div className={`px-3 py-6 mt-auto ${isCompact ? 'flex flex-col items-center' : ''}`}>
        {!isCompact && <h3 className="px-4 text-[11px] font-bold text-gray-400 uppercase tracking-wider mb-2 animate-in fade-in duration-300">Management</h3>}
        <div className="space-y-1 w-full">

          {managementItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeFolder === item.id;
            
            return (
              <button
                key={item.id}
                onClick={() => setActiveFolder(item.id)}
                className={`group relative w-full flex items-center rounded-lg font-medium transition-all duration-200 hover:bg-gray-50
                   ${isCompact ? 'justify-center py-4' : 'gap-3 px-4 py-2.5 text-sm'}
                   ${isActive ? 'bg-indigo-50 text-indigo-700' : 'text-gray-600'}
                `}
              >
                <Icon 
                    size={isCompact ? 24 : 18} 
                    strokeWidth={2} 
                    className={`transition-colors ${isActive ? 'text-indigo-600' : 'text-gray-400'} ${item.colorClass}`} 
                />
                {!isCompact && <span className={`${isActive ? 'text-indigo-700' : ''}`}>{item.name}</span>}

                {/* Tooltip for Compact Mode */}
                {isCompact && (
                    <span className="absolute left-full ml-4 px-2 py-1 bg-gray-800 text-white text-xs rounded opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity whitespace-nowrap z-50">
                        {item.name}
                    </span>
                )}
              </button>
            );
          })}
        </div>
      </div>

      {/* Bottom Encryption Status */}
      <div className="p-5">
        <div className={`border border-gray-200 rounded-xl flex items-center shadow-sm bg-gray-50/50 transition-all duration-300
            ${isCompact ? 'justify-center p-3' : 'p-3 gap-3'}
        `}>
          <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center flex-shrink-0 shadow-inner group relative">
             <ShieldCheck size={16} className="text-green-600" />
             {isCompact && (
                <span className="absolute left-full ml-4 px-2 py-1 bg-gray-800 text-white text-xs rounded opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity whitespace-nowrap z-50">
                    Encrypted (2048-bit)
                </span>
             )}
          </div>
          {!isCompact && (
              <div className="animate-in fade-in duration-300">
                 <p className="text-xs font-bold text-gray-800">Encrypted</p>
                 <p className="text-[10px] text-gray-500">QKD Active</p>
              </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Sidebar;