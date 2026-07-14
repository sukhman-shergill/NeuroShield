/**
 * Static data constants for the NeuroShield dashboard.
 *
 * NOTE: Most dashboard views fetch live data from the Flask API.
 * This file only contains type-safe empty defaults used as fallbacks
 * before backend data arrives.
 */

// Class color mapping used across multiple views
export const CLASS_COLORS: Record<string, string> = {
  Normal: '#10b981',
  DoS: '#f43f5e',
  Probe: '#f59e0b',
  R2L: '#3b82f6',
  U2R: '#a855f7',
};

export const CLASS_NAMES = ['Normal', 'DoS', 'Probe', 'R2L', 'U2R'];
