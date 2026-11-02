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

// Events: 'status' (detail: off, connecting, connected, reconnecting), 'event' (detail: the
// programme's message), 'written' (detail: {line, ms}), 'error' (detail: the error).
export class StickyLink extends EventTarget {
  constructor(bluetooth) {
    super();
    this.bluetooth = bluetooth;
    this.device = null;
    this.status = 'off';
    this._rx = null;
    this._received = '';
    this._pending = null;
    this._writing = false;
    this._reconnecting = false;
    this._closing = false;
    this._lost = () => this._reconnect(); // one function, so adding it again adds nothing
  }

  // In a browser this needs a user gesture: requestDevice() opens the chooser.
  async connect() {
    // Refused while active: a failure below disconnects, which would drop a working link.
    if (this.status !== 'off') throw new Error(`already ${this.status}`);
    this._closing = false;
    this._setStatus('connecting');
    try {
      this.device = await this.bluetooth.requestDevice({
        filters: [{ namePrefix: 'sticky-' }],
        optionalServices: [SERVICE],
      });
      this.device.addEventListener('gattserverdisconnected', this._lost);
      await this._setup();
    } catch (e) {
      // A cancelled chooser or a failed first connect: off again, nothing left open.
      this.disconnect();
      throw e;
    }
  }

  disconnect() {
    this._closing = true;
    this.device?.gatt.disconnect();
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
  async _setup() {
    const server = await this._connectGatt();
    const service = await server.getPrimaryService(SERVICE);
    const rx = await service.getCharacteristic(RX);
    const tx = await service.getCharacteristic(TX);
    tx.addEventListener('characteristicvaluechanged', (e) => this._event(e.target.value));
    await tx.startNotifications();
    this._rx = rx;
    this._received = '';
    this._pending = null;
    this._setStatus('connected');
  }

  // connect() has no timeout of its own, so one stuck attempt would stall the backoff loop.
  async _connectGatt() {
    let timer;
    const timeout = new Promise((_, reject) => {
      timer = setTimeout(() => reject(new Error('connect timed out')), CONNECT_TIMEOUT_MS);
    });
    try {
      return await Promise.race([this.device.gatt.connect(), timeout]);
    } catch (e) {
      this.device.gatt.disconnect();
      throw e;
    } finally {
      clearTimeout(timer);
    }
  }

  async _reconnect() {
    if (this._closing || this._reconnecting) return;
    this._reconnecting = true;
    this._setStatus('reconnecting');
    try {
      for (let delay = 500; !this._closing; delay = Math.min(delay * 2, 8000)) {
        try {
          await this._setup();
          return;
        } catch (e) {
          this._emit('error', e);
          await sleep(delay);
        }
      }
    } finally {
      this._reconnecting = false;
    }
  }

  // One GATT operation at a time.
  async _flush() {
    if (this._writing) return;
    this._writing = true;
    try {
      while (this._pending !== null) {
        const line = this._pending;
        this._pending = null;
        const start = performance.now();
        const bytes = encoder.encode(line + '\n');
        for (let i = 0; i < bytes.length; i += CHUNK) {
          await this._rx.writeValueWithResponse(bytes.slice(i, i + CHUNK));
        }
        this._emit('written', { line, ms: performance.now() - start });
      }
    } catch (e) {
      this._emit('error', e);
      // The trigger may or may not have arrived; reconnecting doesn't send it again.
      if (this.device?.gatt.connected) this.device.gatt.disconnect();
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
