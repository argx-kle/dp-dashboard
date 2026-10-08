/* react-bits Stepper (TS-TW). Adapted into a read-only timeline: steps carry their own state
   (complete / active / inactive / skipped), no Back/Continue buttons, brand colours, labelled
   indicators. The indicator, connector and slide-in content animations are the originals. */

import React, { useLayoutEffect, useRef, useState, type ReactNode } from 'react';
import { AnimatePresence, motion, useReducedMotion, type Variants } from 'motion/react';

export type StepState = 'complete' | 'active' | 'inactive' | 'skipped';

export interface StepSpec {
  id: string;
  label: string;
  sublabel?: string;
  state: StepState;
  content: ReactNode;
}

interface StepperProps {
  steps: StepSpec[];
  initialStep?: number; // 1-based
  className?: string;
  ariaLabel?: string;
}

export default function Stepper({ steps, initialStep, className = '', ariaLabel = 'Timeline' }: StepperProps) {
  // Open on the gate being worked towards; otherwise on the last gate passed; otherwise the first.
  const activeIdx = steps.findIndex((s) => s.state === 'active');
  const lastCompleteIdx = steps.map((s) => s.state).lastIndexOf('complete');
  const defaultStep = initialStep ?? (activeIdx >= 0 ? activeIdx + 1 : lastCompleteIdx >= 0 ? lastCompleteIdx + 1 : 1);
  const [currentStep, setCurrentStep] = useState(defaultStep);
  const [direction, setDirection] = useState(0);

  const go = (step: number) => {
    if (step === currentStep) return;
    setDirection(step > currentStep ? 1 : -1);
    setCurrentStep(step);
  };

  return (
    <div className={`w-full ${className}`}>
      <ol className="flex w-full items-start" aria-label={ariaLabel}>
        {steps.map((step, index) => {
          const n = index + 1;
          return (
            <React.Fragment key={step.id}>
              <li className="flex flex-col items-center min-w-0">
                <StepIndicator n={n} state={step.state} selected={currentStep === n} label={step.label} onClick={() => go(n)} />
                <span className={`mt-2 text-small font-semibold ${currentStep === n ? 'text-ink' : 'text-ink-2'}`}>{step.label}</span>
                {step.sublabel && <span className="text-small whitespace-nowrap text-ink-3">{step.sublabel}</span>}
              </li>
              {index < steps.length - 1 && <StepConnector isComplete={steps[index + 1].state === 'complete' || steps[index + 1].state === 'skipped'} />}
            </React.Fragment>
          );
        })}
      </ol>
      <StepContentWrapper currentStep={currentStep} direction={direction} className="mt-5">
        {steps[currentStep - 1]?.content}
      </StepContentWrapper>
    </div>
  );
}

function StepContentWrapper({ currentStep, direction, children, className = '' }: { currentStep: number; direction: number; children: ReactNode; className?: string }) {
  const [parentHeight, setParentHeight] = useState(0);
  const reduced = useReducedMotion();
  return (
    <motion.div
      style={{ position: 'relative', overflow: 'hidden' }}
      animate={{ height: parentHeight }}
      transition={reduced ? { duration: 0 } : { type: 'spring', duration: 0.4 }}
      className={className}
    >
      <AnimatePresence initial={false} mode="sync" custom={direction}>
        <SlideTransition key={currentStep} direction={direction} onHeightReady={(h) => setParentHeight(h)}>
          {children}
        </SlideTransition>
      </AnimatePresence>
    </motion.div>
  );
}

function SlideTransition({ children, direction, onHeightReady }: { children: ReactNode; direction: number; onHeightReady: (h: number) => void }) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const reduced = useReducedMotion();
  useLayoutEffect(() => {
    if (containerRef.current) onHeightReady(containerRef.current.offsetHeight);
  }, [children, onHeightReady]);
  return (
    <motion.div
      ref={containerRef}
      custom={direction}
      variants={stepVariants}
      initial={reduced ? 'center' : 'enter'}
      animate="center"
      exit={reduced ? 'center' : 'exit'}
      transition={{ duration: reduced ? 0 : 0.35 }}
      style={{ position: 'absolute', left: 0, right: 0, top: 0 }}
    >
      {children}
    </motion.div>
  );
}

const stepVariants: Variants = {
  enter: (dir: number) => ({ x: dir >= 0 ? '-60%' : '60%', opacity: 0 }),
  center: { x: '0%', opacity: 1 },
  exit: (dir: number) => ({ x: dir >= 0 ? '40%' : '-40%', opacity: 0 }),
};

const indicatorVariants: Variants = {
  inactive: { scale: 1, backgroundColor: '#002834', borderColor: '#22596A', color: '#93B2BC' },
  skipped: { scale: 1, backgroundColor: 'rgba(0,26,34,0)', borderColor: '#134451', color: '#93B2BC' },
  active: { scale: 1.08, backgroundColor: '#0B3C4A', borderColor: '#D2F1FA', color: '#F2FAFC' },
  complete: { scale: 1, backgroundColor: '#74CBE5', borderColor: '#74CBE5', color: '#001A22' },
};

function StepIndicator({ n, state, selected, label, onClick }: { n: number; state: StepState; selected: boolean; label: string; onClick: () => void }) {
  return (
    <motion.button
      type="button"
      onClick={onClick}
      aria-label={`${label}: ${state}`}
      aria-current={selected ? 'step' : undefined}
      className={`relative flex h-9 w-9 cursor-pointer items-center justify-center rounded-full border-2 text-small font-semibold ${selected ? 'ring-4 ring-clear/25' : ''}`}
      animate={state}
      variants={indicatorVariants}
      initial={false}
      transition={{ duration: 0.3 }}
    >
      {state === 'complete' ? <CheckIcon className="h-4 w-4" /> : state === 'active' ? <span className="h-2.5 w-2.5 rounded-full bg-clear" /> : <span>{n}</span>}
    </motion.button>
  );
}

function StepConnector({ isComplete }: { isComplete: boolean }) {
  const lineVariants: Variants = {
    incomplete: { width: 0, backgroundColor: 'transparent' },
    complete: { width: '100%', backgroundColor: '#74CBE5' },
  };
  return (
    <div className="relative mx-1.5 mt-[17px] h-0.5 flex-1 overflow-hidden rounded bg-line" aria-hidden="true">
      <motion.div className="absolute top-0 left-0 h-full" variants={lineVariants} initial={false} animate={isComplete ? 'complete' : 'incomplete'} transition={{ duration: 0.4 }} />
    </div>
  );
}

function CheckIcon(props: React.SVGProps<SVGSVGElement>) {
  return (
    <svg {...props} fill="none" stroke="currentColor" strokeWidth={2.5} viewBox="0 0 24 24" aria-hidden="true">
      <motion.path initial={{ pathLength: 0 }} animate={{ pathLength: 1 }} transition={{ delay: 0.1, type: 'tween', ease: 'easeOut', duration: 0.3 }} strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
    </svg>
  );
}
