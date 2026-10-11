"""Caption generation engines, kept free of ORM code so they are easy to test.

* ``generate_offline`` builds captions from phrase banks. It needs no network
  and always succeeds, so a demo works anywhere.
* ``generate_with_claude`` asks Claude through the Anthropic Messages API.
"""
import json
import random
import re

import requests

ANGLES = ('sensory', 'moment', 'cta')

ANTHROPIC_URL = 'https://api.anthropic.com/v1/messages'
DEFAULT_MODEL = 'claude-opus-5-5'

TONE_LABELS = {
    'friendly': 'friendly (ودود)',
    'playful': 'playful (مرح)',
    'warm': 'warm and cozy (دافئ)',
    'elegant': 'elegant and professional (راقٍ)',
    'bold': 'bold and urgent (حماسي)',
}

PLATFORM_LIMITS = {
    # platform: (max characters per caption, max hashtags)
    'instagram': (2200, 5),
    'facebook': (2200, 3),
    'tiktok': (2200, 5),
    'linkedin': (3000, 2),
    'x': (280, 2),
}

# ---------------------------------------------------------------------------
# Offline phrase banks
# ---------------------------------------------------------------------------

TONES = {
    'en': {
        'friendly': {
            'hooks': ['Meet', 'Say hello to', "Here's"],
            'ctas': ['Drop by and say hi.', 'Come see us soon.', 'Send us a message to learn more.'],
            'emoji': ['😊', '👋', '✨'],
        },
        'playful': {
            'hooks': ['Plot twist:', 'Breaking news:', 'Big news:'],
            'ctas': ['Your move. 😉', "Don't say we didn't warn you.", 'Go on, treat yourself.'],
            'emoji': ['😉', '🎉', '🙌'],
        },
        'warm': {
            'hooks': ['Slow down with', 'Make room for', 'Settle in with'],
            'ctas': ['Come in and stay a while.', 'We saved you a spot.', "Take your time, we'll be here."],
            'emoji': ['🤍', '☕', '🌙'],
        },
        'elegant': {
            'hooks': ['Introducing', 'Presenting', 'Discover'],
            'ctas': ['Learn more today.', 'Book your visit.', 'Contact us for details.'],
            'emoji': ['', '✨', ''],
        },
        'bold': {
            'hooks': ['Now live:', 'Just dropped:', "Don't miss"],
            'ctas': ['Limited time. Act now.', 'Only until [date]. Go.', 'First come, first served.'],
            'emoji': ['🔥', '⚡', '🚀'],
        },
    },
    'ar': {
        'friendly': {
            'hooks': ['تعرّف على', 'نقدّم لكم', 'جديدنا:'],
            'ctas': ['زورونا قريبًا.', 'راسلونا لمعرفة المزيد.', 'في انتظاركم!'],
            'emoji': ['😊', '👋', '✨'],
        },
        'playful': {
            'hooks': ['خبر عاجل:', 'مفاجأة:', 'انتبهوا:'],
            'ctas': ['الدور عليك! 😉', 'لا تقولوا إننا لم نخبركم.', 'دلّل نفسك.'],
            'emoji': ['😉', '🎉', '🙌'],
        },
        'warm': {
            'hooks': ['خُذ وقتك مع', 'لحظة هادئة مع', 'استمتع بـ'],
            'ctas': ['تعالوا واستمتعوا براحتكم.', 'مكانك محجوز عندنا.', 'نحن في انتظارك.'],
            'emoji': ['🤍', '☕', '🌙'],
        },
        'elegant': {
            'hooks': ['نقدّم', 'اكتشف', 'بكل فخر نقدّم'],
            'ctas': ['تواصل معنا للتفاصيل.', 'احجز زيارتك اليوم.', 'اعرف المزيد الآن.'],
            'emoji': ['', '✨', ''],
        },
        'bold': {
            'hooks': ['متاح الآن:', 'وصل حالًا:', 'لا يفوتك:'],
            'ctas': ['لفترة محدودة. سارع!', 'حتى [التاريخ] فقط.', 'الكمية محدودة.'],
            'emoji': ['🔥', '⚡', '🚀'],
        },
    },
}

