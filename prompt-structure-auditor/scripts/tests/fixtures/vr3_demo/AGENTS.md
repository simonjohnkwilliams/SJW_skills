# Finance Tracker - Agent Context

This document records setup steps and decisions so we don't repeat work.

## Current Focus: CSV Import
Primary flow is now CSV upload for bank transactions.

## CSV Format
- Headers: Date, Description, Money In, Money Out
- Date: DD/MM/YYYY

## Decision: Try Live Environment
Debugging invalid client_id continues. Known Issue remains.

## TrueLayer Setup
### Console Configuration
- Redirect URI: http://localhost:8080/oauth2/callback
- Copy client_id and client_secret

### Config changes for Live
- Redirect URI: http://localhost:8080/oauth2/callback
- Copy client_id and client_secret

### Live Console checklist
- Add redirect URI: http://localhost:8080/oauth2/callback
- Copy client_id and client_secret
