"""
Address Matching System for Real Rent Manager Properties
Matches spoken addresses to actual property database
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional
from rent_manager import RentManagerAPI

logger = logging.getLogger(__name__)

class AddressMatcher:
    """
    Matches spoken addresses to real Rent Manager properties.
    Ensures service issues are created for correct properties.
    """
    
    def __init__(self, rent_manager: RentManagerAPI):
        self.rent_manager = rent_manager
        self.properties_cache = []
        self.cache_loaded = False
    
    async def load_properties(self):
        """Load all properties from Rent Manager for matching"""
        try:
            if self.rent_manager:
                self.properties_cache = await self.rent_manager.get_all_properties()
                self.cache_loaded = True
                logger.info(f"Loaded {len(self.properties_cache)} real properties for address matching")
            else:
                logger.error("No Rent Manager connection for property loading")
        except Exception as e:
            logger.error(f"Error loading properties: {e}")
    
    async def find_matching_property(self, spoken_address: str) -> Optional[Dict[str, Any]]:
        """
        Find the best matching property for a spoken address.
        Returns property data if found, None otherwise.
        """
        try:
            # Ensure properties are loaded
            if not self.cache_loaded:
                await self.load_properties()
            
            if not self.properties_cache:
                logger.error("No properties available for matching")
                return None
            
            spoken_clean = spoken_address.lower().strip()
            logger.info(f"Matching spoken address: '{spoken_address}' against {len(self.properties_cache)} properties")
            
            # Try exact matches first
            for prop in self.properties_cache:
                prop_name = prop.get('Name', '').lower()
                
                # Check for exact street name match
                if spoken_clean in prop_name or prop_name in spoken_clean:
                    logger.info(f"✅ EXACT MATCH: '{prop.get('Name')}' for spoken '{spoken_address}'")
                    return prop
            
            # Try partial word matches
            spoken_words = [word for word in spoken_clean.split() if len(word) > 2]
            for prop in self.properties_cache:
                prop_name = prop.get('Name', '').lower()
                
                # Check if multiple words match
                matches = sum(1 for word in spoken_words if word in prop_name)
                if matches >= 2:  # At least 2 words match
                    logger.info(f"✅ PARTIAL MATCH: '{prop.get('Name')}' for spoken '{spoken_address}'")
                    return prop
            
            # Try single significant word matches
            for word in spoken_words:
                if len(word) > 4:  # Only try longer words
                    for prop in self.properties_cache:
                        prop_name = prop.get('Name', '').lower()
                        if word in prop_name:
                            logger.info(f"✅ WORD MATCH: '{prop.get('Name')}' for spoken '{spoken_address}' (word: '{word}')")
                            return prop
            
            logger.warning(f"❌ NO MATCH: '{spoken_address}' not found in property database")
            return None
            
        except Exception as e:
            logger.error(f"Error matching address '{spoken_address}': {e}")
            return None
    
    def get_property_list(self) -> List[str]:
        """Get list of all property names for reference"""
        try:
            if self.cache_loaded:
                return [prop.get('Name', '') for prop in self.properties_cache if prop.get('Name')]
            return []
        except Exception as e:
            logger.error(f"Error getting property list: {e}")
            return []
    
    async def verify_address_exists(self, address: str) -> bool:
        """Check if an address exists in the property database"""
        matching_prop = await self.find_matching_property(address)
        return matching_prop is not None