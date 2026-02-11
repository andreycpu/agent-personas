"""
Language pattern engine for linguistic adaptations and style modifications.
"""

from typing import Dict, List, Any, Optional, Pattern, Tuple, Callable
import re
import random
from dataclasses import dataclass, field
from enum import Enum


class LanguageLevel(Enum):
    """Levels of language complexity."""
    SIMPLE = "simple"
    STANDARD = "standard" 
    ADVANCED = "advanced"
    TECHNICAL = "technical"


class PatternCategory(Enum):
    """Categories of language patterns."""
    VOCABULARY = "vocabulary"
    SYNTAX = "syntax"
    FORMALITY = "formality"
    EMOTION = "emotion"
    EMPHASIS = "emphasis"
    POLITENESS = "politeness"


@dataclass
class LanguageRule:
    """Represents a language transformation rule."""
    name: str
    category: PatternCategory
    pattern: str  # Regex pattern to match
    replacement: str  # Replacement text
    conditions: Dict[str, Any] = field(default_factory=dict)
    priority: int = 0
    description: str = ""
    
    def matches(self, text: str) -> bool:
        """Check if this rule matches the given text."""
        return bool(re.search(self.pattern, text, re.IGNORECASE))
        
    def apply(self, text: str, context: Dict[str, Any] = None) -> str:
        """Apply this rule to transform the text."""
        if context and not self._check_conditions(context):
            return text
            
        # Apply the transformation
        result = re.sub(self.pattern, self.replacement, text, flags=re.IGNORECASE)
        return result
        
    def _check_conditions(self, context: Dict[str, Any]) -> bool:
        """Check if conditions are met for applying this rule."""
        for key, expected in self.conditions.items():
            actual = context.get(key)
            if actual != expected:
                return False
        return True


