export type ArtifactReturnTarget = {
  pathname: string;
  search?: string;
};

type ArtifactNavigationState = {
  returnTo?: ArtifactReturnTarget;
};

function normalizeSearch(search: string | undefined): string {
  if (!search) {
    return "";
  }

  return search.startsWith("?") ? search : `?${search}`;
}

export function createSearchString(searchParams: URLSearchParams): string {
  const value = searchParams.toString();
  return value.length > 0 ? `?${value}` : "";
}

export function buildArtifactHref(target: ArtifactReturnTarget): string {
  return `${target.pathname}${normalizeSearch(target.search)}`;
}

export function buildArtifactReturnState(
  pathname: string,
  search?: string,
): ArtifactNavigationState {
  return {
    returnTo: {
      pathname,
      search: normalizeSearch(search),
    },
  };
}

export function resolveArtifactReturnHref(
  state: unknown,
  fallbackPathname: string,
): string {
  if (state !== null && typeof state === "object") {
    const candidate = (state as ArtifactNavigationState).returnTo;
    if (candidate && typeof candidate.pathname === "string" && candidate.pathname.length > 0) {
      return buildArtifactHref(candidate);
    }
  }

  return fallbackPathname;
}
