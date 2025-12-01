// Professional avatar color palette - vibrant brand colors, easy on the eyes
export const AVATAR_COLORS = [
  'bg-blue-400',      // Vibrant sky blue
  'bg-indigo-400',    // Vibrant indigo
  'bg-purple-400',    // Vibrant purple
  'bg-pink-400',      // Vibrant pink
  'bg-rose-400',      // Vibrant rose
  'bg-teal-400',      // Vibrant teal
  'bg-cyan-400',      // Vibrant cyan
  'bg-emerald-400',   // Vibrant emerald
];

// Known brand colors for specific senders
export const BRAND_COLORS: Record<string, string> = {
  'google': 'bg-blue-600',
  'google security': 'bg-blue-600',
  'linkedin': 'bg-[#0A66C2]',
  'linkedin job alerts': 'bg-[#0A66C2]',
  'github': 'bg-gray-900',
  'microsoft': 'bg-[#00A4EF]',
  'apple': 'bg-gray-800',
  'amazon': 'bg-[#FF9900]',
  'netflix': 'bg-[#E50914]',
  'spotify': 'bg-[#1DB954]',
  'twitter': 'bg-black',
  'x': 'bg-black',
  'facebook': 'bg-[#1877F2]',
  'meta': 'bg-[#0081FB]',
  'instagram': 'bg-gradient-to-br from-purple-600 via-pink-500 to-orange-400',
  'youtube': 'bg-[#FF0000]',
  'slack': 'bg-[#4A154B]',
  'discord': 'bg-[#5865F2]',
  'zoom': 'bg-[#2D8CFF]',
  'dropbox': 'bg-[#0061FF]',
  'notion': 'bg-gray-900',
  'figma': 'bg-[#F24E1E]',
  'stripe': 'bg-[#635BFF]',
  'paypal': 'bg-[#003087]',
  'mongodb': 'bg-[#00ED64]',
  'mongodb atlas': 'bg-[#00ED64]',
  'render': 'bg-[#46E3B7]',
  'vercel': 'bg-black',
  'netlify': 'bg-[#00C7B7]',
  'heroku': 'bg-[#430098]',
  'aws': 'bg-[#FF9900]',
  'azure': 'bg-[#0078D4]',
  'qkd system': 'bg-purple-600',
  'quantum': 'bg-purple-600',
  'samsung': 'bg-[#1428A0]',
  'codepen': 'bg-gray-900',
  'codecademy': 'bg-[#1F4056]',
  'wellfound': 'bg-black',
  'angellist': 'bg-black',
  'indeed': 'bg-[#2164F3]',
  'glassdoor': 'bg-[#0CAA41]',
  'jobscan': 'bg-[#00B2A9]',
  'hackerearth': 'bg-[#2C3454]',
  'astromix': 'bg-gradient-to-br from-indigo-600 to-purple-600',
  'axis bank': 'bg-[#97144D]',
  'axis': 'bg-[#97144D]',
  'hdfc': 'bg-[#004C8F]',
  'icici': 'bg-[#F58220]',
  'sbi': 'bg-[#22409A]',
};

/**
 * Generate consistent avatar color from sender name
 * Uses brand colors for known companies, otherwise generates a consistent hash-based color
 */
export const getAvatarColor = (name: string): string => {
  if (!name) return 'bg-gray-500';
  
  const lowerName = name.toLowerCase().trim();
  
  // Check for brand colors first
  for (const [brand, color] of Object.entries(BRAND_COLORS)) {
    if (lowerName.includes(brand) || lowerName === brand) {
      return color;
    }
  }
  
  // Generate consistent hash-based color
  let hash = 0;
  for (let i = 0; i < name.length; i++) {
    hash = name.charCodeAt(i) + ((hash << 5) - hash);
  }
  
  const index = Math.abs(hash) % AVATAR_COLORS.length;
  return AVATAR_COLORS[index];
};

/**
 * Get the initial letter(s) for avatar display
 */
export const getAvatarInitial = (name: string): string => {
  if (!name) return '?';
  return name.charAt(0).toUpperCase();
};

export default getAvatarColor;
