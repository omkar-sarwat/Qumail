import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Grid, 
  Paper, 
  Typography, 
  Button, 
  List, 
  ListItem, 
  ListItemText, 
  ListItemIcon,
  Drawer,
  AppBar,
  Toolbar,
  IconButton,
  Badge,
  Avatar,
  Chip,
  Divider,
  TextField,
  InputAdornment,
  Menu,
  MenuItem
} from '@mui/material';
import {
  Inbox as InboxIcon,
  Send as SendIcon,
  Drafts as DraftsIcon,
  Delete as DeleteIcon,
  Star as StarIcon,
  StarBorder as StarBorderIcon,
  Security as SecurityIcon,
  Email as EmailIcon,
  Search as SearchIcon,
  Add as AddIcon,
  Menu as MenuIcon,
  Notifications as NotificationsIcon,
  Settings as SettingsIcon,
  Logout as LogoutIcon,
  Shield as ShieldIcon,
  Lock as LockIcon,
  VpnKey as VpnKeyIcon
} from '@mui/icons-material';
import axios from 'axios';

const drawerWidth = 280;

const Dashboard = () => {
  const [user, setUser] = useState(null);
  const [emails, setEmails] = useState([]);
  const [selectedEmail, setSelectedEmail] = useState(null);
  const [selectedFolder, setSelectedFolder] = useState('inbox');
  const [mobileOpen, setMobileOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [anchorEl, setAnchorEl] = useState(null);
  const [composeOpen, setComposeOpen] = useState(false);

  const folders = [
    { id: 'inbox', name: 'Inbox', icon: <InboxIcon />, count: 42, color: '#1976d2' },
    { id: 'sent', name: 'Sent', icon: <SendIcon />, count: 128, color: '#388e3c' },
    { id: 'drafts', name: 'Drafts', icon: <DraftsIcon />, count: 7, color: '#f57c00' },
    { id: 'starred', name: 'Starred', icon: <StarIcon />, count: 15, color: '#fbc02d' },
    { id: 'trash', name: 'Trash', icon: <DeleteIcon />, count: 23, color: '#d32f2f' },
  ];

  const quantumFeatures = [
    { id: 'quantum-otp', name: 'Quantum OTP', icon: <VpnKeyIcon />, level: 'Level 1', color: '#e91e63' },
    { id: 'quantum-aes', name: 'Quantum AES', icon: <LockIcon />, level: 'Level 2', color: '#9c27b0' },
    { id: 'pqc-kyber', name: 'Kyber KEM', icon: <ShieldIcon />, level: 'PQC', color: '#3f51b5' },
    { id: 'pqc-dilithium', name: 'Dilithium', icon: <SecurityIcon />, level: 'Signature', color: '#00bcd4' },
  ];

  useEffect(() => {
    fetchUserProfile();
    fetchEmails();
  }, [selectedFolder]);

  const fetchUserProfile = async () => {
    try {
      const response = await axios.get('http://localhost:8001/api/v1/auth/profile', {
        withCredentials: true
      });
      setUser(response.data);
    } catch (error) {
      console.error('Failed to fetch user profile:', error);
    }
  };

  const fetchEmails = async () => {
    try {
      const response = await axios.get(`http://localhost:8001/api/v1/emails/${selectedFolder}`, {
        withCredentials: true
      });
      setEmails(response.data?.emails || []);
    } catch (error) {
      console.error('Failed to fetch emails:', error);
      // Set empty emails array on error
      setEmails([]);
    }
  };

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  const handleMenuClick = (event) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const formatTimestamp = (timestamp) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffTime = Math.abs(now - date);
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    if (diffDays === 1) return 'Today';
    if (diffDays === 2) return 'Yesterday';
    if (diffDays <= 7) return `${diffDays} days ago`;
    return date.toLocaleDateString();
  };

  const getSecurityBadge = (securityLevel) => {
    const feature = quantumFeatures.find(f => f.id === securityLevel);
    if (!feature) return null;
    
    return (
      <Chip
        icon={feature.icon}
        label={feature.level}
        size="small"
        sx={{ 
          backgroundColor: feature.color + '20',
          color: feature.color,
          border: `1px solid ${feature.color}40`
        }}
      />
    );
  };

  const drawer = (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Compose Button */}
      <Box sx={{ p: 2 }}>
        <Button
          variant="contained"
          fullWidth
          startIcon={<AddIcon />}
          onClick={() => setComposeOpen(true)}
          sx={{
            backgroundColor: '#1976d2',
            '&:hover': { backgroundColor: '#1565c0' },
            borderRadius: 2,
            py: 1.5,
            fontSize: '1rem',
            fontWeight: 600
          }}
        >
          Compose
        </Button>
      </Box>

      {/* Folders */}
      <Box sx={{ px: 1 }}>
        <Typography variant="body2" sx={{ px: 2, py: 1, color: 'text.secondary', fontWeight: 600 }}>
          FOLDERS
        </Typography>
        <List dense>
          {folders.map((folder) => (
            <ListItem
              key={folder.id}
              button
              selected={selectedFolder === folder.id}
              onClick={() => setSelectedFolder(folder.id)}
              sx={{
                borderRadius: 1,
                mx: 1,
                mb: 0.5,
                '&.Mui-selected': {
                  backgroundColor: folder.color + '15',
                  '&:hover': { backgroundColor: folder.color + '20' }
                }
              }}
            >
              <ListItemIcon sx={{ color: folder.color, minWidth: 40 }}>
                {folder.icon}
              </ListItemIcon>
              <ListItemText 
                primary={folder.name}
                primaryTypographyProps={{ fontWeight: selectedFolder === folder.id ? 600 : 400 }}
              />
              {folder.count > 0 && (
                <Chip
                  label={folder.count}
                  size="small"
                  sx={{ 
                    backgroundColor: folder.color + '20',
                    color: folder.color,
                    fontWeight: 600,
                    minWidth: 32
                  }}
                />
              )}
            </ListItem>
          ))}
        </List>
      </Box>

      <Divider sx={{ my: 2 }} />

      {/* Quantum Security Features */}
      <Box sx={{ px: 1, flexGrow: 1 }}>
        <Typography variant="body2" sx={{ px: 2, py: 1, color: 'text.secondary', fontWeight: 600 }}>
          QUANTUM SECURITY
        </Typography>
        <List dense>
          {quantumFeatures.map((feature) => (
            <ListItem
              key={feature.id}
              sx={{
                borderRadius: 1,
                mx: 1,
                mb: 0.5,
                border: `1px solid ${feature.color}30`,
                backgroundColor: feature.color + '08'
              }}
            >
              <ListItemIcon sx={{ color: feature.color, minWidth: 40 }}>
                {feature.icon}
              </ListItemIcon>
              <ListItemText 
                primary={feature.name}
                secondary={feature.level}
                primaryTypographyProps={{ fontSize: '0.875rem', fontWeight: 500 }}
                secondaryTypographyProps={{ fontSize: '0.75rem', color: feature.color }}
              />
            </ListItem>
          ))}
        </List>
      </Box>

      {/* User Profile */}
      {user && (
        <Box sx={{ p: 2, borderTop: 1, borderColor: 'divider' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Avatar sx={{ bgcolor: '#1976d2' }}>
              {user.email?.charAt(0).toUpperCase()}
            </Avatar>
            <Box sx={{ flexGrow: 1 }}>
              <Typography variant="body2" sx={{ fontWeight: 600 }}>
                {user.display_name || user.email}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Quantum Secured
              </Typography>
            </Box>
          </Box>
        </Box>
      )}
    </Box>
  );

  return (
    <Box sx={{ display: 'flex', height: '100vh', backgroundColor: '#f5f5f5' }}>
      {/* App Bar */}
      <AppBar
        position="fixed"
        sx={{
          width: { sm: `calc(100% - ${drawerWidth}px)` },
          ml: { sm: `${drawerWidth}px` },
          backgroundColor: 'white',
          color: 'text.primary',
          boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
          borderBottom: '1px solid #e0e0e0'
        }}
      >
        <Toolbar>
          <IconButton
            color="inherit"
            edge="start"
            onClick={handleDrawerToggle}
            sx={{ mr: 2, display: { sm: 'none' } }}
          >
            <MenuIcon />
          </IconButton>
          
          <Typography variant="h6" sx={{ fontWeight: 700, color: '#1976d2', flexGrow: 0, mr: 3 }}>
            QuMail
          </Typography>

          {/* Search Bar */}
          <TextField
            variant="outlined"
            placeholder="Search emails..."
            size="small"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            sx={{ 
              flexGrow: 1, 
              maxWidth: 600,
              '& .MuiOutlinedInput-root': {
                backgroundColor: '#f8f9fa',
                borderRadius: 2
              }
            }}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon color="action" />
                </InputAdornment>
              ),
            }}
          />

          <Box sx={{ ml: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
            <IconButton color="inherit">
              <Badge badgeContent={4} color="error">
                <NotificationsIcon />
              </Badge>
            </IconButton>
            <IconButton color="inherit" onClick={handleMenuClick}>
              <SettingsIcon />
            </IconButton>
            <Menu
              anchorEl={anchorEl}
              open={Boolean(anchorEl)}
              onClose={handleMenuClose}
            >
              <MenuItem onClick={handleMenuClose}>
                <SettingsIcon sx={{ mr: 1 }} /> Settings
              </MenuItem>
              <MenuItem onClick={handleMenuClose}>
                <LogoutIcon sx={{ mr: 1 }} /> Logout
              </MenuItem>
            </Menu>
          </Box>
        </Toolbar>
      </AppBar>

      {/* Sidebar */}
      <Box
        component="nav"
        sx={{ width: { sm: drawerWidth }, flexShrink: { sm: 0 } }}
      >
        <Drawer
          variant="temporary"
          open={mobileOpen}
          onClose={handleDrawerToggle}
          ModalProps={{ keepMounted: true }}
          sx={{
            display: { xs: 'block', sm: 'none' },
            '& .MuiDrawer-paper': { boxSizing: 'border-box', width: drawerWidth }
          }}
        >
          {drawer}
        </Drawer>
        <Drawer
          variant="permanent"
          sx={{
            display: { xs: 'none', sm: 'block' },
            '& .MuiDrawer-paper': { 
              boxSizing: 'border-box', 
              width: drawerWidth,
              borderRight: '1px solid #e0e0e0'
            }
          }}
          open
        >
          {drawer}
        </Drawer>
      </Box>

      {/* Main Content */}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          width: { sm: `calc(100% - ${drawerWidth}px)` },
          mt: 8
        }}
      >
        <Grid container sx={{ height: 'calc(100vh - 64px)' }}>
          {/* Email List */}
          <Grid item xs={12} md={4} sx={{ borderRight: '1px solid #e0e0e0' }}>
            <Box sx={{ p: 2, borderBottom: '1px solid #e0e0e0' }}>
              <Typography variant="h6" sx={{ fontWeight: 600, display: 'flex', alignItems: 'center', gap: 1 }}>
                <InboxIcon color="primary" />
                {folders.find(f => f.id === selectedFolder)?.name || 'Inbox'}
                <Chip 
                  label={folders.find(f => f.id === selectedFolder)?.count || 0} 
                  size="small" 
                  color="primary" 
                />
              </Typography>
            </Box>
            
            <List sx={{ p: 0 }}>
              {emails.map((email) => (
                <ListItem
                  key={email.id}
                  button
                  selected={selectedEmail?.id === email.id}
                  onClick={() => setSelectedEmail(email)}
                  sx={{
                    borderBottom: '1px solid #f0f0f0',
                    '&:hover': { backgroundColor: '#f8f9fa' },
                    '&.Mui-selected': { backgroundColor: '#e3f2fd' }
                  }}
                >
                  <Box sx={{ width: '100%' }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
                      <Typography 
                        variant="body2" 
                        sx={{ 
                          fontWeight: email.isRead ? 400 : 700,
                          color: email.isRead ? 'text.secondary' : 'text.primary'
                        }}
                      >
                        {email.sender}
                      </Typography>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                        {email.isStarred && <StarIcon sx={{ color: '#fbc02d', fontSize: 16 }} />}
                        {getSecurityBadge(email.securityLevel)}
                      </Box>
                    </Box>
                    <Typography 
                      variant="body2" 
                      sx={{ 
                        fontWeight: email.isRead ? 400 : 600,
                        mb: 0.5,
                        color: email.isRead ? 'text.secondary' : 'text.primary'
                      }}
                    >
                      {email.subject}
                    </Typography>
                    <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1 }}>
                      {email.snippet}
                    </Typography>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <Box sx={{ display: 'flex', gap: 0.5 }}>
                        {email.labels?.map((label) => (
                          <Chip
                            key={label}
                            label={label}
                            size="small"
                            variant="outlined"
                            sx={{ fontSize: '0.7rem', height: 20 }}
                          />
                        ))}
                      </Box>
                      <Typography variant="caption" color="text.secondary">
                        {formatTimestamp(email.timestamp)}
                      </Typography>
                    </Box>
                  </Box>
                </ListItem>
              ))}
            </List>
          </Grid>

          {/* Email Content */}
          <Grid item xs={12} md={8}>
            {selectedEmail ? (
              <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                {/* Email Header */}
                <Paper sx={{ p: 3, borderRadius: 0, borderBottom: '1px solid #e0e0e0' }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                    <Box sx={{ flexGrow: 1 }}>
                      <Typography variant="h5" sx={{ fontWeight: 600, mb: 1 }}>
                        {selectedEmail.subject}
                      </Typography>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                        <Avatar sx={{ bgcolor: '#1976d2', width: 40, height: 40 }}>
                          {selectedEmail.sender.charAt(0).toUpperCase()}
                        </Avatar>
                        <Box>
                          <Typography variant="body1" sx={{ fontWeight: 600 }}>
                            {selectedEmail.sender}
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            {formatTimestamp(selectedEmail.timestamp)}
                          </Typography>
                        </Box>
                      </Box>
                    </Box>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      {getSecurityBadge(selectedEmail.securityLevel)}
                      <IconButton>
                        {selectedEmail.isStarred ? <StarIcon color="warning" /> : <StarBorderIcon />}
                      </IconButton>
                      <IconButton>
                        <DeleteIcon />
                      </IconButton>
                    </Box>
                  </Box>
                </Paper>

                {/* Email Body */}
                <Box sx={{ flexGrow: 1, p: 3, overflow: 'auto' }}>
                  <Typography variant="body1" sx={{ lineHeight: 1.6 }}>
                    {selectedEmail.snippet}
                  </Typography>
                </Box>
              </Box>
            ) : (
              <Box sx={{ 
                height: '100%', 
                display: 'flex', 
                alignItems: 'center', 
                justifyContent: 'center',
                flexDirection: 'column',
                gap: 2
              }}>
                <EmailIcon sx={{ fontSize: 64, color: 'text.secondary' }} />
                <Typography variant="h6" color="text.secondary">
                  Select an email to read
                </Typography>
              </Box>
            )}
          </Grid>
        </Grid>
      </Box>
    </Box>
  );
};

export default Dashboard;