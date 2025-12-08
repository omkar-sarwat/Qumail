import React from 'react'

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
    <div className="titlebar bg-slate-900 h-8 flex items-center justify-between select-none border-b border-slate-800" style={{ WebkitAppRegion: 'drag' } as any}>
      <div className="flex items-center gap-3 pl-3">
        <img src="./qumail-icon.svg" alt="QuMail" className="qumail-logo-mark" />
        <span className="text-xs font-semibold text-slate-200 tracking-wide">QuMail Secure</span>
      </div>
      
      <div className="flex items-center h-full" style={{ WebkitAppRegion: 'no-drag' } as any}>
        {/* Minimize Button */}
        <button
          onClick={handleMinimize}
          className="h-8 w-12 flex items-center justify-center hover:bg-slate-700 active:bg-slate-600 transition-colors duration-100"
          title="Minimize"
        >
          <svg className="w-3.5 h-3.5 text-slate-300" viewBox="0 0 12 12" fill="currentColor">
            <rect x="2" y="5.5" width="8" height="1" />
          </svg>
        </button>
        
        {/* Maximize/Restore Button */}
        <button
          onClick={handleMaximize}
          className="h-8 w-12 flex items-center justify-center hover:bg-slate-700 active:bg-slate-600 transition-colors duration-100"
          title={isMaximized ? "Restore Down" : "Maximize"}
        >
          {isMaximized ? (
            <svg className="w-3.5 h-3.5 text-slate-300" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="1">
              <rect x="3" y="1" width="7" height="7" />
              <path d="M1 4v7h7" />
            </svg>
          ) : (
            <svg className="w-3.5 h-3.5 text-slate-300" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="1">
              <rect x="1.5" y="1.5" width="9" height="9" />
            </svg>
          )}
        </button>
        
        {/* Close Button */}
        <button
          onClick={handleClose}
          className="h-8 w-12 flex items-center justify-center hover:bg-[#e81123] active:bg-[#bf0f1d] transition-colors duration-100 group"
          title="Close"
        >
          <svg className="w-3.5 h-3.5 text-slate-300 group-hover:text-white" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="1.5">
            <path d="M2 2l8 8M10 2l-8 8" />
          </svg>
        </button>
      </div>
    </div>
  )
}
