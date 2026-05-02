const CATEGORY_COLORS: Record<string, string> = {
  'Sociální služby': 'bg-amber-100 text-amber-700',
  'Vzdělávání': 'bg-yellow-100 text-yellow-700',
  'Zdravotnictví': 'bg-red-100 text-red-700',
  'Kultura': 'bg-purple-100 text-purple-700',
  'Životní prostředí': 'bg-emerald-100 text-emerald-700',
  'Sport': 'bg-green-100 text-green-700',
  'Mládež': 'bg-rose-100 text-rose-700',
  'Podpora seniorů': 'bg-teal-100 text-teal-700',
  'Zdravotně postižení': 'bg-cyan-100 text-cyan-700',
  'Komunitní rozvoj': 'bg-indigo-100 text-indigo-700',
  'Lidská práva': 'bg-orange-100 text-orange-700',
  'Charita a fundraising': 'bg-blue-100 text-blue-700',
  'Umění a tvůrčí činnost': 'bg-fuchsia-100 text-fuchsia-700',
  'Ochrana zvířat': 'bg-lime-100 text-lime-700',
  'Ostatní': 'bg-gray-100 text-gray-700',  
};

export const getCategoryColor = (categoryName: string): string =>
  CATEGORY_COLORS[categoryName] ?? CATEGORY_COLORS['Other'];