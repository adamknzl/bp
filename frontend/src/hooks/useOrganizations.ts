/**
 * @file  useOrganizations.ts
 * @brief Hook managing the organization list, filter state, and pagination.
 * @author Adam Kinzel (xkinzea00)
 *
 * Filter selections are persisted in sessionStorage so they persist during
 * navigation to the detail view and back without losing the user's context.
 */

import { useEffect, useState } from 'react';
import { API_BASE_URL } from '../config/api';
import type { Category, Organization, SizeCategory, LegalForm } from '../types/organization';

// Constants

const PAGE_SIZE = 24;

/** sessionStorage keys for persisted filter state. */
const SESSION_KEYS = {
  size:       'org_filter_size',
  legalForm:  'org_filter_legal_form',
  categories: 'org_filter_categories',
} as const;


// Helpers

/** Read the selected category IDs from sessionStorage, returning [] on parse failure. */
function readSessionCategories(): string[] {
  try {
    return JSON.parse(sessionStorage.getItem(SESSION_KEYS.categories) ?? '[]');
  } catch {
    return [];
  }
}

/** Build the URLSearchParams object for a list request. */
function buildParams(opts: {
  searchQuery?: string | null;
  size?:        string;
  legalForm?:   string;
  categories?:  string[];
  page?:        number;
  pageSize?:    number;
}): URLSearchParams {
  const params = new URLSearchParams();
  params.set('page',     String(opts.page     ?? 1));
  params.set('pageSize', String(opts.pageSize ?? PAGE_SIZE));
  if (opts.searchQuery)      params.set('search',       opts.searchQuery);
  if (opts.size)             params.set('size',          opts.size);
  if (opts.legalForm)        params.set('legal_form',    opts.legalForm);
  if (opts.categories?.length) params.set('categories', opts.categories.join(','));
  return params;
}


// Hook

export function useOrganizations(searchQuery: string | null) {
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [categories,    setCategories]    = useState<Category[]>([]);
  const [sizes,         setSizes]         = useState<SizeCategory[]>([]);
  const [legalForms,    setLegalForms]    = useState<LegalForm[]>([]);

  // Filter state - initialised from sessionStorage so selections persist during navigation.
  const [selectedSize,       setSelectedSize]       = useState(() => sessionStorage.getItem(SESSION_KEYS.size)      ?? '');
  const [selectedLegalForm,  setSelectedLegalForm]  = useState(() => sessionStorage.getItem(SESSION_KEYS.legalForm) ?? '');
  const [selectedCategories, setSelectedCategories] = useState<string[]>(readSessionCategories);

  // Pagination
  const [page,       setPage]       = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total,      setTotal]      = useState(0);

  const [loading, setLoading] = useState(true);
  const [error,   setError]   = useState<string | null>(null);

  const hasActiveFilters =
    selectedSize !== '' || selectedLegalForm !== '' || selectedCategories.length > 0;

  // Reset to page 1 when the search query changes
  useEffect(() => { setPage(1); }, [searchQuery]);

  // Fetch whenever the search query or page changes
  useEffect(() => {
    const controller = new AbortController();

    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const params = buildParams({
          searchQuery,
          size:       sessionStorage.getItem(SESSION_KEYS.size)      ?? '',
          legalForm:  sessionStorage.getItem(SESSION_KEYS.legalForm) ?? '',
          categories: readSessionCategories(),
          page,
        });

        const [orgsRes, filtersRes] = await Promise.all([
          fetch(`${API_BASE_URL}/organizations?${params}`,  { signal: controller.signal }),
          fetch(`${API_BASE_URL}/organizations/filters`,    { signal: controller.signal }),
        ]);

        if (!orgsRes.ok || !filtersRes.ok) throw new Error('Chyba při načítání dat.');

        const [orgsResult, filtersResult] = await Promise.all([
          orgsRes.json(),
          filtersRes.json(),
        ]);

        setOrganizations(orgsResult.data);
        setTotalPages(orgsResult.pagination?.totalPages ?? 1);
        setTotal(orgsResult.pagination?.total          ?? 0);
        setCategories(filtersResult.data.categories);
        setSizes(filtersResult.data.sizes);
        setLegalForms(filtersResult.data.legalForms);
      } catch (err) {
        if (err instanceof Error && err.name !== 'AbortError') {
          setError('Nepodařilo se načíst data.');
        }
      } finally {
        setLoading(false);
      }
    };

    load();
    return () => controller.abort();
  }, [searchQuery, page]);

  // Filter actions

  /** Toggle a single category ID in the selected set. */
  const toggleCategory = (categoryId: string) => {
    setSelectedCategories(prev =>
      prev.includes(categoryId)
        ? prev.filter(id => id !== categoryId)
        : [...prev, categoryId],
    );
  };

  /** Persist the current filter selections and re-fetch from page 1. */
  const applyFilters = async () => {
    setLoading(true);
    setError(null);
    try {
      sessionStorage.setItem(SESSION_KEYS.size,       selectedSize);
      sessionStorage.setItem(SESSION_KEYS.legalForm,  selectedLegalForm);
      sessionStorage.setItem(SESSION_KEYS.categories, JSON.stringify(selectedCategories));
      setPage(1);

      const params = buildParams({
        searchQuery,
        size:       selectedSize,
        legalForm:  selectedLegalForm,
        categories: selectedCategories,
        page:       1,
      });

      const response = await fetch(`${API_BASE_URL}/organizations?${params}`);
      if (!response.ok) throw new Error();
      const result = await response.json();
      setOrganizations(result.data);
      setTotalPages(result.pagination?.totalPages ?? 1);
      setTotal(result.pagination?.total          ?? 0);
    } catch {
      setError('Nepodařilo se aplikovat filtry.');
    } finally {
      setLoading(false);
    }
  };

  /** Clear all filter selections, remove them from sessionStorage, and re-fetch. */
  const clearFilters = async () => {
    setSelectedSize('');
    setSelectedLegalForm('');
    setSelectedCategories([]);
    setPage(1);

    sessionStorage.removeItem(SESSION_KEYS.size);
    sessionStorage.removeItem(SESSION_KEYS.legalForm);
    sessionStorage.removeItem(SESSION_KEYS.categories);

    setLoading(true);
    setError(null);
    try {
      const params   = buildParams({ searchQuery, page: 1 });
      const response = await fetch(`${API_BASE_URL}/organizations?${params}`);
      if (!response.ok) throw new Error();
      const result   = await response.json();
      setOrganizations(result.data);
      setTotalPages(result.pagination?.totalPages ?? 1);
      setTotal(result.pagination?.total          ?? 0);
    } catch {
      setError('Nepodařilo se obnovit seznam.');
    } finally {
      setLoading(false);
    }
  };

  return {
    organizations,
    categories,
    sizes,
    legalForms,
    selectedSize,      setSelectedSize,
    selectedLegalForm, setSelectedLegalForm,
    selectedCategories, toggleCategory,
    loading,
    error,
    hasActiveFilters,
    applyFilters,
    clearFilters,
    page, setPage,
    totalPages,
    total,
    pageSize: PAGE_SIZE,
  };
}