/** Presentation-only formatting — never recomputes metric semantics. */

export function formatCount(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "—";
  }
  return new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 }).format(value);
}

export function formatShare(share: number | null | undefined): string | null {
  if (share === null || share === undefined || Number.isNaN(share)) {
    return null;
  }
  return `${(share * 100).toFixed(share >= 0.1 || share === 0 ? 0 : 1)}%`;
}

export function groupLabel(key: string, suppressed: boolean): string {
  if (suppressed || key === "other_suppressed") {
    return "Other (suppressed)";
  }
  return key;
}
