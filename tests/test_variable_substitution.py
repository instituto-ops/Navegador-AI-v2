import logging
from typing import Any, cast
import pytest
from unittest.mock import MagicMock, patch
from pydantic import BaseModel, Field, create_model

from browser_use.agent.service import Agent
from browser_use.agent.views import (
    AgentHistoryList,
    AgentHistory,
    AgentOutput,
    DetectedVariable,
    BrowserStateHistory,
    StepMetadata,
    ActionResult,
)
from browser_use.tools.registry.views import ActionModel, RegisteredAction

# Setup a test agent
class MockAgent(Agent):
    def __init__(self):
        pass

    @property
    def logger(self):
        return logging.getLogger('test_agent')

@pytest.fixture
def agent():
    return MockAgent()

# Helper to create an action model with arbitrary fields for testing
def create_test_action_model(action_name: str, params: dict):
    # Create a dynamic Pydantic model for params
    field_definitions = {k: (type(v), Field(default=v)) for k, v in params.items()}
    ParamModel = create_model(f'{action_name}Params', **cast(Any, field_definitions))

    # Create the action model
    ActionModelType = create_model(
        f'Test{action_name.capitalize()}Action',
        __base__=ActionModel,
        **{action_name: (ParamModel, Field(default_factory=lambda: ParamModel(**params)))} # type: ignore
    )
    return ActionModelType()

def create_history_item(action_model: ActionModel) -> AgentHistory:
    return AgentHistory(
        model_output=AgentOutput(
            action=[action_model],
            evaluation_previous_goal="eval",
            memory="mem",
            next_goal="next"
        ),
        result=[],
        state=BrowserStateHistory(
            url="http://example.com",
            title="Example",
            tabs=[],
            interacted_element=[],
            screenshot_path=None
        ),
        metadata=StepMetadata(
            step_start_time=0.0,
            step_end_time=1.0,
            step_number=0
        )
    )

def test_substitute_variables_happy_path(agent):
    """Test simple string substitution in a flat dictionary"""
    # Setup
    original_value = "John Doe"
    new_value = "Jane Smith"
    variable_name = "full_name"

    action = create_test_action_model("input", {"text": original_value})
    history = AgentHistoryList(history=[create_history_item(action)])

    detected_vars = {
        variable_name: DetectedVariable(name=variable_name, original_value=original_value)
    }

    with patch("browser_use.agent.variable_detector.detect_variables_in_history", return_value=detected_vars):
        new_history = agent._substitute_variables_in_history(
            history,
            {variable_name: new_value}
        )

    # Verify
    assert new_history.history[0].model_output is not None
    new_action = new_history.history[0].model_output.action[0]
    # Access the 'input' attribute of the action model
    # Note: _substitute_variables_in_history replaces nested models with dicts due to model_dump()
    if isinstance(getattr(new_action, 'input'), dict):
        assert getattr(new_action, 'input')['text'] == new_value
    else:
        assert getattr(new_action, 'input').text == new_value

    # Verify original history is not modified (deep copy check)
    assert history.history[0].model_output is not None
    original_action = history.history[0].model_output.action[0]
    # Original should still be a model if it started as one
    assert getattr(original_action, 'input').text == original_value

def test_substitute_variables_nested(agent):
    """Test substitution in nested dictionary/list structures"""
    # Setup
    original_email = "test@example.com"
    new_email = "new@example.com"
    variable_name = "email"

    class NestedParams(BaseModel):
        details: dict
        tags: list[str]

    class ComplexAction(ActionModel):
        complex_op: NestedParams

    action = ComplexAction(
        complex_op=NestedParams(
            details={"contact": {"email": original_email}},
            tags=["tag1", original_email]
        )
    ) # type: ignore

    history = AgentHistoryList(history=[create_history_item(action)])

    detected_vars = {
        variable_name: DetectedVariable(name=variable_name, original_value=original_email)
    }

    with patch("browser_use.agent.variable_detector.detect_variables_in_history", return_value=detected_vars):
        new_history = agent._substitute_variables_in_history(
            history,
            {variable_name: new_email}
        )

    assert new_history.history[0].model_output is not None
    new_action = new_history.history[0].model_output.action[0]

    # Check if complex_op became a dict
    complex_op = getattr(new_action, 'complex_op')
    if isinstance(complex_op, dict):
        assert complex_op['details']["contact"]["email"] == new_email
        assert complex_op['tags'][1] == new_email
    else:
        assert complex_op.details["contact"]["email"] == new_email
        assert complex_op.tags[1] == new_email

def test_substitute_variables_no_match(agent):
    """Test that unrelated values are not modified"""
    original_value = "Keep Me"

    action = create_test_action_model("input", {"text": original_value})
    history = AgentHistoryList(history=[create_history_item(action)])

    detected_vars = {
        "some_var": DetectedVariable(name="some_var", original_value="Change Me")
    }

    with patch("browser_use.agent.variable_detector.detect_variables_in_history", return_value=detected_vars):
        new_history = agent._substitute_variables_in_history(
            history,
            {"some_var": "New Value"}
        )

    assert new_history.history[0].model_output is not None
    new_action = new_history.history[0].model_output.action[0]
    # It might be converted to dict even if no substitution happened, because the loop runs for all actions
    if isinstance(getattr(new_action, 'input'), dict):
        assert getattr(new_action, 'input')['text'] == original_value
    else:
        assert getattr(new_action, 'input').text == original_value

def test_substitute_variables_unknown_var(agent, caplog):
    """Test warning when variable is not found in history"""
    action = create_test_action_model("input", {"text": "something"})
    history = AgentHistoryList(history=[create_history_item(action)])

    detected_vars = {} # No variables detected

    with patch("browser_use.agent.variable_detector.detect_variables_in_history", return_value=detected_vars):
        with caplog.at_level(logging.WARNING):
            agent._substitute_variables_in_history(
                history,
                {"unknown_var": "value"}
            )

    assert "Variable \"unknown_var\" not found in history" in caplog.text

def test_substitute_multiple_variables(agent):
    """Test substituting multiple variables at once"""
    val1 = "Value1"
    val2 = "Value2"

    # Custom action with two fields
    Field1 = create_model('Field1', field1=(str, ...), field2=(str, ...))
    MultiAction = create_model('MultiAction', multi=(Field1, ...), __base__=ActionModel)

    action = MultiAction(multi=Field1(field1=val1, field2=val2)) # type: ignore
    history = AgentHistoryList(history=[create_history_item(action)])

    detected_vars = {
        "var1": DetectedVariable(name="var1", original_value=val1),
        "var2": DetectedVariable(name="var2", original_value=val2)
    }

    with patch("browser_use.agent.variable_detector.detect_variables_in_history", return_value=detected_vars):
        new_history = agent._substitute_variables_in_history(
            history,
            {"var1": "New1", "var2": "New2"}
        )

    assert new_history.history[0].model_output is not None
    new_action = new_history.history[0].model_output.action[0]
    multi = getattr(new_action, 'multi')
    if isinstance(multi, dict):
        assert multi['field1'] == "New1"
        assert multi['field2'] == "New2"
    else:
        assert multi.field1 == "New1"
        assert multi.field2 == "New2"
