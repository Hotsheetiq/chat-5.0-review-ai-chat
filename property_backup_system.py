"""
Comprehensive Property Backup System for Rent Manager API
Maintains complete backup of all 430+ properties with unit numbers
Automatically updates backup when API is accessible and checks for new addresses
"""

import os
import json
import logging
import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional
from rent_manager import RentManagerAPI

logger = logging.getLogger(__name__)

class PropertyBackupSystem:
    """
    Comprehensive backup system for all Rent Manager properties
    - Maintains complete backup of 430+ properties with unit numbers
    - Updates backup when API is accessible
    - Detects new addresses automatically
    - Provides fallback when API sessions are limited
    """
    
    def __init__(self, rent_manager: RentManagerAPI):
        self.rent_manager = rent_manager
        self.backup_file = "property_backup.json"
        self.properties_cache = []
        self.last_update = None
        self.new_addresses_detected = []
        
    async def load_backup_properties(self) -> List[Dict[str, Any]]:
        """Load properties from backup file"""
        try:
            if os.path.exists(self.backup_file):
                with open(self.backup_file, 'r') as f:
                    backup_data = json.load(f)
                    self.properties_cache = backup_data.get('properties', [])
                    self.last_update = backup_data.get('last_update')
                    logger.info(f"📋 BACKUP LOADED: {len(self.properties_cache)} properties from backup file")
                    return self.properties_cache
        except Exception as e:
            logger.error(f"Error loading backup properties: {e}")
        
        # Return hardcoded essential properties if backup file doesn't exist
        return self._get_essential_hardcoded_properties()
    
    async def update_from_api_and_detect_new(self) -> List[Dict[str, Any]]:
        """
        Update backup from API and detect new addresses
        Returns current properties (from API if available, backup otherwise)
        """
        try:
            # Try to get fresh properties from API
            if self.rent_manager:
                fresh_properties = await self.rent_manager.get_all_properties()
                
                if fresh_properties and len(fresh_properties) > 0:
                    logger.info(f"🔄 API SUCCESS: Retrieved {len(fresh_properties)} properties from Rent Manager API")
                    
                    # Check for new addresses
                    await self._detect_new_addresses(fresh_properties)
                    
                    # Update backup file
                    await self._save_backup(fresh_properties)
                    
                    self.properties_cache = fresh_properties
                    return fresh_properties
                else:
                    logger.warning("⚠️ API returned empty properties - using backup")
            
        except Exception as e:
            logger.error(f"❌ API failed: {e} - using backup properties")
        
        # Fallback to backup
        return await self.load_backup_properties()
    
    async def _detect_new_addresses(self, fresh_properties: List[Dict[str, Any]]):
        """Detect new addresses by comparing with backup"""
        if not self.properties_cache:
            await self.load_backup_properties()
        
        # Create sets of existing addresses for comparison
        backup_addresses = {prop.get('Name', '').lower().strip() 
                          for prop in self.properties_cache}
        fresh_addresses = {prop.get('Name', '').lower().strip() 
                          for prop in fresh_properties}
        
        # Find new addresses
        new_addresses = fresh_addresses - backup_addresses
        
        if new_addresses:
            self.new_addresses_detected = list(new_addresses)
            logger.info(f"🆕 NEW ADDRESSES DETECTED: {len(new_addresses)} new properties found")
            for addr in new_addresses:
                logger.info(f"   📍 NEW: {addr}")
        else:
            logger.info("✅ No new addresses detected - property database unchanged")
    
    async def _save_backup(self, properties: List[Dict[str, Any]]):
        """Save properties to backup file with timestamp"""
        try:
            backup_data = {
                'properties': properties,
                'last_update': datetime.now().isoformat(),
                'total_count': len(properties),
                'backup_created': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            with open(self.backup_file, 'w') as f:
                json.dump(backup_data, f, indent=2)
            
            logger.info(f"💾 BACKUP SAVED: {len(properties)} properties saved to {self.backup_file}")
            
        except Exception as e:
            logger.error(f"Error saving backup: {e}")
    
    def _get_essential_hardcoded_properties(self) -> List[Dict[str, Any]]:
        """
        Essential hardcoded properties as ultimate fallback
        Loads comprehensive property database from hardcoded data
        """
        try:
            from comprehensive_property_data import get_comprehensive_property_database
            comprehensive_properties = get_comprehensive_property_database()
            logger.info(f"🏢 COMPREHENSIVE FALLBACK: Loaded {len(comprehensive_properties)} properties with unit information")
            return comprehensive_properties
        except ImportError:
            logger.warning("⚠️ Comprehensive property data not available - using minimal fallback")
            # Minimal fallback if comprehensive data isn't available
            return [
                {'Name': '29 Port Richmond Avenue', 'ID': '29PRA', 'Address': '29 Port Richmond Avenue', 'Units': ['Apt 1', 'Apt 2', 'Apt 3']},
                {'Name': '31 Port Richmond Avenue', 'ID': '31PRA', 'Address': '31 Port Richmond Avenue', 'Units': ['Apt 1', 'Apt 2']},
                {'Name': '32 Port Richmond Avenue', 'ID': '32PRA', 'Address': '32 Port Richmond Avenue', 'Units': ['Apt 1', 'Apt 2', 'Apt 3']},
                {'Name': '122 Targee Street', 'ID': '122TS', 'Address': '122 Targee Street', 'Units': ['Apt 1', 'Apt 2', 'Apt 3', 'Apt 4']},
                {'Name': '124 Targee Street', 'ID': '124TS', 'Address': '124 Targee Street', 'Units': ['Apt 1', 'Apt 2', 'Apt 3']},
                {'Name': '126 Targee Street', 'ID': '126TS', 'Address': '126 Targee Street', 'Units': ['Apt 1', 'Apt 2']},
                {'Name': '128 Targee Street', 'ID': '128TS', 'Address': '128 Targee Street', 'Units': ['Apt 1', 'Apt 2', 'Apt 3']},
                {'Name': '130 Targee Street', 'ID': '130TS', 'Address': '130 Targee Street', 'Units': ['Apt 1', 'Apt 2', 'Apt 3', 'Apt 4']},
                {'Name': '132 Targee Street', 'ID': '132TS', 'Address': '132 Targee Street', 'Units': ['Apt 1', 'Apt 2']},
                {'Name': '134 Targee Street', 'ID': '134TS', 'Address': '134 Targee Street', 'Units': ['Apt 1', 'Apt 2', 'Apt 3']},
            ]
    
    async def get_all_properties_with_backup(self) -> List[Dict[str, Any]]:
        """
        Main method to get all properties with comprehensive backup system
        1. Try API first and detect new addresses
        2. Update backup if API succeeds  
        3. Fall back to backup if API fails
        4. Use hardcoded essentials as ultimate fallback
        """
        properties = await self.update_from_api_and_detect_new()
        
        if not properties:
            logger.warning("⚠️ All methods failed - using essential hardcoded properties")
            properties = self._get_essential_hardcoded_properties()
        
        return properties
    
    def get_new_addresses_report(self) -> str:
        """Get report of newly detected addresses"""
        if self.new_addresses_detected:
            return f"🆕 {len(self.new_addresses_detected)} new addresses detected: {', '.join(self.new_addresses_detected)}"
        return "✅ No new addresses detected since last update"