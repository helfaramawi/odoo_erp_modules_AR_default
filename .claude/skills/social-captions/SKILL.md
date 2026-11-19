---
name: social-captions
description: Generate exactly 3 short Instagram captions for TBS The Bakery Shop (@tbsegypt, Cairo) from a topic and a tone. Use whenever the user asks for captions, posts, post ideas, or "something to post" about coffee, iced drinks, focaccia/sourdough sandwiches, breakfast, donuts, pastries, Egyptian desserts (Om Ali), seasonal kahk boxes, protein snacks, or this week's offers, in Arabic or English, e.g. "3 كابشن عن القهوة المثلجة، بروح مرحة" or "captions for our kahk boxes, cozy tone". Also works for any other bakery if the user describes it.
---

# Social Captions (TBS The Bakery Shop)

Turn a **topic** and a **tone** into **3 short, ready-to-post Instagram captions** for TBS.

## Default brand context

Use this unless the user gives their own "about your bakery" text (that text replaces it):

> **TBS The Bakery Shop** (@tbsegypt): an everyday bakery-café in Cairo. Coffee and iced drinks, focaccia and sourdough sandwiches, breakfast, donuts and pastries, Egyptian desserts, and seasonal treats.
> Brand line: «طزاجة في كل رشفة، وكل طبق وكل قضمة.»

## Inputs

| Input | Required | Default |
|---|---|---|
| Topic (موضوع) | Yes | — |
| Tone (الأسلوب) | No | friendly / ودود |
| Language | No | Arabic, Egyptian dialect (عامية مصرية). English if the user writes in English or asks for it. "Both" gives each caption in Arabic, then English under it. |
| About the bakery (عن مخبزك) | No | Brand context above |
| Extras | No | price, date, branch, offer, delivery app |

**Preset topics** (match loosely, in either language):
- القهوة والمشروبات المثلجة: coffee & iced drinks
- ساندويتشات الفوكاتشيا والساوردو: focaccia & sourdough sandwiches
- الفطار: breakfast
- الدونتس والمخبوزات: donuts & baked goods
- الحلويات المصرية (أم علي): Egyptian desserts (Om Ali)
- علب كحك الموسم: seasonal kahk boxes (Eid)
- سناكس البروتين: protein snacks
- هذا الأسبوع في TBS (العروض): this week at TBS (offers)

Any free-text topic is fine too. If there's no topic, ask one short question and list the presets. Don't ask about optional inputs; use the defaults.

## Rules

1. **Exactly 3 captions**, each taking a different angle:
   - **١ · حسّي / Sensory**: taste, smell, texture, temperature ("الكرواسون لسه طالع من الفرن").
   - **٢ · لحظة / Moment**: the Cairo moment it fits (the morning commute, a hot afternoon, suhoor, Friday with the family, a study session).
   - **٣ · دعوة / Call to action**: come in, order, tag a friend, or "before it runs out".
2. **Short**: 1–3 lines, at most ~220 characters before hashtags.
3. **Match the tone**: playful (مرح) → wordplay and light Egyptian slang; cozy (دافي) → warm and slow; elegant (راقي) → spare, clean MSA-leaning, few emojis; bold/urgent (حماسي) → short punchy lines and time pressure.
4. **Egyptian Arabic should sound native**, like "يلا", "الحق", "على الريق", "مزاج". Don't translate English idioms word for word. Keep product names the way customers say them: لاتيه، آيس كوفي، فوكاتشيا، ساوردو، دونتس، كحك.
5. **Emojis**: 0–3 per caption, matched to the tone.
6. **Hashtags**: 3–5 on a last line. Always include `#TBSEgypt`, then mix Arabic and English, e.g. `#القاهرة #قهوة #CairoEats #bakerycairo`.
7. **Use only facts the user gave or the brand context.** Never invent prices, discounts, dates, branches, ingredients, or health/allergen claims. For a missing detail, use a placeholder such as `[السعر]`, `[الفرع]`, or `[التاريخ]`.
8. Mention @tbsegypt or "TBS" in at most one caption. Avoid clichés like «لا تفوتوا الفرصة» and "We're excited to announce".
9. Kahk and Ramadan/Eid topics: be warm and seasonal. Don't make religious statements beyond ordinary greetings such as «كل سنة وانتم طيبين».

## Output format

Output only this, with no preamble:

```
**١ · حسّي**
<caption>
<hashtags>

**٢ · لحظة**
<caption>
<hashtags>

**٣ · دعوة**
<caption>
<hashtags>
```

For English output, use the headings `1 · Sensory`, `2 · Moment`, and `3 · Call to action`. After the captions you may add one line offering a tweak (e.g. «تحبها أقصر، أو بالإنجليزي؟»). Nothing else.

## Example

**Input:** topic «القهوة والمشروبات المثلجة», tone «مرح»

**Output:**

**١ · حسّي**
تلج بيطقطق، إسبريسو غامق، ورغوة حليب نازلة على مهلها… الصوت ده لوحده بيفوّق 🧊☕
#TBSEgypt #آيس_كوفي #قهوة #CairoCoffee

**٢ · لحظة**
الساعة ٣ العصر، والحر مش بيهزر، وانت محتاج حاجة تصالحك على اليوم. إحنا عارفين وجهزناها 😌
#TBSEgypt #القاهرة #مزاج #icedlatte

**٣ · دعوة**
منشن صاحبك اللي مابيشتغلش غير بالقهوة، وتعالوا TBS على حسابه 😉 الآيس لاتيه مستنيكم في [الفرع].
#TBSEgypt #CairoEats #قهوة_مثلجة #bakerycairo
