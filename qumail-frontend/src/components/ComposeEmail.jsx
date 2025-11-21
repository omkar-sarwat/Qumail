import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
  Box,
  Chip,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Typography,
  Divider,
  IconButton,
  Alert,
  Switch,
  FormControlLabel,
  Tooltip
} from '@mui/material';
import {
  Close as CloseIcon,
  Send as SendIcon,
  AttachFile as AttachFileIcon,
  Security as SecurityIcon,
  VpnKey as VpnKeyIcon,
  Lock as LockIcon,
  Shield as ShieldIcon,
  Info as InfoIcon
} from '@mui/icons-material';
import axios from 'axios';

const ComposeEmail = ({ open, onClose }) => {
  const [emailData, setEmailData] = useState({
    to: '',
    cc: '',
    bcc: '',
    subject: '',
    body: '',
    securityLevel: 'quantum-otp',
    priority: 'normal'
  });
  const [sending, setSending] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const securityLevels = [
    {
      id: 'quantum-otp',
      name: 'Quantum OTP (Level 1)',
      description: 'One-time pad encryption with quantum keys',
      icon: <VpnKeyIcon />,
      color: '#e91e63'
    },
    {
      id: 'quantum-aes',
      name: 'Quantum AES (Level 2)',
      description: 'AES encryption with quantum-generated keys',
      icon: <LockIcon />,
      color: '#9c27b0'
    },
    {
      id: 'pqc-kyber',
      name: 'Post-Quantum Kyber',
      description: 'Kyber key encapsulation mechanism',
      icon: <ShieldIcon />,
      color: '#3f51b5'
    }
  ];

  const handleInputChange = (field) => (event) => {
    setEmailData({ ...emailData, [field]: event.target.value });
    setError('');
  };

  const handleSend = async () => {
    if (!emailData.to || !emailData.subject || !emailData.body) {
      setError('Please fill in all required fields');
      return;
    }

    setSending(true);
    setError('');

    try {
      const response = await axios.post('http://localhost:8001/api/v1/emails/send', {
        to: emailData.to.split(',').map(email => email.trim()),
        cc: emailData.cc ? emailData.cc.split(',').map(email => email.trim()) : [],
        bcc: emailData.bcc ? emailData.bcc.split(',').map(email => email.trim()) : [],
        subject: emailData.subject,
        body: emailData.body,
        security_level: emailData.securityLevel,
        priority: emailData.priority
      }, {
        withCredentials: true
      });

      setSuccess('Email sent successfully with quantum encryption!');
      setTimeout(() => {
        onClose();
        setEmailData({
          to: '',
          cc: '',
          bcc: '',
          subject: '',
          body: '',
          securityLevel: 'quantum-otp',
          priority: 'normal'
        });
        setSuccess('');
      }, 2000);
    } catch (error) {
      console.error('Failed to send email:', error);
      setError(error.response?.data?.detail || 'Failed to send email');
    } finally {
      setSending(false);
    }
  };

  const selectedSecurity = securityLevels.find(level => level.id === emailData.securityLevel);

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="md"
      fullWidth
      PaperProps={{
        sx: { height: '80vh', display: 'flex', flexDirection: 'column' }
      }}
    >
      <DialogTitle sx={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        borderBottom: '1px solid #e0e0e0',
        backgroundColor: '#f8f9fa'
      }}>
        <Typography variant="h6" sx={{ fontWeight: 600, display: 'flex', alignItems: 'center', gap: 1 }}>
          <SendIcon color="primary" />
          Compose Quantum Email
        </Typography>
        <IconButton onClick={onClose} size="small">
          <CloseIcon />
        </IconButton>
      </DialogTitle>

      <DialogContent sx={{ flexGrow: 1, p: 0 }}>
        <Box sx={{ p: 3 }}>
          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}
          
          {success && (
            <Alert severity="success" sx={{ mb: 2 }}>
              {success}
            </Alert>
          )}

          {/* Recipients */}
          <Box sx={{ mb: 2 }}>
            <TextField
              fullWidth
              label="To"
              placeholder="recipient@example.com"
              value={emailData.to}
              onChange={handleInputChange('to')}
              required
              sx={{ mb: 1.5 }}
            />
            <TextField
              fullWidth
              label="CC"
              placeholder="cc@example.com"
              value={emailData.cc}
              onChange={handleInputChange('cc')}
              sx={{ mb: 1.5 }}
            />
            <TextField
              fullWidth
              label="BCC"
              placeholder="bcc@example.com"
              value={emailData.bcc}
              onChange={handleInputChange('bcc')}
              sx={{ mb: 1.5 }}
            />
          </Box>

          {/* Subject */}
          <TextField
            fullWidth
            label="Subject"
            placeholder="Email subject"
            value={emailData.subject}
            onChange={handleInputChange('subject')}
            required
            sx={{ mb: 2 }}
          />

          {/* Security Level Selection */}
          <Box sx={{ mb: 2, p: 2, border: '1px solid #e0e0e0', borderRadius: 1, backgroundColor: '#f8f9fa' }}>
            <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600, display: 'flex', alignItems: 'center', gap: 1 }}>
              <SecurityIcon color="primary" />
              Quantum Security Level
            </Typography>
            <FormControl fullWidth sx={{ mb: 1 }}>
              <Select
                value={emailData.securityLevel}
                onChange={handleInputChange('securityLevel')}
                displayEmpty
              >
                {securityLevels.map((level) => (
                  <MenuItem key={level.id} value={level.id}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Box sx={{ color: level.color }}>{level.icon}</Box>
                      <Box>
                        <Typography variant="body2" sx={{ fontWeight: 600 }}>
                          {level.name}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {level.description}
                        </Typography>
                      </Box>
                    </Box>
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            
            {selectedSecurity && (
              <Box sx={{ 
                p: 1.5, 
                backgroundColor: selectedSecurity.color + '10', 
                border: `1px solid ${selectedSecurity.color}30`,
                borderRadius: 1,
                display: 'flex',
                alignItems: 'center',
                gap: 1
              }}>
                <Box sx={{ color: selectedSecurity.color }}>{selectedSecurity.icon}</Box>
                <Box>
                  <Typography variant="body2" sx={{ fontWeight: 600 }}>
                    {selectedSecurity.name}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {selectedSecurity.description}
                  </Typography>
                </Box>
              </Box>
            )}
          </Box>

          {/* Priority */}
          <FormControl sx={{ mb: 2, minWidth: 150 }}>
            <InputLabel>Priority</InputLabel>
            <Select
              value={emailData.priority}
              onChange={handleInputChange('priority')}
              label="Priority"
            >
              <MenuItem value="low">Low</MenuItem>
              <MenuItem value="normal">Normal</MenuItem>
              <MenuItem value="high">High</MenuItem>
              <MenuItem value="urgent">Urgent</MenuItem>
            </Select>
          </FormControl>

          {/* Message Body */}
          <TextField
            fullWidth
            multiline
            rows={12}
            label="Message"
            placeholder="Type your quantum-secured message..."
            value={emailData.body}
            onChange={handleInputChange('body')}
            required
            sx={{ 
              mb: 2,
              '& .MuiOutlinedInput-root': {
                backgroundColor: 'white'
              }
            }}
          />

          {/* Attachments (placeholder for future implementation) */}
          <Box sx={{ 
            p: 2, 
            border: '2px dashed #e0e0e0', 
            borderRadius: 1, 
            textAlign: 'center',
            backgroundColor: '#fafafa'
          }}>
            <AttachFileIcon sx={{ color: 'text.secondary', mb: 1 }} />
            <Typography variant="body2" color="text.secondary">
              Quantum-encrypted attachments (Coming soon)
            </Typography>
          </Box>
        </Box>
      </DialogContent>

      <Divider />

      <DialogActions sx={{ p: 2, justifyContent: 'space-between', backgroundColor: '#f8f9fa' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Chip
            icon={selectedSecurity?.icon}
            label={`Security: ${selectedSecurity?.name}`}
            variant="outlined"
            size="small"
            sx={{ 
              borderColor: selectedSecurity?.color,
              color: selectedSecurity?.color
            }}
          />
          <Tooltip title="This email will be encrypted using quantum cryptography">
            <InfoIcon sx={{ color: 'text.secondary', fontSize: 16 }} />
          </Tooltip>
        </Box>
        
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button onClick={onClose} disabled={sending}>
            Cancel
          </Button>
          <Button
            variant="contained"
            onClick={handleSend}
            disabled={sending || !emailData.to || !emailData.subject || !emailData.body}
            startIcon={<SendIcon />}
            sx={{
              backgroundColor: '#1976d2',
              '&:hover': { backgroundColor: '#1565c0' }
            }}
          >
            {sending ? 'Sending...' : 'Send Quantum Email'}
          </Button>
        </Box>
      </DialogActions>
    </Dialog>
  );
};

export default ComposeEmail;