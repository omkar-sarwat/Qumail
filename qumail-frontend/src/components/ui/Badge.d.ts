import * as React from 'react'

export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'secondary' | 'destructive' | 'outline'
  size?: 'default' | 'sm' | 'lg'
}
export declare const Badge: React.FC<BadgeProps>
export default Badge