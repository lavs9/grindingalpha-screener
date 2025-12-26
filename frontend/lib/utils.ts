import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/**
 * Format market cap in Indian format (₹ X,XXX Cr)
 * Market cap from backend is in absolute ₹ value (not crores)
 * Convert to crores and format with Indian numbering system
 */
export function formatMarketCap(marketCap: number | null): string {
  if (marketCap === null || marketCap === undefined) {
    return "—";
  }

  // Convert to crores (1 crore = 10,000,000)
  const crores = marketCap / 10000000;

  // Format with Indian numbering system
  // For values >= 1000 Cr, show in thousands of crores (e.g., "1.2K Cr")
  if (crores >= 100000) {
    return `₹${(crores / 100000).toFixed(2)}L Cr`;
  } else if (crores >= 1000) {
    return `₹${(crores / 1000).toFixed(2)}K Cr`;
  } else if (crores >= 1) {
    return `₹${crores.toFixed(2)} Cr`;
  } else {
    // Less than 1 crore, show in lakhs
    const lakhs = marketCap / 100000;
    return `₹${lakhs.toFixed(2)} L`;
  }
}
