import asyncio
import json
import unittest
from unittest.mock import AsyncMock, Mock, patch

from agents.tool_context import ToolContext

from commongrown.ai import AgentModel, build_agent, obj, STRING


class SDKTests(unittest.TestCase):
    def test_context_is_scoped_and_submission_can_repair_validation(self):
        agent, audit = build_agent('COMPANY_A_ONLY', obj({'reply': STRING}), 'test-model')
        tools = {tool.name: tool for tool in agent.tools}
        async def exercise():
            rejected = await tools['submit_result'].on_invoke_tool(ToolContext(context=None, tool_name='test', tool_call_id='call', tool_arguments='{}'), json.dumps({'result_json': '{"reply":"too early"}'}))
            self.assertFalse(rejected['accepted'])
            context = await tools['read_scoped_context'].on_invoke_tool(ToolContext(context=None, tool_name='test', tool_call_id='call', tool_arguments='{}'), '{}')
            self.assertIn('COMPANY_A_ONLY', context)
            self.assertNotIn('COMPANY_B', context)
            rejected = await tools['submit_result'].on_invoke_tool(ToolContext(context=None, tool_name='test', tool_call_id='call', tool_arguments='{}'), json.dumps({'result_json': '{"wrong":1}'}))
            self.assertFalse(rejected['accepted'])
            valid = await tools['submit_result'].on_invoke_tool(ToolContext(context=None, tool_name='test', tool_call_id='call', tool_arguments='{}'), json.dumps({'result_json': '{"reply":"ok"}'}))
            self.assertTrue(valid['accepted'])
            final = await agent.tool_use_behavior(None, [Mock(output=valid)])
            self.assertTrue(final.is_final_output)
            self.assertEqual(json.loads(final.final_output), {'reply': 'ok'})
        asyncio.run(exercise())
        self.assertEqual(audit, {'context_reads': 1, 'submissions': 3, 'accepted': True})

    def test_context_does_not_survive_next_agent_creation(self):
        first, _ = build_agent('FIRST_SECRET', obj({'reply': STRING}), 'test-model')
        second, _ = build_agent('SECOND_SECRET', obj({'reply': STRING}), 'test-model')
        output = asyncio.run(second.tools[0].on_invoke_tool(ToolContext(context=None, tool_name='test', tool_call_id='call', tool_arguments='{}'), '{}'))
        self.assertNotIn('FIRST_SECRET', output)
        self.assertIn('SECOND_SECRET', output)

    @patch('commongrown.ai.Runner.run', new_callable=AsyncMock)
    def test_failure_does_not_echo_credentials_or_provider_response(self, run):
        run.side_effect = RuntimeError('SECRET_API_KEY provider payload')
        with patch.dict('os.environ', {'AGENT_BASE_URL': 'https://example.com/v1', 'AGENT_MODEL': 'test', 'AGENT_API_KEY': 'secret'}):
            with self.assertRaises(RuntimeError) as raised:
                AgentModel().generate('private prompt', obj({'reply': STRING}))
        self.assertNotIn('SECRET_API_KEY', str(raised.exception))
        self.assertNotIn('private prompt', str(raised.exception))
        self.assertTrue(run.call_args.kwargs['run_config'].tracing_disabled)
        self.assertLessEqual(run.call_args.kwargs['max_turns'], 5)

    @patch('commongrown.ai.Runner.run', new_callable=AsyncMock)
    def test_model_cannot_bypass_tool_validation_with_final_text(self, run):
        run.return_value = Mock(final_output={'reply': 'bypass'})
        with patch.dict('os.environ', {'AGENT_BASE_URL': 'https://example.com/v1', 'AGENT_MODEL': 'test', 'AGENT_API_KEY': 'secret'}):
            with self.assertRaises(RuntimeError):
                AgentModel().generate('request', obj({'reply': STRING}))
