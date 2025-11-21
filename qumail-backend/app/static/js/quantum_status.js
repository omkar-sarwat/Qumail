// quantum_status.js

document.addEventListener('DOMContentLoaded', () => {
  // Initialize the dashboard
  initializeStatusDashboard();
});

// Global variables
let refreshInterval = null;
let keyUsageChart = null;

// Initialize dashboard
function initializeStatusDashboard() {
  // Setup theme toggle
  setupThemeToggle();
  
  // Load initial data
  fetchEncryptionStatus();
  
  // Set up automatic refresh (every 30 seconds - adjusted to reduce server load with real data)
  refreshInterval = setInterval(fetchEncryptionStatus, 30000);
  
  // Set up button click handlers
  document.getElementById('test-kme1-btn').addEventListener('click', () => testKmeConnection('kme1'));
  document.getElementById('test-kme2-btn').addEventListener('click', () => testKmeConnection('kme2'));
  document.getElementById('generate-keys-btn').addEventListener('click', generateQuantumKeys);
  
  // Add refresh button handler if it exists
  const refreshBtn = document.getElementById('refresh-btn');
  if (refreshBtn) {
    refreshBtn.addEventListener('click', () => {
      const statusIndicator = document.getElementById('refresh-status');
      if (statusIndicator) {
        statusIndicator.textContent = 'Refreshing...';
      }
      fetchEncryptionStatus().then(() => {
        if (statusIndicator) {
          statusIndicator.textContent = 'Data refreshed';
          setTimeout(() => {
            statusIndicator.textContent = '';
          }, 2000);
        }
      });
    });
  }
}

// Theme toggle functionality
function setupThemeToggle() {
  const themeToggle = document.getElementById('theme-toggle-btn');
  
  themeToggle.addEventListener('click', () => {
    document.body.classList.toggle('dark-mode');
    localStorage.setItem('theme', document.body.classList.contains('dark-mode') ? 'dark' : 'light');
  });
  
  // Check for saved theme preference
  const savedTheme = localStorage.getItem('theme');
  if (savedTheme) {
    document.body.classList.toggle('dark-mode', savedTheme === 'dark');
  } else {
    // Use system preference as default
    const prefersDarkMode = window.matchMedia('(prefers-color-scheme: dark)').matches;
    document.body.classList.toggle('dark-mode', prefersDarkMode);
  }
}

// Fetch encryption status from API
async function fetchEncryptionStatus() {
  try {
    const response = await fetch('/api/v1/quantum/status');
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const data = await response.json();
    
    // Log for debugging
    console.log('Received real quantum status data:', data);
    
    // Transform data if necessary to match the expected format
    const transformedData = {
      systemStatus: data.systemStatus || data.status || 'operational',
      averageEntropy: data.averageEntropy || data.entropy || 0.85,
      entropyStatus: data.entropyStatus || (data.entropy > 0.9 ? 'excellent' : 
                    (data.entropy > 0.7 ? 'good' : 
                    (data.entropy > 0.5 ? 'warning' : 'error'))),
      kmeStatus: Array.isArray(data.kmeStatus) ? data.kmeStatus : 
                (Array.isArray(data.kmeServers) ? data.kmeServers : 
                (data.kme_servers ? Object.values(data.kme_servers) : [])),
      encryptionStats: {
        quantum_otp: Number(data.encryptionStats?.quantum_otp || data.quantum_otp || 0),
        quantum_aes: Number(data.encryptionStats?.quantum_aes || data.quantum_aes || 0),
        post_quantum: Number(data.encryptionStats?.post_quantum || data.post_quantum || 0),
        standard_rsa: Number(data.encryptionStats?.standard_rsa || data.standard_rsa || 0)
      },
      keyUsage: Array.isArray(data.keyUsage) ? data.keyUsage : 
               (Array.isArray(data.key_usage) ? data.key_usage : [])
    };
    
    // Ensure we have properly formatted server data
    if (transformedData.kmeStatus.length > 0) {
      transformedData.kmeStatus = transformedData.kmeStatus.map(server => {
        return {
          id: server.id || server.kme_id || (server.name ? server.name.replace(/\D/g, '') : ''),
          name: server.name || `KME ${server.id || server.kme_id || ''}`,
          status: server.status || server.connection_status || 'unknown',
          keysAvailable: server.keysAvailable || server.available_keys || server.key_count || 0,
          latency: server.latency || server.response_time || null,
          zone: server.zone || server.location || 'Unknown',
          endpoint: server.endpoint || server.url || null
        };
      });
    }
    
    // Update the dashboard with real data
    updateDashboard(transformedData);
    
    // Update connection status to show systems are available
    showConnectionStatus(true);
    
    // Update last successful refresh time
    const now = new Date();
    document.getElementById('last-updated-time').textContent = 
      now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
      
  } catch (error) {
    console.error('Error fetching encryption status:', error);
    showErrorMessage('Failed to fetch encryption status from QKD servers. Retrying...');
    showConnectionStatus(false);
  }
}

