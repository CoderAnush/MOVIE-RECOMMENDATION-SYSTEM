# fuzzy_system.py

import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl

# Step 1: Define fuzzy input
rating = ctrl.Antecedent(np.arange(0, 5.1, 0.1), 'rating')

# Step 2: Membership functions
rating['low'] = fuzz.trimf(rating.universe, [0, 0, 2.5])
rating['medium'] = fuzz.trimf(rating.universe, [2, 3, 4])
rating['high'] = fuzz.trimf(rating.universe, [3.5, 5, 5])

# Step 3: Define fuzzy output (recommendation strength)
recommendation = ctrl.Consequent(np.arange(0, 11, 1), 'recommendation')

recommendation['poor'] = fuzz.trimf(recommendation.universe, [0, 0, 5])
recommendation['average'] = fuzz.trimf(recommendation.universe, [3, 5, 7])
recommendation['good'] = fuzz.trimf(recommendation.universe, [6, 10, 10])

# Step 4: Fuzzy rules
rule1 = ctrl.Rule(rating['low'], recommendation['poor'])
rule2 = ctrl.Rule(rating['medium'], recommendation['average'])
rule3 = ctrl.Rule(rating['high'], recommendation['good'])

# Step 5: Build control system
recommendation_ctrl = ctrl.ControlSystem([rule1, rule2, rule3])
recommendation_sim = ctrl.ControlSystemSimulation(recommendation_ctrl)

# Quick test
if __name__ == "__main__":
    recommendation_sim.input['rating'] = 4.2
    recommendation_sim.compute()
    print("Recommendation Strength:", recommendation_sim.output['recommendation'])
