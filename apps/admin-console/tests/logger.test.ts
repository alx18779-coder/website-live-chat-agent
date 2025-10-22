import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

type LoggerModule = typeof import('../services/logger');

const FIXED_DATE = new Date('2024-01-01T00:00:00.000Z');

async function loadLoggerModule(): Promise<LoggerModule> {
  return import('../services/logger');
}

describe('logger', () => {
  beforeEach(() => {
    vi.resetModules();
    vi.useFakeTimers();
    vi.setSystemTime(FIXED_DATE);
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
    delete process.env.NEXT_PUBLIC_LOG_LEVEL;
  });

  it('formats info logs with metadata and timestamp', async () => {
    const consoleInfo = vi.spyOn(console, 'info').mockImplementation(() => {});
    const { logger } = await loadLoggerModule();

    logger.info('fetch completed', { duration: 123 });

    expect(consoleInfo).toHaveBeenCalledWith(
      '2024-01-01T00:00:00.000Z [admin-console] fetch completed',
      { duration: 123 },
    );
  });

  it('skips debug logs when level is set to info', async () => {
    const consoleDebug = vi.spyOn(console, 'debug').mockImplementation(() => {});
    const { logger } = await loadLoggerModule();

    logger.debug('verbose event');

    expect(consoleDebug).not.toHaveBeenCalled();
  });

  it('propagates scope to child loggers', async () => {
    const consoleWarn = vi.spyOn(console, 'warn').mockImplementation(() => {});
    const { logger } = await loadLoggerModule();

    const httpLogger = logger.child('http');
    httpLogger.warn('request timeout');

    expect(consoleWarn).toHaveBeenCalledWith(
      '2024-01-01T00:00:00.000Z [admin-console:http] request timeout',
    );
  });

  it('honours the NEXT_PUBLIC_LOG_LEVEL override', async () => {
    process.env.NEXT_PUBLIC_LOG_LEVEL = 'error';

    const consoleError = vi.spyOn(console, 'error').mockImplementation(() => {});
    const consoleInfo = vi.spyOn(console, 'info').mockImplementation(() => {});

    const { createLogger } = await loadLoggerModule();
    const scopedLogger = createLogger('upload');

    scopedLogger.info('upload started');
    scopedLogger.error('upload failed');

    expect(consoleInfo).not.toHaveBeenCalled();
    expect(consoleError).toHaveBeenCalledWith(
      '2024-01-01T00:00:00.000Z [upload] upload failed',
    );
  });
});
