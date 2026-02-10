# Drone Operations Coordinator AI Agent

## Overview
This is a prototype AI agent that coordinates pilots, drones, and missions using Google Sheets as the source of truth.

## Features
- Pilot roster management (2-way sync with Google Sheets)
- Drone inventory tracking
- Assignment matching
- Conflict detection
- Urgent reassignment handling

## Run
pip install -r requirements.txt
uvicorn app.main:app --reload
