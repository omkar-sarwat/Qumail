import React, { useEffect, useState, useRef } from 'react'
import { Shield } from 'lucide-react'

interface SplashScreenProps {
  onFinish: () => void
}

const SplashScreen: React.FC<SplashScreenProps> = ({ onFinish }) => {
  const [isVisible, setIsVisible] = useState(true)
  const onFinishRef = useRef(onFinish)
  
  // Keep ref updated to avoid stale closure
  useEffect(() => {
    onFinishRef.current = onFinish
  }, [onFinish])

  useEffect(() => {
    // Shorter splash duration for better UX
    const fadeTimer = setTimeout(() => {
      setIsVisible(false)
    }, 1500)

    const finishTimer = setTimeout(() => {
      onFinishRef.current()
    }, 2000)

    return () => {
      clearTimeout(fadeTimer)
      clearTimeout(finishTimer)
    }
  }, []) // Empty deps - only run once

  return (
    <div
      className={`fixed inset-0 z-[100] bg-white flex items-center justify-center transition-opacity duration-700 ease-in-out ${
        isVisible ? 'opacity-100' : 'opacity-0 pointer-events-none'
      }`}
    >
      <div className="relative flex flex-col items-center">
        <div className="relative w-24 h-24 mb-8 flex items-center justify-center">
          <div
            className="absolute inset-0 border border-indigo-100 rounded-full animate-[spin_3s_linear_infinite]"
            style={{ borderRadius: '40% 60% 70% 30% / 40% 50% 60% 50%' }}
          ></div>

          <div
            className="absolute inset-0 border border-indigo-200 rounded-full animate-[spin_4s_linear_infinite_reverse]"
            style={{ borderRadius: '60% 40% 30% 70% / 60% 30% 70% 40%' }}
          ></div>

          <div className="absolute w-12 h-12 bg-indigo-50 rounded-full animate-ping opacity-20"></div>

          <div className="relative z-10 bg-white p-1 rounded-xl">
            <div className="w-12 h-12 bg-indigo-600 rounded-lg flex items-center justify-center shadow-lg shadow-indigo-200 animate-in zoom-in duration-700">
              <Shield className="text-white w-6 h-6 fill-white/20" />
            </div>
          </div>

          <div className="absolute w-full h-full animate-[spin_5s_linear_infinite]">
            <div className="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-1 w-2 h-2 bg-indigo-400 rounded-full shadow-[0_0_10px_rgba(99,102,241,0.5)]"></div>
          </div>
        </div>

        <div className="text-center overflow-hidden">
          <div className="flex items-center justify-center mb-2 animate-in slide-in-from-bottom-4 fade-in duration-700 delay-300 fill-mode-backwards">
            <img src="/qumail-logo.svg" alt="QuMail" className="h-12 w-auto" />
          </div>
          <div className="flex items-center gap-2 justify-center animate-in slide-in-from-bottom-2 fade-in duration-700 delay-500 fill-mode-backwards">
            <div className="h-px w-4 bg-indigo-200"></div>
            <p className="text-[10px] font-bold text-indigo-600 uppercase tracking-[0.2em]">
              Secure Workspace
            </p>
            <div className="h-px w-4 bg-indigo-200"></div>
          </div>
        </div>

        <div className="absolute -bottom-16 w-48 h-1 bg-gray-100 rounded-full overflow-hidden">
          <div
            className="h-full bg-indigo-600 w-1/2 rounded-full animate-[shimmer_1.5s_infinite] translate-x-[-100%]"
            style={{ animation: 'indeterminate 1.5s infinite ease-in-out' }}
          ></div>
        </div>

        <style>{`
          @keyframes indeterminate {
            0% { transform: translateX(-100%); width: 20%; }
            50% { transform: translateX(50%); width: 50%; }
            100% { transform: translateX(200%); width: 20%; }
          }
        `}</style>
      </div>
    </div>
  )
}

export default SplashScreen
