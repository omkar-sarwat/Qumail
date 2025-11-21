import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { Button } from '../ui/Button';
export const Sidebar = ({ activeFolder, onFolderChange, onCompose, emailCounts, onNavigateToView }) => {
    const folders = [
        {
            id: 'inbox',
            name: 'Inbox',
            icon: (_jsx("svg", { className: "w-5 h-5", fill: "none", stroke: "currentColor", viewBox: "0 0 24 24", children: _jsx("path", { strokeLinecap: "round", strokeLinejoin: "round", strokeWidth: 2, d: "M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" }) })),
            count: emailCounts.inbox,
            color: 'from-blue-500 to-blue-600',
            bgColor: 'bg-blue-50 dark:bg-blue-900/20'
        },
        {
            id: 'sent',
            name: 'Sent',
            icon: (_jsx("svg", { className: "w-5 h-5", fill: "none", stroke: "currentColor", viewBox: "0 0 24 24", children: _jsx("path", { strokeLinecap: "round", strokeLinejoin: "round", strokeWidth: 2, d: "M12 19l9 2-9-18-9 18 9-2zm0 0v-8" }) })),
            count: emailCounts.sent,
            color: 'from-green-500 to-green-600',
            bgColor: 'bg-green-50 dark:bg-green-900/20'
        },
        {
            id: 'drafts',
            name: 'Drafts',
            icon: (_jsx("svg", { className: "w-5 h-5", fill: "none", stroke: "currentColor", viewBox: "0 0 24 24", children: _jsx("path", { strokeLinecap: "round", strokeLinejoin: "round", strokeWidth: 2, d: "M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" }) })),
            count: emailCounts.drafts,
            color: 'text-yellow-600'
        },
        {
            id: 'trash',
            name: 'Trash',
            icon: (_jsx("svg", { className: "w-5 h-5", fill: "none", stroke: "currentColor", viewBox: "0 0 24 24", children: _jsx("path", { strokeLinecap: "round", strokeLinejoin: "round", strokeWidth: 2, d: "M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" }) })),
            count: emailCounts.trash,
            color: 'text-red-600'
        }
    ];
    return (_jsxs("div", { className: "h-full flex flex-col bg-white dark:bg-[#161b22] rounded-xl border border-gray-200 dark:border-gray-800 overflow-hidden", children: [_jsx("div", { className: "p-3 border-b border-gray-100 dark:border-gray-800", children: _jsxs(Button, { onClick: onCompose, className: "w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2.5 px-4 rounded-lg transition-colors duration-200 flex items-center justify-center gap-2 text-sm", children: [_jsx("svg", { className: "w-4 h-4", fill: "none", stroke: "currentColor", viewBox: "0 0 24 24", children: _jsx("path", { strokeLinecap: "round", strokeLinejoin: "round", strokeWidth: 2, d: "M12 4v16m8-8H4" }) }), _jsx("span", { children: "Compose" })] }) }), _jsxs("div", { className: "px-2 py-3", children: [_jsx("h3", { className: "text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide px-3 mb-2", children: "Folders" }), _jsx("nav", { className: "space-y-0.5", children: folders.map((folder) => (_jsxs("button", { onClick: () => onFolderChange(folder.id), className: `group w-full flex items-center justify-between px-3 py-2 rounded-md text-left transition-colors duration-150 ${activeFolder === folder.id
                                ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-400'
                                : 'text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800/50'}`, children: [_jsxs("div", { className: "flex items-center gap-2.5", children: [_jsx("div", { className: `w-4 h-4 flex items-center justify-center ${activeFolder === folder.id ? 'text-blue-600 dark:text-blue-400' : 'text-gray-500 dark:text-gray-400'}`, children: folder.icon }), _jsx("span", { className: "font-medium text-sm", children: folder.name })] }), folder.count > 0 && (_jsx("span", { className: `text-xs font-medium px-2 py-0.5 rounded ${activeFolder === folder.id
                                        ? 'bg-blue-100 dark:bg-blue-800/30 text-blue-700 dark:text-blue-300'
                                        : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400'}`, children: folder.count }))] }, folder.id))) })] }), _jsxs("div", { className: "mt-auto w-full", children: [_jsxs("div", { className: "px-2 py-3 border-t border-gray-100 dark:border-gray-800", children: [_jsx("h3", { className: "text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide px-3 mb-2", children: "Management" }), _jsx("nav", { children: _jsxs("button", { onClick: () => onNavigateToView && onNavigateToView('quantum'), className: "group w-full flex items-center justify-between px-3 py-2 rounded-md text-left transition-colors duration-150 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800/50", children: [_jsxs("div", { className: "flex items-center gap-2.5", children: [_jsx("div", { className: "w-4 h-4 flex items-center justify-center text-purple-600 dark:text-purple-400", children: _jsx("svg", { className: "w-4 h-4", fill: "none", stroke: "currentColor", viewBox: "0 0 24 24", children: _jsx("path", { strokeLinecap: "round", strokeLinejoin: "round", strokeWidth: 2, d: "M13 10V3L4 14h7v7l9-11h-7z" }) }) }), _jsx("span", { className: "font-medium text-sm", children: "Quantum Dashboard" })] }), _jsx("svg", { className: "w-3.5 h-3.5 text-gray-400", fill: "none", stroke: "currentColor", viewBox: "0 0 24 24", children: _jsx("path", { strokeLinecap: "round", strokeLinejoin: "round", strokeWidth: 2, d: "M9 5l7 7-7 7" }) })] }) })] }), _jsx("div", { className: "p-3 pt-0", children: _jsx("div", { className: "bg-blue-50 dark:bg-blue-900/10 rounded-md p-2 text-center border border-blue-200 dark:border-blue-800/30", children: _jsxs("div", { className: "flex items-center justify-center gap-2", children: [_jsx("div", { className: "w-5 h-5 bg-blue-600 rounded flex items-center justify-center flex-shrink-0", children: _jsx("svg", { className: "w-3 h-3 text-white", fill: "none", stroke: "currentColor", viewBox: "0 0 24 24", children: _jsx("path", { strokeLinecap: "round", strokeLinejoin: "round", strokeWidth: 2, d: "M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" }) }) }), _jsxs("div", { className: "text-left min-w-0", children: [_jsx("div", { className: "text-xs font-semibold text-blue-700 dark:text-blue-300 truncate", children: "ETSI Compliant" }), _jsx("div", { className: "text-xs text-gray-600 dark:text-gray-400", children: "GS QKD-014" })] })] }) }) })] })] }));
};
