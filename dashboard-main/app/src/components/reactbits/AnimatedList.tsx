/* react-bits AnimatedList (TS-TW). Adapted: generic items with a render prop, arrow keys only while the
   list is focused (the original intercepted Tab globally), Clear Blue scroll gradients. */

import React, { useCallback, useEffect, useRef, useState, type ReactNode, type UIEvent } from 'react';
import { motion, useInView, useReducedMotion } from 'motion/react';

interface AnimatedItemProps {
  children: ReactNode;
  delay?: number;
  index: number;
  onMouseEnter?: () => void;
}

const AnimatedItem: React.FC<AnimatedItemProps> = ({ children, delay = 0, index, onMouseEnter }) => {
  const ref = useRef<HTMLDivElement>(null);
  const inView = useInView(ref, { amount: 0.3, once: true });
  const reduced = useReducedMotion();
  return (
    <motion.div
      ref={ref}
      data-index={index}
      onMouseEnter={onMouseEnter}
      initial={reduced ? false : { y: 12, opacity: 0, scale: 0.98 }}
      animate={inView || reduced ? { y: 0, opacity: 1, scale: 1 } : { y: 12, opacity: 0, scale: 0.98 }}
      transition={{ duration: 0.28, delay, ease: 'easeOut' }}
      className="mb-0.5"
    >
      {children}
    </motion.div>
  );
};

interface AnimatedListProps<T> {
  items: T[];
  getKey: (item: T, index: number) => string;
  renderItem: (item: T, index: number, selected: boolean) => ReactNode;
  onItemSelect?: (item: T, index: number) => void;
  showGradients?: boolean;
  className?: string;
  maxHeight?: string;
  ariaLabel?: string;
  fill?: boolean;
}

export default function AnimatedList<T>({
  items,
  getKey,
  renderItem,
  onItemSelect,
  showGradients = true,
  className = '',
  maxHeight = '70vh',
  ariaLabel,
  fill = false,
}: AnimatedListProps<T>) {
  const listRef = useRef<HTMLDivElement>(null);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const [keyboardNav, setKeyboardNav] = useState(false);
  const [topGradientOpacity, setTopGradientOpacity] = useState(0);
  const [bottomGradientOpacity, setBottomGradientOpacity] = useState(1);

  const handleScroll = (e: UIEvent<HTMLDivElement>) => {
    const { scrollTop, scrollHeight, clientHeight } = e.target as HTMLDivElement;
    setTopGradientOpacity(Math.min(scrollTop / 50, 1));
    const bottomDistance = scrollHeight - (scrollTop + clientHeight);
    setBottomGradientOpacity(scrollHeight <= clientHeight ? 0 : Math.min(bottomDistance / 50, 1));
  };

  useEffect(() => {
    const el = listRef.current;
    if (el) setBottomGradientOpacity(el.scrollHeight <= el.clientHeight ? 0 : 1);
  }, [items]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLDivElement>) => {
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        setKeyboardNav(true);
        setSelectedIndex((prev) => Math.min(prev + 1, items.length - 1));
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        setKeyboardNav(true);
        setSelectedIndex((prev) => Math.max(prev - 1, 0));
      } else if (e.key === 'Enter' && selectedIndex >= 0 && selectedIndex < items.length) {
        e.preventDefault();
        onItemSelect?.(items[selectedIndex], selectedIndex);
      }
    },
    [items, selectedIndex, onItemSelect],
  );

  useEffect(() => {
    if (!keyboardNav || selectedIndex < 0 || !listRef.current) return;
    const container = listRef.current;
    const selectedItem = container.querySelector(`[data-index="${selectedIndex}"]`) as HTMLElement | null;
    if (selectedItem) {
      const extraMargin = 40;
      const itemTop = selectedItem.offsetTop;
      const itemBottom = itemTop + selectedItem.offsetHeight;
      if (itemTop < container.scrollTop + extraMargin) {
        container.scrollTo({ top: itemTop - extraMargin, behavior: 'smooth' });
      } else if (itemBottom > container.scrollTop + container.clientHeight - extraMargin) {
        container.scrollTo({ top: itemBottom - container.clientHeight + extraMargin, behavior: 'smooth' });
      }
    }
    setKeyboardNav(false);
  }, [selectedIndex, keyboardNav]);

  return (
    <div className={`relative ${fill ? 'flex min-h-0 flex-1 flex-col' : ''} ${className}`}>
      <div
        ref={listRef}
        role="list"
        aria-label={ariaLabel}
        tabIndex={0}
        onKeyDown={handleKeyDown}
        onScroll={handleScroll}
        className={`overflow-y-auto pr-1 outline-none ${fill ? 'min-h-0 flex-1 xl:max-h-none' : ''}`}
        style={{ maxHeight }}
      >
        {items.map((item, index) => (
          <AnimatedItem key={getKey(item, index)} delay={Math.min(index, 8) * 0.06} index={index} onMouseEnter={() => setSelectedIndex(index)}>
            <div role="listitem">{renderItem(item, index, selectedIndex === index)}</div>
          </AnimatedItem>
        ))}
      </div>
      {showGradients && (
        <>
          <div
            className="pointer-events-none absolute top-0 right-0 left-0 h-6 bg-gradient-to-b from-panel to-transparent transition-opacity duration-300"
            style={{ opacity: topGradientOpacity }}
          />
          <div
            className="pointer-events-none absolute right-0 bottom-0 left-0 h-12 bg-gradient-to-t from-panel to-transparent transition-opacity duration-300"
            style={{ opacity: bottomGradientOpacity }}
          />
        </>
      )}
    </div>
  );
}
