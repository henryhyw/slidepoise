# SlidePoise authoritative first-generation brief

Use the host image-generation capability to create the visual target. Preferred configured model: `gpt-image-2`. In ChatGPT use native image generation/editing; in Codex use the available image-generation skill/tool or bounded image-capable delegation. Do not replace this stage with Python plotting, HTML/SVG drawing, deterministic diagram generation, or a fixed template.

Treat exact content, canvas, explicit user requirements, selected assets, and PROFILE HARD RULES as authoritative. Interpret palette, typography, density, and icon treatment according to PROFILE STYLE AGENCY. Session and user overrides take precedence.

## ADAPTIVE GENERATION AND REVIEW
- Generate one well-considered initial candidate by default. Explore alternatives only when the user requests them or when the host Agent judges that the expected benefit justifies the additional creative call.
- Read and inspect the actual downloaded candidate before semantic mapping or reconstruction. The host Agent owns the visual judgement.
- When the user requested an automatic deck, continue without per-slide approval after correcting material issues. Pause only when an unresolved choice would materially change the brief, identity, evidence, page count, or creative-call cost.
- If the candidate has a localized material issue, prefer a targeted edit that preserves unaffected regions. Regenerate when the composition itself is unsuitable.
- Bind reconstruction and review records to the exact inspected visual target. A user-approved target, when one exists, remains authoritative until the user requests a change.

## NON-NEGOTIABLE: canvas and frame
- Generate exactly the substantive canvas at `1600 x 900` pixels (aspect ratio `1.777778`).
- This canvas excludes the Slide Master frame. Do not draw any header, footer, page number, or master-frame rule/decoration.

## NON-NEGOTIABLE: exact communication content
- Audience question: A second thinking system
- Dominant message: A second thinking system
- Required content:
```json
[
  "Working with AI without outsourcing a point of view.",
  "FIELD NOTES / 01",
  "An essay in five parts"
]
```
- Semantic relationships:
```json
[]
```
- Hierarchy:
```json
[
  "A second thinking system",
  "Working with AI without outsourcing a point of view.",
  "FIELD NOTES / 01",
  "An essay in five parts"
]
```
- Visual obligations:
```json
[
  "Keep required presentation copy visually clear and separable from artwork."
]
```

## COMPLETE AGREED PLAN
Preserve required facts, semantic relationships, qualifications and explicit constraints. Use optional context selectively without changing the agreed meaning. The plan describes information structure, not a required visual layout. Do not infer a numbered process from an array of content items.
```json
{
  "audience_question": "A second thinking system",
  "dominant_message": "A second thinking system",
  "information_structure": {
    "type": "opening",
    "description": "Visual composition follows the communication job and active profile."
  },
  "required_content": [
    "Working with AI without outsourcing a point of view.",
    "FIELD NOTES / 01",
    "An essay in five parts"
  ],
  "semantic_relationships": [],
  "hierarchy": [
    "A second thinking system",
    "Working with AI without outsourcing a point of view.",
    "FIELD NOTES / 01",
    "An essay in five parts"
  ],
  "evidence": [
    "An authored editorial essay for the SlidePoise showcase. First-person framing is illustrative and does not assert the user's personal history."
  ],
  "assumptions": [
    "An authored editorial essay for the SlidePoise showcase. First-person framing is illustrative and does not assert the user's personal history."
  ],
  "open_questions": [],
  "avoid": [
    "Generic dashboard cards",
    "Extra factual claims",
    "Decorative logos"
  ],
  "visual_obligations": [
    "Keep required presentation copy visually clear and separable from artwork."
  ],
  "user_required_assets": [],
  "density_intent": "balanced",
  "explicit_user_visual_requirements": []
}
```

## USER-FACING LANGUAGE
Write slide copy for the reader. Preserve user-authored wording and the language of the agreed plan. Use direct, specific sentences. Do not add ceremonial introductions, generic assistant phrases, empty transitions, or meta commentary about the slide. Do not use an em dash in newly authored copy. Avoid semicolons. Use a colon only when it materially improves a label, quotation, data value, or short lead-in. Profile writing guidance may add character while these clarity rules remain in force.
```json
{
  "preserve_user_language_and_wording": true,
  "reader_first": true,
  "new_copy_em_dash": "avoid",
  "new_copy_semicolon": "avoid",
  "new_copy_colon": "use_only_when_materially_clearer",
  "avoid_stock_assistant_phrasing": true,
  "avoid_meta_interface_explanations": true,
  "profile_may_extend_voice": true
}
```