TEMPLATES = {
    'en': {
        'sensory': [
            '{hook} {topic}{brand}: fresh, carefully made, and even better in person. {e}',
            '{hook} {topic}{brand}. Every detail is there for a reason, and you can feel it. {e}',
        ],
        'moment': [
            'Some days need a small win. {topic} is ours. What is yours? {e}',
            'Picture it: a busy week, a short break, and {topic} waiting for you. {e}',
            'Made for the moments that matter, big or small: {topic}{brand}. {e}',
        ],
        'cta': [
            '{cta} Ask us about {topic}{brand}. {e}',
            'Tag someone who needs to see this: {topic}{brand}. {cta} {e}',
        ],
    },
    'ar': {
        'sensory': [
            '{hook} {topic}{brand}: تفاصيل مصنوعة بعناية وجودة تشعر بها من أول نظرة. {e}',
            '{hook} {topic}{brand}. كل تفصيلة لها سبب، وستلاحظ الفرق. {e}',
        ],
        'moment': [
            'وسط أسبوع مزدحم، تستحق لحظة جميلة. {topic} هنا من أجلك. {e}',
            'لكل لحظة مهمة، كبيرة أو صغيرة: {topic}{brand}. {e}',
            'تخيّل: يوم طويل، استراحة قصيرة، و{topic} في انتظارك. {e}',
        ],
        'cta': [
            '{cta} اسألنا عن {topic}{brand}. {e}',
            'منشن شخصًا يجب أن يرى هذا: {topic}{brand}. {cta} {e}',
        ],
    },
}

GENERIC_TAGS = {
    'en': ['#SmallBusiness', '#ShopLocal', '#NewArrival'],
    'ar': ['#جديد', '#تسوق_محلي', '#مشاريع_صغيرة'],
}

_ARABIC = re.compile(r'[؀-ۿ]')


def _hashtag(text, camel):
    words = re.findall(r'\w+', text or '')
    if not words:
        return ''
    if camel:
        return '#' + ''.join(w[:1].upper() + w[1:] for w in words)
    return '#' + '_'.join(words)


def _hashtags(topic, business_name, lang, rng):
    camel = lang == 'en' and not _ARABIC.search(topic or '')
    tags = [_hashtag(topic, camel), _hashtag(business_name, True)]
    generic = list(GENERIC_TAGS[lang])
    rng.shuffle(generic)
    tags += generic
    seen, out = set(), []
    for tag in tags:
        if tag and len(tag) > 1 and tag.lower() not in seen:
            seen.add(tag.lower())
            out.append(tag)
    return out


def _offline_text(lang, angle, tone, topic, business_name, rng):
    bank = TONES[lang].get(tone) or TONES[lang]['friendly']
    if business_name:
        brand = (' من ' if lang == 'ar' else ' from ') + business_name
    else:
        brand = ''
    text = rng.choice(TEMPLATES[lang][angle]).format(
        hook=rng.choice(bank['hooks']),
        topic=topic,
        brand=brand,
        cta=rng.choice(bank['ctas']),
        e=rng.choice(bank['emoji']),
    )
    return re.sub(r'\s+', ' ', text).strip()


def generate_offline(topic, tone='friendly', language='ar', business_name='', seed=None):
    """Return 3 caption dicts: {angle, text, text_en, hashtags}."""
    rng = random.Random(seed)
    topic = (topic or '').strip()
    business_name = (business_name or '').strip()
    main_lang = 'en' if language == 'en' else 'ar'
    captions = []
    for angle in ANGLES:
        caption = {
            'angle': angle,
            'text': _offline_text(main_lang, angle, tone, topic, business_name, rng),
            'text_en': '',
            'hashtags': _hashtags(topic, business_name, main_lang, rng),
        }
        if language == 'both':
            caption['text_en'] = _offline_text('en', angle, tone, topic, business_name, rng)
            caption['hashtags'] += _hashtags(topic, business_name, 'en', rng)[:2]
        captions.append(caption)
    return captions


# ---------------------------------------------------------------------------
# Claude
# ---------------------------------------------------------------------------

