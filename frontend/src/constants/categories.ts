const CATEGORY_COLORS: Record<string, string> = {
  'Animal welfare': 'bg-amber-100 text-amber-700',
  'Arts & creative activities': 'bg-fuchsia-100 text-fuchsia-700',
  'Charity & fundraising': 'bg-blue-100 text-blue-700',
  'Community development': 'bg-indigo-100 text-indigo-700',
  'Culture': 'bg-purple-100 text-purple-700',
  'Disability support': 'bg-cyan-100 text-cyan-700',
  'Education': 'bg-yellow-100 text-yellow-700',
  'Environment': 'bg-emerald-100 text-emerald-700',
  'Healthcare': 'bg-red-100 text-red-700',
  'Human rights': 'bg-orange-100 text-orange-700',
  'Other': 'bg-gray-100 text-gray-700',
  'Senior support': 'bg-teal-100 text-teal-700',
  'Seniors': 'bg-[#E2F5EA] text-[#2D6A4F]',
  'Social care': 'bg-red-100 text-red-700',
  'Social services': 'bg-sky-100 text-sky-700',
  'Sports': 'bg-green-100 text-green-700',
  'Youth': 'bg-rose-100 text-rose-700',
};

export const getCategoryColor = (categoryName: string): string =>
  CATEGORY_COLORS[categoryName] ?? CATEGORY_COLORS['Other'];