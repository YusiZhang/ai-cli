"""Role-based prompting system for roundtable discussions."""

import logging
from enum import Enum
from typing import Optional

from .messages import ChatMessage

logger = logging.getLogger(__name__)


class RoundtableRole(Enum):
    """Defines the different roles models can play in roundtable discussions."""

    GENERATOR = "generator"
    CRITIC = "critic"
    REFINER = "refiner"
    EVALUATOR = "evaluator"


class RolePromptTemplates:
    """Default prompt templates for different roundtable roles."""

    TEMPLATES: dict[RoundtableRole, str] = {
        RoundtableRole.GENERATOR: """You are participating in a roundtable discussion as a GENERATOR.

Original request: {original_prompt}

Your task: Generate creative and well-reasoned suggestions based on the user's request. Provide multiple options with clear explanations for why each suggestion is valuable and relevant to the user's needs.

Please provide your response in a clear, structured format with explanations for each suggestion.""",
        RoundtableRole.CRITIC: """You are participating in a roundtable discussion as a CRITIC.

Original request: {original_prompt}

Previous responses to review:
{previous_responses}

Your task: Critically analyze the previous suggestions. Identify strengths and weaknesses, point out any gaps or issues, and provide constructive criticism. Then offer your own alternative suggestions that address the limitations you've identified.

Structure your response as:
1. Analysis of previous suggestions (strengths/weaknesses)
2. Your alternative suggestions with rationale""",
        RoundtableRole.REFINER: """You are participating in a roundtable discussion as a REFINER.

Original request: {original_prompt}

Discussion so far:
{previous_responses}

Your task: Review all the suggestions and critiques provided so far. Take the best elements from the previous responses and refine them into improved, polished suggestions. Focus on enhancing quality and addressing any concerns raised during the discussion.

Provide refined suggestions that incorporate the best insights from the discussion.""",
        RoundtableRole.EVALUATOR: """You are participating in a roundtable discussion as an EVALUATOR.

Original request: {original_prompt}

All suggestions and discussion:
{previous_responses}

Your task: Evaluate all the suggestions that have been presented during this discussion. Rank them based on how well they meet the user's needs, provide a final assessment, and recommend the top choices with clear reasoning.

Structure your response as:
1. Summary of all suggestions discussed
2. Evaluation criteria used
3. Ranked recommendations with rationale
4. Final recommendation for the user""",
    }

    @classmethod
    def get_template(cls, role: RoundtableRole) -> str:
        """Get the prompt template for a specific role."""
        return cls.TEMPLATES[role]

    @classmethod
    def format_template(
        cls, role: RoundtableRole, original_prompt: str, previous_responses: str = ""
    ) -> str:
        """Format a role template with the provided context."""
        template = cls.get_template(role)
        return template.format(
            original_prompt=original_prompt, previous_responses=previous_responses
        )


