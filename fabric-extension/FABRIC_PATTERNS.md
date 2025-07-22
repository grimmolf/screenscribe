# Fabric Pattern Documentation

This document details the specialized Fabric patterns included with Screenscribe, particularly the enhanced `extract_trading_strategy` pattern designed for accurate content extraction.

## 🎯 extract_trading_strategy Pattern

### Overview
The `extract_trading_strategy` pattern has been specifically designed to combat AI hallucination and provide faithful extraction of trading methodologies, particularly for unconventional approaches like ICT (Inner Circle Trader) concepts.

### Key Features

**🚫 Anti-Hallucination Design**
- Only extracts concepts explicitly mentioned by the speaker
- Prohibits addition of conventional trading wisdom (Fibonacci, candlesticks, etc.)
- Uses speaker's exact terminology instead of generic trading language
- Marks missing sections as "*Not discussed*" rather than inventing content

**📝 Faithful Content Extraction**  
- Preserves unique methodologies (e.g., ICT's "seeking liquidity", "fair value gaps")
- Includes direct quotes to validate each extracted point
- Maintains speaker's language and conceptual framework
- Avoids standardization that dilutes original teachings

**🔍 Verification Features**
- Requires direct quotes supporting each section
- Flags uncertain content with `[NEEDS VERIFICATION]` markers
- Documents what is NOT discussed to prevent assumption gaps

### Output Format

The pattern generates structured output with six main sections:

```markdown
# STRATEGY_NAME
**[Exact name/title mentioned by speaker]**

# ENTRY_RULES
[Specific entry conditions using speaker's terminology]
[If not mentioned: "*Not discussed*"]

# EXIT_RULES  
[Exit criteria as stated by speaker]
[If not mentioned: "*Not discussed*"]

# RISK_PARAMETERS
[Risk management specifically mentioned]
[If not mentioned: "*Not discussed*"]

# MARKET_CONDITIONS
[Conditions/requirements mentioned by speaker]
[If not mentioned: "*Not discussed*"]

# PERFORMANCE_METRICS
[Metrics specifically stated by speaker]
[If not mentioned: "*Not discussed*"]
```

### Usage Examples

**Basic transcript-only extraction:**
```bash
scribe analyze trading_video.mp4 | fabric -p extract_trading_strategy
```

**With visual analysis for comprehensive extraction:**
```bash
scribe analyze --generate-captions trading_video.mp4 | fabric -p extract_trading_strategy
```

**High-quality analysis with premium vision model:**
```bash
scribe analyze --generate-captions --captions-two-pass --captions-rich-model qwen2.5vl:72b trading_video.mp4 | fabric -p extract_trading_strategy
```

### Common Issues and Solutions

**Problem**: AI adding conventional trading concepts not mentioned
**Solution**: Pattern now prohibits external knowledge injection

**Problem**: Standardizing unique terminology  
**Solution**: Pattern preserves speaker's exact language and concepts

**Problem**: Filling gaps with assumptions
**Solution**: Pattern marks missing sections as "*Not discussed*"

**Problem**: Losing validation trail
**Solution**: Pattern requires direct quotes for each extracted point

### Pattern Design Philosophy

This pattern embodies a **content-first** approach:

1. **Fidelity over completeness** - Better to have accurate incomplete information than complete inaccurate information
2. **Speaker's voice preserved** - Maintains original terminology and conceptual frameworks
3. **Transparent gaps** - Explicitly shows what wasn't covered rather than inventing content
4. **Verifiable extraction** - Every point backed by direct quotes from the source material

### ICT-Specific Enhancements

The pattern has been specifically optimized for ICT (Inner Circle Trader) methodologies:

- **Recognizes ICT terminology**: "seeking liquidity", "fair value gaps", "market structure shifts"
- **Avoids conventional bias**: Won't add Fibonacci levels, standard candlestick patterns
- **Preserves time-based approach**: Captures specific time windows (3-4 AM, 10-11 AM, 2-3 PM)
- **Respects unconventional logic**: Doesn't force content into standard trading frameworks

### Contributing

When improving the pattern, maintain these principles:

1. **Never add external knowledge** - Extract only what's explicitly stated
2. **Preserve speaker terminology** - Don't translate to "standard" trading language  
3. **Mark gaps transparently** - Use "*Not discussed*" for missing sections
4. **Require verification** - Every extracted point needs a supporting quote
5. **Respect methodology uniqueness** - Don't force unconventional approaches into conventional frameworks

This approach ensures users receive accurate, faithful extractions of trading methodologies while maintaining the integrity of the original teaching.