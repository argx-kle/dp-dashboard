import { useEffect, useState } from 'react';
import { SnapshotContext } from '@/lib/context';
import { FocusProvider } from '@/lib/focus';
import { loadSnapshot } from '@/lib/snapshot';
import { useRoute } from '@/lib/router';
import type { Snapshot } from '@/types/snapshot';
import Header from '@/components/Header';
import Footer from '@/components/Footer';
import ExecView from '@/views/ExecView';
import DomainView from '@/views/DomainView';
import ProductsView from '@/views/ProductsView';
import ProductView from '@/views/ProductView';
import DefinitionsView from '@/views/DefinitionsView';

export default function App() {
  const [snapshot, setSnapshot] = useState<Snapshot | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    loadSnapshot().then(setSnapshot).catch((e: Error) => setError(e.message));
  }, []);
  if (error) {
    return (
      <main className="mx-auto max-w-xl px-6 py-20">
        <h1 className="text-title font-semibold text-ink">This dashboard has no data</h1>
        <p className="mt-3 text-lead text-ink-2">{error}</p>
      </main>
    );
  }
  if (!snapshot) return <div className="min-h-screen bg-bg" aria-busy="true" />;
  return (
    <SnapshotContext.Provider value={snapshot}>
      <FocusProvider>
        <Shell />
      </FocusProvider>
    </SnapshotContext.Provider>
  );
}

function Shell() {
  const route = useRoute();
  return (
    <div className="min-h-screen">
      <Header route={route} />
      <main className="mx-auto max-w-[1440px] px-6 pt-8 lg:px-10" id="main">
        {route.view === 'exec' && <ExecView params={route.params} />}
        {route.view === 'domain' && <DomainView id={route.id} />}
        {route.view === 'products' && <ProductsView params={route.params} />}
        {route.view === 'product' && <ProductView urn={route.urn} />}
        {route.view === 'definitions' && <DefinitionsView />}
        {route.view === 'notfound' && (
          <div className="py-16">
            <h1 className="text-title font-semibold text-ink">Nothing at this address</h1>
            <p className="mt-2 text-lead text-ink-2">
              <code className="text-ink-3">{route.path}</code> is not a view. <a href="#/">Back to the executive overview</a>.
            </p>
          </div>
        )}
        <Footer />
      </main>
    </div>
  );
}
