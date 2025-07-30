Enhanced Roundtable Mode Implementation Plan

Current Issues Analysis

The existing roundtable mode simply passes conversation history between models without:
- Specific role assignments (generator vs critic)
- Clear task instructions for each model
- Structured context about what each model should do
- Preservation of original user context across rounds

Core Enhancements

1. Role-Based Prompting System

- Create new RoundtableRole enum with roles: GENERATOR, CRITIC, REFINER, EVALUATOR
- Add role-specific prompt templates that give clear instructions:
    - Generator: "Based on the user's request for [context], provide [X] suggestions with explanations"
    - Critic: "Review the previous response for [context]. Provide constructive criticism and your own alternative suggestions"
    - Refiner: "Consider the previous suggestions and critiques. Refine and improve the best ideas"
- Enhanced context building that always includes:
    - Original user prompt
    - Current role and specific task
    - Relevant conversation history
    - Clear instructions on expected output format

2. Advanced Configuration

- Extend RoundTableConfig with:
    - role_assignments: Dict[str, List[RoundtableRole]] - which roles each model can play
    - role_rotation: bool - whether to rotate roles or keep fixed assignments
    - prompt_templates: Dict[RoundtableRole, str] - customizable role instructions
    - preserve_original_context: bool - always include original prompt
- Model-specific role capabilities - some models might be better critics than generators

3. Intelligent Round Management

- Round orchestration logic that:
    - Assigns appropriate roles to models based on configuration
    - Builds context-aware prompts for each model's specific role
    - Maintains conversation flow while preserving original intent
- Dynamic role assignment based on round number and model capabilities
- Critique-focused rounds where models specifically review and improve previous work

4. Enhanced Context Builder

- Structured prompt construction that clearly separates:
    - Original user request and context
    - Current role assignment and specific task
    - Previous responses relevant to the current role
    - Output format expectations
- Context relevance filtering - only include conversation history relevant to current task

5. Implementation Details

- Modify _run_sequential_round() to use role-based prompt building
- Create RolePromptBuilder class for constructing role-specific prompts
- Add assign_roles_for_round() method for intelligent role distribution
- Update conversation history tracking to include role metadata
- Preserve backward compatibility with current simple roundtable mode

6. Example Flow (Your Domain Name Use Case)

1. Round 1: Model 1 (Generator) gets original context + task to suggest domain names
2. Round 1: Model 2 (Critic) gets original context + Model 1's response + task to critique and provide alternatives
3. Round 2: Model 1 (Refiner) gets original context + all previous + task to refine based on criticism
4. Round 2: Model 2 (Evaluator) gets all context + task to evaluate final suggestions

7. Testing & Validation

- Unit tests for role assignment logic and prompt building
- Integration tests for complete roundtable flows with different role configurations
- Example configurations demonstrating various roundtable patterns (critique, brainstorming, evaluation)

This implementation will transform roundtable mode from a simple conversation chain into a structured, role-based collaborative system where models have
specific purposes and can meaningfully build on each other's work.
