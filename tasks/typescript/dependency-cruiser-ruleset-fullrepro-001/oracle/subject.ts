import { createRequire } from 'node:module';

/* The package under test, loaded the way a consumer loads it.
 *
 * It is installed as a directory link, which the runner treats as source and
 * loads through its own module registry; that registry does not reproduce Node's
 * CommonJS interop, so a delivery whose ES entry re-exports a CommonJS module
 * would yield an undefined import here while importing correctly under Node.
 * Resolving it through Node keeps the suite on the same footing as a consumer.
 */
const required = createRequire(import.meta.url);
let mod: unknown;
try {
  mod = required('dependency-cruiser');
} catch {
  mod = await import('dependency-cruiser');
}
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const m = mod as any;
export const format = m.format ?? m.default?.format ?? m.default;
