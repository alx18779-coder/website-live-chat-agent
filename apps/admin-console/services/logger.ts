export type LogLevel = 'debug' | 'info' | 'warn' | 'error';

export interface LogMetadata {
  [key: string]: unknown;
}

interface LogConfig {
  level: LogLevel;
}

const levelWeight: Record<LogLevel, number> = {
  debug: 10,
  info: 20,
  warn: 30,
  error: 40,
};

const consoleMethod: Record<LogLevel, (message?: unknown, ...optionalParams: unknown[]) => void> = {
  debug: (...args) => (typeof console.debug === 'function' ? console.debug(...args) : console.log(...args)),
  info: (...args) => (typeof console.info === 'function' ? console.info(...args) : console.log(...args)),
  warn: (...args) => (typeof console.warn === 'function' ? console.warn(...args) : console.log(...args)),
  error: (...args) => (typeof console.error === 'function' ? console.error(...args) : console.log(...args)),
};

function isLogLevel(value: string): value is LogLevel {
  return ['debug', 'info', 'warn', 'error'].includes(value);
}

function resolveLogLevel(): LogLevel {
  const envLevel = process.env.NEXT_PUBLIC_LOG_LEVEL;
  if (envLevel && isLogLevel(envLevel.toLowerCase())) {
    return envLevel.toLowerCase() as LogLevel;
  }

  return process.env.NODE_ENV === 'production' ? 'warn' : 'info';
}

const globalConfig: LogConfig = {
  level: resolveLogLevel(),
};

function shouldLog(level: LogLevel) {
  return levelWeight[level] >= levelWeight[globalConfig.level];
}

function formatTimestamp(): string {
  try {
    return new Date().toISOString();
  } catch {
    return '';
  }
}

function formatScope(scope?: string) {
  if (!scope) {
    return '';
  }
  return `[${scope}]`;
}

function createLogMessage(scope: string | undefined, message: string) {
  const timestamp = formatTimestamp();
  const scopeLabel = formatScope(scope);
  return timestamp ? `${timestamp} ${scopeLabel} ${message}`.trim() : `${scopeLabel} ${message}`.trim();
}

export interface ScopedLogger {
  debug: (message: string, metadata?: LogMetadata) => void;
  info: (message: string, metadata?: LogMetadata) => void;
  warn: (message: string, metadata?: LogMetadata) => void;
  error: (message: string, metadata?: LogMetadata) => void;
  child: (scope: string) => ScopedLogger;
}

function log(level: LogLevel, scope: string | undefined, message: string, metadata?: LogMetadata) {
  if (!shouldLog(level)) {
    return;
  }

  const formattedMessage = createLogMessage(scope, message);

  if (metadata && Object.keys(metadata).length > 0) {
    consoleMethod[level](formattedMessage, metadata);
    return;
  }

  consoleMethod[level](formattedMessage);
}

export function createLogger(scope: string): ScopedLogger {
  const scoped = (childScope?: string): ScopedLogger => ({
    debug: (message, metadata) => log('debug', childScope, message, metadata),
    info: (message, metadata) => log('info', childScope, message, metadata),
    warn: (message, metadata) => log('warn', childScope, message, metadata),
    error: (message, metadata) => log('error', childScope, message, metadata),
    child: (nestedScope) => scoped(childScope ? `${childScope}:${nestedScope}` : nestedScope),
  });

  return scoped(scope);
}

export const logger = createLogger('admin-console');