class RolePromptBuilder:
    """Builds context-aware prompts for different roundtable roles."""

    def __init__(self, custom_templates: Optional[dict[RoundtableRole, str]] = None):
        """Initialize the prompt builder with optional custom templates."""
        self.custom_templates = custom_templates or {}

    def build_role_prompt(
        self,
        role: RoundtableRole,
        original_prompt: str,
        conversation_history: list[ChatMessage],
        current_round: int = 1,
        total_rounds: int = 1,
    ) -> str:
        """Build a complete prompt for a model based on its assigned role."""

        # Get the appropriate template (custom or default)
        template = self._get_template_for_role(role)

        # Validate template variables before formatting
        is_custom = role in self.custom_templates
        self._validate_template_variables(template, role, is_custom)

        # Format previous responses based on role requirements
        previous_responses = self._format_previous_responses(
            role, conversation_history, original_prompt
        )

        # Add round context if multiple rounds
        if total_rounds > 1:
            round_context = f"\n\nThis is round {current_round} of {total_rounds} in the discussion."
            template += round_context

        # Format the final prompt
        try:
            formatted_prompt = template.format(
                original_prompt=original_prompt,
                previous_responses=previous_responses,
                current_round=current_round,
                total_rounds=total_rounds,
            )

            logger.debug(
                f"Successfully built role prompt for {role.value} ({'custom' if is_custom else 'default'} template)"
            )
            return formatted_prompt

        except KeyError as e:
            # If template formatting fails, provide a helpful error message
            template_type = "custom" if is_custom else "default"
            raise ValueError(
                f"Template formatting failed for {template_type} {role.value} template: missing variable {e}. "
                f"Available variables: original_prompt, previous_responses, current_round, total_rounds"
            ) from e

    def _validate_template_variables(
        self, template: str, role: RoundtableRole, is_custom: bool
    ) -> None:
        """Validate that template contains expected variables and warn about issues."""
        import re

        # Find all format variables in the template
        format_vars = re.findall(r"\{(\w+)\}", template)
        expected_vars = {
            "original_prompt",
            "previous_responses",
            "current_round",
            "total_rounds",
        }
        found_vars = set(format_vars)

        # Check for unexpected variables
        unexpected_vars = found_vars - expected_vars
        if unexpected_vars and is_custom:
            logger.warning(
                f"Custom template for {role.value} contains unexpected variables: {unexpected_vars}. "
                f"Available variables: {expected_vars}"
            )

        # Check for missing essential variables (original_prompt is always needed)
        if "original_prompt" not in found_vars:
            template_type = "custom" if is_custom else "default"
            logger.warning(
                f"{template_type.title()} template for {role.value} does not contain 'original_prompt' variable"
            )

    def _get_template_for_role(self, role: RoundtableRole) -> str:
        """Get the template for a role, preferring custom over default."""
        if role in self.custom_templates:
            logger.debug(f"Using custom template for role {role.value}")
            return self.custom_templates[role]

        logger.debug(
            f"Using default template for role {role.value} (no custom template found)"
        )
        return RolePromptTemplates.get_template(role)

    def _format_previous_responses(
        self,
        role: RoundtableRole,
        conversation_history: list[ChatMessage],
        original_prompt: str,
    ) -> str:
        """Format previous responses based on what the current role needs to see."""

        if not conversation_history:
            return ""

        # Filter out the original user prompt from history
        responses = [
            msg
            for msg in conversation_history
            if msg.role == "assistant" and msg.content.strip()
        ]

        if not responses:
            return ""

        # Different roles need different context
        if role == RoundtableRole.GENERATOR:
            # Generators typically work fresh, but might want to see previous rounds
            if len(responses) == 0:
                return ""
            return (
                "Previous round responses (for reference):\n"
                + self._format_response_list(responses)
            )

        elif role == RoundtableRole.CRITIC:
            # Critics need to see what they're critiquing
            return self._format_response_list(responses)

        elif role == RoundtableRole.REFINER:
            # Refiners need to see the full discussion
            return "Full discussion so far:\n" + self._format_response_list(responses)

        elif role == RoundtableRole.EVALUATOR:
            # Evaluators need comprehensive view
            return "Complete discussion thread:\n" + self._format_response_list(
                responses
            )

        return self._format_response_list(responses)

    def _format_response_list(self, responses: list[ChatMessage]) -> str:
        """Format a list of responses for inclusion in prompts."""
        formatted_responses = []

        for i, response in enumerate(responses, 1):
            model_name = response.metadata.get("model", "Unknown Model")
            role_info = response.metadata.get("role", "")

            header = f"Response {i}"
            if model_name != "Unknown Model":
                header += f" (from {model_name}"
                if role_info:
                    header += f" as {role_info}"
                header += ")"
            header += ":"

            formatted_responses.append(f"{header}\n{response.content}\n")

        return "\n".join(formatted_responses)


