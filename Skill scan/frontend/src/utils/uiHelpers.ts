/**
 * Accessibility & Mobile Optimization Utilities
 * WCAG 2.1 AA compliance and responsive design helpers
 */

// ============================================================================
// ACCESSIBILITY: ARIA & SEMANTIC HTML HELPERS
// ============================================================================

export const accessibilityHelpers = {
  /**
   * Generate ARIA label for form input
   */
  getAriaLabel: (fieldName: string, isRequired: boolean = false) => {
    const required = isRequired ? ", required" : "";
    return `${fieldName}${required}`;
  },

  /**
   * Generate ARIA describedby ID
   */
  getAriaDescribedBy: (fieldName: string) => `${fieldName}-help`,

  /**
   * Validate color contrast ratio (WCAG AA: 4.5:1 for normal text)
   */
  isColorContrastValid: (bgColor: string, fgColor: string): boolean => {
    const getLuminance = (color: string) => {
      const rgb = parseInt(color.slice(1), 16);
      const r = (rgb >> 16) & 0xff;
      const g = (rgb >> 8) & 0xff;
      const b = (rgb >> 0) & 0xff;

      const [rs, gs, bs] = [r, g, b].map((x) => {
        x = x / 255;
        return x <= 0.03928 ? x / 12.92 : Math.pow((x + 0.055) / 1.055, 2.4);
      });

      return 0.2126 * rs + 0.7152 * gs + 0.0722 * bs;
    };

    const lum1 = getLuminance(bgColor);
    const lum2 = getLuminance(fgColor);
    const ratio = (Math.max(lum1, lum2) + 0.05) / (Math.min(lum1, lum2) + 0.05);

    return ratio >= 4.5;
  },

  /**
   * Create focus trap for modals
   */
  createFocusTrap: (element: HTMLElement) => {
    const focusableElements = element.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    const firstElement = focusableElements[0] as HTMLElement;
    const lastElement = focusableElements[focusableElements.length - 1] as HTMLElement;

    return {
      handleKeyDown: (e: KeyboardEvent) => {
        if (e.key === "Tab") {
          if (e.shiftKey) {
            if (document.activeElement === firstElement) {
              e.preventDefault();
              lastElement.focus();
            }
          } else {
            if (document.activeElement === lastElement) {
              e.preventDefault();
              firstElement.focus();
            }
          }
        }
      },
    };
  },

  /**
   * Announce to screen readers
   */
  announceToScreenReader: (message: string, priority: "polite" | "assertive" = "polite") => {
    const announcement = document.createElement("div");
    announcement.setAttribute("role", "status");
    announcement.setAttribute("aria-live", priority);
    announcement.setAttribute("aria-atomic", "true");
    announcement.className = "sr-only"; // Screen reader only
    announcement.textContent = message;
    document.body.appendChild(announcement);

    setTimeout(() => {
      announcement.remove();
    }, 1000);
  },
};

// ============================================================================
// MOBILE OPTIMIZATION: RESPONSIVE DESIGN UTILITIES
// ============================================================================

