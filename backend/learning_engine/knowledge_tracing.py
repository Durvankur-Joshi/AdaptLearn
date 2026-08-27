import math
from typing import Dict, Any, Optional

def bkt_update(p_know: float, correct: bool, p_slip: float = 0.1, 
               p_guess: float = 0.2, p_learn: float = 0.15) -> float:
    """
    Bayesian Knowledge Tracing update
    
    Args:
        p_know: Current probability student knows the skill
        correct: Whether answer was correct
        p_slip: Probability of slip (wrong despite knowing)
        p_guess: Probability of guess (correct despite not knowing)
        p_learn: Probability of learning after opportunity
    
    Returns:
        Updated probability of knowledge
    """
    if correct:
        numerator = p_know * (1 - p_slip)
        denominator = numerator + (1 - p_know) * p_guess
    else:
        numerator = p_know * p_slip
        denominator = numerator + (1 - p_know) * (1 - p_guess)
    
    posterior = numerator / denominator if denominator != 0 else p_know
    
    # Learning transition
    updated = posterior + (1 - posterior) * p_learn
    
    return min(1.0, max(0.0, updated))

def irt_probability(theta: float, b: float, a: float = 1.0) -> float:
    """
    Item Response Theory 2PL model
    
    Args:
        theta: Student ability
        b: Item difficulty
        a: Item discrimination
    
    Returns:
        Probability of correct response
    """
    return 1 / (1 + math.exp(-a * (theta - b)))

def update_theta(theta: float, correct: bool, b: float, 
                 a: float = 1.0, lr: float = 0.4) -> float:
    """
    Update theta using gradient of log-likelihood
    
    Args:
        theta: Current ability estimate
        correct: Whether answer was correct
        b: Item difficulty
        a: Item discrimination
        lr: Learning rate
    
    Returns:
        Updated ability estimate
    """
    predicted = irt_probability(theta, b, a)
    actual = 1.0 if correct else 0.0
    
    # Simple gradient update
    theta = theta + lr * (actual - predicted)
    
    return theta

def classify_behavior(correct: bool, time_taken: float, 
                      estimated_time: int) -> str:
    """
    Classify student behavior based on correctness and time
    
    Args:
        correct: Whether answer was correct
        time_taken: Actual time taken in seconds
        estimated_time: Expected time in seconds
    
    Returns:
        Behavior classification
    """
    if estimated_time <= 0:
        return "normal_correct" if correct else "confused"
        
    ratio = time_taken / estimated_time
    
    if correct:
        if ratio < 0.7:
            return "strong_mastery"
        elif ratio > 1.3:
            return "weak_mastery"
        else:
            return "normal_correct"
    else:
        if ratio < 0.7:
            return "guessing"
        else:
            return "confused"

def update_mastery_from_behavior(score: float, behavior: str) -> float:
    """
    Update mastery score based on behavior classification
    
    Args:
        score: Current mastery score
        behavior: Behavior classification
    
    Returns:
        Updated mastery score
    """
    weights = {
        "strong_mastery": 2.0,
        "normal_correct": 1.0,
        "weak_mastery": 0.5,
        "guessing": -1.0,
        "confused": -0.5,
    }
    
    # Convert to 0-1 range update
    update = weights.get(behavior, 0) * 0.05
    return min(1.0, max(0.0, score + update))

def classify_error_type(question: Dict[str, Any], answer: int, 
                       time_taken: float, atom_name: str) -> Optional[str]:
    """
    Classify error type based on question, answer, and timing
    
    Args:
        question: Question dictionary
        answer: Selected answer index
        time_taken: Time taken in seconds
        atom_name: Name of the teaching atom
    
    Returns:
        Error type string or None if correct
    """
    correct = (answer == question.get('correct_index'))
    estimated = question.get('estimated_time', 60)
    time_ratio = time_taken / estimated if estimated > 0 else 1.0
    
    if not correct:
        # Fast wrong = guessing
        if time_ratio < 0.5:
            return "guessing"
        
        # Slow wrong on easy question = conceptual
        if question.get('difficulty') == 'easy' and time_ratio > 1.3:
            return "conceptual"
        
        # Check for structural errors
        q_text = question.get('question', '').lower()
        if any(term in q_text for term in ['mapping', 'between', 'versus', 'vs', 'relationship']):
            return "structural"
        
        # Check if it's a factual error
        if question.get('difficulty') == 'easy':
            return "factual"
        
        # Default
        return "procedural"
    
    # Even correct answers can indicate issues
    if correct and time_ratio < 0.3:
        return "attentional"
    
    return None


