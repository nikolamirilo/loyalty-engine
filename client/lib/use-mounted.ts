"use client";

import { useSyncExternalStore } from "react";

/** Nothing ever changes, so the store never notifies. */
const subscribe = () => () => {};
const onClient = () => true;
const onServer = () => false;

/**
 * False while rendering on the server and through hydration, true afterwards.
 *
 * The usual way to write this is `useState(false)` plus
 * `useEffect(() => setMounted(true), [])`, which costs an extra render pass on
 * every mount and trips `react-hooks/set-state-in-effect`. `useSyncExternalStore`
 * expresses the same thing directly: React asks for the server snapshot while
 * rendering on the server, and the client snapshot once it is running in the
 * browser.
 *
 * Use it to gate anything that needs the DOM - `createPortal`, `localStorage` -
 * so the server and the first client render agree and hydration stays quiet.
 */
export function useMounted(): boolean {
  return useSyncExternalStore(subscribe, onClient, onServer);
}
