import type { Change } from '@graphql-inspector/core';

/** The machine-readable half of a change record.
 *
 * Message and reason wording are not part of the contract, so a comparison
 * reads the change type, the coordinate, the grade, and whether a reason
 * accompanies the grade at all.
 */
export interface Outlined {
  type: string;
  path: string | undefined;
  level: string;
  reason: boolean;
}

export function outline(changes: readonly Change[]): Outlined[] {
  return changes.map(change => ({
    type: change.type,
    path: change.path,
    level: change.criticality.level,
    reason: change.criticality.reason !== undefined,
  }));
}

export function changesAt(changes: readonly Change[], path: string): Change[] {
  return changes.filter(change => change.path === path);
}

export function firstChangeAt(changes: readonly Change[], path: string): Change {
  const found = changesAt(changes, path)[0];
  if (found === undefined) {
    throw new Error(`no change reported at ${path}`);
  }
  return found;
}

export function typesOf(changes: readonly Change[]): string[] {
  return changes.map(change => change.type);
}

export function pathsOf(changes: readonly Change[]): (string | undefined)[] {
  return changes.map(change => change.path);
}

export function levelsAt(changes: readonly Change[], path: string): string[] {
  return changesAt(changes, path).map(change => change.criticality.level);
}

/** Object keys as a set, so a projection can be compared by membership. */
export function keysOf(record: Record<string, unknown> | undefined): string[] {
  return Object.keys(record ?? {}).sort();
}

export function sorted(values: readonly string[]): string[] {
  return [...values].sort();
}