# backend/learning_engine/knowledge_tracing.py

def classify_error_type(question, answer, time_taken, atom_name):
    """Classify error type based on question, answer, and timing"""
    if answer == -1:  # No answer
        return "no_answer"
    
    estimated = question.get('estimated_time', 60)
    time_ratio = time_taken / estimated if estimated > 0 else 1.0
    
    # Fast wrong = guessing
    if time_ratio < 0.5:
        return "guessing"
    
    # Slow wrong on easy question = conceptual
    if question.get('difficulty') == 'easy' and time_ratio > 1.3:
        return "conceptual"
    
    # Check for structural errors based on question content
    q_text = question.get('question', '').lower()
    if any(term in q_text for term in ['compare', 'contrast', 'difference', 'relationship']):
        return "structural"
    
    # Check if it's a factual error
    if question.get('difficulty') == 'easy':
        return "factual"
    
    # Default
    return "procedural"

def bkt_update(p_know, correct, p_slip=0.1, p_guess=0.2, p_learn=0.15):
    """Bayesian Knowledge Tracing update"""
    if correct:
        numerator = p_know * (1 - p_slip)
        denominator = numerator + (1 - p_know) * p_guess
    else:
        numerator = p_know * p_slip
        denominator = numerator + (1 - p_know) * (1 - p_guess)
    
    posterior = numerator / denominator if denominator != 0 else p_know
    
    # Learning transition
    updated = posterior + (1 - posterior) * p_learn
    
    return min(1.0, max(0.0, updated))

def update_theta(theta, correct, b=0.0, a=1.0, lr=0.4):
    """Update IRT theta parameter"""
    import math
    
    # IRT probability
    def irt_prob(theta, b, a):
        return 1 / (1 + math.exp(-a * (theta - b)))
    
    predicted = irt_prob(theta, b, a)
    actual = 1.0 if correct else 0.0
    
    # Gradient update
    theta = theta + lr * (actual - predicted)
    
    return theta



# backend/learning_engine/knowledge_tracing.py - Enhanced version

import math
import numpy as np
from typing import Dict, Any, Optional, Tuple

def calculate_updated_mastery(
    current_mastery: float,
    current_theta: float,
    question: Dict[str, Any],
    correct: bool,
    time_taken: float,
    error_type: Optional[str]
) -> Tuple[float, float, Dict[str, float]]:
    """
    Real-time mastery estimation after every answer
    
    Args:
        current_mastery: Current mastery score (0-1)
        current_theta: Current ability parameter
        question: Question dictionary with difficulty, estimated_time
        correct: Whether answer was correct
        time_taken: Time taken in seconds
        error_type: Classified error type or None if correct
    
    Returns:
        Tuple of (new_mastery, new_theta, metrics)
    """
    # Extract question parameters
    difficulty = question.get('difficulty', 'medium')
    estimated_time = question.get('estimated_time', 60)
    cognitive = question.get('cognitive_operation', 'recall')
    
    # Map difficulty to item parameter b (IRT difficulty)
    difficulty_map = {
        'easy': -1.0,
        'medium': 0.0,
        'hard': 1.0
    }
    b = difficulty_map.get(difficulty, 0.0)
    
    # Map cognitive to discrimination a (IRT discrimination)
    cognitive_map = {
        'recall': 0.8,
        'apply': 1.2,
        'analyze': 1.5
    }
    a = cognitive_map.get(cognitive, 1.0)
    
    # Calculate time ratio (normalized)
    time_ratio = time_taken / estimated_time if estimated_time > 0 else 1.0
    
    # 1. Update IRT theta (ability)
    new_theta = update_theta_weighted(
        current_theta, correct, b, a, 
        time_ratio, error_type
    )
    
    # 2. Update mastery based on multiple factors
    mastery_update = calculate_mastery_update(
        current_mastery, correct, time_ratio, 
        error_type, difficulty
    )
    
    new_mastery = min(1.0, max(0.0, current_mastery + mastery_update))
    
    # 3. Calculate performance metrics
    metrics = {
        'theta_change': new_theta - current_theta,
        'mastery_change': mastery_update,
        'confidence': calculate_confidence(correct, time_ratio, error_type),
        'learning_rate': mastery_update / 0.1,  # Normalized learning rate
        'performance_quality': calculate_performance_quality(correct, time_ratio, error_type)
    }
    
    return new_mastery, new_theta, metrics