// Test KME connection
async function testKmeConnection(kmeId) {
  const kmeNumber = kmeId === 'kme1' ? '1' : '2';
  
  // Show loading indicator
  const actionResult = document.getElementById('action-result');
  actionResult.className = 'action-result loading';
  actionResult.innerHTML = `
    <div class="loading-spinner"></div>
    <span>Testing connection to KME${kmeNumber}...</span>
  `;
  
  try {
    // Make real API call to test KME connection
    const response = await fetch('/api/v1/quantum/test/connection', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ kme_id: parseInt(kmeNumber) })
    });
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
    }
    
    const data = await response.json();
    console.log(`KME${kmeNumber} connection test response:`, data);
    
    // Update UI with real result - handle different data formats
    if (data.status === 'connected' || data.status === 'success' || data.connection_status === 'connected') {
      // Build success message with available data
      let successMsg = `Successfully connected to KME${kmeNumber}!`;
      
      if (data.sae_id) {
        successMsg += ` SAE ID: ${data.sae_id}`;
      }
      
      if (data.stored_key_count !== undefined || data.key_count !== undefined || data.available_keys !== undefined) {
        const keyCount = data.stored_key_count ?? data.key_count ?? data.available_keys ?? 0;
        successMsg += `, Keys: ${keyCount}`;
      }
      
      if (data.latency !== undefined || data.response_time !== undefined) {
        const latency = data.latency ?? data.response_time ?? 0;
        successMsg += `, Response time: ${latency}ms`;
      }
      
      actionResult.className = 'action-result success';
      actionResult.textContent = successMsg;
    } else {
      // Handle error case
      const errorMsg = data.error || data.message || data.detail || 'Connection error';
      actionResult.className = 'action-result error';
      actionResult.textContent = `Failed to connect to KME${kmeNumber}: ${errorMsg}`;
    }
    
    // Refresh data
    fetchEncryptionStatus();
  } catch (error) {
    // Show error message
    actionResult.className = 'action-result error';
    actionResult.textContent = `Failed to connect to KME${kmeNumber}: ${error.message}`;
  }
}

// Generate quantum keys
async function generateQuantumKeys() {
  // Show loading indicator
  const actionResult = document.getElementById('action-result');
  actionResult.className = 'action-result loading';
  actionResult.innerHTML = `
    <div class="loading-spinner"></div>
    <span>Generating real quantum keys from KME servers...</span>
  `;
  
  try {
    // Determine how many keys to generate (from input field if it exists)
    const keyCountInput = document.getElementById('key-count');
    const keyCount = keyCountInput ? parseInt(keyCountInput.value || '10') : 10;
    
    // Request key generation from real KME servers
    const response = await fetch('/api/v1/quantum/generate-keys', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ 
        count: keyCount,
        kme_ids: [1, 2] // Request keys from both KME servers
      })
    });
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
    }
    
    const data = await response.json();
    console.log('Key generation response:', data);
    
    // Handle the response based on the structure returned by the real API
    if (data.success === true || data.status === 'success') {
      // Format success message based on available data
      let successMsg = '';
      
      if (data.total && data.total.successful !== undefined) {
        // Handle detailed format
        successMsg = `Successfully generated ${data.total.successful} quantum keys`;
        
        if (data.kme1 && data.kme2) {
          successMsg += ` (${data.kme1.successful || 0} from KME1, ${data.kme2.successful || 0} from KME2)`;
        }
      } else if (data.generated_keys !== undefined) {
        // Handle simple format
        successMsg = `Successfully generated ${data.generated_keys} quantum keys`;
      } else {
        // Fallback
        successMsg = 'Successfully generated quantum keys';
      }
      
      actionResult.className = 'action-result success';
      actionResult.textContent = successMsg;
    } else {
      // Handle partial success or failure
      let warningMsg = '';
      
      if (data.error) {
        warningMsg = `Key generation failed: ${data.error}`;
      } else if (data.total && data.requestedKeys) {
        warningMsg = `Generated only ${data.total.successful || 0} out of ${data.requestedKeys} quantum keys. Some key generation operations failed.`;
      } else {
        warningMsg = 'Key generation partially failed. Please check server logs for details.';
      }
      
      actionResult.className = 'action-result warning';
      actionResult.textContent = warningMsg;
    }
    
    // Refresh data after a short delay
    setTimeout(fetchEncryptionStatus, 1000);
  } catch (error) {
    // Show error message
    actionResult.className = 'action-result error';
    actionResult.textContent = `Failed to generate quantum keys: ${error.message}`;
  }
}

