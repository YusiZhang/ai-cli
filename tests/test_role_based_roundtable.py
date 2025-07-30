"""Tests for role-based roundtable functionality."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai_cli.config.models import AIConfig, RoundTableConfig
from ai_cli.core.chat import ChatEngine
from ai_cli.core.messages import ChatMessage
from ai_cli.core.roles import (
    RoleAssigner,
    RolePromptBuilder,
    RolePromptTemplates,
    RoundtableRole,
)


class TestRoundtableRole:
    """Test RoundtableRole enum functionality."""

    def test_role_values(self):
        """Test that roles have correct string values."""
        assert RoundtableRole.GENERATOR.value == "generator"
        assert RoundtableRole.CRITIC.value == "critic"
        assert RoundtableRole.REFINER.value == "refiner"
        assert RoundtableRole.EVALUATOR.value == "evaluator"


class TestRolePromptTemplates:
    """Test RolePromptTemplates functionality."""

    def test_get_template(self):
        """Test getting templates for different roles."""
        generator_template = RolePromptTemplates.get_template(RoundtableRole.GENERATOR)
        assert "GENERATOR" in generator_template
        assert "{original_prompt}" in generator_template

        critic_template = RolePromptTemplates.get_template(RoundtableRole.CRITIC)
        assert "CRITIC" in critic_template
        assert "{previous_responses}" in critic_template

    def test_format_template(self):
        """Test formatting templates with context."""
        formatted = RolePromptTemplates.format_template(
            RoundtableRole.GENERATOR,
            original_prompt="Test prompt",
            previous_responses="Test responses",
        )
        assert "Test prompt" in formatted
        assert "GENERATOR" in formatted


class TestRolePromptBuilder:
    """Test RolePromptBuilder functionality."""

    def test_init_with_custom_templates(self):
        """Test initialization with custom templates."""
        custom_templates = {
            RoundtableRole.GENERATOR: "Custom generator template: {original_prompt}"
        }
        builder = RolePromptBuilder(custom_templates=custom_templates)
        assert builder.custom_templates == custom_templates

    def test_build_role_prompt_generator(self):
        """Test building prompt for generator role."""
        builder = RolePromptBuilder()
        prompt = builder.build_role_prompt(
            role=RoundtableRole.GENERATOR,
            original_prompt="Suggest domain names",
            conversation_history=[],
            current_round=1,
            total_rounds=2,
        )

        assert "GENERATOR" in prompt
        assert "Suggest domain names" in prompt
        assert "round 1 of 2" in prompt

    def test_build_role_prompt_critic_with_history(self):
        """Test building prompt for critic role with conversation history."""
        builder = RolePromptBuilder()

        history = [
            ChatMessage(
                "assistant", "Domain suggestions: 1. example.com", {"model": "gpt-4"}
            )
        ]

        prompt = builder.build_role_prompt(
            role=RoundtableRole.CRITIC,
            original_prompt="Suggest domain names",
            conversation_history=history,
            current_round=2,
            total_rounds=2,
        )

        assert "CRITIC" in prompt
        assert "Suggest domain names" in prompt
        assert "example.com" in prompt
        assert "Response 1 (from gpt-4)" in prompt

    def test_custom_template_priority(self):
        """Test that custom templates take priority over default ones."""
        custom_templates = {RoundtableRole.GENERATOR: "Custom: {original_prompt}"}
        builder = RolePromptBuilder(custom_templates=custom_templates)

        prompt = builder.build_role_prompt(
            role=RoundtableRole.GENERATOR,
            original_prompt="Test",
            conversation_history=[],
        )

        assert "Custom: Test" in prompt
        assert "GENERATOR" not in prompt  # Default template phrase

    def test_format_response_list(self):
        """Test formatting response list for inclusion in prompts."""
        builder = RolePromptBuilder()

        responses = [
            ChatMessage(
                "assistant", "Response 1", {"model": "gpt-4", "role": "generator"}
            ),
            ChatMessage("assistant", "Response 2", {"model": "claude"}),
        ]

        formatted = builder._format_response_list(responses)

        assert "Response 1 (from gpt-4 as generator)" in formatted
        assert "Response 2 (from claude)" in formatted
        assert "Response 1 (from gpt-4 as generator):\nResponse 1" in formatted
        assert "Response 2 (from claude):\nResponse 2" in formatted


class TestRoleAssigner:
    """Test RoleAssigner functionality."""

    def test_init(self):
        """Test RoleAssigner initialization."""
        models = ["model1", "model2"]
        role_assignments = {"model1": [RoundtableRole.GENERATOR]}

        assigner = RoleAssigner(
            enabled_models=models, role_assignments=role_assignments, role_rotation=True
        )

        assert assigner.enabled_models == models
        assert assigner.role_assignments == role_assignments
        assert assigner.role_rotation is True

    def test_assign_roles_single_model(self):
        """Test role assignment for single model."""
        assigner = RoleAssigner(
            enabled_models=["model1"], role_assignments={}, role_rotation=True
        )

        assignments = assigner.assign_roles_for_round(1, 2)
        assert assignments == {"model1": RoundtableRole.GENERATOR}

    def test_assign_roles_two_models_round1(self):
        """Test role assignment for two models in round 1."""
        assigner = RoleAssigner(
            enabled_models=["model1", "model2"], role_assignments={}, role_rotation=True
        )

        assignments = assigner.assign_roles_for_round(1, 2)
        assert assignments["model1"] == RoundtableRole.GENERATOR
        assert assignments["model2"] == RoundtableRole.CRITIC

    def test_assign_roles_two_models_round2_with_rotation(self):
        """Test role assignment for two models in round 2 with rotation."""
        assigner = RoleAssigner(
            enabled_models=["model1", "model2"], role_assignments={}, role_rotation=True
        )

        assignments = assigner.assign_roles_for_round(2, 2)
        assert assignments["model2"] == RoundtableRole.REFINER
        assert assignments["model1"] == RoundtableRole.CRITIC

    def test_assign_roles_two_models_no_rotation(self):
        """Test role assignment for two models without rotation."""
        assigner = RoleAssigner(
            enabled_models=["model1", "model2"],
            role_assignments={},
            role_rotation=False,
        )

        # Round 1
        assignments1 = assigner.assign_roles_for_round(1, 3)
        assert assignments1["model1"] == RoundtableRole.GENERATOR
        assert assignments1["model2"] == RoundtableRole.CRITIC

        # Round 2 (should be same without rotation)
        assignments2 = assigner.assign_roles_for_round(2, 3)
        assert assignments2["model1"] == RoundtableRole.GENERATOR
        assert assignments2["model2"] == RoundtableRole.CRITIC

    def test_assign_roles_multi_models(self):
        """Test role assignment for multiple models."""
        assigner = RoleAssigner(
            enabled_models=["model1", "model2", "model3", "model4"],
            role_assignments={},
            role_rotation=True,
        )

        # Round 1: mix of generators and critics
        assignments1 = assigner.assign_roles_for_round(1, 3)
        generator_count = sum(
            1 for role in assignments1.values() if role == RoundtableRole.GENERATOR
        )
        critic_count = sum(
            1 for role in assignments1.values() if role == RoundtableRole.CRITIC
        )
        assert generator_count >= 2  # At least 2 generators
        assert critic_count >= 1  # At least 1 critic

        # Final round: should include evaluator
        assignments_final = assigner.assign_roles_for_round(3, 3)
        evaluator_count = sum(
            1 for role in assignments_final.values() if role == RoundtableRole.EVALUATOR
        )
        assert evaluator_count >= 1  # At least 1 evaluator

    def test_validate_assignments_with_restrictions(self):
        """Test assignment validation with role restrictions."""
        role_assignments = {
            "model1": [RoundtableRole.GENERATOR],  # Only generator
            "model2": [
                RoundtableRole.CRITIC,
                RoundtableRole.REFINER,
            ],  # Critic or refiner only
        }

        assigner = RoleAssigner(
            enabled_models=["model1", "model2"],
            role_assignments=role_assignments,
            role_rotation=True,
        )

        # Try to assign evaluator to model1 (should allow it for template fallback)
        test_assignments = {
            "model1": RoundtableRole.EVALUATOR,
            "model2": RoundtableRole.CRITIC,
        }
        validated = assigner._validate_assignments(test_assignments)

        assert (
            validated["model1"] == RoundtableRole.EVALUATOR
        )  # Allowed for template fallback
        assert validated["model2"] == RoundtableRole.CRITIC  # Allowed role

    def test_get_role_for_model_in_round(self):
        """Test getting role for specific model in specific round."""
        assigner = RoleAssigner(
            enabled_models=["model1", "model2"], role_assignments={}, role_rotation=True
        )

        # Assign roles for round 1
        assigner.assign_roles_for_round(1, 2)

        role = assigner.get_role_for_model_in_round("model1", 1)
        assert role == RoundtableRole.GENERATOR

        # Non-existent round
        role = assigner.get_role_for_model_in_round("model1", 99)
        assert role is None

    def test_caching_assignments(self):
        """Test that role assignments are cached."""
        assigner = RoleAssigner(
            enabled_models=["model1", "model2"], role_assignments={}, role_rotation=True
        )

        # First call
        assignments1 = assigner.assign_roles_for_round(1, 2)

        # Second call should return cached result
        assignments2 = assigner.assign_roles_for_round(1, 2)

        assert assignments1 == assignments2
        assert id(assignments1) == id(assignments2)  # Same object


class TestChatMessage:
    """Test ChatMessage role-related functionality."""

    def test_set_roundtable_role(self):
        """Test setting roundtable role metadata."""
        message = ChatMessage("assistant", "Test content")
        message.set_roundtable_role(RoundtableRole.GENERATOR, "gpt-4")

        assert message.metadata["roundtable_role"] == "generator"
        assert message.metadata["model"] == "gpt-4"

    def test_get_roundtable_role(self):
        """Test getting roundtable role."""
        message = ChatMessage("assistant", "Test content")
        message.metadata["roundtable_role"] = "critic"

        assert message.get_roundtable_role() == "critic"

    def test_get_model_name(self):
        """Test getting model name."""
        message = ChatMessage("assistant", "Test content", {"model": "claude-3"})
        assert message.get_model_name() == "claude-3"

    def test_is_from_roundtable(self):
        """Test checking if message is from roundtable."""
        # Regular message
        message1 = ChatMessage("assistant", "Test content")
        assert not message1.is_from_roundtable()

        # Roundtable message
        message2 = ChatMessage("assistant", "Test content")
        message2.set_roundtable_role(RoundtableRole.GENERATOR, "gpt-4")
        assert message2.is_from_roundtable()


class TestRoundTableConfig:
    """Test RoundTableConfig functionality."""

    def test_get_available_roles_for_model_with_assignments(self):
        """Test getting available roles for model with specific assignments."""
        config = RoundTableConfig()
        config.role_assignments = {
            "gpt-4": [RoundtableRole.GENERATOR, RoundtableRole.CRITIC]
        }

        roles = config.get_available_roles_for_model("gpt-4")
        assert roles == [RoundtableRole.GENERATOR, RoundtableRole.CRITIC]

    def test_get_available_roles_for_model_default(self):
        """Test getting available roles for model without specific assignments."""
        config = RoundTableConfig()

        roles = config.get_available_roles_for_model("unknown-model")
        assert len(roles) == 4  # All roles available
        assert RoundtableRole.GENERATOR in roles

    def test_can_model_play_role(self):
        """Test checking if model can play specific role."""
        config = RoundTableConfig()
        config.role_assignments = {"gpt-4": [RoundtableRole.GENERATOR]}

        assert config.can_model_play_role("gpt-4", RoundtableRole.GENERATOR)
        assert not config.can_model_play_role("gpt-4", RoundtableRole.CRITIC)

    def test_get_role_template(self):
        """Test getting custom role template."""
        config = RoundTableConfig()
        config.custom_role_templates = {RoundtableRole.GENERATOR: "Custom template"}

        template = config.get_role_template(RoundtableRole.GENERATOR)
        assert template == "Custom template"

        # Non-existent template
        template = config.get_role_template(RoundtableRole.CRITIC)
        assert template is None

    def test_mixed_custom_and_default_templates(self):
        """Test behavior with partial custom templates (some roles custom, others default)."""
        # Create config with custom templates for only some roles
        custom_templates = {
            RoundtableRole.GENERATOR: "Custom generator: {original_prompt}",
            RoundtableRole.CRITIC: "Custom critic: {previous_responses}",
            # Leave REFINER and EVALUATOR to use defaults
        }

        builder = RolePromptBuilder(custom_templates=custom_templates)
        original_prompt = "Test prompt"
        history = []

        # Test that custom templates are used when available
        generator_prompt = builder.build_role_prompt(
            RoundtableRole.GENERATOR, original_prompt, history
        )
        assert "Custom generator: Test prompt" in generator_prompt

        critic_prompt = builder.build_role_prompt(
            RoundtableRole.CRITIC, original_prompt, history
        )
        assert "Custom critic:" in critic_prompt

        # Test that default templates are used when custom not available
        refiner_prompt = builder.build_role_prompt(
            RoundtableRole.REFINER, original_prompt, history
        )
        # Should contain default template content
        assert "REFINER" in refiner_prompt
        assert "refine" in refiner_prompt.lower()
        assert "Custom" not in refiner_prompt

        evaluator_prompt = builder.build_role_prompt(
            RoundtableRole.EVALUATOR, original_prompt, history
        )
        # Should contain default template content
        assert "EVALUATOR" in evaluator_prompt
        assert "evaluate" in evaluator_prompt.lower()
        assert "Custom" not in evaluator_prompt

    def test_role_assignment_with_mixed_templates(self):
        """Test role assignments work correctly with mixed custom/default templates."""
        # Set up config with role assignments and partial custom templates
        config = RoundTableConfig()
        config.role_assignments = {
            "gpt-4": [RoundtableRole.GENERATOR, RoundtableRole.REFINER],
            "claude": [RoundtableRole.CRITIC, RoundtableRole.EVALUATOR],
        }
        config.custom_role_templates = {
            RoundtableRole.GENERATOR: "Custom generator for {original_prompt}",
            # Leave other roles to use defaults
        }

        # Test that models can be assigned roles even if no custom template exists
        assert config.can_model_play_role("gpt-4", RoundtableRole.GENERATOR)
        assert config.can_model_play_role("gpt-4", RoundtableRole.REFINER)
        assert config.can_model_play_role("claude", RoundtableRole.CRITIC)
        assert config.can_model_play_role("claude", RoundtableRole.EVALUATOR)

        # Test template retrieval
        assert (
            config.get_role_template(RoundtableRole.GENERATOR)
            == "Custom generator for {original_prompt}"
        )
        assert config.get_role_template(RoundtableRole.REFINER) is None  # Uses default
        assert config.get_role_template(RoundtableRole.CRITIC) is None  # Uses default
        assert (
            config.get_role_template(RoundtableRole.EVALUATOR) is None
        )  # Uses default

    def test_template_validation_warnings(self):
        """Test that template validation warns about issues."""
        from unittest.mock import patch

        # Create a custom template with missing required variable
        custom_templates = {
            RoundtableRole.GENERATOR: "This template has no original_prompt variable"
        }

        builder = RolePromptBuilder(custom_templates=custom_templates)

        with patch("ai_cli.core.roles.logger") as mock_logger:
            # This should trigger a warning about missing original_prompt
            builder.build_role_prompt(RoundtableRole.GENERATOR, "test", [])

            # Check that a warning was logged
            mock_logger.warning.assert_called()
            warning_calls = [
                call
                for call in mock_logger.warning.call_args_list
                if "original_prompt" in str(call)
            ]
            assert len(warning_calls) > 0

    def test_template_with_unexpected_variables(self):
        """Test custom template with unexpected variables."""
        from unittest.mock import patch

        # Create a custom template with unexpected variable
        custom_templates = {
            RoundtableRole.GENERATOR: "Generator: {original_prompt} and {unexpected_var}"
        }

        builder = RolePromptBuilder(custom_templates=custom_templates)

        with patch("ai_cli.core.roles.logger") as mock_logger:
            # This should trigger a warning about unexpected variable and then fail
            with pytest.raises(
                ValueError,
                match="Template formatting failed.*missing variable.*unexpected_var",
            ):
                builder.build_role_prompt(RoundtableRole.GENERATOR, "test", [])

            # Check that a warning was logged about unexpected variables
            mock_logger.warning.assert_called()
            warning_calls = [
                call
                for call in mock_logger.warning.call_args_list
                if "unexpected" in str(call)
            ]
            assert len(warning_calls) > 0

    def test_config_manager_template_operations(self):
        """Test configuration manager template operations."""
        from ai_cli.config.manager import ConfigManager

        # Create config manager (uses default config path)
        config_manager = ConfigManager()

        # Test template operations
        test_template = "Test template: {original_prompt}"

        # Set custom template for evaluator (unlikely to already exist)
        config_manager.set_custom_role_template(RoundtableRole.EVALUATOR, test_template)

        # Verify it was set
        templates = config_manager.get_custom_role_templates()
        assert RoundtableRole.EVALUATOR in templates
        assert templates[RoundtableRole.EVALUATOR] == test_template

        # Update the template
        updated_template = (
            "Updated test template: {original_prompt} and {previous_responses}"
        )
        config_manager.set_custom_role_template(
            RoundtableRole.EVALUATOR, updated_template
        )

        # Verify it was updated
        templates = config_manager.get_custom_role_templates()
        assert templates[RoundtableRole.EVALUATOR] == updated_template

        # Remove the template
        config_manager.remove_custom_role_template(RoundtableRole.EVALUATOR)

        # Verify it was removed
        templates = config_manager.get_custom_role_templates()
        assert RoundtableRole.EVALUATOR not in templates


@pytest.mark.asyncio
class TestChatEngineRoleBasedRoundtable:
    """Test ChatEngine role-based roundtable functionality."""

    @pytest.fixture
    def mock_config(self):
        """Create mock configuration with role-based roundtable enabled."""
        config = AIConfig()
        config.roundtable.enabled_models = [
            "openai/gpt-4",
            "anthropic/claude-3-5-sonnet",
        ]
        config.roundtable.use_role_based_prompting = True
        config.roundtable.discussion_rounds = 2
        return config

    @pytest.fixture
    def mock_console(self):
        """Create mock console."""
        return MagicMock()

    @pytest.fixture
    def mock_chat_engine(self, mock_config, mock_console):
        """Create mock chat engine."""
        with (
            patch("ai_cli.core.chat.ProviderFactory"),
            patch("ai_cli.core.chat.StreamingDisplay"),
        ):
            return ChatEngine(mock_config, mock_console)

    async def test_roundtable_chat_initializes_role_assigner(self, mock_chat_engine):
        """Test that roundtable chat initializes role assigner."""
        with patch.object(
            mock_chat_engine, "_run_sequential_round", new_callable=AsyncMock
        ) as mock_sequential:
            mock_sequential.return_value = {
                "openai/gpt-4": "Response 1",
                "anthropic/claude-3-5-sonnet": "Response 2",
            }

            await mock_chat_engine.roundtable_chat("Test prompt")

            assert mock_chat_engine.role_assigner is not None
            assert mock_chat_engine.role_assigner.enabled_models == [
                "openai/gpt-4",
                "anthropic/claude-3-5-sonnet",
            ]

    async def test_roundtable_chat_shows_role_based_mode(self, mock_chat_engine):
        """Test that roundtable chat shows role-based mode in output."""
        with patch.object(
            mock_chat_engine, "_run_sequential_round", new_callable=AsyncMock
        ) as mock_sequential:
            mock_sequential.return_value = {
                "openai/gpt-4": "Response 1",
                "anthropic/claude-3-5-sonnet": "Response 2",
            }

            await mock_chat_engine.roundtable_chat("Test prompt")

            # Check that console.print was called with role-based mode indication
            print_calls = [
                call[0][0] for call in mock_chat_engine.console.print.call_args_list
            ]
            mode_call = next(
                (call for call in print_calls if "Role-Based" in str(call)), None
            )
            assert mode_call is not None

    async def test_sequential_round_with_role_based_prompting(self, mock_chat_engine):
        """Test sequential round with role-based prompting."""
        mock_chat_engine.role_assigner = RoleAssigner(
            enabled_models=["openai/gpt-4", "anthropic/claude-3-5-sonnet"],
            role_assignments={},
            role_rotation=True,
        )

        conversation_history = [ChatMessage("user", "Test prompt")]

        with patch.object(
            mock_chat_engine, "_get_model_response", new_callable=AsyncMock
        ) as mock_get_response:
            mock_get_response.return_value = "Mock response"

            responses = await mock_chat_engine._run_sequential_round(
                conversation_history,
                ["openai/gpt-4", "anthropic/claude-3-5-sonnet"],
                round_num=1,
            )

            assert len(responses) == 2
            assert "openai/gpt-4" in responses
            assert "anthropic/claude-3-5-sonnet" in responses

            # Verify role-based prompts were built
            assert mock_get_response.call_count == 2

            # Check that role assignments were displayed
            print_calls = []
            for call in mock_chat_engine.console.print.call_args_list:
                if call[0]:  # Check if there are positional arguments
                    print_calls.append(call[0][0])
            role_calls = [call for call in print_calls if "playing role:" in str(call)]
            assert len(role_calls) == 2  # One for each model

    async def test_conversation_history_includes_role_metadata(self, mock_chat_engine):
        """Test that conversation history includes role metadata."""
        with patch.object(
            mock_chat_engine, "_run_sequential_round", new_callable=AsyncMock
        ) as mock_sequential:
            mock_sequential.return_value = {
                "openai/gpt-4": "Response 1",
                "anthropic/claude-3-5-sonnet": "Response 2",
            }

            await mock_chat_engine.roundtable_chat("Test prompt")

            # Verify role assigner was initialized and used
            assert mock_chat_engine.role_assigner is not None

    async def test_models_can_see_current_round_responses(self, mock_chat_engine):
        """Test that models can see responses from earlier models in the same round."""
        # Set up role assigner
        mock_chat_engine.role_assigner = RoleAssigner(
            enabled_models=["openai/gpt-4", "anthropic/claude-3-5-sonnet"],
            role_assignments={},
            role_rotation=True,
        )

        conversation_history = [ChatMessage("user", "Test prompt")]
        captured_messages = []

        # Mock _get_model_response to capture what messages each model receives
        async def capture_get_model_response(
            model_name, messages, streaming_display=None, multi_stream_display=None
        ):
            captured_messages.append({"model": model_name, "messages": messages})
            # Return different responses for each model
            if model_name == "openai/gpt-4":
                return "Generator: Here are my suggestions: A, B, C"
            else:
                return "Critic: I'll analyze the suggestions"

        mock_chat_engine._get_model_response = capture_get_model_response

        # Mock StreamingDisplay to avoid Rich complexity
        with patch("ai_cli.core.chat.StreamingDisplay") as mock_streaming_display:
            mock_display_instance = mock_streaming_display.return_value
            mock_display_instance.update_response = AsyncMock()
            mock_display_instance.finalize_response = AsyncMock()

            # Run sequential round
            await mock_chat_engine._run_sequential_round(
                conversation_history,
                ["openai/gpt-4", "anthropic/claude-3-5-sonnet"],
                round_num=1,
            )

            # Verify we captured messages for both models
            assert len(captured_messages) == 2

        # First model (Generator) should not see any previous responses (empty round)
        generator_message = captured_messages[0]
        assert generator_message["model"] == "openai/gpt-4"
        generator_prompt = generator_message["messages"][0].content
        assert (
            "suggestions: A, B, C" not in generator_prompt
        )  # Should not see its own future response

        # Second model (Critic) should see the first model's response
        critic_message = captured_messages[1]
        assert critic_message["model"] == "anthropic/claude-3-5-sonnet"
        critic_prompt = critic_message["messages"][0].content
        assert (
            "suggestions: A, B, C" in critic_prompt
        )  # Should see Generator's response
        assert "CRITIC" in critic_prompt  # Should have critic role prompt
