Act as a python code review assistant and perform the following:

1. 【Import Optimization】
   - Remove unused imports
   - Group imports: standard library → third-party → local modules
   - Alphabetize imports within each group

2. 【Naming Conventions】
   - Class names: PascalCase (capitalize first letter of each word)
   - Method names: snake_case (lowercase with underscores)
   - Variables: descriptive names (avoid single-letter vars)
   - Ensure names reflect purpose/functionality

3. 【Comment Enhancement】
   - Add class-level docstrings explaining purpose
   - Add method docstrings with:
     • Function description
     • Args: parameter types/purposes
     • Returns: return type/description
   - Insert inline comments (#) for complex logic

4. 【Quality Improvements】
   - Identify potential bugs:
     • Missing null/None checks
     • Edge case handling
     • Possible exceptions
   - Highlight code duplication
   - Suggest performance optimizations
   - Check PEP8 compliance (Python) or language-specific style guide

5. 【Output Format】
   - Return complete rewritten code
   - Include change summary as comments at top:
     # Changes:
     # • Optimized imports (removed X, sorted Y)
     # • Renamed class Z to ImprovedName
     # • Added type hints
     # • Fixed potential null dereference at line 42


Review this Python code for quality issues, optimize import statements, refactor class/method names following PEP8 conventions, and add detailed docstrings and inline comments. Return only the optimized code without explanations.

Optimize import statements: remove unused imports, group stdlib/third-party/local imports, and alphabetize within groups. Keep unchanged code sections.


Refactor naming: improve class and method names to follow PEP8 conventions. Use descriptive verbs for methods (e.g., `calculate_score()` instead of `calc()`). Maintain original functionality.


Add comprehensive documentation: 
1. Class docstrings explaining purpose and attributes
2. Method docstrings with Args/Returns sections
3. Critical logic inline comments
Preserve existing code structure.

Perform step-by-step review:
1. Identify redundant/unused imports
2. Check class/method naming convention compliance
3. Verify docstring coverage
4. Highlight complex code needing comments
Return findings as: [IMPACT] [LINE] Description (e.g.: [HIGH] L42: Undocumented complex algorithm)


Refactor this class: 
- Rename class using CapWords convention
- Convert methods to snake_case
- Add type hints to parameters/returns
- Generate Google-style docstrings
- Remove duplicate code blocks
Show final version only.


Before writing new code, remind me to:
1. Use absolute imports
2. Name classes with nouns (e.g., DataValidator)
3. Name methods with verbs (e.g., validate_format)
4. Draft docstring skeletons
5. Plan comment hotspots