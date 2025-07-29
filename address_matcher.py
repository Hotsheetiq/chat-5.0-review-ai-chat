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
    
    async def find_matching_property(self, spoken_address: str, strict_mode: bool = False) -> Dict[str, Any]:
        """
        Enhanced address matching with detailed collection fallback.
        Returns match result with suggestions for unclear addresses.
        """
        try:
            # Ensure properties are loaded
            if not self.cache_loaded:
                await self.load_properties()
            
            if not self.properties_cache:
                logger.error("No properties available for matching")
                return {"status": "error", "message": "Property database unavailable"}
            
            spoken_clean = spoken_address.lower().strip().replace(',', '').replace('.', '')
            logger.info(f"🔍 ENHANCED MATCHING: '{spoken_address}' against {len(self.properties_cache)} properties (strict_mode: {strict_mode})")
            
            # STEP 1: Try exact matches first
            exact_match = self._find_exact_match(spoken_clean)
            if exact_match:
                logger.info(f"✅ EXACT MATCH: '{exact_match.get('Name')}' for spoken '{spoken_address}'")
                return {"status": "exact_match", "property": exact_match}
            
            # STEP 2: If strict mode (after detailed collection), use intelligent fuzzy matching
            if strict_mode:
                best_match = self._find_best_fuzzy_match(spoken_clean)
                if best_match:
                    logger.info(f"🎯 INTELLIGENT MATCH: '{best_match.get('Name')}' for spoken '{spoken_address}'")
                    return {"status": "intelligent_match", "property": best_match}
                else:
                    return {"status": "no_match", "message": "No properties found matching your address"}
            
            # STEP 3: No exact match found - request detailed collection
            logger.info(f"🔍 NO EXACT MATCH - requesting detailed collection for '{spoken_address}'")
            return {
                "status": "need_detail_collection", 
                "message": "I need to get your address more clearly. Can you please say your house number one digit at a time, then spell your street name one letter at a time?"
            }
            
        except Exception as e:
            logger.error(f"Error matching address '{spoken_address}': {e}")
            return {"status": "error", "message": "Error processing your address"}
    
    def _find_exact_match(self, spoken_clean: str) -> Optional[Dict[str, Any]]:
        """Find exact matches in property database"""
        for prop in self.properties_cache:
            prop_name = prop.get('Name', '').lower()
            
            # Check for exact street name match
            if spoken_clean in prop_name or prop_name in spoken_clean:
                return prop
        return None
    
    def _find_best_fuzzy_match(self, spoken_clean: str) -> Optional[Dict[str, Any]]:
        """
        Find best fuzzy match with STREET SIMILARITY carrying most weight.
        Prioritizes street name matching over house numbers.
        """
        street_info = self._extract_street_components(spoken_clean)
        logger.info(f"📍 EXTRACTED COMPONENTS: {street_info}")
        
        best_matches = []
        for prop in self.properties_cache:
            prop_name = prop.get('Name', '').lower()
            score = self._calculate_street_priority_score(street_info, prop_name)
            if score > 0:
                best_matches.append((score, prop))
        
        # Sort by score (highest first) and return best match
        if best_matches:
            best_matches.sort(reverse=True, key=lambda x: x[0])
            best_score, best_prop = best_matches[0]
            logger.info(f"🎯 BEST INTELLIGENT MATCH: '{best_prop.get('Name')}' (score: {best_score}) for '{spoken_clean}'")
            return best_prop
        
        return None
    
    def _calculate_street_priority_score(self, street_info: Dict, prop_name: str) -> float:
        """
        Calculate match score with STREET SIMILARITY carrying most weight.
        Street name similarity = 70% weight, number proximity = 30% weight.
        """
        score = 0.0
        
        # Extract property components
        prop_parts = prop_name.split()
        
        # STREET SIMILARITY (70% weight) - most important
        street_words = street_info.get('words', [])
        for street_word in street_words:
            if len(street_word) > 2:  # Ignore very short words
                for prop_part in prop_parts:
                    if street_word in prop_part or prop_part in street_word:
                        score += 7.0  # High weight for street matches
                    elif self._are_similar_streets(street_word, prop_part):
                        score += 5.0  # Medium weight for similar streets
        
        # NUMBER PROXIMITY (30% weight) - secondary
        if 'number' in street_info and street_info['number']:
            spoken_num = street_info['number']
            for prop_part in prop_parts:
                if prop_part.isdigit():
                    prop_num = int(prop_part)
                    diff = abs(spoken_num - prop_num)
                    if diff == 0:
                        score += 3.0  # Exact number match
                    elif diff <= 5:
                        score += 2.0  # Close number match
                    elif diff <= 10:
                        score += 1.0  # Nearby number match
        
        return score
    
    def _are_similar_streets(self, word1: str, word2: str) -> bool:
        """Check if two words represent similar street names"""
        similar_pairs = [
            ('richmond', 'richmondave'),  # Richmond/Richmond Avenue
            ('port', 'portrichmond'),     # Port/Port Richmond  
            ('targee', 'targeest'),       # Targee/Targee Street
            ('midland', 'midlandave'),    # Midland/Midland Avenue
            ('victory', 'victoryblvd'),   # Victory/Victory Boulevard
            ('ave', 'avenue'),            # Avenue abbreviations
            ('st', 'street'),             # Street abbreviations
            ('blvd', 'boulevard'),        # Boulevard abbreviations
        ]
        
        word1, word2 = word1.lower(), word2.lower()
        
        for pair in similar_pairs:
            if (word1 in pair and word2 in pair) or (word2 in pair and word1 in pair):
                return True
        
        return False
    
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
        """Check if EXACT address exists in property database - not intelligent suggestions"""
        if not self.cache_loaded:
            await self.load_properties()
        
        if not self.properties_cache:
            return False
            
        # Only return True for EXACT matches, not intelligent suggestions
        address_clean = address.lower().strip().replace(',', '').replace('.', '')
        
        for prop in self.properties_cache:
            prop_name = prop.get('Name', '').lower()
            # Exact match: spoken address must match property name exactly or be contained within
            if address_clean == prop_name or address_clean in prop_name or prop_name in address_clean:
                return True
        
        return False

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