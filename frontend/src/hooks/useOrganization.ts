/**
 * @file  useOrganization.ts
 * @brief Hook for fetching the detail of a single organization by ID.
 * @author Adam Kinzel (xkinzea00)
 */

import { useEffect, useState } from 'react';
import { API_BASE_URL } from '../config/api';
import type { OrganizationDetail } from '../types/organization';

interface UseOrganizationResult {
  org:     OrganizationDetail | null;
  loading: boolean;
  error:   string | null;
}

/**
 * Fetch the full detail of an organization identified by UUID.
 * The request is aborted automatically when the component unmounts or the ID changes.
 */
export function useOrganization(id: string | undefined): UseOrganizationResult {
  const [org,     setOrg]     = useState<OrganizationDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error,   setError]   = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;

    const controller = new AbortController();

    const fetchDetail = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await fetch(`${API_BASE_URL}/organizations/${id}`, {
          signal: controller.signal,
        });

        if (!response.ok) {
          throw new Error(
            response.status === 404
              ? 'Organizace nebyla nalezena.'
              : 'Chyba při načítání detailu.',
          );
        }

        const result = await response.json();
        setOrg(result.data ?? result);
      } catch (err) {
        if (err instanceof Error && err.name !== 'AbortError') {
          setError(err.message);
        }
      } finally {
        setLoading(false);
      }
    };

    fetchDetail();
    return () => controller.abort();
  }, [id]);

  return { org, loading, error };
}