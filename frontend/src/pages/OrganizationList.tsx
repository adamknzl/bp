import { useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';

import { useOrganizations } from '../hooks/useOrganizations';
import { getCategoryColor } from '../constants/categories';

export default function OrganizationList() {
  const [searchParams] = useSearchParams();
  const searchQuery = searchParams.get('search');

  const {
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
  } = useOrganizations(searchQuery);

  const [showAllCategories, setShowAllCategories] = useState(false);

  const displayedCategories = showAllCategories ? categories : categories.slice(0, 4);

  if (loading && organizations.length === 0) {
    return <div className="p-12 text-center text-gray-500 font-medium">Loading data...</div>;
  }
  if (error && organizations.length === 0) {
    return <div className="p-12 text-center text-red-500 font-bold">{error}</div>;
  }

  return (
    <div className="max-w-[1400px] mx-auto p-8">
      <h1 className="text-4xl font-extrabold text-[#005A92] mb-8 font-['Manrope',sans-serif]">
        {searchQuery ? `Výsledky hľadania pre: "${searchQuery}"` : 'Non-profits overview'}
      </h1>

      <div className="flex flex-col lg:flex-row gap-8">

        {/* ── Filters sidebar ─────────────────────────────────────────────── */}
        <aside className="w-full lg:w-1/4 lg:sticky lg:top-24 self-start">
          <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">

            <div className="flex justify-between items-center mb-6">
              <h2 className="text-xl font-bold text-[#005A92] font-['Manrope',sans-serif]">Filters</h2>
              {hasActiveFilters && (
                <button
                  onClick={clearFilters}
                  className="text-xs font-bold text-red-500 hover:text-red-700 uppercase tracking-wider transition"
                >
                  Zrušiť filtre
                </button>
              )}
            </div>

            {/* Legal form */}
            <div className="mb-6">
              <label className="block text-xs font-bold text-gray-500 mb-2 uppercase tracking-wider">
                Legal Form
              </label>
              <select
                value={selectedLegalForm}
                onChange={e => setSelectedLegalForm(e.target.value)}
                className="w-full p-2.5 bg-gray-50 border border-gray-200 rounded text-gray-700 text-sm focus:outline-none"
              >
                <option value="">All legal forms</option>
                {legalForms.map(form => (
                  <option key={form} value={form}>
                    {form}
                  </option>
                ))}
              </select>
            </div>

            {/* Size category */}
            <div className="mb-6">
              <label className="block text-xs font-bold text-gray-500 mb-2 uppercase tracking-wider">
                Size Category
              </label>
              <select
                value={selectedSize}
                onChange={e => setSelectedSize(e.target.value)}
                className="w-full p-2.5 bg-gray-50 border border-gray-200 rounded text-gray-700 text-sm focus:outline-none"
              >
                <option value="">All sizes</option>
                {sizes.map(size => (
                  <option key={size.cat_id} value={size.cat_id}>
                    {size.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Categories */}
            <div className="mb-8">
              <label className="block text-xs font-bold text-gray-500 mb-3 uppercase tracking-wider">
                Kategorie
              </label>
              <div className="space-y-3">
                {displayedCategories.map(category => (
                  <label
                    key={category.category_id}
                    className="flex items-center gap-3 cursor-pointer"
                  >
                    <input
                      type="checkbox"
                      value={category.category_id}
                      checked={selectedCategories.includes(category.category_id)}
                      onChange={() => toggleCategory(category.category_id)}
                      className="w-4 h-4 rounded border-gray-300 text-[#005A92] focus:ring-[#005A92]"
                    />
                    <span className="text-sm text-gray-700">{category.name}</span>
                  </label>
                ))}
              </div>

              {categories.length > 4 && (
                <button
                  onClick={() => setShowAllCategories(v => !v)}
                  className="mt-3 text-sm text-[#005A92] font-bold hover:underline focus:outline-none"
                >
                  {showAllCategories ? '- Zobraziť menej' : '+ Zobraziť všetky'}
                </button>
              )}
            </div>

            <button
              onClick={applyFilters}
              disabled={loading}
              className="w-full py-3 bg-[#005A92] text-white font-semibold rounded hover:bg-blue-800 transition disabled:opacity-50 cursor-pointer"
            >
              {loading ? 'Filtrujem...' : 'Použít filtry'}
            </button>
          </div>
        </aside>

        {/* ── Main content ─────────────────────────────────────────────────── */}
        <main className="w-full lg:w-3/4">

          {/* GPS promo banner */}
          <div className="bg-[#E2F5EA] border border-[#A8E6CF] rounded-xl p-6 mb-8 flex items-center justify-between">
            <div className="flex items-center gap-5">
              <div className="w-14 h-14 bg-white rounded-lg flex items-center justify-center shadow-sm">
                <svg className="w-7 h-7 text-[#2D6A4F] rotate-45" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                </svg>
              </div>
              <div>
                <h3 className="text-lg font-bold text-[#2D6A4F] font-['Manrope',sans-serif]">
                  Find non-profits near me
                </h3>
                <p className="text-[#2D6A4F] text-sm opacity-90 mt-1">
                  Display non-profits in your vicinity using GPS.
                </p>
              </div>
            </div>
            <button className="flex items-center gap-2 px-5 py-2.5 bg-[#A8E6CF] text-[#2D6A4F] font-bold rounded hover:bg-[#8ee0c2] transition cursor-pointer">
              Find non-profits near me
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M14 5l7 7m0 0l-7 7m7-7H3" />
              </svg>
            </button>
          </div>

          {/* Organization cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
            {organizations.length === 0 && !loading ? (
              <div className="col-span-full py-12 text-center text-gray-500">
                Pre zvolené filtre sa nenašli žiadne organizácie.
              </div>
            ) : (
              organizations.map(org => (
                <div
                  key={org.organization_id}
                  className="bg-white rounded-xl p-6 shadow-sm border border-gray-100 flex flex-col h-full hover:shadow-md transition-shadow"
                >
                  <div className="flex gap-2 mb-4 flex-wrap">
                    {org.organization_category?.map(({ category }) => (
                      <span
                        key={category.category_id}
                        className={`px-2.5 py-1 text-[10px] font-bold rounded-full uppercase ${getCategoryColor(category.name)}`}
                      >
                        {category.name}
                      </span>
                    ))}
                  </div>

                  <h3 className="text-xl font-bold text-[#005A92] mb-3 font-['Manrope',sans-serif] leading-tight">
                    {org.name}
                  </h3>

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
                          {org.hq_address.split(',')[0]}
                        </span>
                      </div>
                    )}
                  </div>

                  <Link
                    to={`/org/${org.organization_id}`}
                    className="w-full py-2.5 bg-[#E9F1FF] text-[#00426D] text-center font-bold rounded hover:text-white hover:bg-[#00426D] transition text-sm"
                  >
                    Zobrazit detail
                  </Link>
                </div>
              ))
            )}
          </div>
        </main>

      </div>
    </div>
  );
}