interface PaginationProps {
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
}

export default function Pagination({ currentPage, totalPages, onPageChange }: PaginationProps) {
  if (totalPages <= 1) return null;

  // Generate visible page numbers with ellipsis (e.g. 1 ... 4 5 6 ... 20)
  const getVisiblePages = (): (number | 'ellipsis')[] => {
    const pages: (number | 'ellipsis')[] = [];
    const delta = 1;

    pages.push(1);

    if (currentPage - delta > 2) {
      pages.push('ellipsis');
    }

    for (
      let i = Math.max(2, currentPage - delta);
      i <= Math.min(totalPages - 1, currentPage + delta);
      i++
    ) {
      pages.push(i);
    }

    if (currentPage + delta < totalPages - 1) {
      pages.push('ellipsis');
    }

    if (totalPages > 1) {
      pages.push(totalPages);
    }

    return pages;
  };

  const visiblePages = getVisiblePages();

  const baseBtnClass =
    'min-w-[40px] h-10 px-3 rounded-md text-sm font-medium transition-colors flex items-center justify-center';
  const activeBtnClass = 'bg-[#005A92] text-white';
  const inactiveBtnClass = 'bg-white text-gray-700 border border-gray-200 hover:bg-gray-50 cursor-pointer';
  const disabledBtnClass = 'bg-white text-gray-300 border border-gray-100 cursor-not-allowed';

  return (
    <nav className="flex items-center justify-center gap-2 mt-12" aria-label="Stránkování">
      <button
        onClick={() => onPageChange(currentPage - 1)}
        disabled={currentPage === 1}
        className={`${baseBtnClass} ${currentPage === 1 ? disabledBtnClass : inactiveBtnClass}`}
        aria-label="Předchozí stránka"
      >
        ←
      </button>

      {visiblePages.map((p, idx) =>
        p === 'ellipsis' ? (
          <span key={`ellipsis-${idx}`} className="px-2 text-gray-400">
            …
          </span>
        ) : (
          <button
            key={p}
            onClick={() => onPageChange(p)}
            className={`${baseBtnClass} ${p === currentPage ? activeBtnClass : inactiveBtnClass}`}
            aria-current={p === currentPage ? 'page' : undefined}
          >
            {p}
          </button>
        ),
      )}

      <button
        onClick={() => onPageChange(currentPage + 1)}
        disabled={currentPage === totalPages}
        className={`${baseBtnClass} ${currentPage === totalPages ? disabledBtnClass : inactiveBtnClass}`}
        aria-label="Další stránka"
      >
        →
      </button>
    </nav>
  );
}