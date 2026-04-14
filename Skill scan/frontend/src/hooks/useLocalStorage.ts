import { useCallback } from 'react';

export const useLocalStorage = <T>(key: string, initialValue?: T) => {
  // Get from local storage by key
  const getStoredValue = useCallback((): T | null => {
    try {
      const item = window.localStorage.getItem(key);
      return item ? JSON.parse(item) : initialValue || null;
    } catch (error) {
      console.error(`Error reading from localStorage [${key}]:`, error);
      return initialValue || null;
    }
  }, [key, initialValue]);

  // State to store our value
  const storedValue = getStoredValue();

  // Return a wrapped version of useState's setter function that
  // persists the new value to localStorage
  const setValue = useCallback(
    (value: T | ((val: T | null) => T)) => {
      try {
        // Allow value to be a function so we have same API as useState
        const valueToStore = value instanceof Function ? value(storedValue) : value;
        // Save state
        window.localStorage.setItem(key, JSON.stringify(valueToStore));
      } catch (error) {
        console.error(`Error writing to localStorage [${key}]:`, error);
      }
    },
    [key, storedValue]
  );

  const removeValue = useCallback(() => {
    try {
      window.localStorage.removeItem(key);
    } catch (error) {
      console.error(`Error removing from localStorage [${key}]:`, error);
    }
  }, [key]);

  return [storedValue, setValue, removeValue] as const;
};
