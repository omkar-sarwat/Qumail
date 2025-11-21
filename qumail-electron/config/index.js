const defaultConfig = {
  apiBaseUrl: 'http://localhost:8000/api/v1',
  oauthRedirect: 'http://localhost:3000/auth/callback'
};

let fileOverrides = {};
try {
  // eslint-disable-next-line global-require, import/no-dynamic-require
  const maybeConfig = require('../config.production');
  fileOverrides = maybeConfig?.config || maybeConfig || {};
} catch (error) {
  fileOverrides = {};
}

module.exports = {
  ...defaultConfig,
  ...fileOverrides
};
