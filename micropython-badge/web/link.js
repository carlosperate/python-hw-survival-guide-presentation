// The deck's side of the link to the Sticky, on the Web Bluetooth API only: the port's BLE UART
// (the Nordic UART Service, its docs/bleuart.md), carrying one trigger per line.

export const SERVICE = '6e400001-b5a3-f393-e0a9-e50e24dcca9e';
const RX = '6e400002-b5a3-f393-e0a9-e50e24dcca9e'; // the Sticky receives what we write here
const TX = '6e400003-b5a3-f393-e0a9-e50e24dcca9e'; // and notifies what it sends here
export const MAX_LEN = 64; // deck/lines.py's MAX_LINE
const CHUNK = 20; // fits one write at any MTU

const encoder = new TextEncoder();
const decoder = new TextDecoder();
const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
const CONNECT_TIMEOUT_MS = 10_000;
const WRITE_TIMEOUT_MS = 2000; // a write is acknowledged in under 70 ms on a unit

// Neither gatt.connect() nor a write has a timeout of its own, and one that never settles would
// stall the link for good.
async function withTimeout(promise, ms, what) {
  let timer;
  const timeout = new Promise((_, reject) => {
    timer = setTimeout(() => reject(new Error(`${what} timed out`)), ms);
  });
  try {
    return await Promise.race([promise, timeout]);
  } finally {
    clearTimeout(timer);
  }
}

// Events: 'status' (detail: off, connecting, connected, reconnecting), 'event' (detail: the
// programme's message), 'written' (detail: {line, ms}), 'error' (detail: the error).
export class StickyLink extends EventTarget {
  constructor(bluetooth) {
    super();
    this.bluetooth = bluetooth;
    this.device = null;
    this.status = 'off';
    // One per connect(), until disconnect(): work begun for an older one sees it and stops.
    this._session = null;
    this._rx = null;
    this._received = '';
    this._pending = null;
    this._writing = false;
  }

  // In a browser this needs a user gesture: requestDevice() opens the chooser.
  async connect() {
    // Refused while active: a failure below disconnects, which would drop a working link.
    if (this.status !== 'off') throw new Error(`already ${this.status}`);
    const session = { device: null, reconnecting: false };
    this._session = session;
    this._setStatus('connecting');
    try {
      const device = await this.bluetooth.requestDevice({
        filters: [{ namePrefix: 'sticky-badge-' }], // deck/app.py's NAME_PREFIX
        optionalServices: [SERVICE],
      });
      this._live(session);
      session.device = this.device = device;
      device.addEventListener('gattserverdisconnected', () => this._reconnect(session));
      await this._setup(session);
    } catch (e) {
      // A cancelled chooser or a failed first connect: off again, nothing left open.
      if (this._session === session) this.disconnect();
      throw e;
    }
  }

  disconnect() {
    const device = this._session?.device;
    this._session = null;
    device?.gatt.disconnect();
    this._setStatus('off');
  }

  // Each trigger plays once on the Sticky, so one that can't go now is dropped rather than played
  // late: while disconnected, and when a newer one comes before it's sent. Returns whether it's
  // on its way.
  trigger(line) {
    if (encoder.encode(line).length > MAX_LEN) {
      throw new RangeError(`trigger over ${MAX_LEN} bytes: ${line}`);
    }
    if (this.status !== 'connected') return false;
    this._pending = line;
    this._flush();
    return true;
  }

  // The same steps on first connect and every reconnect: a disconnect invalidates the
  // characteristics and ends notifications.
  async _setup(session) {
    const { gatt } = session.device;
    let server;
    try {
      server = await withTimeout(gatt.connect(), CONNECT_TIMEOUT_MS, 'connect');
    } catch (e) {
      // A stale attempt mustn't drop the connection a newer connect() made to the same device.
      if (this._session === session) gatt.disconnect();
      throw e;
    }
    const service = await server.getPrimaryService(SERVICE);
    const rx = await service.getCharacteristic(RX);
    const tx = await service.getCharacteristic(TX);
    tx.addEventListener('characteristicvaluechanged', (e) => {
      if (this._session === session) this._event(e.target.value);
    });
    await tx.startNotifications();
    this._live(session);
    this._rx = rx;
    this._received = '';
    this._pending = null;
    this._setStatus('connected');
  }

  _live(session) {
    if (this._session !== session) throw new DOMException('disconnected', 'AbortError');
  }

  async _reconnect(session) {
    if (this._session !== session || session.reconnecting) return;
    session.reconnecting = true;
    this._setStatus('reconnecting');
    try {
      for (let delay = 500; this._session === session; delay = Math.min(delay * 2, 8000)) {
        try {
          await this._setup(session);
          return;
        } catch (e) {
          if (this._session !== session) return;
          this._emit('error', e);
          await sleep(delay);
        }
      }
    } finally {
      session.reconnecting = false;
    }
  }

  // One GATT operation at a time.
  async _flush() {
    if (this._writing) return;
    this._writing = true;
    let rx;
    try {
      while (this._pending !== null) {
        const line = this._pending;
        this._pending = null;
        rx = this._rx;
        const start = performance.now();
        const bytes = encoder.encode(line + '\n');
        for (let i = 0; i < bytes.length; i += CHUNK) {
          const write = rx.writeValueWithResponse(bytes.slice(i, i + CHUNK));
          await withTimeout(write, WRITE_TIMEOUT_MS, 'write');
        }
        this._emit('written', { line, ms: performance.now() - start });
      }
    } catch (e) {
      this._emit('error', e);
      // The trigger may or may not have arrived; reconnecting doesn't send it again. A write
      // that failed on a connection since replaced leaves the new one alone.
      if (rx === this._rx && this.device?.gatt.connected) this.device.gatt.disconnect();
    } finally {
      this._writing = false;
    }
  }

  // Notifications are a byte stream: emit one 'event' per complete line.
  _event(value) {
    const lines = (this._received + decoder.decode(value)).split('\n');
    this._received = lines.pop();
    for (const line of lines) this._emit('event', line);
  }

  _setStatus(status) {
    this.status = status;
    this._emit('status', status);
  }

  _emit(type, detail) {
    this.dispatchEvent(new CustomEvent(type, { detail }));
  }
}
