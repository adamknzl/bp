/**
 * @file  OrganizationList.tsx
 * @brief Main listing page - renders the filter sidebar, organization card grid,
 *        GPS proximity search, and pagination controls.
 * @author Adam Kinzel (xkinzea00)
 */

import { useEffect, useState, useRef } from 'react';
import { Link, useSearchParams }        from 'react-router-dom';

import { useOrganizations }      from '../hooks/useOrganizations';
import { useNearbyOrganizations } from '../hooks/useNearbyOrganizations';
import { getCategoryColor }       from '../constants/categories';
import type { NearbyOrganization } from '../types/organization';
import Pagination from '../components/Pagination';
import Card       from '../components/Card';
import Badge      from '../components/Badge';

type ViewMode = 'all' | 'nearby';

export default function OrganizationList() {
  const [searchParams] = useSearchParams();
  const searchQuery    = searchParams.get('search');

  const {
    organizations, categories, sizes, legalForms,
    selectedSize,      setSelectedSize,
    selectedLegalForm, setSelectedLegalForm,
    selectedCategories, toggleCategory,
    loading, error, hasActiveFilters,
    applyFilters, clearFilters,
    page, setPage, totalPages, total, pageSize,
  } = useOrganizations(searchQuery);

  const {
    organizations: nearbyOrgs,
    loading: nearbyLoading,
    error:   nearbyError,
    findNearby,
  } = useNearbyOrganizations();

  const [showAllCategories, setShowAllCategories] = useState(false);
  const [viewMode,          setViewMode]          = useState<ViewMode>('all');

  const displayedCategories = showAllCategories ? categories : categories.slice(0, 4);

  const activeOrgs    = viewMode === 'nearby' ? nearbyOrgs    : organizations;
  const activeLoading = viewMode === 'nearby' ? nearbyLoading : loading;

  // Scroll to top after page change (only when loading completes)
  const justChangedPage = useRef(false);
  useEffect(() => {
    if (justChangedPage.current && !loading) {
      window.scrollTo({ top: 0, behavior: 'smooth' });
      justChangedPage.current = false;
    }
  }, [loading]);

  const handleFindNearby = () => { setViewMode('nearby'); findNearby(10); };
  const handleBackToAll  = () => { setViewMode('all'); };

  if (viewMode === 'all' && loading && organizations.length === 0) {
    return <div className="p-12 text-center text-gray-500 font-medium">Načítám data...</div>;
  }
  if (viewMode === 'all' && error && organizations.length === 0) {
    return <div className="p-12 text-center text-red-500 font-bold">{error}</div>;
  }

  return (
    <div className="max-w-[1400px] mx-auto p-8">
      <h1 className="text-4xl font-extrabold text-brand mb-8 font-['Manrope',sans-serif]">
        {viewMode === 'nearby'
          ? 'Neziskové organizace ve vašem okolí'
          : searchQuery
            ? `Výsledky hledání pro: "${searchQuery}"`
            : 'Přehled neziskových organizací'}
      </h1>

      <div className="flex flex-col lg:flex-row gap-8">

        {/* Filter sidebar */}
        <aside className="w-full lg:w-1/4 lg:sticky lg:top-24 self-start">
          <Card padding="md">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-xl font-bold text-brand font-['Manrope',sans-serif]">Filtry</h2>
              {hasActiveFilters && viewMode === 'all' && (
                <button
                  onClick={clearFilters}
                  className="text-xs font-bold text-red-500 hover:text-red-700 uppercase tracking-wider transition"
                >
                  Zrušit filtry
                </button>
              )}
            </div>

            {viewMode === 'nearby' && (
              <div className="mb-6 p-3 bg-accent-light rounded text-sm text-accent-dark">
                Zobrazují se organizace v okolí vaší polohy. Pokud chcete použít filtry,
                nejprve se vraťte na celý seznam.
              </div>
            )}

            <fieldset disabled={viewMode === 'nearby'} className="contents">

              {/* Legal form */}
              <div className="mb-6">
                <label className="block text-xs font-bold text-gray-500 mb-2 uppercase tracking-wider">
                  Právní forma
                </label>
                <select
                  value={selectedLegalForm}
                  onChange={e => setSelectedLegalForm(e.target.value)}
                  className="w-full p-2.5 bg-gray-50 border border-gray-200 rounded text-gray-700 text-sm focus:outline-none"
                >
                  <option value="">Všechny právní formy</option>
                  {legalForms.map(form => (
                    <option key={form.code} value={form.code}>{form.name}</option>
                  ))}
                </select>
              </div>

              {/* Size category */}
              <div className="mb-6">
                <label className="block text-xs font-bold text-gray-500 mb-2 uppercase tracking-wider">
                  Velikostní kategorie
                </label>
                <select
                  value={selectedSize}
                  onChange={e => setSelectedSize(e.target.value)}
                  className="w-full p-2.5 bg-gray-50 border border-gray-200 rounded text-gray-700 text-sm focus:outline-none"
                >
                  <option value="">Všechny velikosti</option>
                  {sizes.map(size => (
                    <option key={size.code} value={size.code}>{size.label}</option>
                  ))}
                </select>
              </div>

              {/* Thematic categories */}
              <div className="mb-8">
                <label className="block text-xs font-bold text-gray-500 mb-3 uppercase tracking-wider">
                  Kategorie
                </label>
                <div className="space-y-2 max-h-75 overflow-y-scroll">
                  {displayedCategories.map(category => (
                    <label key={category.category_id} className="flex items-center gap-3 cursor-pointer">
                      <input
                        type="checkbox"
                        value={category.category_id}
                        checked={selectedCategories.includes(category.category_id)}
                        onChange={() => toggleCategory(category.category_id)}
                        className="w-4 h-4 rounded border-gray-300 text-brand focus:ring-brand"
                      />
                      <span className="text-sm text-gray-700">{category.name}</span>
                    </label>
                  ))}
                </div>

                {categories.length > 4 && (
                  <button
                    onClick={() => setShowAllCategories(v => !v)}
                    className="mt-3 text-sm text-brand font-bold hover:underline focus:outline-none"
                  >
                    {showAllCategories ? '- Zobrazit méně' : '+ Zobrazit všechny'}
                  </button>
                )}
              </div>

              <button
                onClick={applyFilters}
                disabled={loading || viewMode === 'nearby'}
                className="w-full py-3 bg-brand text-white font-semibold rounded hover:bg-blue-800 transition disabled:opacity-50 cursor-pointer"
              >
                {loading ? 'Filtruji...' : 'Použít filtry'}
              </button>

            </fieldset>
          </Card>
        </aside>

        {/* Main content */}
        <main className="w-full lg:w-3/4">

          {/* GPS promo banner */}
          {viewMode === 'all' && (
            <div className="bg-accent-light border border-accent rounded-xl p-6 mb-8 flex items-center justify-between">
              <div className="flex items-center gap-5">
                <div className="w-14 h-14 bg-white rounded-lg flex items-center justify-center shadow-sm">
                  <svg className="w-7 h-7 text-accent-dark rotate-45" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                  </svg>
                </div>
                <div>
                  <h3 className="text-lg font-bold text-accent-dark font-['Manrope',sans-serif]">
                    Najít neziskové organizace ve vašem okolí
                  </h3>
                  <p className="text-accent-dark text-sm opacity-90 mt-1">
                    Zobrazte neziskové organizace ve vašem okolí pomocí GPS.
                  </p>
                </div>
              </div>
              <button
                onClick={handleFindNearby}
                disabled={nearbyLoading}
                className="flex items-center gap-2 px-5 py-2.5 bg-accent text-accent-dark font-bold rounded hover:bg-[#8ee0c2] transition cursor-pointer disabled:opacity-60"
              >
                {nearbyLoading ? 'Vyhledávám...' : 'Najít organizace v okolí'}
                {!nearbyLoading && (
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M14 5l7 7m0 0l-7 7m7-7H3" />
                  </svg>
                )}
              </button>
            </div>
          )}

          {/* Back-to-all banner */}
          {viewMode === 'nearby' && (
            <div className="bg-white border border-gray-200 rounded-xl p-4 mb-8 flex items-center justify-between">
              <p className="text-sm text-gray-600">Zobrazují se organizace v okolí vaší polohy.</p>
              <button onClick={handleBackToAll} className="text-sm font-bold text-brand hover:underline cursor-pointer">
                ← Zpět na celý seznam
              </button>
            </div>
          )}

          {/* Nearby error */}
          {viewMode === 'nearby' && nearbyError && (
            <div className="p-6 mb-8 bg-red-50 border border-red-200 rounded-xl text-red-700 text-sm">
              {nearbyError}
            </div>
          )}

          {/* Nearby loading */}
          {viewMode === 'nearby' && nearbyLoading && (
            <div className="p-12 text-center text-gray-500 font-medium">
              Načítám organizace ve vašem okolí...
            </div>
          )}

          {/* Organization card grid */}
          {!(viewMode === 'nearby' && nearbyLoading) && (
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
              {activeOrgs.length === 0 && !activeLoading ? (
                <div className="col-span-full py-12 text-center text-gray-500">
                  {viewMode === 'nearby'
                    ? 'V okolí vaší polohy jsme nenašli žádné organizace.'
                    : 'Pro zvolené filtry nebyly nalezeny žádné organizace.'}
                </div>
              ) : (
                activeOrgs.map(org => (
                  <Card key={org.organization_id} hoverable padding="md" className="flex flex-col h-full">
                    <div className="flex gap-2 mb-4 flex-wrap">
                      {org.organization_category?.map(({ category }) => (
                        <Badge key={category.category_id} size="sm" colorClass={getCategoryColor(category.name)}>
                          {category.name}
                        </Badge>
                      ))}
                    </div>

                    <h3 className="text-xl font-bold text-brand mb-3 font-['Manrope',sans-serif] leading-tight">
                      {org.name}
                    </h3>

                    {/* Distance badge - visible only in nearby view */}
                    {viewMode === 'nearby' && (
                      <div className="text-xs text-accent-dark font-bold mb-2">
                        {(org as NearbyOrganization).distance_km.toFixed(1)} km od vás
                      </div>
                    )}

                    <div className="mb-6 flex-grow flex flex-col">
                      <p className="text-gray-500 text-sm leading-relaxed line-clamp-3">
                        {org.description}
                      </p>

                      {org.hq_address && (
                        <div className="flex items-center gap-1.5 mt-auto pt-4 text-gray-400">
                          <svg className="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                          </svg>
                          <span className="text-sm text-gray-500">
                            {org.hq_address?.includes(',')
                              ? org.hq_address.split(',').pop()?.trim().replace(/^\d{3}\s?\d{2}\s+/, '')
                              : org.hq_address}
                          </span>
                        </div>
                      )}
                    </div>

                    <Link
                      to={`/org/${org.organization_id}`}
                      className="w-full py-2.5 bg-brand-light text-brand-dark text-center font-bold rounded hover:text-white hover:bg-brand-dark transition text-sm"
                    >
                      Zobrazit detail
                    </Link>
                  </Card>
                ))
              )}
            </div>
          )}

          {/* Pagination */}
          {viewMode === 'all' && !loading && activeOrgs.length > 0 && (
            <>
              <div className="text-sm text-gray-500 mt-8 text-center">
                Zobrazeno {(page - 1) * pageSize + 1}–{Math.min(page * pageSize, total)} z {total} organizací
              </div>
              <Pagination
                currentPage={page}
                totalPages={totalPages}
                onPageChange={newPage => {
                  justChangedPage.current = true;
                  setPage(newPage);
                }}
              />
            </>
          )}

        </main>
      </div>
    </div>
  );
}