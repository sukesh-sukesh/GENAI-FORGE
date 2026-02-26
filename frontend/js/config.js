/**
 * InsureGuard AI - Configuration
 * API endpoints and app constants.
 */

const CONFIG = {
  API_BASE: 'http://localhost:8000/api',
  APP_NAME: 'InsureGuard AI',
  APP_VERSION: '1.0.0',
  TOKEN_KEY: 'insureguard_token',
  USER_KEY: 'insureguard_user',

  INSURANCE_CATEGORIES: {
    vehicle: { label: 'Vehicle Insurance', icon: '🚗', color: '#3b82f6' },
    health: { label: 'Health Insurance', icon: '🏥', color: '#10b981' },
    property: { label: 'Property Insurance', icon: '🏠', color: '#8b5cf6' },
  },

  STATUS_LABELS: {
    pending: 'Pending',
    under_review: 'Under Review',
    approved: 'Approved',
    rejected: 'Rejected',
    escalated: 'Escalated',
  },

  RISK_LABELS: {
    low: 'Low Risk',
    medium: 'Medium Risk',
    high: 'High Risk',
  },

  REQUIRED_DOCUMENTS: {
    vehicle: [
      { type: 'rc_copy', label: 'RC Copy', required: true },
      { type: 'driving_license', label: 'Driving License', required: true },
      { type: 'fir_copy', label: 'FIR Copy', required: true },
      { type: 'damage_images', label: 'Damage Images', required: true },
      { type: 'repair_estimate', label: 'Repair Estimate', required: true },
    ],
    health: [
      { type: 'hospital_bill', label: 'Hospital Bill', required: true },
      { type: 'discharge_summary', label: 'Discharge Summary', required: true },
      { type: 'prescription', label: 'Prescription', required: true },
      { type: 'id_proof', label: 'ID Proof', required: true },
    ],
    property: [
      { type: 'damage_images', label: 'Damage Images', required: true },
      { type: 'police_report', label: 'Police Report', required: true },
      { type: 'ownership_proof', label: 'Ownership Proof', required: true },
      { type: 'cost_estimation', label: 'Cost Estimation', required: true },
    ],
  },
};
