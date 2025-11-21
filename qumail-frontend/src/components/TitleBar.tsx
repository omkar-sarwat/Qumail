import React from 'react'
import { X, Minimize, Maximize2, Square } from 'lucide-react'

export const TitleBar: React.FC = () => {
  const [isMaximized, setIsMaximized] = React.useState(false)

  const handleMinimize = async () => {
    if (window.electronAPI) {
      await window.electronAPI.minimizeWindow()
    }
  }

  const handleMaximize = async () => {
    if (window.electronAPI) {
      await window.electronAPI.maximizeWindow()
      const maximized = await window.electronAPI.isMaximized()
      setIsMaximized(maximized)
    }
  }

  const handleClose = async () => {
    if (window.electronAPI) {
      await window.electronAPI.closeWindow()
    }
  }

  React.useEffect(() => {
    if (window.electronAPI) {
      window.electronAPI.isMaximized().then(setIsMaximized)
    }
  }, [])

  return (
    <div className="titlebar bg-slate-900 h-8 flex items-center justify-between px-3 select-none border-b border-slate-800" style={{ WebkitAppRegion: 'drag' } as any}>
      <div className="flex items-center gap-2">
        <div className="w-4 h-4 bg-gradient-to-br from-blue-500 to-purple-600 rounded flex items-center justify-center">
          <svg className="w-2.5 h-2.5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
          </svg>
        </div>
        <span className="text-xs font-medium text-slate-200">QuMail Secure Email</span>
      </div>
      
      <div className="flex items-center gap-0" style={{ WebkitAppRegion: 'no-drag' } as any}>
        <button
          onClick={handleMinimize}
          className="group h-8 w-10 flex items-center justify-center hover:bg-slate-800 transition-colors"
          title="Minimize"
        >
          <Minimize className="w-3.5 h-3.5 text-slate-400 group-hover:text-white transition-colors" />
        </button>
        <button
          onClick={handleMaximize}
          className="group h-8 w-10 flex items-center justify-center hover:bg-slate-800 transition-colors"
          title={isMaximized ? "Restore Down" : "Maximize"}
        >
          {isMaximized ? (
            <Maximize2 className="w-3.5 h-3.5 text-slate-400 group-hover:text-white transition-colors" />
          ) : (
            <Square className="w-3.5 h-3.5 text-slate-400 group-hover:text-white transition-colors" />
          )}
        </button>
        <button
          onClick={handleClose}
          className="group h-8 w-10 flex items-center justify-center hover:bg-red-600 transition-colors"
          title="Close"
        >
          <X className="w-3.5 h-3.5 text-slate-400 group-hover:text-white transition-colors" />
        </button>
      </div>
    </div>
  )
}
