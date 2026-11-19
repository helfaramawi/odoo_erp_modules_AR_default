import json
from unittest.mock import MagicMock, patch

from odoo.tests import TransactionCase, tagged

from ..models import caption_engine

POST = 'odoo.addons.social_caption_generator.models.caption_engine.requests.post'


def _api_reply(status=200, body=None):
    reply = MagicMock(status_code=status, reason='OK' if status == 200 else 'Error')
    reply.json.return_value = body or {}
    return reply


@tagged('post_install', '-at_install')
class TestSocialCaptions(TransactionCase):

    def setUp(self):
        super().setUp()
        self.env['ir.config_parameter'].sudo().set_param('social_caption_generator.api_key', '')
        self.request = self.env['social.caption.request'].create({
            'name': 'New iced coffee menu',
            'tone': 'playful',
            'language': 'en',
            'business_name': 'Demo Café',
        })

    def test_offline_engine_shapes(self):
        for language in ('ar', 'en', 'both'):
            for tone in ('friendly', 'playful', 'warm', 'elegant', 'bold'):
                caps = caption_engine.generate_offline('قهوة مثلجة', tone, language, 'Demo', seed=1)
                self.assertEqual([c['angle'] for c in caps], ['sensory', 'moment', 'cta'])
                for cap in caps:
                    self.assertIn('قهوة مثلجة', cap['text'])
                    self.assertTrue(cap['hashtags'])
                    self.assertEqual(bool(cap['text_en']), language == 'both')

    def test_generate_without_key_uses_builtin(self):
        with patch.dict('os.environ', {'ANTHROPIC_API_KEY': ''}), patch(POST) as post:
            self.request.action_generate()
        post.assert_not_called()
        self.assertEqual(self.request.state, 'done')
        self.assertEqual(self.request.engine, 'offline')
        for field in ('caption_1', 'caption_2', 'caption_3'):
            self.assertIn('New iced coffee menu', self.request[field])

    def test_generate_with_claude(self):
        self.env['ir.config_parameter'].sudo().set_param('social_caption_generator.api_key', 'sk-ant-test')
        captions = {'captions': [
            {'angle': 'sensory', 'text': 'Ice, espresso, slow milk swirl.', 'hashtags': ['#IcedCoffee']},
            {'angle': 'moment', 'text': '3 pm slump? Fixed.', 'hashtags': ['#CoffeeBreak']},
            {'angle': 'cta', 'text': 'Tag your coffee buddy.', 'hashtags': ['#DemoCafe']},
        ]}
        body = {'stop_reason': 'end_turn', 'content': [
            {'type': 'thinking', 'thinking': ''},
            {'type': 'text', 'text': '```json\n%s\n```' % json.dumps(captions)},
        ]}
        with patch(POST, return_value=_api_reply(200, body)) as post:
            self.request.action_generate()
        headers = post.call_args.kwargs['headers']
        payload = post.call_args.kwargs['json']
        self.assertEqual(headers['x-api-key'], 'sk-ant-test')
        self.assertEqual(payload['model'], 'claude-opus-5-5')
        self.assertIn('New iced coffee menu', payload['messages'][0]['content'])
        self.assertEqual(self.request.engine, 'claude')
        self.assertEqual(self.request.caption_1, 'Ice, espresso, slow milk swirl.\n\n#IcedCoffee')

    def test_claude_failure_falls_back(self):
        self.env['ir.config_parameter'].sudo().set_param('social_caption_generator.api_key', 'bad-key')
        body = {'error': {'message': 'invalid x-api-key'}}
        with patch(POST, return_value=_api_reply(401, body)):
            self.request.action_generate()
        self.assertEqual(self.request.engine, 'offline')
        self.assertIn('401', self.request.generation_note)
        self.assertTrue(self.request.caption_3)

    def test_x_platform_limits(self):
        self.request.platform = 'x'
        with patch.dict('os.environ', {'ANTHROPIC_API_KEY': ''}):
            self.request.action_generate()
        for field in ('caption_1', 'caption_2', 'caption_3'):
            self.assertLessEqual(len(self.request[field]), 280)
            self.assertLessEqual(self.request[field].count('#'), 2)

    def test_sample_data_generated_at_install(self):
        sample = self.env.ref('social_caption_generator.sample_request_coffee')
        self.assertEqual(sample.state, 'done')
        self.assertIn('قائمة القهوة المثلجة الجديدة', sample.caption_1)
