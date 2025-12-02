import React from 'react';
import { Zap, Cpu, Shield, Lock, Check } from 'lucide-react';
import { SecurityLevel } from '../types';

interface EncryptionSelectorProps {
    selected: SecurityLevel;
    onSelect: (level: SecurityLevel) => void;
}

const EncryptionSelector: React.FC<EncryptionSelectorProps> = ({ selected, onSelect }) => {
    const options = [
        {
            id: SecurityLevel.LEVEL_1,
            title: 'Quantum Secure (Level 1)',
            desc: 'One Time Pad with Quantum Keys - Maximum Security',
            icon: Zap,
            color: 'text-purple-600',
            bg: 'bg-purple-50'
        },
        {
            id: SecurityLevel.LEVEL_2,
            title: 'Quantum-Aided AES (Level 2)',
            desc: 'AES encryption with quantum key enhancement',
            icon: Cpu,
            color: 'text-indigo-600',
            bg: 'bg-indigo-50'
        },
        {
            id: SecurityLevel.LEVEL_3,
            title: 'Post-Quantum (Level 3)',
            desc: 'Future-proof encryption for post-quantum era',
            icon: Shield,
            color: 'text-teal-600',
            bg: 'bg-teal-50'
        },
        {
            id: SecurityLevel.LEVEL_4,
            title: 'Standard (Level 4)',
            desc: 'Regular encryption without quantum enhancement',
            icon: Lock,
            color: 'text-gray-600',
            bg: 'bg-gray-50'
        }
    ];

    return (
        <div className="absolute bottom-14 left-0 w-80 bg-white rounded-xl shadow-2xl border border-gray-200 z-50 overflow-hidden animate-in fade-in zoom-in-95 duration-200">
            <div className="px-4 py-3 border-b border-gray-100 bg-gray-50/50">
                <span className="text-xs font-bold text-gray-500 uppercase tracking-wider">Select Encryption Protocol</span>
            </div>
            <div className="p-1 max-h-80 overflow-y-auto">
                {options.map(opt => (
                    <button
                        key={opt.id}
                        onClick={() => onSelect(opt.id)}
                        className={`w-full text-left px-3 py-3 rounded-lg flex items-start gap-3 hover:bg-gray-50 transition-colors group ${selected === opt.id ? 'bg-gray-50' : ''}`}
                    >
                        <div className={`mt-0.5 w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${opt.bg}`}>
                            <opt.icon size={16} className={opt.color} />
                        </div>
                        <div className="flex-1">
                            <div className="flex items-center justify-between">
                                <span className={`text-sm font-medium ${selected === opt.id ? 'text-gray-900' : 'text-gray-700'}`}>{opt.title}</span>
                                {selected === opt.id && <div className="w-1.5 h-1.5 rounded-full bg-black"></div>}
                            </div>
                            <p className="text-xs text-gray-500 mt-0.5 leading-normal">{opt.desc}</p>
                        </div>
                    </button>
                ))}
            </div>
        </div>
    );
};

export default EncryptionSelector;