class LanguagePatternEngine:
    """
    Engine for applying language patterns and transformations.
    """
    
    def __init__(self):
        self._rules: Dict[str, LanguageRule] = {}
        self._category_rules: Dict[PatternCategory, List[str]] = {
            category: [] for category in PatternCategory
        }
        self._vocabulary_maps: Dict[str, Dict[str, List[str]]] = {}
        
        # Load default patterns
        self._load_default_patterns()
        
    def add_rule(self, rule: LanguageRule) -> None:
        """Add a language transformation rule."""
        self._rules[rule.name] = rule
        self._category_rules[rule.category].append(rule.name)
        
    def remove_rule(self, name: str) -> bool:
        """Remove a language rule."""
        if name in self._rules:
            rule = self._rules[name]
            self._category_rules[rule.category].remove(name)
            del self._rules[name]
            return True
        return False
        
    def get_rule(self, name: str) -> Optional[LanguageRule]:
        """Get a language rule by name."""
        return self._rules.get(name)
        
    def add_vocabulary_map(self, level: str, word_map: Dict[str, List[str]]) -> None:
        """
        Add vocabulary mappings for different language levels.
        
        Args:
            level: Language level (simple, standard, advanced, technical)
            word_map: Dictionary mapping base words to alternatives
        """
        self._vocabulary_maps[level] = word_map
        
    def transform_text(
        self, 
        text: str, 
        target_style: Dict[str, Any],
        context: Dict[str, Any] = None
    ) -> str:
        """
        Transform text according to target style parameters.
        
        Args:
            text: Original text
            target_style: Style parameters (formality, complexity, etc.)
            context: Additional context for transformations
            
        Returns:
            Transformed text
        """
        if context is None:
            context = {}
            
        # Merge style into context
        merged_context = {**context, **target_style}
        
        # Apply transformations in priority order
        transformed = text
        
        # 1. Vocabulary level adjustments
        vocabulary_level = target_style.get("vocabulary_level", "standard")
        transformed = self._adjust_vocabulary_level(transformed, vocabulary_level)
        
        # 2. Formality adjustments
        formality = target_style.get("formality", 0.0)
        transformed = self._adjust_formality(transformed, formality, merged_context)
        
        # 3. Sentence structure adjustments
        sentence_structure = target_style.get("sentence_structure", "mixed")
        transformed = self._adjust_sentence_structure(transformed, sentence_structure)
        
        # 4. Emotional tone adjustments
        emotiveness = target_style.get("emotiveness", 0.0)
        transformed = self._adjust_emotional_tone(transformed, emotiveness)
        
        # 5. Politeness adjustments
        politeness = target_style.get("politeness", 0.0)
        transformed = self._adjust_politeness(transformed, politeness)
        
        # 6. Apply category-specific rules
        for category in PatternCategory:
            transformed = self._apply_category_rules(transformed, category, merged_context)
            
        return transformed
        
    def _adjust_vocabulary_level(self, text: str, level: str) -> str:
        """Adjust vocabulary complexity based on target level."""
        if level not in self._vocabulary_maps:
            return text
            
        word_map = self._vocabulary_maps[level]
        words = text.split()
        
        for i, word in enumerate(words):
            # Remove punctuation for lookup
            clean_word = re.sub(r'[^\w]', '', word.lower())
            
            if clean_word in word_map:
                alternatives = word_map[clean_word]
                if alternatives:
                    replacement = random.choice(alternatives)
                    # Preserve original casing and punctuation
                    if word[0].isupper():
                        replacement = replacement.capitalize()
                    # Replace the clean word but preserve punctuation
                    words[i] = re.sub(re.escape(clean_word), replacement, word, flags=re.IGNORECASE)
                    
        return " ".join(words)
        
    def _adjust_formality(self, text: str, formality: float, context: Dict[str, Any]) -> str:
        """Adjust formality level (-1.0 to 1.0)."""
        if abs(formality) < 0.1:
            return text
            
        if formality > 0:
            # Make more formal
            context["target_formality"] = "formal"
        else:
            # Make more casual
            context["target_formality"] = "casual"
            
        return self._apply_category_rules(text, PatternCategory.FORMALITY, context)
        
    def _adjust_sentence_structure(self, text: str, structure: str) -> str:
        """Adjust sentence structure complexity."""
        if structure == "simple":
            # Break down complex sentences
            text = re.sub(r',\s*which\s+', '. This ', text)
            text = re.sub(r',\s*and\s+', '. Also, ', text)
            text = re.sub(r';\s*', '. ', text)
        elif structure == "complex":
            # Combine simple sentences (basic implementation)
            sentences = re.split(r'\.\s+', text)
            if len(sentences) > 1:
                # Randomly combine some adjacent sentences
                combined = []
                i = 0
                while i < len(sentences):
                    if i < len(sentences) - 1 and random.random() < 0.3:
                        # Combine with next sentence
                        combined.append(f"{sentences[i]}, and {sentences[i+1].lower()}")
                        i += 2
                    else:
                        combined.append(sentences[i])
                        i += 1
                text = ". ".join(combined)
                
        return text
        
    def _adjust_emotional_tone(self, text: str, emotiveness: float) -> str:
        """Adjust emotional expressiveness."""
        if abs(emotiveness) < 0.1:
            return text
            
        if emotiveness > 0:
            # Add emotional expressions
            text = self._add_emotional_expressions(text, emotiveness)
        else:
            # Remove emotional expressions
            text = self._remove_emotional_expressions(text)
            
        return text
        
    def _add_emotional_expressions(self, text: str, intensity: float) -> str:
        """Add emotional expressions to text."""
        if intensity > 0.7:
            # High intensity
            text = re.sub(r'\.', '!', text, count=int(intensity * 3))
            if random.random() < intensity:
                exclamations = [" That's amazing!", " Wow!", " Incredible!"]
                text += random.choice(exclamations)
        elif intensity > 0.3:
            # Moderate intensity
            if random.random() < intensity:
                expressions = [" :)", " That's great!", " Interesting!"]
                text += random.choice(expressions)
                
        return text
        
    def _remove_emotional_expressions(self, text: str) -> str:
        """Remove emotional expressions from text."""
        # Remove exclamation marks
        text = re.sub(r'!+', '.', text)
        
        # Remove emotional words/phrases
        emotional_patterns = [
            r'\s*:\)\s*', r'\s*:-\)\s*',
            r'\s*wow\s*', r'\s*amazing\s*', r'\s*incredible\s*',
            r'\s*awesome\s*', r'\s*fantastic\s*'
        ]
        
        for pattern in emotional_patterns:
            text = re.sub(pattern, ' ', text, flags=re.IGNORECASE)
            
        # Clean up extra spaces
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
        
    def _adjust_politeness(self, text: str, politeness: float) -> str:
        """Adjust politeness level."""
        if politeness > 0.3:
            # Add polite expressions
            if not re.search(r'\b(please|thank you|excuse me)\b', text, re.IGNORECASE):
                if random.random() < politeness:
                    polite_additions = ["Please ", "Kindly ", "If you would, "]
                    text = random.choice(polite_additions) + text.lower()
                    text = text[0].upper() + text[1:]
                    
        elif politeness < -0.3:
            # Remove overly polite expressions
            text = re.sub(r'\bplease\s+', '', text, flags=re.IGNORECASE)
            text = re.sub(r'\bkindly\s+', '', text, flags=re.IGNORECASE)
            text = re.sub(r'\bif you would,?\s*', '', text, flags=re.IGNORECASE)
            
        return text
        
    def _apply_category_rules(self, text: str, category: PatternCategory, context: Dict[str, Any]) -> str:
        """Apply all rules in a specific category."""
        rule_names = self._category_rules[category]
        
        # Sort by priority (higher first)
        rules = [self._rules[name] for name in rule_names if name in self._rules]
        rules.sort(key=lambda r: r.priority, reverse=True)
        
        transformed = text
        for rule in rules:
            if rule.matches(transformed):
                transformed = rule.apply(transformed, context)
                
        return transformed
        
    def analyze_text_complexity(self, text: str) -> Dict[str, Any]:
        """Analyze the complexity characteristics of text."""
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        words = text.split()
        
        # Calculate metrics
        avg_sentence_length = len(words) / max(len(sentences), 1)
        
        # Count complex words (more than 6 characters)
        complex_words = sum(1 for word in words if len(word) > 6)
        complex_word_ratio = complex_words / max(len(words), 1)
        
        # Count formal words
        formal_indicators = ['however', 'furthermore', 'therefore', 'consequently', 'nevertheless']
        formal_words = sum(1 for word in words if word.lower() in formal_indicators)
        
        # Count emotional expressions
        emotional_indicators = ['!', ':)', 'wow', 'amazing', 'great', 'awesome']
        emotional_expressions = sum(1 for indicator in emotional_indicators if indicator in text.lower())
        
        return {
            "total_words": len(words),
            "total_sentences": len(sentences),
            "avg_sentence_length": avg_sentence_length,
            "complex_word_ratio": complex_word_ratio,
            "formal_word_count": formal_words,
            "emotional_expression_count": emotional_expressions,
            "estimated_reading_level": self._estimate_reading_level(avg_sentence_length, complex_word_ratio)
        }
        
    def _estimate_reading_level(self, avg_sentence_length: float, complex_word_ratio: float) -> str:
        """Estimate reading level based on text metrics."""
        complexity_score = (avg_sentence_length * 0.4) + (complex_word_ratio * 60)
        
        if complexity_score < 8:
            return "elementary"
        elif complexity_score < 12:
            return "middle_school"
        elif complexity_score < 16:
            return "high_school"
        elif complexity_score < 20:
            return "college"
        else:
            return "graduate"
            
    def suggest_improvements(self, text: str, target_style: Dict[str, Any]) -> List[str]:
        """Suggest specific improvements to match target style."""
        suggestions = []
        
        analysis = self.analyze_text_complexity(text)
        
        target_formality = target_style.get("formality", 0.0)
        target_vocabulary = target_style.get("vocabulary_level", "standard")
        
        # Formality suggestions
        if target_formality > 0.5 and analysis["formal_word_count"] == 0:
            suggestions.append("Consider adding formal transition words like 'however', 'furthermore', or 'therefore'")
            
        if target_formality < -0.5 and analysis["formal_word_count"] > 2:
            suggestions.append("Consider using simpler, more casual language")
            
        # Complexity suggestions
        if target_vocabulary == "simple" and analysis["complex_word_ratio"] > 0.3:
            suggestions.append("Use simpler words - avoid words longer than 6 characters where possible")
            
        if target_vocabulary == "advanced" and analysis["complex_word_ratio"] < 0.2:
            suggestions.append("Consider using more sophisticated vocabulary")
            
        # Sentence structure suggestions
        if analysis["avg_sentence_length"] > 20:
            suggestions.append("Consider breaking down long sentences for better readability")
        elif analysis["avg_sentence_length"] < 8:
            suggestions.append("Consider combining short sentences for better flow")
            
        return suggestions
        
    def _load_default_patterns(self) -> None:
        """Load default language transformation patterns."""
        
        # Formality rules
        formal_rules = [
            LanguageRule(
                name="casual_to_formal_contractions",
                category=PatternCategory.FORMALITY,
                pattern=r"\b(can't|won't|don't|isn't|aren't)\b",
                replacement=lambda m: {
                    "can't": "cannot",
                    "won't": "will not", 
                    "don't": "do not",
                    "isn't": "is not",
                    "aren't": "are not"
                }.get(m.group(1), m.group(1)),
                conditions={"target_formality": "formal"},
                description="Expand contractions for formal writing"
            ),
            
            LanguageRule(
                name="formal_to_casual_contractions",
                category=PatternCategory.FORMALITY,
                pattern=r"\b(cannot|will not|do not|is not|are not)\b",
                replacement=lambda m: {
                    "cannot": "can't",
                    "will not": "won't",
                    "do not": "don't", 
                    "is not": "isn't",
                    "are not": "aren't"
                }.get(m.group(1), m.group(1)),
                conditions={"target_formality": "casual"},
                description="Use contractions for casual writing"
            )
        ]
        
        # Add vocabulary mappings
        simple_vocab = {
            "utilize": ["use"],
            "demonstrate": ["show"],
            "approximately": ["about"],
            "consequently": ["so"],
            "furthermore": ["also"],
            "nevertheless": ["but"]
        }
        
        advanced_vocab = {
            "use": ["utilize", "employ", "leverage"],
            "show": ["demonstrate", "illustrate", "exhibit"],
            "about": ["approximately", "roughly"],
            "so": ["consequently", "therefore", "thus"],
            "also": ["furthermore", "additionally", "moreover"],
            "but": ["however", "nevertheless", "nonetheless"]
        }
        
        self.add_vocabulary_map("simple", simple_vocab)
        self.add_vocabulary_map("advanced", advanced_vocab)
        
        # Add rules
        for rule in formal_rules:
            self.add_rule(rule)