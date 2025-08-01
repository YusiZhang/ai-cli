"""Role-based prompting system for roundtable discussions."""

import logging
from enum import Enum
from typing import TYPE_CHECKING, Optional

from .messages import ChatMessage

if TYPE_CHECKING:
    from ..config.models import RoundTableConfig

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
    """Handles role-to-model assignments using explicit mapping configuration."""

    def __init__(
        self,
        roundtable_config: "RoundTableConfig",
        default_model: str,
    ):
        """Initialize the role assigner with roundtable configuration."""
        self.roundtable_config = roundtable_config
        self.default_model = default_model
        self._round_assignments: dict[int, dict[RoundtableRole, str]] = {}

    def get_role_assignments_for_round(
        self, round_num: int
    ) -> dict[RoundtableRole, str]:
        """Get role-to-model assignments for a specific round."""

        if round_num in self._round_assignments:
            return self._round_assignments[round_num]

        # Build assignments for all enabled roles
        assignments = {}
        enabled_roles = self.roundtable_config.get_enabled_roles()

        for role in enabled_roles:
            model = self.roundtable_config.get_model_for_role(role, self.default_model)
            assignments[role] = model
            logger.debug(f"Assigned {role.value} to {model}")

        self._round_assignments[round_num] = assignments
        return assignments

    def get_model_for_role(self, role: RoundtableRole, round_num: int = 1) -> str:
        """Get the model assigned to a specific role for a specific round."""
        assignments = self.get_role_assignments_for_round(round_num)
        return assignments.get(role, self.default_model)

    def get_role_for_model_in_round(
        self, model: str, round_num: int
    ) -> Optional[RoundtableRole]:
        """Get the role assigned to a specific model in a specific round (legacy compatibility)."""
        assignments = self.get_role_assignments_for_round(round_num)
        # Reverse lookup: find role for given model
        for role, assigned_model in assignments.items():
            if assigned_model == model:
                return role
        return None

    def get_all_assignments(self) -> dict[int, dict[RoundtableRole, str]]:
        """Get all role assignments across all rounds."""
        return self._round_assignments.copy()
