import React, { useEffect, useState } from 'react';
import { Activity, Key, PieChart, ShieldCheck, Server, Globe, Lock, RefreshCw, AlertCircle } from 'lucide-react';

const Dashboard: React.FC = () => {
  // --- State for Network Status ---
  const [nodes, setNodes] = useState([
    { id: 1, status: 'active', load: 45 },
    { id: 2, status: 'active', load: 32 },
    { id: 3, status: 'active', load: 78 },
    { id: 4, status: 'encrypting', load: 92 },
  ]);

  // --- State for Key Management ---
  const [keys, setKeys] = useState([
    { id: 'K-9921', time: 'Just now', status: 'Rotated', type: 'QKD-2048' },
    { id: 'K-9920', time: '2s ago', status: 'Expired', type: 'QKD-2048' },
    { id: 'K-9919', time: '5s ago', status: 'Expired', type: 'QKD-2048' },
    { id: 'K-9918', time: '8s ago', status: 'Expired', type: 'QKD-2048' },
  ]);

  // --- State for Analytics ---
  const [threats, setThreats] = useState(0);
  const [uptime, setUptime] = useState(99.999);

  // Simulation Effects
  useEffect(() => {
    const interval = setInterval(() => {
      // Rotate Keys
      const newKeyId = `K-${Math.floor(Math.random() * 10000)}`;
      setKeys(prev => [
        { id: newKeyId, time: 'Just now', status: 'Rotated', type: 'QKD-2048' },
        ...prev.slice(0, 4)
      ]);

      // Fluctuage Node Load
      setNodes(prev => prev.map(n => ({
        ...n,
        load: Math.max(10, Math.min(100, n.load + (Math.random() * 20 - 10)))
      })));

      // Random Threat Blocked
      if (Math.random() > 0.8) {
        setThreats(t => t + 1);
      }
    }, 2000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="flex-1 bg-gray-50 h-full overflow-y-auto p-6 animate-in fade-in duration-500">
      
      {/* Header */}
      <div className="mb-8 flex items-center justify-between">
        <div>
            <h1 className="text-2xl font-bold text-gray-900">Quantum Dashboard</h1>
            <p className="text-sm text-gray-500">Real-time monitoring of QKD grid and workspace security.</p>
        </div>
        <div className="flex items-center gap-2 bg-white px-3 py-1.5 rounded-lg border border-gray-200 shadow-sm">
            <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse"></div>
            <span className="text-xs font-bold text-gray-700">SYSTEM OPTIMAL</span>
        </div>
      </div>

      {/* Grid Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        
        {/* 1. Network Status */}
        <div className="bg-white p-6 rounded-2xl border border-gray-200 shadow-sm relative overflow-hidden">
            <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-2">
                    <div className="p-2 bg-emerald-100 text-emerald-600 rounded-lg">
                        <Activity size={20} />
                    </div>
                    <h2 className="font-bold text-gray-800">Network Status</h2>
                </div>
                <span className="text-xs bg-emerald-50 text-emerald-700 px-2 py-1 rounded font-medium border border-emerald-100">
                    Mesh Active
                </span>
            </div>

            {/* Visual Node Graph */}
            <div className="h-48 bg-slate-900 rounded-xl mb-4 relative flex items-center justify-center overflow-hidden">
                <div className="absolute inset-0 opacity-20" style={{ backgroundImage: 'radial-gradient(#4f46e5 1px, transparent 1px)', backgroundSize: '20px 20px' }}></div>
                
                {/* Center Hub */}
                <div className="relative z-10">
                    <div className="w-12 h-12 bg-indigo-500 rounded-full flex items-center justify-center shadow-[0_0_20px_rgba(99,102,241,0.6)] animate-pulse">
                        <Globe className="text-white" size={24} />
                    </div>
                </div>

                {/* Nodes */}
                <div className="absolute top-10 left-10 animate-bounce duration-[2000ms]">
                    <Server size={20} className="text-emerald-400" />
                </div>
                <div className="absolute bottom-10 right-10 animate-bounce duration-[3000ms]">
                     <Server size={20} className="text-emerald-400" />
                </div>
                <div className="absolute top-10 right-20 animate-bounce duration-[2500ms]">
                     <Server size={20} className="text-blue-400" />
                </div>
                
                {/* Connecting Lines (SVG Overlay) */}
                <svg className="absolute inset-0 w-full h-full pointer-events-none opacity-40">
                    <line x1="50%" y1="50%" x2="20%" y2="25%" stroke="#6366f1" strokeWidth="2" />
                    <line x1="50%" y1="50%" x2="80%" y2="80%" stroke="#6366f1" strokeWidth="2" />
                    <line x1="50%" y1="50%" x2="75%" y2="20%" stroke="#6366f1" strokeWidth="2" />
                </svg>
            </div>

            <div className="grid grid-cols-2 gap-4">
                {nodes.slice(0,2).map(node => (
                    <div key={node.id} className="bg-gray-50 rounded-lg p-3 border border-gray-100">
                        <div className="flex justify-between text-xs mb-1">
                            <span className="font-medium text-gray-600">Node {node.id}</span>
                            <span className="text-emerald-600">{node.load}% Load</span>
                        </div>
                        <div className="h-1.5 bg-gray-200 rounded-full overflow-hidden">
                            <div className="h-full bg-emerald-500 transition-all duration-500" style={{ width: `${node.load}%` }}></div>
                        </div>
                    </div>
                ))}
            </div>
        </div>

        {/* 2. Key Management */}
        <div className="bg-white p-6 rounded-2xl border border-gray-200 shadow-sm">
            <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-2">
                    <div className="p-2 bg-purple-100 text-purple-600 rounded-lg">
                        <Key size={20} />
                    </div>
                    <h2 className="font-bold text-gray-800">Key Management</h2>
                </div>
                <div className="flex items-center gap-1 text-xs text-gray-500">
                    <RefreshCw size={12} className="animate-spin" />
                    Auto-Rotating
                </div>
            </div>

            <div className="space-y-3">
                {keys.map((key, index) => (
                    <div key={key.id} className={`flex items-center justify-between p-3 rounded-lg border transition-all duration-500 ${index === 0 ? 'bg-purple-50 border-purple-100 transform scale-105' : 'bg-white border-gray-100 opacity-70'}`}>
                        <div className="flex items-center gap-3">
                            <div className={`w-8 h-8 rounded-full flex items-center justify-center ${index === 0 ? 'bg-purple-200 text-purple-700' : 'bg-gray-100 text-gray-400'}`}>
                                <Lock size={14} />
                            </div>
                            <div>
                                <p className={`text-xs font-mono font-bold ${index === 0 ? 'text-purple-900' : 'text-gray-600'}`}>{key.id}</p>
                                <p className="text-[10px] text-gray-500">{key.type}</p>
                            </div>
                        </div>
                        <div className="text-right">
                            <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${index === 0 ? 'bg-emerald-100 text-emerald-700' : 'bg-gray-100 text-gray-500'}`}>
                                {key.status}
                            </span>
                            <p className="text-[10px] text-gray-400 mt-0.5">{key.time}</p>
                        </div>
                    </div>
                ))}
            </div>
        </div>

        {/* 3. Analytics */}
        <div className="col-span-1 lg:col-span-2 bg-white p-6 rounded-2xl border border-gray-200 shadow-sm">
             <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-2">
                    <div className="p-2 bg-blue-100 text-blue-600 rounded-lg">
                        <PieChart size={20} />
                    </div>
                    <h2 className="font-bold text-gray-800">Security Analytics</h2>
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {/* Stat 1 */}
                <div className="p-4 bg-gray-50 rounded-xl border border-gray-100">
                    <div className="flex items-center gap-2 mb-2">
                        <ShieldCheck size={16} className="text-indigo-600" />
                        <span className="text-xs font-bold text-gray-500 uppercase">Threats Blocked</span>
                    </div>
                    <p className="text-2xl font-bold text-gray-900">{342 + threats}</p>
                    <p className="text-xs text-green-600 mt-1">+12% from yesterday</p>
                </div>

                {/* Stat 2 */}
                <div className="p-4 bg-gray-50 rounded-xl border border-gray-100">
                    <div className="flex items-center gap-2 mb-2">
                        <Activity size={16} className="text-emerald-600" />
                        <span className="text-xs font-bold text-gray-500 uppercase">System Uptime</span>
                    </div>
                    <p className="text-2xl font-bold text-gray-900">{uptime}%</p>
                    <p className="text-xs text-gray-400 mt-1">Continuous QKD stream</p>
                </div>

                {/* Stat 3 */}
                <div className="p-4 bg-gray-50 rounded-xl border border-gray-100">
                    <div className="flex items-center gap-2 mb-2">
                        <AlertCircle size={16} className="text-orange-600" />
                        <span className="text-xs font-bold text-gray-500 uppercase">Encryption Rate</span>
                    </div>
                    <p className="text-2xl font-bold text-gray-900">2.4 Gbps</p>
                    <div className="w-full bg-gray-200 h-1.5 rounded-full mt-2 overflow-hidden">
                        <div className="bg-indigo-600 h-full w-[85%] animate-[pulse_2s_infinite]"></div>
                    </div>
                </div>
            </div>
        </div>

      </div>
    </div>
  );
};

export default Dashboard;