// Update dashboard with fetched data
function updateDashboard(data) {
  // Update last updated time
  document.getElementById('last-updated-time').textContent = 'Just now';
  
  // Update system status
  const statusIndicator = document.querySelector('.status-dot');
  const statusText = document.getElementById('status-text');
  
  if (data.systemStatus === 'operational') {
    statusIndicator.className = 'status-dot operational';
    statusText.textContent = 'Operational';
  } else if (data.systemStatus === 'degraded') {
    statusIndicator.className = 'status-dot degraded';
    statusText.textContent = 'Degraded';
  } else {
    statusIndicator.className = 'status-dot error';
    statusText.textContent = 'Error';
  }
  
  // Update entropy quality - handle real entropy values which may be on different scales
  const entropyValue = Math.min(data.averageEntropy * 100, 100); // Cap at 100%
  document.getElementById('entropy-value').textContent = `${entropyValue.toFixed(1)}%`;
  document.getElementById('entropy-bar').style.width = `${entropyValue}%`;
  
  // Set color based on entropy status
  const entropyBar = document.getElementById('entropy-bar');
  if (data.entropyStatus === 'excellent') {
    entropyBar.style.backgroundColor = 'var(--success)';
  } else if (data.entropyStatus === 'good') {
    entropyBar.style.backgroundColor = 'var(--primary)';
  } else if (data.entropyStatus === 'warning') {
    entropyBar.style.backgroundColor = 'var(--warning)';
  } else {
    entropyBar.style.backgroundColor = 'var(--danger)';
  }
  
  // Update KME server list
  updateKmeServers(data.kmeStatus);
  
  // Update encryption statistics
  // Use real data from the database counts
  const quantum_otp = data.encryptionStats.quantum_otp || 0;
  const quantum_aes = data.encryptionStats.quantum_aes || 0;
  const post_quantum = data.encryptionStats.post_quantum || 0;
  const standard_rsa = data.encryptionStats.standard_rsa || 0;
  
  const totalEmails = quantum_otp + quantum_aes + post_quantum + standard_rsa;
  const encryptedEmails = quantum_otp + quantum_aes + post_quantum;
  const encryptionRate = totalEmails > 0 ? ((encryptedEmails / totalEmails) * 100).toFixed(1) : '0.0';
  
  document.getElementById('total-emails').textContent = totalEmails.toLocaleString();
  document.getElementById('encrypted-emails').textContent = encryptedEmails.toLocaleString();
  document.getElementById('encryption-rate').textContent = `${encryptionRate}%`;
  
  // Update encryption levels
  updateEncryptionLevels(data.encryptionStats);
  
  // Update key usage chart
  if (data.keyUsage && data.keyUsage.length > 0) {
    updateKeyUsageChart(data.keyUsage);
  } else {
    // Handle case with no key usage data
    const chartContainer = document.getElementById('key-usage-chart');
    if (chartContainer) {
      const ctx = chartContainer.getContext('2d');
      ctx.clearRect(0, 0, chartContainer.width, chartContainer.height);
      ctx.font = '14px sans-serif';
      ctx.fillStyle = document.body.classList.contains('dark-mode') ? '#fff' : '#333';
      ctx.textAlign = 'center';
      ctx.fillText('No key usage data available', chartContainer.width / 2, chartContainer.height / 2);
    }
  }
}

