import React from 'react';
import { Search, Shield, Menu, Settings, Bell } from 'lucide-react';
import { User } from '../types';
import { FALLBACK_USER } from '../constants';

interface HeaderProps {
    onToggleSidebar: () => void;
    user?: User;
}

const Header: React.FC<HeaderProps> = ({ onToggleSidebar, user }) => {
  const currentUser = user || FALLBACK_USER;
  return (
    <header className="h-20 bg-white border-b border-gray-200 flex items-center justify-between px-6 flex-shrink-0 z-10 transition-all duration-300">
      {/* Logo Area - Matched to Sidebar w-64 */}
      <div className="flex items-center gap-3 w-64">
        <button 
            onClick={onToggleSidebar}
            className="p-2 -ml-2 hover:bg-gray-100 rounded-lg text-gray-500 transition-colors focus:outline-none"
        >
            <Menu size={22} />
        </button>
        <div className="w-10 h-10 bg-indigo-600 rounded-xl flex items-center justify-center shadow-md shadow-indigo-200 flex-shrink-0">
          <Shield className="text-white w-6 h-6" />
        </div>
        <div className="hidden sm:block">
            <h1 className="font-bold text-gray-900 text-xl leading-tight">QuMail</h1>
            <p className="text-[10px] font-bold text-indigo-600 tracking-widest uppercase">Secure Workspace</p>
        </div>
      </div>

      {/* Search Bar */}
      <div className="flex-1 max-w-3xl mx-6">
        <div className="relative">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400 w-5 h-5" />
          <input 
            type="text" 
            placeholder="Search secured messages, hashes, or contacts..." 
            className="w-full pl-12 pr-4 py-3 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all shadow-sm"
          />
        </div>
      </div>

      {/* Right Actions */}
      <div className="flex items-center gap-4 sm:gap-6">
        <div className="flex items-center gap-2 sm:gap-3 text-gray-400">
            <button className="p-2 hover:bg-gray-100 rounded-full transition-colors relative" title="Notifications">
                <Bell size={20} />
                <span className="absolute top-2 right-2.5 w-2 h-2 bg-red-500 rounded-full border border-white"></span>
            </button>
            <button className="p-2 hover:bg-gray-100 rounded-full transition-colors" title="Settings">
                <Settings size={20} />
            </button>
        </div>

        <div className="h-8 w-px bg-gray-200 hidden sm:block"></div>

        <div className="flex items-center gap-3">
            <div className="text-right hidden md:block">
            <p className="text-sm font-semibold text-gray-900">{currentUser.name}</p>
            <p className="text-xs text-gray-500">{currentUser.accountType}</p>
            </div>
            <img 
            src={currentUser.avatar} 
                alt="User Profile" 
                className="w-10 h-10 rounded-full border border-gray-200 object-cover cursor-pointer hover:ring-2 hover:ring-indigo-100 transition-all"
            />
        </div>
      </div>
    </header>
  );
};

export default Header;