{
    'name': 'Social Caption Generator / مولد كابشنز السوشيال ميديا',
    'version': '17.0.1.0.0',
    'category': 'Marketing',
    'summary': 'Generate 3 short social media captions from a topic and a tone (Arabic / English)',
    'description': """
Social Caption Generator
========================
Enter a topic and pick a tone; get 3 short, ready-to-post captions
(sensory, moment, call to action) with hashtags, in Arabic, English or both.

* Works out of the box with a built-in offline generator (no AI service needed).
* Uses Claude automatically when an Anthropic API key is set in
  Settings > Social Captions, or in the ANTHROPIC_API_KEY environment variable.
""",
    'author': 'ERP Migration Team',
    'depends': ['base_setup'],
    'external_dependencies': {'python': ['requests']},
    'data': [
        'security/ir.model.access.csv',
        'views/caption_request_views.xml',
        'views/res_config_settings_views.xml',
        'data/sample_requests.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'social_caption_generator/static/src/css/social_caption.css',
        ],
    },
    'post_init_hook': 'post_init_hook',
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