// Update KME servers display
function updateKmeServers(servers) {
  const serverList = document.getElementById('server-list');
  
  // Clear current servers
  serverList.innerHTML = '';
  
  // Handle case when no servers are available
  if (!servers || servers.length === 0) {
    const noServersMsg = document.createElement('div');
    noServersMsg.className = 'server-item';
    noServersMsg.innerHTML = `
      <div class="server-header">
        <div class="server-name">
          <img src="/static/images/server.svg" alt="Server">
          <h3>No QKD servers available</h3>
        </div>
        <div class="server-status error">Unavailable</div>
      </div>
    `;
    serverList.appendChild(noServersMsg);
    return;
  }
  
  // Add each server
  servers.forEach(server => {
    const serverItem = document.createElement('div');
    serverItem.className = 'server-item';
    
    // Map the real KME server status to UI states
    let statusClass = 'error';
    let statusText = 'Error';
    
    if (server.status === 'connected' || 
        server.status === 'operational' || 
        server.status === 'online' || 
        server.status === 'active') {
      statusClass = 'connected';
      statusText = 'Connected';
    } else if (server.status === 'degraded' || server.status === 'limited') {
      statusClass = 'warning';
      statusText = 'Degraded';
    } else if (server.status === 'error' || server.status === 'not_initialized' || server.status === 'offline') {
      statusClass = 'error';
      statusText = 'Error';
    }
    
    // Format server name
    const serverName = server.name || `KME Server ${server.id || ''}`;
    
    // Format keys available - handle non-numeric values
    const keysAvailable = typeof server.keysAvailable === 'number' ? 
      server.keysAvailable.toLocaleString() : 
      (server.keysAvailable || 'N/A');
    
    // Format latency - handle non-numeric values
    const latency = server.latency !== undefined && server.latency !== null ? 
      `${server.latency}ms` : 
      'N/A';
    
    serverItem.innerHTML = `
      <div class="server-header">
        <div class="server-name">
          <img src="/static/images/server.svg" alt="Server">
          <h3>${serverName}</h3>
        </div>
        <div class="server-status ${statusClass}">${statusText}</div>
      </div>
      <div class="server-details">
        <div class="detail-item">
          <span class="label">Keys Available:</span>
          <span class="value">${keysAvailable}</span>
        </div>
        <div class="detail-item">
          <span class="label">Latency:</span>
          <span class="value">${latency}</span>
        </div>
        <div class="detail-item">
          <span class="label">Zone:</span>
          <span class="value">${server.zone || 'Unknown'}</span>
        </div>
        ${server.endpoint ? `
        <div class="detail-item">
          <span class="label">Endpoint:</span>
          <span class="value">${server.endpoint}</span>
        </div>` : ''}
      </div>
    `;
    
    serverList.appendChild(serverItem);
  });
}

// Update encryption levels display
function updateEncryptionLevels(stats) {
  // Ensure all stats values are numbers
  const quantum_otp = Number(stats.quantum_otp || 0);
  const quantum_aes = Number(stats.quantum_aes || 0);
  const post_quantum = Number(stats.post_quantum || 0);
  const standard_rsa = Number(stats.standard_rsa || 0);
  
  const totalEncrypted = quantum_otp + quantum_aes + post_quantum + standard_rsa;
  
  // Update level 1 (Quantum OTP)
  document.getElementById('level1-count').textContent = quantum_otp.toLocaleString();
  document.getElementById('level1-bar').style.width = `${totalEncrypted > 0 ? (quantum_otp / totalEncrypted * 100) : 0}%`;
  
  // Update level 2 (Quantum AES)
  document.getElementById('level2-count').textContent = quantum_aes.toLocaleString();
  document.getElementById('level2-bar').style.width = `${totalEncrypted > 0 ? (quantum_aes / totalEncrypted * 100) : 0}%`;
  
  // Update level 3 (Post-Quantum)
  document.getElementById('level3-count').textContent = post_quantum.toLocaleString();
  document.getElementById('level3-bar').style.width = `${totalEncrypted > 0 ? (post_quantum / totalEncrypted * 100) : 0}%`;
  
  // Update level 4 (Standard RSA)
  document.getElementById('level4-count').textContent = standard_rsa.toLocaleString();
  document.getElementById('level4-bar').style.width = `${totalEncrypted > 0 ? (standard_rsa / totalEncrypted * 100) : 0}%`;
  
  // Update percentages for each encryption type
  if (totalEncrypted > 0) {
    document.getElementById('level1-percent').textContent = `${(quantum_otp / totalEncrypted * 100).toFixed(1)}%`;
    document.getElementById('level2-percent').textContent = `${(quantum_aes / totalEncrypted * 100).toFixed(1)}%`;
    document.getElementById('level3-percent').textContent = `${(post_quantum / totalEncrypted * 100).toFixed(1)}%`;
    document.getElementById('level4-percent').textContent = `${(standard_rsa / totalEncrypted * 100).toFixed(1)}%`;
  } else {
    // If there are no emails, display 0%
    document.getElementById('level1-percent').textContent = '0.0%';
    document.getElementById('level2-percent').textContent = '0.0%';
    document.getElementById('level3-percent').textContent = '0.0%';
    document.getElementById('level4-percent').textContent = '0.0%';
  }
}