## RESOLVED DESIGN SYSTEM
Concrete values are exact only when PROFILE STYLE AGENCY marks that dimension as `specified`. With `guided`, preserve the visual character while allowing a coherent adaptation. With `agent_decides` or `agent_decides_from_references`, use the values as reconstruction fallbacks and derive the generated visual from the profile purpose, approved references, and current content.
### Title
```json
{
  "anchor_px": [
    72,
    54
  ],
  "max_width_px": 1840,
  "font_family": "Georgia",
  "weight": "regular",
  "nominal_size_px": 72,
  "color": "#242321",
  "alignment": "left",
  "allowed_lines": [
    1,
    2
  ],
  "minimum_gap_to_body_px": 34
}
```
### Style
```json
{
  "icon_treatment": "agent_decides",
  "background": "#FBFAF8",
  "display_font": "Georgia",
  "body_font": "Arial",
  "density": "balanced",
  "accent_colors": [
    "#242321",
    "#505050",
    "#8F8F8F"
  ],
  "neutral_colors": [
    "#111111",
    "#242321",
    "#505050",
    "#8F8F8F",
    "#D8D7D3",
    "#E8E7E4",
    "#F4F3F0",
    "#FBFAF8",
    "#FFFFFF"
  ],
  "visual_language": "Monochrome editorial portfolio language with sharp rectangular modules, deliberate asymmetry, flat tonal fields, generous negative space, precise optical alignment, serif and humanist sans contrast, occasional archival texture, typewriter metadata, and restrained handwritten annotation.",
  "whitespace": "Treat empty space as active structure. Preserve clear outer margins and allow one dominant visual or statement to breathe."
}
```
### Typography size/spacing policies
Use these as the resolved typography scale when the corresponding visual text style is present.
```json
{
  "default": {
    "font_size_range_px": [
      14,
      24
    ],
    "line_spacing": 1.15,
    "inset_px": 2,
    "font_family": "Arial",
    "color": "#242321"
  },
  "slide_title": {
    "font_family": "Georgia",
    "font_size_range_px": [
      30,
      76
    ],
    "line_spacing": 1.0,
    "inset_px": 0,
    "color": "#242321"
  },
  "subtitle": {
    "font_size_range_px": [
      20,
      30
    ],
    "line_spacing": 1.08,
    "inset_px": 2
  },
  "section_number": {
    "font_size_range_px": [
      22,
      34
    ],
    "line_spacing": 1.0,
    "inset_px": 0
  },
  "heading_large": {
    "font_size_range_px": [
      20,
      28
    ],
    "line_spacing": 1.05,
    "inset_px": 2,
    "font_family": "Georgia",
    "font_weight": "regular",
    "color": "#242321"
  },
  "body": {
    "font_size_range_px": [
      16,
      22
    ],
    "line_spacing": 1.35,
    "inset_px": 2,
    "font_family": "Georgia",
    "font_weight": "regular",
    "color": "#505050"
  },
  "heading": {
    "font_size_range_px": [
      16,
      24
    ],
    "line_spacing": 1.1,
    "inset_px": 2,
    "font_family": "Arial",
    "font_weight": "bold",
    "color": "#242321"
  },
  "body_standard": {
    "font_size_range_px": [
      15,
      22
    ],
    "line_spacing": 1.35,
    "inset_px": 2,
    "font_family": "Georgia",
    "font_weight": "regular",
    "color": "#505050"
  },
  "heading_compact": {
    "font_size_range_px": [
      15.5,
      23
    ],
    "line_spacing": 1.06,
    "inset_px": 2
  },
  "body_compact": {
    "font_size_range_px": [
      14,
      20
    ],
    "line_spacing": 1.25,
    "inset_px": 2,
    "font_family": "Arial",
    "font_weight": "regular",
    "color": "#505050"
  },
  "label": {
    "font_size_range_px": [
      14,
      21
    ],
    "line_spacing": 1.0,
    "inset_px": 2,
    "font_family": "Arial",
    "font_weight": "bold",
    "color": "#242321"
  },
  "emphasis_label": {
    "font_size_range_px": [
      20,
      34
    ],
    "line_spacing": 1.0,
    "inset_px": 2,
    "font_family": "Courier New",
    "font_weight": "regular",
    "color": "#505050"
  },
  "quote": {
    "font_family": "Georgia",
    "font_weight": "regular",
    "color": "#242321",
    "line_spacing": 1.2
  },
  "large_data_number": {
    "font_family": "Georgia",
    "font_weight": "regular",
    "color": "#242321",
    "line_spacing": 1.0
  }
}
```
### Exact semantic style tokens
Use these only when the corresponding semantic treatment is appropriate; do not substitute approximate colours or fonts.
```json
{
  "accent_badge": {
    "fill": "#242321",
    "text_color": "#FBFAF8",
    "font_weight": "bold"
  },
  "muted_panel": {
    "fill": "#F4F3F0",
    "text_color": "#242321"
  },
  "primary_text": {
    "color": "#242321"
  },
  "secondary_text": {
    "color": "#686868"
  },
  "dark_field": {
    "fill": "#1C1C1E",
    "text_color": "#F4F1EC"
  },
  "archive_paper": {
    "fill": "#F1ECE2",
    "text_color": "#242321"
  },
  "typewriter_label": {
    "font_family": "Courier New",
    "color": "#505050",
    "font_weight": "regular"
  },
  "handwritten_note": {
    "font_family": "Segoe Print",
    "color": "#686868",
    "font_weight": "regular"
  }
}
```
### Data-visualisation defaults
```json
{
  "default_level": 1,
  "default_series_colors": [
    "#242321",
    "#505050",
    "#8F8F8F",
    "#B8B7B3",
    "#D8D7D3",
    "#E8E7E4"
  ],
  "key_data_color": "#242321",
  "chart_title_font": "Georgia",
  "data_font": "Arial",
  "allow_gradient_in_default_level": false,
  "gridline_color": "#D8D7D3"
}
```
### Explicit user visual requirements
```json
[]
```
### Icon slot rule
For every icon, reserve a visually unambiguous bounded slot that protects its room from surrounding content. The icon may have no designed surface or may sit on a profile-approved background surface. When there is no designed surface, a subtle generation-only boundary may mark the slot for localization; that boundary is scaffolding, not a decorative container and is not reconstructed downstream. When the icon sits on a larger colored panel/card and no distinct icon tile is intended, the downstream reconstruction should keep the icon background transparent rather than turning the scaffold into a white box.