export const mobileHelpers = {
  /**
   * Get current breakpoint
   */
  getCurrentBreakpoint: (): "mobile" | "tablet" | "desktop" => {
    const width = window.innerWidth;
    if (width < 640) return "mobile";
    if (width < 1024) return "tablet";
    return "desktop";
  },

  /**
   * Detect touch device
   */
  isTouchDevice: (): boolean => {
    return (
      window.matchMedia("(hover: none) and (pointer: coarse)").matches ||
      navigator.maxTouchPoints > 0
    );
  },

  /**
   * Get safe area insets (for notched devices)
   */
  getSafeAreaInsets: () => ({
    top: window.getComputedStyle(document.documentElement).getPropertyValue("--safe-area-inset-top"),
    right: window.getComputedStyle(document.documentElement).getPropertyValue("--safe-area-inset-right"),
    bottom: window.getComputedStyle(document.documentElement).getPropertyValue("--safe-area-inset-bottom"),
    left: window.getComputedStyle(document.documentElement).getPropertyValue("--safe-area-inset-left"),
  }),

  /**
   * Get optimal touch target size (48x48px minimum)
   */
  getTouchTargetSize: (label?: string): string => {
    const size = "h-12 w-12"; // 48x48px
    const padding = label ? "px-4" : "";
    return `${size} ${padding} flex items-center justify-center`;
  },

  /**
   * Create mobile-friendly menu
   */
  createMobileMenu: (items: string[]) => ({
    isOpen: false,
    toggle: function () {
      this.isOpen = !this.isOpen;
    },
    close: function () {
      this.isOpen = false;
    },
    items,
  }),

  /**
   * Handle viewport orientation changes
   */
  onOrientationChange: (callback: (orientation: "portrait" | "landscape") => void) => {
    const handleChange = () => {
      const orientation = window.innerHeight > window.innerWidth ? "portrait" : "landscape";
      callback(orientation);
    };

    window.addEventListener("orientationchange", handleChange);
    window.addEventListener("resize", handleChange);

    return () => {
      window.removeEventListener("orientationchange", handleChange);
      window.removeEventListener("resize", handleChange);
    };
  },
};

// ============================================================================
// ANIMATION & TRANSITIONS: SMOOTH UX
// ============================================================================

export const animationHelpers = {
  /**
   * Fade in animation
   */
  fadeIn: (duration = 300) => ({
    from: { opacity: 0 },
    to: { opacity: 1 },
    duration,
    easing: "ease-in-out",
  }),

  /**
   * Slide in from left
   */
  slideInLeft: (duration = 300) => ({
    from: { transform: "translateX(-100%)", opacity: 0 },
    to: { transform: "translateX(0)", opacity: 1 },
    duration,
    easing: "ease-out",
  }),

  /**
   * Scale up animation
   */
  scaleUp: (duration = 300) => ({
    from: { transform: "scale(0.95)", opacity: 0 },
    to: { transform: "scale(1)", opacity: 1 },
    duration,
    easing: "cubic-bezier(0.34, 1.56, 0.64, 1)",
  }),

  /**
   * Loading skeleton animation
   */
  skeletonPulse: () => ({
    animation: "pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite",
  }),

  /**
   * Success checkmark animation
   */
  successCheckmark: (duration = 600) => ({
    from: { transform: "scale(0)", opacity: 0 },
    to: { transform: "scale(1)", opacity: 1 },
    duration,
    easing: "cubic-bezier(0.34, 1.56, 0.64, 1)",
  }),
};

// ============================================================================
// LOADING STATES: SKELETON & SPINNER
// ============================================================================

export const loadingHelpers = {
  /**
   * Create skeleton loader HTML
   */
  createSkeletonLoader: (rows: number = 3) => {
    return Array(rows)
      .fill(0)
      .map((_, i) => ({
        id: `skeleton-${i}`,
        className: "h-12 bg-gray-200 rounded animate-pulse mb-4",
      }));
  },

  /**
   * Get spinner size based on context
   */
  getSpinnerSize: (context: "page" | "button" | "inline"): string => {
    const sizes = {
      page: "w-12 h-12",
      button: "w-4 h-4",
      inline: "w-3 h-3",
    };
    return sizes[context];
  },

  /**
   * Create loading message
   */
  getLoadingMessage: (action: string): string => {
    const messages = {
      uploading: "Uploading your file...",
      parsing: "Parsing resume...",
      generating: "Generating assessment...",
      scoring: "Scoring your response...",
      exporting: "Preparing your export...",
      saving: "Saving your data...",
    };
    return messages[action as keyof typeof messages] || `${action}...`;
  },
};

// ============================================================================
// ERROR HANDLING & RECOVERY
// ============================================================================