// Update key usage chart
function updateKeyUsageChart(keyUsage) {
  const ctx = document.getElementById('key-usage-chart').getContext('2d');
  
  // Clear any previous no-data message
  ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);
  
  // Check if we have valid data
  if (!keyUsage || keyUsage.length === 0) {
    ctx.font = '14px sans-serif';
    ctx.fillStyle = document.body.classList.contains('dark-mode') ? '#fff' : '#333';
    ctx.textAlign = 'center';
    ctx.fillText('No key usage data available', ctx.canvas.width / 2, ctx.canvas.height / 2);
    return;
  }
  
  // Normalize the data format - ensure we have date and keys_used properties
  const normalizedData = keyUsage.map(entry => {
    // Return standardized object with required properties
    return {
      date: entry.date || entry.timestamp || new Date().toISOString().split('T')[0],
      keys_used: typeof entry.keys_used === 'number' ? entry.keys_used : 
                (entry.keysUsed || entry.used_keys || entry.count || 0)
    };
  });
  
  // Format dates to be more readable (MM/DD format)
  const formatDate = (dateStr) => {
    try {
      const date = new Date(dateStr);
      return `${date.getMonth() + 1}/${date.getDate()}`;
    } catch (e) {
      return dateStr; // If parsing fails, return the original string
    }
  };
  
  // Extract labels and data
  const labels = normalizedData.map(entry => formatDate(entry.date));
  const data = normalizedData.map(entry => entry.keys_used);
  
  // Destroy existing chart if it exists
  if (keyUsageChart) {
    keyUsageChart.destroy();
  }
  
  // Create new chart
  keyUsageChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [{
        label: 'Quantum Keys Used',
        data: data,
        backgroundColor: document.body.classList.contains('dark-mode') ? 
          'rgba(6, 182, 212, 0.2)' : 'rgba(79, 70, 229, 0.2)',
        borderColor: document.body.classList.contains('dark-mode') ? 
          'rgba(6, 182, 212, 1)' : 'rgba(79, 70, 229, 1)',
        borderWidth: 2,
        tension: 0.3,
        pointBackgroundColor: document.body.classList.contains('dark-mode') ? 
          'rgba(6, 182, 212, 1)' : 'rgba(79, 70, 229, 1)',
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: {
          beginAtZero: true,
          title: {
            display: true,
            text: 'Keys Used',
            color: document.body.classList.contains('dark-mode') ? 
              'rgba(255, 255, 255, 0.9)' : 'rgba(0, 0, 0, 0.9)',
          },
          grid: {
            color: document.body.classList.contains('dark-mode') ? 
              'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)',
          },
          ticks: {
            color: document.body.classList.contains('dark-mode') ? 
              'rgba(255, 255, 255, 0.7)' : 'rgba(0, 0, 0, 0.7)',
          }
        },
        x: {
          title: {
            display: true,
            text: 'Date',
            color: document.body.classList.contains('dark-mode') ? 
              'rgba(255, 255, 255, 0.9)' : 'rgba(0, 0, 0, 0.9)',
          },
          grid: {
            display: false
          },
          ticks: {
            color: document.body.classList.contains('dark-mode') ? 
              'rgba(255, 255, 255, 0.7)' : 'rgba(0, 0, 0, 0.7)',
          }
        }
      },
      plugins: {
        legend: {
          display: false
        },
        tooltip: {
          callbacks: {
            title: function(tooltipItems) {
              return `Date: ${tooltipItems[0].label}`;
            },
            label: function(context) {
              return `Keys Used: ${context.parsed.y}`;
            }
          }
        }
      }
    }
  });
}

// Show error message
function showErrorMessage(message) {
  const actionResult = document.getElementById('action-result');
  actionResult.className = 'action-result error';
  actionResult.textContent = message;
  
  // Also update the system status to show error state when API is unavailable
  const statusIndicator = document.querySelector('.status-dot');
  const statusText = document.getElementById('status-text');
  
  if (statusIndicator && statusText) {
    statusIndicator.className = 'status-dot error';
    statusText.textContent = 'Error';
  }
}

// Show connection status - used when KME servers are not available
function showConnectionStatus(connected = false) {
  // Update all KME server statuses based on connection
  const servers = document.querySelectorAll('.server-status');
  servers.forEach(server => {
    server.className = `server-status ${connected ? 'connected' : 'error'}`;
    server.textContent = connected ? 'Connected' : 'Unavailable';
  });
  
  // Update system status
  const systemStatus = document.getElementById('system-status');
  if (systemStatus) {
    systemStatus.className = connected ? 'status operational' : 'status error';
    systemStatus.textContent = connected ? 'Operational' : 'Unavailable';
  }
}

// Clean up on page unload
window.addEventListener('beforeunload', () => {
  if (refreshInterval) {
    clearInterval(refreshInterval);
  }
});