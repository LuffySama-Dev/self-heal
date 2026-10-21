// Copyright The OpenTelemetry Authors
// SPDX-License-Identifier: Apache-2.0
const assert = require('node:assert/strict');
const { readFileSync } = require('node:fs');
const { randomUUID } = require('node:crypto');
const { test } = require('node:test');
const vm = require('node:vm');

const source = readFileSync(`${__dirname}/charge.js`, 'utf8');

function harness(now) {
  const effects = { transactions: 0, logs: 0, spans: [] };
  const modules = {
    '@opentelemetry/api': {
      context: { active: () => ({}) },
      propagation: { getBaggage: () => undefined },
      trace: { getTracer: () => ({ startSpan: () => {
        const span = {
          attributes: {}, exceptions: [], ended: false,
          setAttributes(attributes) { Object.assign(this.attributes, attributes); },
          setAttribute(key, value) { this.attributes[key] = value; },
          recordException(error) { this.exceptions.push(error); },
          setStatus(status) { this.status = status; },
          end() { this.ended = true; }
        };
        effects.spans.push(span);
        return span;
      } }) },
      metrics: { getMeter: () => ({ createCounter: () => ({
        add: value => { effects.transactions += value; }
      }) }) },
      SpanStatusCode: { ERROR: 2 }
    },
    '@opentelemetry/semantic-conventions': { ATTR_ERROR_TYPE: 'error.type' },
    'simple-card-validator': number => ({ getCardDetails: () => ({
      valid: number !== 'invalid',
      card_type: number === 'unsupported' ? 'amex' : number === 'mastercard' ? 'mastercard' : 'visa'
    }) }),
    uuid: { v4: randomUUID },
    '@openfeature/server-sdk': { OpenFeature: {
      setProviderAndWait: async () => {},
      getClient: () => ({ getNumberValue: async () => 0, getBooleanValue: async () => false })
    } },
    '@openfeature/flagd-provider': { FlagdProvider: class {} },
    './logger': { info: () => { effects.logs++; } }
  };
  class FixedDate extends Date {
    constructor(...args) { super(...(args.length ? args : [now.getTime()])); }
    static now() { return now.getTime(); }
  }
  const sandbox = {
    module: { exports: {} }, Date: FixedDate,
    require(name) {
      assert.ok(Object.hasOwn(modules, name), `Unexpected dependency: ${name}`);
      return modules[name];
    }
  };
  vm.runInNewContext(source, sandbox, { filename: 'charge.js' });
  return { charge: sandbox.module.exports.charge, effects };
}

// Error patterns match the expiration date or the specific card-rejection reason.
const cases = [
  { name: 'current month on first day', now: [2026, 9, 1, 0, 0, 0], expiry: [2026, 10] },
  { name: 'current month on incident date', now: [2026, 9, 20, 7, 44, 0], expiry: [2026, 10] },
  { name: 'current month through final second', now: [2026, 9, 31, 23, 59, 59], expiry: [2026, 10] },
  { name: 'next month', now: [2026, 9, 20], expiry: [2026, 11] },
  { name: 'December in current year', now: [2026, 11, 31, 23, 59, 59], expiry: [2026, 12] },
  { name: 'January in next year', now: [2026, 11, 31], expiry: [2027, 1] },
  { name: 'previous month', now: [2026, 9, 20], expiry: [2026, 9], error: /expired on 9\/2026/ },
  { name: 'previous year', now: [2026, 0, 1], expiry: [2025, 12], error: /expired on 12\/2025/ },
  { name: 'first second after expiration month', now: [2026, 10, 1, 0, 0, 0], expiry: [2026, 10], error: /expired on 10\/2026/ },
  { name: 'valid Mastercard accepted', now: [2026, 9, 21], expiry: [2027, 10], number: 'mastercard' },
  { name: 'invalid card still rejected', now: [2026, 9, 20], expiry: [2026, 10], number: 'invalid', error: /Credit card info is invalid/ },
  { name: 'unsupported card still rejected', now: [2026, 9, 20], expiry: [2026, 10], number: 'unsupported', error: /Only VISA or MasterCard is accepted/ }
];

for (const entry of cases) {
  test(entry.name, async () => {
    const { charge, effects } = harness(new Date(...entry.now));
    const request = {
      creditCard: {
        creditCardNumber: entry.number || '4111111111111111', creditCardCvv: '123',
        creditCardExpirationYear: entry.expiry[0], creditCardExpirationMonth: entry.expiry[1]
      },
      amount: { units: 25, nanos: 0, currencyCode: 'USD' }
    };
    if (entry.error) {
      await assert.rejects(charge(request), entry.error);
      assert.equal(effects.transactions, 0);
      assert.equal(effects.logs, 0);
      assert.equal(effects.spans[0].status.code, 2);
      assert.equal(effects.spans[0].exceptions.length, 1);
      assert.equal(effects.spans[0].attributes['error.type'], 'Error');
    } else {
      const response = await charge(request);
      assert.equal(typeof response.transactionId, 'string');
      assert.equal(response.transactionId.length, 36);
      assert.equal(effects.transactions, 1);
      assert.equal(effects.logs, 1);
      assert.equal(effects.spans[0].attributes['demo.payment.charged'], true);
      assert.equal(effects.spans[0].exceptions.length, 0);
      assert.equal(effects.spans[0].status, undefined);
    }
    assert.equal(effects.spans.length, 1);
    assert.equal(effects.spans[0].ended, true);
  });
}
