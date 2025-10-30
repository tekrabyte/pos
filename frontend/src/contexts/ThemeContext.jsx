import React, { createContext, useContext, useState, useEffect } from 'react';

const ThemeContext = createContext();

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within ThemeProvider');
  }
  return context;
};

export const ThemeProvider = ({ children }) => {
  const [themeSettings, setThemeSettings] = useState({
    mode: 'light', // light, dark, system
    colors: {
      primary: { h: 221, s: 83, l: 53 }, // Blue
      accent: { h: 142, s: 76, l: 36 }, // Green
      background: { h: 0, s: 0, l: 100 }, // White
      foreground: { h: 0, s: 0, l: 4 }, // Almost black
    },
  });

  // Load theme from localStorage on mount
  useEffect(() => {
    const savedTheme = localStorage.getItem('themeSettings');
    if (savedTheme) {
      try {
        setThemeSettings(JSON.parse(savedTheme));
      } catch (error) {
        console.error('Error parsing theme settings:', error);
      }
    }
  }, []);

  // Apply theme to document
  useEffect(() => {
    const root = document.documentElement;
    const { mode, colors } = themeSettings;

    // Set theme mode class
    if (mode === 'system') {
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      root.classList.toggle('dark', prefersDark);
    } else {
      root.classList.toggle('dark', mode === 'dark');
    }

    // Apply custom colors as CSS variables
    root.style.setProperty('--primary', `${colors.primary.h} ${colors.primary.s}% ${colors.primary.l}%`);
    root.style.setProperty('--accent', `${colors.accent.h} ${colors.accent.s}% ${colors.accent.l}%`);
    root.style.setProperty('--background', `${colors.background.h} ${colors.background.s}% ${colors.background.l}%`);
    root.style.setProperty('--foreground', `${colors.foreground.h} ${colors.foreground.s}% ${colors.foreground.l}%`);

    // Calculate foreground colors for primary and accent
    const primaryForeground = colors.primary.l > 50 ? '0 0% 9%' : '0 0% 98%';
    const accentForeground = colors.accent.l > 50 ? '0 0% 9%' : '0 0% 98%';
    root.style.setProperty('--primary-foreground', primaryForeground);
    root.style.setProperty('--accent-foreground', accentForeground);

    // Save to localStorage
    localStorage.setItem('themeSettings', JSON.stringify(themeSettings));
  }, [themeSettings]);

  const updateTheme = (updates) => {
    setThemeSettings((prev) => ({
      ...prev,
      ...updates,
    }));
  };

  const updateColors = (colorUpdates) => {
    setThemeSettings((prev) => ({
      ...prev,
      colors: {
        ...prev.colors,
        ...colorUpdates,
      },
    }));
  };

  const resetTheme = () => {
    const defaultTheme = {
      mode: 'light',
      colors: {
        primary: { h: 221, s: 83, l: 53 },
        accent: { h: 142, s: 76, l: 36 },
        background: { h: 0, s: 0, l: 100 },
        foreground: { h: 0, s: 0, l: 4 },
      },
    };
    setThemeSettings(defaultTheme);
    localStorage.setItem('themeSettings', JSON.stringify(defaultTheme));
  };

  return (
    <ThemeContext.Provider value={{ themeSettings, updateTheme, updateColors, resetTheme }}>
      {children}
    </ThemeContext.Provider>
  );
};