def update_theta_weighted(
    theta: float,
    correct: bool,
    b: float,
    a: float,
    time_ratio: float,
    error_type: Optional[str],
    base_lr: float = 0.4
) -> float:
    """
    Update theta with time and error-type weighting
    """
    # IRT probability
    prob_correct = 1 / (1 + math.exp(-a * (theta - b)))
    
    # Actual outcome (continuous for weighted updates)
    actual = 1.0 if correct else 0.0
    
    # Calculate confidence weight based on time
    if correct:
        # Fast correct = high confidence
        confidence_weight = min(1.5, 1.0 / max(0.3, time_ratio))
    else:
        # Slow wrong = low confidence, fast wrong = guessing
        if time_ratio < 0.5:  # Guessing
            confidence_weight = 0.3
        elif time_ratio > 1.5:  # Struggling
            confidence_weight = 0.7
        else:
            confidence_weight = 0.5
    
    # Adjust learning rate based on error type
    error_multipliers = {
        'guessing': 0.3,      # Less update from guesses
        'attentional': 0.6,    # Moderate update
        'factual': 0.8,        # Stronger update
        'procedural': 0.9,     # Strong update
        'conceptual': 1.2,     # Very strong update (conceptual errors matter)
        'structural': 1.1,      # Strong update
        None: 1.0               # Normal for correct
    }
    
    error_mult = error_multipliers.get(error_type, 1.0)
    
    # Apply weighted update
    adjusted_lr = base_lr * confidence_weight * error_mult
    theta_update = adjusted_lr * (actual - prob_correct)
    
    return theta + theta_update


def calculate_mastery_update(
    current_mastery: float,
    correct: bool,
    time_ratio: float,
    error_type: Optional[str],
    difficulty: str
) -> float:
    """
    Calculate mastery update with nuanced factors
    """
    # Base update amount
    base_update = 0.05
    
    # Difficulty multiplier
    difficulty_multipliers = {
        'easy': 0.7,    # Less impact from easy questions
        'medium': 1.0,
        'hard': 1.3     # More impact from hard questions
    }
    diff_mult = difficulty_multipliers.get(difficulty, 1.0)
    
    if correct:
        # Time factor for correct answers
        if time_ratio < 0.7:  # Fast correct
            time_factor = 1.3
        elif time_ratio < 1.0:  # Normal
            time_factor = 1.0
        else:  # Slow but correct
            time_factor = 0.7
        
        # Mastery increases less as it approaches 1.0
        ceiling_factor = (1.0 - current_mastery) * 2
        
        update = base_update * diff_mult * time_factor * ceiling_factor
        
    else:  # Incorrect
        # Different impacts based on error type
        error_impacts = {
            'guessing': -0.02,      # Small penalty - just guessing
            'attentional': -0.03,    # Small penalty - careless
            'factual': -0.06,        # Moderate - missing facts
            'procedural': -0.08,     # Significant - don't know process
            'conceptual': -0.12,     # Severe - fundamental misunderstanding
            'structural': -0.10      # Severe - can't see relationships
        }
        
        update = error_impacts.get(error_type, -0.05)
        
        # Additional time factor for wrong answers
        if time_ratio > 1.5:  # Very slow wrong = struggling
            update *= 1.3
        elif time_ratio < 0.5:  # Fast wrong = guessing
            update *= 0.7
    
    return update


def calculate_confidence(correct: bool, time_ratio: float, error_type: Optional[str]) -> float:
    """
    Calculate confidence in the response (0-1)
    """
    if correct:
        # Higher confidence for fast correct answers
        confidence = min(1.0, 1.2 - time_ratio * 0.3)
    else:
        # Lower confidence for wrong answers, especially fast wrong
        if error_type == 'guessing':
            confidence = 0.1
        elif error_type == 'attentional':
            confidence = 0.3
        elif time_ratio < 0.5:
            confidence = 0.2
        elif time_ratio > 1.5:
            confidence = 0.5  # At least tried
        else:
            confidence = 0.4
    
    return max(0.1, min(1.0, confidence))


def calculate_performance_quality(correct: bool, time_ratio: float, error_type: Optional[str]) -> float:
    """
    Calculate overall performance quality (-1 to 1)
    """
    if correct:
        quality = 1.0 - abs(1.0 - time_ratio) * 0.5
    else:
        if error_type == 'guessing':
            quality = -0.8
        elif error_type == 'attentional':
            quality = -0.3
        elif error_type == 'conceptual':
            quality = -0.6
        else:
            quality = -0.4
    
    return max(-1.0, min(1.0, quality))