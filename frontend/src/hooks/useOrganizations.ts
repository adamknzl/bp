import { useEffect, useState } from 'react';
import { API_BASE_URL } from '../config/api';
import type { Category, Organization, SizeCategory } from '../types/organization';

// ─── Session storage keys ────────────────────────────────────────────────────

const SESSION_KEYS = {
  size: 'org_filter_size',
  legalForm: 'org_filter_legal_form',
  categories: 'org_filter_categories',
} as const;

// ─── Helpers ─────────────────────────────────────────────────────────────────

const FALLBACK_LEGAL_FORMS = [
  'Spolek',
  'Ústav',
  'Nadace',
  'Nadační fond',
  'Obecně prospěšná společnost',
];

function readSessionCategories(): string[] {
  try {
    return JSON.parse(sessionStorage.getItem(SESSION_KEYS.categories) ?? '[]');
  } catch {
    return [];
  }
}

function buildParams(opts: {
  searchQuery?: string | null;
  size?: string;
  legalForm?: string;
  categories?: string[];
  limit?: number;
}): URLSearchParams {
  const params = new URLSearchParams();
  params.set('limit', String(opts.limit ?? 50));
  if (opts.searchQuery) params.set('search', opts.searchQuery);
  if (opts.size) params.set('size', opts.size);
  if (opts.legalForm) params.set('legal_form', opts.legalForm);
  if (opts.categories?.length) params.set('categories', opts.categories.join(','));
  return params;
}

// ─── Hook ─────────────────────────────────────────────────────────────────────

export function useOrganizations(searchQuery: string | null) {
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [sizes, setSizes] = useState<SizeCategory[]>([]);
  const [legalForms, setLegalForms] = useState<string[]>([]);

  // Filter state — initialised from sessionStorage so selections survive navigation
  const [selectedSize, setSelectedSize] = useState<string>(
    () => sessionStorage.getItem(SESSION_KEYS.size) ?? '',
  );
  const [selectedLegalForm, setSelectedLegalForm] = useState<string>(
    () => sessionStorage.getItem(SESSION_KEYS.legalForm) ?? '',
  );
  const [selectedCategories, setSelectedCategories] = useState<string[]>(readSessionCategories);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const hasActiveFilters =
    selectedSize !== '' || selectedLegalForm !== '' || selectedCategories.length > 0;

  // ─── Initial load ──────────────────────────────────────────────────────────

  useEffect(() => {
    const controller = new AbortController();

    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const params = buildParams({
          searchQuery,
          // Read persisted filters directly — state may not yet reflect sessionStorage
          size: sessionStorage.getItem(SESSION_KEYS.size) ?? '',
          legalForm: sessionStorage.getItem(SESSION_KEYS.legalForm) ?? '',
          categories: readSessionCategories(),
        });

        const [orgsRes, filtersRes] = await Promise.all([
          fetch(`${API_BASE_URL}/organizations?${params}`, { signal: controller.signal }),
          fetch(`${API_BASE_URL}/organizations/filters`, { signal: controller.signal }),
        ]);

        if (!orgsRes.ok || !filtersRes.ok) throw new Error('Error while downloading data.');

        const [orgsResult, filtersResult] = await Promise.all([
          orgsRes.json(),
          filtersRes.json(),
        ]);

        setOrganizations(orgsResult.data);
        setCategories(filtersResult.data.categories);
        setSizes(filtersResult.data.sizes);
        setLegalForms(filtersResult.data.legalForms ?? FALLBACK_LEGAL_FORMS);
      } catch (err) {
        if (err instanceof Error && err.name !== 'AbortError') {
          setError('Unable to load data.');
        }
      } finally {
        setLoading(false);
      }
    };

    load();
    return () => controller.abort();
  }, [searchQuery]);

  // ─── Filter actions ────────────────────────────────────────────────────────

  const toggleCategory = (categoryId: string) => {
    setSelectedCategories(prev =>
      prev.includes(categoryId)
        ? prev.filter(id => id !== categoryId)
        : [...prev, categoryId],
    );
  };

  const applyFilters = async () => {
    setLoading(true);
    setError(null);
    try {
      sessionStorage.setItem(SESSION_KEYS.size, selectedSize);
      sessionStorage.setItem(SESSION_KEYS.legalForm, selectedLegalForm);
      sessionStorage.setItem(SESSION_KEYS.categories, JSON.stringify(selectedCategories));

      const params = buildParams({
        searchQuery,
        size: selectedSize,
        legalForm: selectedLegalForm,
        categories: selectedCategories,
      });

      const response = await fetch(`${API_BASE_URL}/organizations?${params}`);
      if (!response.ok) throw new Error('Chyba pri filtrovaní dát');
      const result = await response.json();
      setOrganizations(result.data);
    } catch {
      setError('Nepodarilo sa aplikovať filtre.');
    } finally {
      setLoading(false);
    }
  };

  const clearFilters = async () => {
    setSelectedSize('');
    setSelectedLegalForm('');
    setSelectedCategories([]);

    sessionStorage.removeItem(SESSION_KEYS.size);
    sessionStorage.removeItem(SESSION_KEYS.legalForm);
    sessionStorage.removeItem(SESSION_KEYS.categories);

    setLoading(true);
    setError(null);
    try {
      const params = buildParams({ searchQuery });
      const response = await fetch(`${API_BASE_URL}/organizations?${params}`);
      if (!response.ok) throw new Error('Chyba pri obnove dát');
      const result = await response.json();
      setOrganizations(result.data);
    } catch {
      setError('Nepodarilo sa obnoviť zoznam.');
    } finally {
      setLoading(false);
    }
  };

  return {
    organizations,
    categories,
    sizes,
    legalForms,
    selectedSize,
    setSelectedSize,
    selectedLegalForm,
    setSelectedLegalForm,
    selectedCategories,
    toggleCategory,
    loading,
    error,
    hasActiveFilters,
    applyFilters,
    clearFilters,
  };
}