## PROFILE HARD RULES: Editorial Archive (personal-website)
These rules control the visual system but not the slide's exact composition.
```json
{
  "icons": {
    "default_treatment": "neutral_outline",
    "proxy_treatments": [
      {
        "id": "neutral_outline",
        "description": "Thin neutral outline icon with no enclosing badge.",
        "glyph_color": "#242321",
        "surface": "none"
      },
      {
        "id": "inverse_outline",
        "description": "Off-white outline icon used directly on a dark field.",
        "glyph_color": "#F4F1EC",
        "surface": "none"
      }
    ]
  },
  "color": [
    "Do not introduce green as a presentation accent. Preserve exact canonical asset identity when a required source contains green."
  ],
  "geometry": [
    "Core information modules use square corners or an optically negligible radius.",
    "Rounded media frames may use a restrained radius only when inherited from a photographed or embedded interface.",
    "Avoid repeated floating cards. Build a composed page from fields, rules, blocks, and negative space."
  ],
  "typography": {
    "font_family_policy": "agent_observed",
    "italics_allowed": true,
    "tracking_allowed": true
  },
  "composition": [
    "Each slide has one dominant statement or visual field.",
    "Use asymmetry deliberately and balance it through scale, alignment, and empty space.",
    "Use blocks to organize evidence. Do not imitate a product dashboard."
  ],
  "reconstruction": [
    "The Agent decides which visual regions carry irreducible texture and may remain raster.",
    "Mechanical validation confirms package and geometry facts only. The Agent must visually compare the accepted image, measured overlay, rendered PowerPoint, and difference view before release.",
    "Connector routes require an Agent-authored visual route decision. A script-generated route is only a candidate."
  ]
}
```

## PROFILE STYLE AGENCY
```json
{
  "palette": "agent_decides_from_references",
  "typography": "guided",
  "density": "guided",
  "icon_treatment": "agent_decides_within_profile"
}
```

## PROFILE DESIGN GUIDANCE
- Purpose: Create tactile editorial slides with archival paper, collage, documentary imagery, typewriter detail and restrained handwritten marks.
- Density profile: balanced
- Density guidance:
```json
{
  "generation_guidance": [
    "Use the substantive canvas efficiently while retaining clear separation between information groups.",
    "Balance whitespace across the composition rather than leaving one large accidental dead zone."
  ],
  "visual_review_guidance": [
    "Reject conspicuous unused peripheral regions that do not support hierarchy.",
    "Keep the page readable without making it sparse or crowded."
  ]
}
```
- Visual principles:
- Writing principles:
- Avoid:

## Attachments and their roles
- Attach the same style and asset context sheet reviewed by the user: `/Users/henry/Codes/AI_slide_drafting/examples/personal-thinking-system/run/slides/s01-opening/work/generation-context-sheet.png`.
- Style swatches, typeface labels and context-sheet arrangement explain the visual vocabulary. They are not slide content or a slide-layout template. Apply the recorded creative-freedom settings.
- Agreed slide-specific visual direction:
```json
{
  "intent": "A coherent five-page editorial deck with varied content-led compositions. Typography remains native in the final deck.",
  "freedom": "Use the profile visual language. Avoid copying reference content or composition."
}
```
- Visual reference `showcase-style-reference`: attach `/Users/henry/Codes/AI_slide_drafting/profiles/personal-website/libraries/visual_references/editorial-archive.png`.
  - Why attached: Profile visual language only. Exact new content is in the slide intent.
  - Use as a visual/style/communication precedent only unless the user explicitly authorized factual-content reuse.
- No reusable component precedent selected; design components freely.
- No selected canonical assets.

## COMPOSITION FREEDOM
- Choose the visual composition, grouping structure, exact object placement, connector arrangement, and emphasis system that best communicates the semantic intent.
- Do not force a fixed template, grid, card count, chart archetype, component precedent, or one icon treatment when another composition better supports the slide.
- Preserve compositional freedom without relaxing resolved design values, profile hard rules, content, asset, or canvas constraints.
- Density is a separate user/session control. Apply the selected density inside the profile rather than equating the profile with sparse or dense composition.

Before sending the image-generation call, attach every selected visual reference, component preview, and asset above that is available to the host and use this brief as the authoritative generation instruction.
