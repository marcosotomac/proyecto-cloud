/**
 * Polyfills for Node.js compatibility
 * Must be imported before any other modules
 */
import * as crypto from 'crypto';

// Fix for TypeORM crypto issue in Node 18
if (!globalThis.crypto) {
  (globalThis as any).crypto = {
    randomUUID: () => crypto.randomUUID(),
    getRandomValues: (arr: any) => crypto.randomFillSync(arr),
  };
}
