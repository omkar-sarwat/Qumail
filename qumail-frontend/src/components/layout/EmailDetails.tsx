import React from 'react'
import { Card, Button, Badge } from '../ui'
import { Star, Reply, ReplyAll, Forward, Archive, Trash2, Shield } from 'lucide-react'

interface Email {
  id: string
  sender: string
  subject: string
  snippet: string
  timestamp: string
  isRead: boolean
  isStarred: boolean
  securityLevel: string
  content?: string
  attachments?: Array<{
    name: string
    size: string
    type: string
  }>
}

interface EmailDetailsProps {
  email: Email | null
  onReply?: () => void
  onReplyAll?: () => void
  onForward?: () => void
  onArchive?: () => void
  onDelete?: () => void
  onStar?: () => void
}

const getSecurityLevelConfig = (level: string) => {
  switch (level) {
    case 'Level 1':
      return { color: 'bg-green-500', text: 'Standard Security', icon: '🟢' }
    case 'Level 2':
      return { color: 'bg-yellow-500', text: 'Enhanced Security', icon: '🟡' }
    case 'Level 3':
      return { color: 'bg-orange-500', text: 'Classified', icon: '🟠' }
    case 'Level 4':
      return { color: 'bg-red-500', text: 'Top Secret', icon: '🔴' }
    default:
      return { color: 'bg-gray-500', text: 'Unknown', icon: '⚪' }
  }
}

export const EmailDetails: React.FC<EmailDetailsProps> = ({
  email,
  onReply,
  onReplyAll,
  onForward,
  onArchive,
  onDelete,
  onStar
}) => {
  if (!email) {
    return (
      <div className="flex-1 flex items-center justify-center bg-gray-50 dark:bg-gray-900">
        <div className="text-center">
          <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-gray-200 dark:bg-gray-700 flex items-center justify-center">
            <Shield className="w-8 h-8 text-gray-400" />
          </div>
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
            No email selected
          </h3>
          <p className="text-gray-500 dark:text-gray-400">
            Select an email from the list to view its contents
          </p>
        </div>
      </div>
    )
  }

  const securityConfig = getSecurityLevelConfig(email.securityLevel)

  return (
    <div className="flex-1 flex flex-col bg-white dark:bg-gray-900">
      {/* Email Header */}
      <div className="border-b border-gray-200 dark:border-gray-700 p-6">
        <div className="flex items-start justify-between mb-4">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <h1 className="text-xl font-semibold text-gray-900 dark:text-white">
                {email.subject}
              </h1>
              <Badge className={`${securityConfig.color} text-white text-xs`}>
                {securityConfig.icon} {securityConfig.text}
              </Badge>
            </div>
            <div className="flex items-center gap-4 text-sm text-gray-600 dark:text-gray-400">
              <span>From: <strong>{email.sender}</strong></span>
              <span>{new Date(email.timestamp).toLocaleString()}</span>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={onStar}
              className={email.isStarred ? 'text-yellow-500' : 'text-gray-400'}
            >
              <Star className="w-4 h-4" fill={email.isStarred ? 'currentColor' : 'none'} />
            </Button>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={onReply}>
            <Reply className="w-4 h-4 mr-2" />
            Reply
          </Button>
          <Button variant="outline" size="sm" onClick={onReplyAll}>
            <ReplyAll className="w-4 h-4 mr-2" />
            Reply All
          </Button>
          <Button variant="outline" size="sm" onClick={onForward}>
            <Forward className="w-4 h-4 mr-2" />
            Forward
          </Button>
          <div className="ml-auto flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={onArchive}>
              <Archive className="w-4 h-4 mr-2" />
              Archive
            </Button>
            <Button variant="outline" size="sm" onClick={onDelete}>
              <Trash2 className="w-4 h-4 mr-2" />
              Delete
            </Button>
          </div>
        </div>
      </div>

      {/* Email Content */}
      <div className="flex-1 overflow-auto p-6">
        <div className="prose max-w-none dark:prose-invert">
          <div className="whitespace-pre-wrap text-gray-900 dark:text-white">
            {email.content || email.snippet}
          </div>
        </div>

        {/* Attachments */}
        {email.attachments && email.attachments.length > 0 && (
          <div className="mt-6">
            <h3 className="text-sm font-medium text-gray-900 dark:text-white mb-3">
              Attachments ({email.attachments.length})
            </h3>
            <div className="space-y-2">
              {email.attachments.map((attachment, index) => (
                <Card key={index} className="p-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded bg-blue-100 dark:bg-blue-900 flex items-center justify-center">
                        <span className="text-xs font-medium text-blue-600 dark:text-blue-400">
                          {attachment.type.toUpperCase()}
                        </span>
                      </div>
                      <div>
                        <p className="text-sm font-medium text-gray-900 dark:text-white">
                          {attachment.name}
                        </p>
                        <p className="text-xs text-gray-500 dark:text-gray-400">
                          {attachment.size}
                        </p>
                      </div>
                    </div>
                    <Button variant="outline" size="sm">
                      Download
                    </Button>
                  </div>
                </Card>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default EmailDetails