class RoleAssigner:
    """Handles assignment of roles to models across roundtable rounds."""

    def __init__(
        self,
        enabled_models: list[str],
        role_assignments: dict[str, list[RoundtableRole]],
        role_rotation: bool = True,
    ):
        """Initialize the role assigner with model and role configuration."""
        self.enabled_models = enabled_models
        self.role_assignments = role_assignments
        self.role_rotation = role_rotation
        self._round_assignments: dict[int, dict[str, RoundtableRole]] = {}

    def assign_roles_for_round(
        self, round_num: int, total_rounds: int
    ) -> dict[str, RoundtableRole]:
        """Assign roles to models for a specific round."""

        if round_num in self._round_assignments:
            return self._round_assignments[round_num]

        assignments = {}

        if len(self.enabled_models) == 1:
            # Single model - assign GENERATOR for all rounds
            assignments[self.enabled_models[0]] = RoundtableRole.GENERATOR
        elif len(self.enabled_models) == 2:
            # Two models - use generator/critic pattern
            assignments = self._assign_two_model_roles(round_num, total_rounds)
        else:
            # Multiple models - use sophisticated assignment
            assignments = self._assign_multi_model_roles(round_num, total_rounds)

        # Validate assignments against model capabilities
        assignments = self._validate_assignments(assignments)

        self._round_assignments[round_num] = assignments
        return assignments

    def _assign_two_model_roles(
        self, round_num: int, total_rounds: int
    ) -> dict[str, RoundtableRole]:
        """Assign roles for two-model roundtable."""
        model1, model2 = self.enabled_models
        assignments = {}

        if round_num == 1:
            # First round: model1 generates, model2 critiques
            assignments[model1] = RoundtableRole.GENERATOR
            assignments[model2] = RoundtableRole.CRITIC
        elif self.role_rotation and round_num > 1:
            # Subsequent rounds: alternate or refine
            if round_num % 2 == 0:
                assignments[model2] = RoundtableRole.REFINER
                assignments[model1] = RoundtableRole.CRITIC
            else:
                assignments[model1] = RoundtableRole.GENERATOR
                assignments[model2] = RoundtableRole.CRITIC
        else:
            # No rotation: maintain generator/critic roles
            assignments[model1] = RoundtableRole.GENERATOR
            assignments[model2] = RoundtableRole.CRITIC

        return assignments

    def _assign_multi_model_roles(
        self, round_num: int, total_rounds: int
    ) -> dict[str, RoundtableRole]:
        """Assign roles for multi-model roundtable."""
        assignments = {}
        num_models = len(self.enabled_models)

        if round_num == 1:
            # First round: distribute generator/critic roles
            for i, model in enumerate(self.enabled_models):
                if i < num_models // 2 + 1:
                    assignments[model] = RoundtableRole.GENERATOR
                else:
                    assignments[model] = RoundtableRole.CRITIC
        elif round_num == total_rounds and total_rounds > 2:
            # Final round: include evaluators
            for i, model in enumerate(self.enabled_models):
                if i == 0:
                    assignments[model] = RoundtableRole.EVALUATOR
                elif i < num_models // 2 + 1:
                    assignments[model] = RoundtableRole.REFINER
                else:
                    assignments[model] = RoundtableRole.CRITIC
        else:
            # Middle rounds: mix of refiners and critics
            for i, model in enumerate(self.enabled_models):
                if i < num_models // 2:
                    assignments[model] = RoundtableRole.REFINER
                else:
                    assignments[model] = RoundtableRole.CRITIC

        return assignments

    def _validate_assignments(
        self, assignments: dict[str, RoundtableRole]
    ) -> dict[str, RoundtableRole]:
        """Validate and adjust role assignments based on model capabilities.

        When role-based prompting is used, we prefer to honor the intended role
        assignments and let the template system handle fallback to default templates.
        Role assignments should be treated as preferences rather than hard restrictions
        unless the model has very specific limitations.
        """
        validated = {}

        for model, role in assignments.items():
            if model in self.role_assignments and self.role_assignments[model]:
                available_roles = self.role_assignments[model]
                if role in available_roles:
                    # Model can play the assigned role
                    validated[model] = role
                    logger.debug(
                        f"Model {model} assigned to preferred role {role.value}"
                    )
                else:
                    # Model has role restrictions but can't play assigned role
                    # In role-based prompting, we want to allow more flexibility
                    # to enable template fallback, so we'll use the assigned role anyway
                    # and rely on the template system to handle missing custom templates
                    validated[model] = role
                    logger.debug(
                        f"Model {model} assigned to role {role.value} (outside preferences {[r.value for r in available_roles]}) "
                        f"- template fallback will handle default prompts"
                    )
            else:
                # No restrictions - use assigned role
                validated[model] = role
                logger.debug(
                    f"No role restrictions for {model}, using assigned role {role.value}"
                )

        return validated

    def get_role_for_model_in_round(
        self, model: str, round_num: int
    ) -> Optional[RoundtableRole]:
        """Get the role assigned to a specific model in a specific round."""
        if round_num in self._round_assignments:
            return self._round_assignments[round_num].get(model)
        return None

    def get_all_assignments(self) -> dict[int, dict[str, RoundtableRole]]:
        """Get all role assignments across all rounds."""
        return self._round_assignments.copy()