def build_prompt(topic, tone='friendly', language='ar', platform='instagram',
                 business_name='', business_description='', extra_facts=''):
    language_rule = {
        'ar': 'Write the captions in clear, natural Arabic.',
        'en': 'Write the captions in English.',
        'both': ('Write each caption in natural Arabic in "text", and an English version '
                 'of the same caption in "text_en".'),
    }.get(language, 'Write the captions in clear, natural Arabic.')
    max_chars, max_tags = PLATFORM_LIMITS.get(platform, PLATFORM_LIMITS['instagram'])
    about = business_description or business_name or 'not given'
    return '\n'.join([
        'You write social media captions for a business. Produce exactly 3 short captions '
        'for the topic and tone below.',
        '',
        'Business: %s' % (business_name or 'not named'),
        'About the business: %s' % about,
        'Platform: %s' % platform,
        'Topic: %s' % topic,
        'Tone: %s' % TONE_LABELS.get(tone, tone),
        'Facts the user supplied: %s' % (extra_facts or 'none'),
        '',
        'Rules:',
        '- Caption 1 angle "sensory": what it looks, feels, tastes or works like.',
        '- Caption 2 angle "moment": the real situation or occasion it fits into.',
        '- Caption 3 angle "cta": a clear call to action.',
        '- Each caption 1-3 sentences, at most about 220 characters before hashtags '
        '(never more than %d characters including hashtags). 0-3 emojis matched to the tone.'
        % max_chars,
        '- Up to %d hashtags per caption, specific to the topic.' % max_tags,
        '- Use only facts given above. Never invent prices, discounts, dates, locations or '
        'product claims. Use placeholders such as [price], [date], [السعر], [التاريخ] instead.',
        '- No cliches such as "Look no further" or "We are excited to announce".',
        '- ' + language_rule,
        '',
        'Reply with only this JSON and no other text:',
        '{"captions": [{"angle": "sensory", "text": "...", "text_en": "", "hashtags": ["#..."]}, '
        '{"angle": "moment", ...}, {"angle": "cta", ...}]}',
    ])


def parse_captions(raw):
    """Read the JSON reply tolerantly and return 3 caption dicts."""
    candidates = [raw]
    fence = re.search(r'```(?:json)?\s*(.*?)```', raw or '', re.S)
    if fence:
        candidates.append(fence.group(1))
    start, end = (raw or '').find('{'), (raw or '').rfind('}')
    if start != -1 and end > start:
        candidates.append(raw[start:end + 1])
    data = None
    for candidate in candidates:
        try:
            data = json.loads(candidate)
            break
        except (TypeError, ValueError):
            continue
    items = data.get('captions') if isinstance(data, dict) else data
    if not isinstance(items, list):
        raise ValueError('The reply did not contain a captions list.')
    captions = []
    for index, item in enumerate(items[:3]):
        if not isinstance(item, dict) or not str(item.get('text') or '').strip():
            continue
        tags = item.get('hashtags') or []
        captions.append({
            'angle': item.get('angle') if item.get('angle') in ANGLES else ANGLES[index],
            'text': str(item['text']).strip(),
            'text_en': str(item.get('text_en') or '').strip(),
            'hashtags': [str(t) for t in tags] if isinstance(tags, list) else [],
        })
    if len(captions) != 3:
        raise ValueError('Expected 3 captions, got %d.' % len(captions))
    return captions


class ClaudeError(Exception):
    pass


def generate_with_claude(api_key, prompt, model=DEFAULT_MODEL, timeout=90):
    try:
        response = requests.post(
            ANTHROPIC_URL,
            headers={
                'content-type': 'application/json',
                'x-api-key': api_key,
                'anthropic-version': '2023-06-01',
                'anthropic-beta': 'server-side-fallback-2026-07-01',
            },
            json={
                'model': model or DEFAULT_MODEL,
                'max_tokens': 4000,
                'fallbacks': 'default',
                'output_config': {'effort': 'low'},
                'messages': [{'role': 'user', 'content': prompt}],
            },
            timeout=timeout,
        )
    except requests.RequestException as exc:
        raise ClaudeError('Could not reach api.anthropic.com (%s).' % exc.__class__.__name__)
    try:
        body = response.json()
    except ValueError:
        body = {}
    if response.status_code != 200:
        message = (body.get('error') or {}).get('message') or response.reason
        raise ClaudeError('Claude API error %s: %s' % (response.status_code, message))
    if body.get('stop_reason') == 'refusal':
        raise ClaudeError('Claude declined this topic.')
    text = '\n'.join(
        block.get('text', '') for block in body.get('content', []) if block.get('type') == 'text'
    )
    try:
        return parse_captions(text)
    except ValueError as exc:
        raise ClaudeError(str(exc))


# ---------------------------------------------------------------------------
# Formatting
# ---------------------------------------------------------------------------

def format_caption(caption, platform='instagram'):
    """One copy-ready block: caption, optional English version, then hashtags."""
    max_chars, max_tags = PLATFORM_LIMITS.get(platform, PLATFORM_LIMITS['instagram'])
    tags = ' '.join(caption.get('hashtags', [])[:max_tags])
    parts = [caption['text']]
    if caption.get('text_en'):
        parts.append(caption['text_en'])
    if tags:
        parts.append(tags)
    text = '\n\n'.join(parts)
    if len(text) > max_chars:
        text = text[:max_chars - 1].rstrip() + '…'
    return text
