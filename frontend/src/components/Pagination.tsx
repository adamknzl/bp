/**
 * @file  Pagination.tsx
 * @brief Page navigation control with ellipsis compression for large page counts.
 * @author Adam Kinzel (xkinzea00)
 */

interface PaginationProps {
  currentPage:  number;
  totalPages:   number;
  /** Called with the new page number when the user clicks a navigation control. */
  onPageChange: (page: number) => void;
}

/**
 * Build the sequence of page numbers and ellipsis markers to display.
 * Always shows the first and last page; compresses remaining pages with "…".
 */
function getVisiblePages(currentPage: number, totalPages: number): (number | 'ellipsis')[] {
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

  // totalPages > 1 is guaranteed here (component returns null for <= 1)
  pages.push(totalPages);

  return pages;
}

// Button style helpers

const BASE_BTN     = 'min-w-[40px] h-10 px-3 rounded-md text-sm font-medium transition-colors flex items-center justify-center';
const ACTIVE_BTN   = 'bg-brand text-white';
const INACTIVE_BTN = 'bg-white text-gray-700 border border-gray-200 hover:bg-gray-50 cursor-pointer';
const DISABLED_BTN = 'bg-white text-gray-300 border border-gray-100 cursor-not-allowed';

export default function Pagination({ currentPage, totalPages, onPageChange }: PaginationProps) {
  if (totalPages <= 1) return null;

  const visiblePages = getVisiblePages(currentPage, totalPages);

  return (
    <nav className="flex items-center justify-center gap-2 mt-12" aria-label="Stránkování">

      <button
        onClick={() => onPageChange(currentPage - 1)}
        disabled={currentPage === 1}
        className={`${BASE_BTN} ${currentPage === 1 ? DISABLED_BTN : INACTIVE_BTN}`}
        aria-label="Předchozí stránka"
      >
        ←
      </button>

      {visiblePages.map((p, idx) =>
        p === 'ellipsis' ? (
          <span key={`ellipsis-${idx}`} className="px-2 text-gray-400">…</span>
        ) : (
          <button
            key={p}
            onClick={() => onPageChange(p)}
            className={`${BASE_BTN} ${p === currentPage ? ACTIVE_BTN : INACTIVE_BTN}`}
            aria-current={p === currentPage ? 'page' : undefined}
          >
            {p}
          </button>
        ),
      )}

      <button
        onClick={() => onPageChange(currentPage + 1)}
        disabled={currentPage === totalPages}
        className={`${BASE_BTN} ${currentPage === totalPages ? DISABLED_BTN : INACTIVE_BTN}`}
        aria-label="Další stránka"
      >
        →
      </button>

    </nav>
  );
}