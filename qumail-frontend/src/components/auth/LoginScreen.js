import { jsx as _jsx, jsxs as _jsxs, Fragment as _Fragment } from "react/jsx-runtime";
import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Button } from '../ui/Button';
import { Card, CardContent } from '../ui/Card';
import { authService } from '../../services/authService';
import { toast } from 'react-hot-toast';
export const LoginScreen = () => {
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState(null);
    const [message, setMessage] = useState(null);
    // Clear any existing auth data on login screen
    useEffect(() => {
        localStorage.removeItem('authToken');
        localStorage.removeItem('user');
        localStorage.removeItem('userEmail');
        console.log('LoginScreen: Cleared any existing auth data');
    }, []);
    const handleGoogleLogin = async () => {
        setIsLoading(true);
        try {
            console.log('Initiating Google OAuth login...');
            // Check if running in Electron
            const isElectron = !!window.electronAPI;
            // Start Google OAuth flow using authService
            // Backend will automatically use port 5174 for Electron based on is_electron flag
            const authResponse = await authService.startGoogleAuth();
            console.log('Got OAuth URL');
            // Store state in localStorage to prevent CSRF
            localStorage.setItem('oauth_state', authResponse.state);
            if (isElectron) {
                // Electron: Open in system browser and wait for callback
                console.log('Running in Electron - opening system browser...');
                setMessage('Opening your browser for secure authentication...');
                try {
                    const electronAPI = window.electronAPI;
                    // Start OAuth flow - this will open browser and wait
                    const result = await electronAPI.startOAuthFlow({
                        authUrl: authResponse.authorization_url,
                        state: authResponse.state
                    });
                    console.log('OAuth callback received in Electron');
                    setMessage('Authentication successful! Setting up your quantum mailbox...');
                    // Now handle the callback with the code
                    const authResult = await authService.handleCallback(result.code, result.state);
                    console.log('User authenticated:', authResult.user_email);
                    // Initialize quantum pool
                    try {
                        const token = localStorage.getItem('authToken');
                        const response = await fetch('http://localhost:8000/api/v1/emails/quantum/pool/initialize', {
                            method: 'POST',
                            headers: {
                                'Authorization': `Bearer ${token}`,
                                'Content-Type': 'application/json'
                            }
                        });
                        if (response.ok) {
                            console.log('Quantum pool initialized');
                            setMessage('Quantum encryption keys synchronized!');
                        }
                    }
                    catch (e) {
                        console.warn('Quantum pool initialization skipped:', e);
                    }
                    // Success! Show success message briefly then reload
                    toast.success(`Welcome ${authResult.user_email}!`);
                    setTimeout(() => {
                        window.location.reload();
                    }, 500);
                }
                catch (error) {
                    console.error('Electron OAuth error:', error);
                    setIsLoading(false);
                    throw error;
                }
            }
            else {
                // Web: Redirect in same window
                console.log('Running in browser - redirecting...');
                window.location.href = authResponse.authorization_url;
            }
        }
        catch (error) {
            console.error('Login failed:', error);
            setError(error instanceof Error ? error.message : 'Failed to start authentication');
            setIsLoading(false);
            toast.error('Failed to start authentication. Please try again.');
        }
    };
    const features = [
        {
            icon: (_jsx("svg", { className: "w-8 h-8", fill: "none", stroke: "currentColor", viewBox: "0 0 24 24", children: _jsx("path", { strokeLinecap: "round", strokeLinejoin: "round", strokeWidth: 2, d: "M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" }) })),
            title: "Quantum Security",
            description: "Military-grade encryption using real quantum key distribution for perfect secrecy",
            color: "from-purple-500 to-purple-600"
        },
        {
            icon: (_jsx("svg", { className: "w-8 h-8", fill: "none", stroke: "currentColor", viewBox: "0 0 24 24", children: _jsx("path", { strokeLinecap: "round", strokeLinejoin: "round", strokeWidth: 2, d: "M13 10V3L4 14h7v7l9-11h-7z" }) })),
            title: "Lightning Fast",
            description: "Instant email encryption and decryption with optimized quantum algorithms",
            color: "from-blue-500 to-blue-600"
        },
        {
            icon: (_jsx("svg", { className: "w-8 h-8", fill: "none", stroke: "currentColor", viewBox: "0 0 24 24", children: _jsx("path", { strokeLinecap: "round", strokeLinejoin: "round", strokeWidth: 2, d: "M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" }) })),
            title: "ETSI Compliant",
            description: "Fully compliant with ETSI GS QKD-014 quantum key management standards",
            color: "from-green-500 to-green-600"
        }
    ];
    const containerVariants = {
        hidden: { opacity: 0 },
        visible: {
            opacity: 1,
            transition: {
                duration: 0.8,
                staggerChildren: 0.2
            }
        }
    };
    const itemVariants = {
        hidden: { opacity: 0, y: 30 },
        visible: {
            opacity: 1,
            y: 0,
            transition: { duration: 0.6, ease: [0.6, -0.05, 0.01, 0.99] }
        }
    };
    const floatingVariants = {
        animate: {
            y: [0, -10, 0],
            transition: {
                duration: 3,
                repeat: Infinity,
                ease: "easeInOut"
            }
        }
    };
    return (_jsxs("div", { className: "min-h-screen relative overflow-hidden", children: [_jsxs("div", { className: "absolute inset-0 bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900", children: [_jsx("div", { className: "absolute top-1/4 left-1/4 w-96 h-96 bg-purple-500/20 rounded-full blur-3xl animate-pulse" }), _jsx("div", { className: "absolute bottom-1/4 right-1/4 w-96 h-96 bg-blue-500/20 rounded-full blur-3xl animate-pulse delay-1000" }), _jsx("div", { className: "absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-green-500/10 rounded-full blur-3xl animate-pulse delay-2000" }), _jsx("div", { className: "absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.02)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.02)_1px,transparent_1px)] bg-[size:50px_50px]" })] }), _jsx(motion.div, { variants: containerVariants, initial: "hidden", animate: "visible", className: "relative z-10 min-h-screen flex items-center justify-center px-4 py-12", children: _jsxs("div", { className: "max-w-6xl mx-auto", children: [_jsxs("div", { className: "text-center mb-12", children: [_jsxs(motion.div, { variants: itemVariants, className: "mb-8", children: [_jsx(motion.div, { variants: floatingVariants, animate: "animate", className: "inline-flex items-center justify-center w-20 h-20 bg-gradient-to-br from-blue-600 to-purple-600 rounded-2xl shadow-2xl mb-6 mx-auto", children: _jsx("svg", { className: "w-10 h-10 text-white", fill: "none", stroke: "currentColor", viewBox: "0 0 24 24", children: _jsx("path", { strokeLinecap: "round", strokeLinejoin: "round", strokeWidth: 2, d: "M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" }) }) }), _jsx("h1", { className: "text-5xl md:text-6xl font-bold text-white mb-4", children: _jsx("span", { className: "bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent", children: "QuMail" }) }), _jsx("p", { className: "text-xl text-gray-300 max-w-2xl mx-auto leading-relaxed", children: "The world's first quantum-secured email platform with military-grade encryption and unbreakable quantum key distribution technology." })] }), _jsx(motion.div, { variants: itemVariants, children: _jsx(Card, { className: "bg-white/10 backdrop-blur-xl border border-white/20 shadow-2xl max-w-md mx-auto", children: _jsxs(CardContent, { className: "p-8", children: [_jsxs("div", { className: "mb-6", children: [_jsx("h2", { className: "text-2xl font-semibold text-white mb-2", children: "Secure Access" }), _jsx("p", { className: "text-gray-300 text-sm", children: "Connect with your Gmail account to start sending quantum-encrypted emails" })] }), _jsx(Button, { onClick: handleGoogleLogin, disabled: isLoading, className: "w-full bg-white hover:bg-gray-100 text-gray-900 font-semibold py-4 px-6 rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 flex items-center justify-center space-x-3", children: isLoading ? (_jsxs("svg", { className: "animate-spin h-5 w-5", viewBox: "0 0 24 24", children: [_jsx("circle", { cx: "12", cy: "12", r: "10", stroke: "currentColor", strokeWidth: "4", className: "opacity-25", fill: "none" }), _jsx("path", { fill: "currentColor", className: "opacity-75", d: "M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" })] })) : (_jsxs(_Fragment, { children: [_jsxs("svg", { className: "w-5 h-5", viewBox: "0 0 24 24", children: [_jsx("path", { fill: "#4285F4", d: "M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" }), _jsx("path", { fill: "#34A853", d: "M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" }), _jsx("path", { fill: "#FBBC05", d: "M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" }), _jsx("path", { fill: "#EA4335", d: "M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" })] }), _jsx("span", { children: "Continue with Gmail" })] })) }), error && (_jsx("div", { className: "mt-4 p-3 bg-red-500/20 border border-red-500/30 rounded-lg", children: _jsx("p", { className: "text-red-300 text-sm", children: error }) })), message && !error && (_jsx("div", { className: "mt-4 p-3 bg-blue-500/20 border border-blue-500/30 rounded-lg", children: _jsxs("p", { className: "text-blue-300 text-sm flex items-center justify-center gap-2", children: [_jsxs("svg", { className: "animate-spin h-4 w-4", viewBox: "0 0 24 24", children: [_jsx("circle", { cx: "12", cy: "12", r: "10", stroke: "currentColor", strokeWidth: "4", className: "opacity-25", fill: "none" }), _jsx("path", { fill: "currentColor", className: "opacity-75", d: "M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" })] }), message] }) })), _jsx("div", { className: "mt-4 text-xs text-gray-400 text-center", children: "Secured by quantum encryption \u2022 ETSI GS QKD-014 compliant" })] }) }) })] }), _jsx(motion.div, { variants: itemVariants, children: _jsx("div", { className: "grid md:grid-cols-3 gap-8 mt-16", children: features.map((feature) => (_jsx(motion.div, { variants: itemVariants, whileHover: {
                                        scale: 1.05,
                                        transition: { duration: 0.2 }
                                    }, className: "group", children: _jsx(Card, { className: "bg-white/5 backdrop-blur-xl border border-white/10 hover:border-white/20 transition-all duration-300 h-full", children: _jsxs(CardContent, { className: "p-6 text-center", children: [_jsx("div", { className: `inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br ${feature.color} mb-4 group-hover:scale-110 transition-transform duration-300`, children: _jsx("div", { className: "text-white", children: feature.icon }) }), _jsx("h3", { className: "text-xl font-semibold text-white mb-3", children: feature.title }), _jsx("p", { className: "text-gray-300 text-sm leading-relaxed", children: feature.description })] }) }) }, feature.title))) }) }), _jsx(motion.div, { variants: itemVariants, className: "text-center mt-16", children: _jsxs("div", { className: "flex flex-wrap justify-center items-center gap-8 text-sm text-gray-400", children: [_jsxs("div", { className: "flex items-center space-x-2", children: [_jsx("div", { className: "w-2 h-2 bg-green-400 rounded-full animate-pulse" }), _jsx("span", { children: "Quantum Keys Available" })] }), _jsxs("div", { className: "flex items-center space-x-2", children: [_jsx("svg", { className: "w-4 h-4", fill: "none", stroke: "currentColor", viewBox: "0 0 24 24", children: _jsx("path", { strokeLinecap: "round", strokeLinejoin: "round", strokeWidth: 2, d: "M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" }) }), _jsx("span", { children: "Bank-Grade Security" })] }), _jsxs("div", { className: "flex items-center space-x-2", children: [_jsx("svg", { className: "w-4 h-4", fill: "none", stroke: "currentColor", viewBox: "0 0 24 24", children: _jsx("path", { strokeLinecap: "round", strokeLinejoin: "round", strokeWidth: 2, d: "M13 10V3L4 14h7v7l9-11h-7z" }) }), _jsx("span", { children: "Real-time Encryption" })] })] }) })] }) })] }));
};
