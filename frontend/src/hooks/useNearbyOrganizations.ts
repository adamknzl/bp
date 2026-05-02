/**
 * @file  useNearbyOrganizations.ts
 * @brief Hook for fetching organizations near the user's current GPS position.
 * @author Adam Kinzel (xkinzea00)
 */

import { useState } from 'react';
import { API_BASE_URL } from '../config/api';
import type { NearbyOrganization } from '../types/organization';

interface UseNearbyOrganizationsResult {
  organizations: NearbyOrganization[];
  loading:       boolean;
  error:         string | null;
  findNearby:    (radiusKm?: number) => void;
}

/**
 * Request the user's geolocation and fetch organizations within the given radius.
 * The Geolocation API is only available over HTTPS (and localhost).
 */
export function useNearbyOrganizations(): UseNearbyOrganizationsResult {
  const [organizations, setOrganizations] = useState<NearbyOrganization[]>([]);
  const [loading,       setLoading]       = useState(false);
  const [error,         setError]         = useState<string | null>(null);

  const findNearby = (radiusKm: number = 10) => {
    setLoading(true);
    setError(null);

    if (!navigator.geolocation) {
      setError('Váš prohlížeč nepodporuje geolokaci.');
      setLoading(false);
      return;
    }

    navigator.geolocation.getCurrentPosition(
      async position => {
        const { latitude, longitude } = position.coords;
        try {
          const response = await fetch(
            `${API_BASE_URL}/organizations/nearby?lat=${latitude}&lon=${longitude}&radius=${radiusKm}`,
          );
          if (!response.ok) throw new Error();
          const result = await response.json();
          setOrganizations(result.data);
        } catch {
          setError('Nepodařilo se načíst organizace v okolí.');
        } finally {
          setLoading(false);
        }
      },
      err => {
        setError(
          err.code === err.PERMISSION_DENIED
            ? 'Pro vyhledání organizací v okolí je nutné povolit přístup k poloze.'
            : 'Nepodařilo se získat vaši polohu.',
        );
        setLoading(false);
      },
    );
  };

  return { organizations, loading, error, findNearby };
}