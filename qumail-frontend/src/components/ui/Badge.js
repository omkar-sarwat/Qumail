import { jsx as _jsx } from "react/jsx-runtime";
import { cn } from '../../utils/cn';
const Badge = ({ className, variant = 'default', size = 'default', ...props }) => {
    const baseClasses = 'inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2';
    const variantClasses = {
        default: 'border-transparent bg-primary text-primary-foreground hover:bg-primary/80',
        secondary: 'border-transparent bg-secondary text-secondary-foreground hover:bg-secondary/80',
        destructive: 'border-transparent bg-destructive text-destructive-foreground hover:bg-destructive/80',
        outline: 'text-foreground'
    };
    const sizeClasses = {
        default: 'px-2.5 py-0.5 text-xs',
        sm: 'px-2 py-0.5 text-xs',
        lg: 'px-3 py-1 text-sm'
    };
    return (_jsx("div", { className: cn(baseClasses, variantClasses[variant], sizeClasses[size], className), ...props }));
};
export { Badge };
export default Badge;
