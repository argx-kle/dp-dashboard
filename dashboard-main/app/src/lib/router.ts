/* Hash router: works from file:// with no server. #/products?domain=hcp&flag=OVERDUE */

import { useEffect, useState } from 'react';

export type Route =
  | { view: 'exec'; params: URLSearchParams }
  | { view: 'domain'; id: string }
  | { view: 'products'; params: URLSearchParams }
  | { view: 'product'; urn: string }
  | { view: 'definitions' }
  | { view: 'notfound'; path: string };

export function parseHash(hash: string): Route {
  const raw = hash.startsWith('#') ? hash.slice(1) : hash;
  const [pathPart, queryPart = ''] = raw.split('?');
  const path = pathPart.replace(/\/+$/, '') || '/';
  const params = new URLSearchParams(queryPart);
  if (path === '/') return { view: 'exec', params };
  if (path === '/definitions') return { view: 'definitions' };
  if (path === '/products') return { view: 'products', params };
  const domain = path.match(/^\/domain\/([^/]+)$/);
  if (domain) return { view: 'domain', id: decodeURIComponent(domain[1]) };
  const product = path.match(/^\/products\/(.+)$/);
  if (product) return { view: 'product', urn: decodeURIComponent(product[1]) };
  return { view: 'notfound', path };
}

export function useRoute(): Route {
  const [route, setRoute] = useState<Route>(() => parseHash(window.location.hash));
  useEffect(() => {
    let path = window.location.hash.split('?')[0];
    const onChange = () => {
      setRoute(parseHash(window.location.hash));
      // A new view starts at the top; a new filter on the same view (e.g. the quarter) keeps the reader's place.
      const next = window.location.hash.split('?')[0];
      if (next !== path) window.scrollTo({ top: 0 });
      path = next;
    };
    window.addEventListener('hashchange', onChange);
    return () => window.removeEventListener('hashchange', onChange);
  }, []);
  return route;
}

export const href = {
  exec: (quarter?: string) => (quarter ? `#/?q=${encodeURIComponent(quarter)}` : '#/'),
  domain: (id: string) => `#/domain/${encodeURIComponent(id)}`,
  products: (params: Record<string, string | undefined> = {}) => {
    const q = new URLSearchParams();
    for (const [k, v] of Object.entries(params)) if (v) q.set(k, v);
    const s = q.toString();
    return s ? `#/products?${s}` : '#/products';
  },
  product: (urn: string) => `#/products/${encodeURIComponent(urn)}`,
  definitions: () => '#/definitions',
};
