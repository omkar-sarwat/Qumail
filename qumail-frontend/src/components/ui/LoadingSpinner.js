import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { motion } from 'framer-motion';
export const LoadingSpinner = ({ size = 'md', className = '', text }) => {
    const sizeClasses = {
        sm: 'w-4 h-4',
        md: 'w-8 h-8',
        lg: 'w-12 h-12'
    };
    return (_jsxs("div", { className: `flex flex-col items-center justify-center ${className}`, children: [_jsx(motion.div, { animate: { rotate: 360 }, transition: { duration: 1, repeat: Infinity, ease: "linear" }, className: `${sizeClasses[size]} border-2 border-gray-200 dark:border-gray-700 border-t-blue-600 dark:border-t-blue-400 rounded-full` }), text && (_jsx("p", { className: "mt-2 text-sm text-gray-600 dark:text-gray-400 font-medium", children: text }))] }));
};
export const EmailListSkeleton = () => {
    return (_jsx("div", { className: "p-4 space-y-4", children: [...Array(8)].map((_, i) => (_jsx("div", { className: "animate-pulse", children: _jsxs("div", { className: "flex items-start space-x-3 p-3", children: [_jsx("div", { className: "w-10 h-10 bg-gray-200 dark:bg-gray-700 rounded-full loading-shimmer" }), _jsxs("div", { className: "flex-1 space-y-2", children: [_jsx("div", { className: "h-4 bg-gray-200 dark:bg-gray-700 rounded loading-shimmer", style: { width: `${Math.random() * 40 + 60}%` } }), _jsx("div", { className: "h-3 bg-gray-200 dark:bg-gray-700 rounded loading-shimmer", style: { width: `${Math.random() * 30 + 50}%` } }), _jsx("div", { className: "h-3 bg-gray-200 dark:bg-gray-700 rounded loading-shimmer", style: { width: `${Math.random() * 50 + 40}%` } })] }), _jsx("div", { className: "h-3 bg-gray-200 dark:bg-gray-700 rounded loading-shimmer w-16" })] }) }, i))) }));
};
export const EmailViewerSkeleton = () => {
    return (_jsxs("div", { className: "h-full flex flex-col bg-white dark:bg-gray-800", children: [_jsx("div", { className: "flex-shrink-0 p-6 border-b border-gray-200 dark:border-gray-700", children: _jsxs("div", { className: "animate-pulse space-y-4", children: [_jsx("div", { className: "flex items-center space-x-2 mb-4", children: [...Array(4)].map((_, i) => (_jsx("div", { className: "h-8 w-16 bg-gray-200 dark:bg-gray-700 rounded loading-shimmer" }, i))) }), _jsx("div", { className: "h-8 bg-gray-200 dark:bg-gray-700 rounded loading-shimmer w-3/4" }), _jsxs("div", { className: "flex items-center space-x-4", children: [_jsx("div", { className: "w-10 h-10 bg-gray-200 dark:bg-gray-700 rounded-full loading-shimmer" }), _jsxs("div", { className: "flex-1 space-y-2", children: [_jsx("div", { className: "h-4 bg-gray-200 dark:bg-gray-700 rounded loading-shimmer w-1/3" }), _jsx("div", { className: "h-3 bg-gray-200 dark:bg-gray-700 rounded loading-shimmer w-1/2" })] }), _jsx("div", { className: "h-3 bg-gray-200 dark:bg-gray-700 rounded loading-shimmer w-20" })] })] }) }), _jsx("div", { className: "flex-1 p-6", children: _jsx("div", { className: "animate-pulse space-y-4", children: [...Array(6)].map((_, i) => (_jsx("div", { className: "h-4 bg-gray-200 dark:bg-gray-700 rounded loading-shimmer", style: { width: `${Math.random() * 30 + 70}%` } }, i))) }) })] }));
};
