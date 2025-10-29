import { useState, useEffect, useCallback, useRef } from 'react';
import { api } from '@/config/axios';

// In-memory cache
const cache = new Map();
const CACHE_DURATION = 5 * 60 * 1000; // 5 minutes

// Hook untuk fetch data dengan caching dan loading state
export const useFetch = (url, options = {}) => {
  const {
    initialData = null,
    dependencies = [],
    enabled = true,
    cacheKey = url,
    cacheDuration = CACHE_DURATION,
    onSuccess,
    onError,
  } = options;

  const [data, setData] = useState(initialData);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const mountedRef = useRef(true);

  const fetchData = useCallback(async (force = false) => {
    if (!enabled || !url) return;

    // Check cache first
    if (!force && cache.has(cacheKey)) {
      const cached = cache.get(cacheKey);
      if (Date.now() - cached.timestamp < cacheDuration) {
        setData(cached.data);
        return cached.data;
      }
    }

    setLoading(true);
    setError(null);

    try {
      const result = await api.get(url);
      
      if (mountedRef.current) {
        setData(result);
        setLoading(false);
        
        // Update cache
        cache.set(cacheKey, {
          data: result,
          timestamp: Date.now(),
        });
        
        if (onSuccess) onSuccess(result);
      }
      
      return result;
    } catch (err) {
      if (mountedRef.current) {
        setError(err);
        setLoading(false);
        if (onError) onError(err);
      }
      throw err;
    }
  }, [url, enabled, cacheKey, cacheDuration, onSuccess, onError]);

  useEffect(() => {
    mountedRef.current = true;
    fetchData();

    return () => {
      mountedRef.current = false;
    };
  }, [fetchData, ...dependencies]);

  const refetch = useCallback(() => {
    return fetchData(true);
  }, [fetchData]);

  const clearCache = useCallback(() => {
    cache.delete(cacheKey);
  }, [cacheKey]);

  return { data, loading, error, refetch, clearCache };
};

// Hook untuk mutations (POST, PUT, DELETE)
export const useMutation = (mutationFn, options = {}) => {
  const { onSuccess, onError, onSettled } = options;
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [data, setData] = useState(null);

  const mutate = useCallback(async (...args) => {
    setLoading(true);
    setError(null);

    try {
      const result = await mutationFn(...args);
      setData(result);
      setLoading(false);
      
      if (onSuccess) onSuccess(result);
      if (onSettled) onSettled(result, null);
      
      return result;
    } catch (err) {
      setError(err);
      setLoading(false);
      
      if (onError) onError(err);
      if (onSettled) onSettled(null, err);
      
      throw err;
    }
  }, [mutationFn, onSuccess, onError, onSettled]);

  return { mutate, loading, error, data };
};

// Hook untuk debounced search
export const useDebounce = (value, delay = 500) => {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(timer);
    };
  }, [value, delay]);

  return debouncedValue;
};

// Clear all cache
export const clearAllCache = () => {
  cache.clear();
};

// Clear specific cache by key pattern
export const clearCacheByPattern = (pattern) => {
  const keys = Array.from(cache.keys());
  keys.forEach(key => {
    if (key.includes(pattern)) {
      cache.delete(key);
    }
  });
};