export const errorHelpers = {
  /**
   * Get user-friendly error message
   */
  getFriendlyErrorMessage: (error: any): string => {
    if (typeof error === "string") return error;

    const status = error?.response?.status;
    const message = error?.response?.data?.error;

    const errorMap: Record<number, string> = {
      400: "Please check your input and try again",
      401: "Please log in to continue",
      403: "You don't have permission to do this",
      404: "The requested resource was not found",
      408: "Request timed out - please try again",
      413: "File is too large - maximum 50MB",
      500: "Server error - please try again later",
      503: "Service temporarily unavailable",
    };

    return message || errorMap[status] || "An unexpected error occurred";
  },

  /**
   * Should retry operation
   */
  shouldRetry: (error: any): boolean => {
    const status = error?.response?.status;
    const retryableStatuses = [408, 429, 500, 502, 503, 504];
    return retryableStatuses.includes(status);
  },

  /**
   * Get retry delay (exponential backoff)
   */
  getRetryDelay: (attempt: number): number => {
    return Math.min(1000 * Math.pow(2, attempt), 10000); // Max 10 seconds
  },

  /**
   * Create error boundary state
   */
  createErrorBoundary: () => ({
    hasError: false,
    error: null,
    resetError: function () {
      this.hasError = false;
      this.error = null;
    },
  }),
};

// ============================================================================
// FORM OPTIMIZATION
// ============================================================================

export const formHelpers = {
  /**
   * Debounce input for search/autocomplete
   */
  debounceInput: (callback: Function, delay: number = 300) => {
    let timeoutId: NodeJS.Timeout;
    return (value: string) => {
      clearTimeout(timeoutId);
      timeoutId = setTimeout(() => callback(value), delay);
    };
  },

  /**
   * Validate form field
   */
  validateField: (
    value: any,
    type: "email" | "password" | "number" | "text"
  ): { isValid: boolean; message?: string } => {
    switch (type) {
      case "email":
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return {
          isValid: emailRegex.test(value),
          message: "Invalid email format",
        };
      case "password":
        return {
          isValid: value.length >= 6,
          message: "Password must be at least 6 characters",
        };
      case "number":
        return {
          isValid: !isNaN(value) && value >= 0 && value <= 10,
          message: "Must be a number between 0 and 10",
        };
      case "text":
        return {
          isValid: value.trim().length > 0,
          message: "This field is required",
        };
      default:
        return { isValid: true };
    }
  },

  /**
   * Get field error state
   */
  getFieldError: (
    touched: boolean,
    dirty: boolean,
    error: string | undefined
  ): { showError: boolean; message?: string } => ({
    showError: (touched || dirty) && !!error,
    message: error,
  }),
};

// ============================================================================
// PERFORMANCE MONITORING
// ============================================================================

export const performanceHelpers = {
  /**
   * Log page load metrics
   */
  logPageMetrics: () => {
    if (window.performance && window.performance.timing) {
      const timing = window.performance.timing;
      const metrics = {
        pageLoadTime: timing.loadEventEnd - timing.navigationStart,
        firstPaint: timing.responseEnd - timing.navigationStart,
        domReady: timing.domContentLoadedEventEnd - timing.navigationStart,
      };
      console.log("Page Metrics:", metrics);
      return metrics;
    }
    return null;
  },

  /**
   * Measure component render time
   */
  measureRenderTime: (componentName: string, callback: Function) => {
    const start = performance.now();
    callback();
    const end = performance.now();
    console.log(`${componentName} render time: ${(end - start).toFixed(2)}ms`);
  },

  /**
   * Monitor API response time
   */
  trackApiCall: async (url: string, init?: RequestInit) => {
    const start = performance.now();
    try {
      const response = await fetch(url, init);
      const end = performance.now();
      console.log(`API ${init?.method || "GET"} ${url}: ${(end - start).toFixed(2)}ms`);
      return response;
    } catch (error) {
      const end = performance.now();
      console.error(`API ${init?.method || "GET"} ${url} failed: ${(end - start).toFixed(2)}ms`);
      throw error;
    }
  },
};

// ============================================================================
// EXPORT ALL HELPERS
// ============================================================================

export default {
  accessibility: accessibilityHelpers,
  mobile: mobileHelpers,
  animation: animationHelpers,
  loading: loadingHelpers,
  error: errorHelpers,
  form: formHelpers,
  performance: performanceHelpers,
};
