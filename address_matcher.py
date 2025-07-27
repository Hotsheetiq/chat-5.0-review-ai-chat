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
        Intelligent address matching - finds best property match with educated guesses.
        Uses fuzzy matching and street name intelligence.
        """
        try:
            # Ensure properties are loaded
            if not self.cache_loaded:
                await self.load_properties()
            
            if not self.properties_cache:
                logger.error("No properties available for matching")
                return None
            
            spoken_clean = spoken_address.lower().strip().replace(',', '').replace('.', '')
            logger.info(f"🔍 INTELLIGENT MATCHING: '{spoken_address}' against {len(self.properties_cache)} properties")
            
            # STEP 1: Extract street components from spoken address
            street_info = self._extract_street_components(spoken_clean)
            logger.info(f"📍 EXTRACTED COMPONENTS: {street_info}")
            
            # STEP 2: Try exact matches first
            for prop in self.properties_cache:
                prop_name = prop.get('Name', '').lower()
                
                # Check for exact street name match
                if spoken_clean in prop_name or prop_name in spoken_clean:
                    logger.info(f"✅ EXACT MATCH: '{prop.get('Name')}' for spoken '{spoken_address}'")
                    return prop
            
            # STEP 3: Try intelligent street matching with common variations
            best_matches = []
            for prop in self.properties_cache:
                prop_name = prop.get('Name', '').lower()
                score = self._calculate_match_score(street_info, prop_name)
                if score > 0:
                    best_matches.append((score, prop))
            
            # Sort by score and return best match
            if best_matches:
                best_matches.sort(reverse=True, key=lambda x: x[0])
                best_score, best_prop = best_matches[0]
                logger.info(f"🎯 BEST INTELLIGENT MATCH: '{best_prop.get('Name')}' (score: {best_score}) for '{spoken_address}'")
                return best_prop
            
            # STEP 4: Try single significant word matches as last resort
            for word in street_info.get('words', []):
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

    def _extract_street_components(self, address: str) -> Dict:
        """Extract components from a spoken address for intelligent matching"""
        import re
        
        address_lower = address.lower().strip()
        
        # Extract numbers
        numbers = re.findall(r'\b\d+\b', address)
        
        # Extract words (excluding common filler words)
        filler_words = {'i', 'think', 'its', 'it\'s', 'the', 'a', 'an', 'is', 'was', 'that', 'this'}
        words = [word for word in re.findall(r'\b[a-zA-Z]+\b', address_lower) if word not in filler_words]
        
        # Extract street-specific words (excluding directional and type words)
        directional_words = {'north', 'south', 'east', 'west', 'n', 's', 'e', 'w'}
        type_words = {'street', 'avenue', 'ave', 'road', 'rd', 'lane', 'ln', 'drive', 'dr', 'blvd', 'boulevard'}
        street_words = [word for word in words if word not in directional_words and word not in type_words]
        
        return {
            'numbers': numbers,
            'words': words,
            'street_words': street_words,
            'has_richmond': 'richmond' in address_lower,
            'has_port': 'port' in address_lower,
            'has_targee': 'targee' in address_lower,
            'original': address
        }

    def _calculate_match_score(self, street_info: Dict, property_name: str) -> float:
        """Calculate intelligent match score with numerical proximity for addresses"""
        score = 0.0
        prop_lower = property_name.lower()
        
        # ENHANCED: Numerical proximity scoring (most important for addresses)
        import re
        user_numbers = [int(n) for n in street_info['numbers']]
        prop_numbers = [int(match) for match in re.findall(r'\b\d+\b', prop_lower)]
        
        best_number_score = 0.0
        if user_numbers and prop_numbers:
            # Find closest numerical match
            for user_num in user_numbers:
                for prop_num in prop_numbers:
                    difference = abs(user_num - prop_num)
                    if difference == 0:
                        # Exact match - highest score
                        best_number_score = max(best_number_score, 10.0)
                    elif difference <= 2:
                        # Very close (within 2 numbers)
                        best_number_score = max(best_number_score, 8.0)
                    elif difference <= 5:
                        # Close (within 5 numbers)
                        best_number_score = max(best_number_score, 6.0)
                    elif difference <= 10:
                        # Moderately close (within 10 numbers)
                        best_number_score = max(best_number_score, 4.0)
                    elif difference <= 20:
                        # Somewhat close (within 20 numbers)
                        best_number_score = max(best_number_score, 2.0)
                    # Numbers >20 apart get 0 points
        
        score += best_number_score
        
        # Street word matches
        for word in street_info['street_words']:
            if word in prop_lower:
                score += 2.0 if len(word) > 4 else 1.0
        
        # Geographic area matching - prioritize similar areas
        if street_info['has_richmond'] and 'richmond' in prop_lower:
            score += 3.0  # Higher weight for same street area
        if street_info['has_port'] and 'port' in prop_lower:
            score += 2.5  # Port Richmond area
        
        # PENALTY for unrelated areas - don't suggest Targee for Richmond addresses
        if (street_info['has_richmond'] or street_info['has_port']) and 'targee' in prop_lower:
            score -= 10.0  # Strong penalty for different geographic areas
        
        if street_info['has_targee'] and 'targee' in prop_lower:
            score += 3.0  # Match Targee area
        
        # Bonus for multiple word matches within same geographic area
        word_matches = sum(1 for word in street_info['words'] if word in prop_lower)
        if word_matches >= 2:
            score += 1.5
        
        return score

    async def get_suggested_addresses(self, spoken_address: str, limit: int = 3) -> List[str]:
        """Get suggested addresses when exact match not found"""
        try:
            if not self.cache_loaded:
                await self.load_properties()
            
            if not self.properties_cache:
                return []
            
            street_info = self._extract_street_components(spoken_address)
            suggestions = []
            
            for prop in self.properties_cache:
                prop_name = prop.get('Name', '')
                if prop_name:
                    score = self._calculate_match_score(street_info, prop_name)
                    if score > 0:
                        suggestions.append((score, prop_name))
            
            # Sort by score and return top suggestions
            suggestions.sort(reverse=True, key=lambda x: x[0])
            return [name for score, name in suggestions[:limit] if score > 0]
            
        except Exception as e:
            logger.error(f"Error getting address suggestions: {e}")
            return []