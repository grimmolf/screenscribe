# Extract Trading Strategy Pattern

This Fabric pattern extracts structured trading strategies from video content, combining transcript analysis with visual chart captions to create actionable trading plans.

## Purpose

Converts trading education videos into structured, searchable strategy documents that can be:
- Easily referenced during live trading
- Parsed by downstream automation
- Organized into a strategy library
- Shared with team members

## Input Requirements

This pattern expects JSON input from `scribe analyze` or `scribe captions` with:

```json
{
  "transcript": {
    "text": "Complete transcript text...",
    "segments": [...],
    "language": "en"
  },
  "captions": {
    "frames": [
      {
        "frame": "frame_0123.jpg",
        "timestamp": 194.0,
        "caption": "Trading chart showing SPY with candlesticks",
        "ocr": "SPY 450.23 VWAP 449.85",
        "model": "moondream:1.8b",
        "source": "fast"
      }
    ]
  }
}
```

## Usage Examples

### Basic Usage
```bash
# Complete workflow with visual analysis
scribe analyze trading_video.mp4 | fabric -p extract_trading_strategy
```

### With Custom Frame Intervals
```bash
# More frequent frames for detailed analysis
scribe analyze --frame-interval 15 day_trade_setup.mp4 | fabric -p extract_trading_strategy
```

### Transcript-Only Mode
```bash
# Audio-only content without charts
scribe analyze --skip-frames trading_podcast.mp3 | fabric -p extract_trading_strategy
```

### YouTube Trading Content
```bash
# Process YouTube trading tutorials
scribe analyze "https://youtube.com/watch?v=VIDEO_ID" | fabric -p extract_trading_strategy
```

## Output Format

The pattern produces structured Markdown with these six sections:

```markdown
# Strategy Summary – SPY (5-minute)

## 1. Trade Setup
- Asset: SPY
- Timeframe: 5-minute chart
- Setup: Consolidation pattern at VWAP
- Key level: Resistance at 450

## 2. Entry Criteria
- Signal: Close above VWAP with volume
- Confirmation: Volume surge above 2M
- Entry price: Above 450

## 3. Exit Plan
- Stop loss: 449.50 (below support)
- Target: 452.00 (1:2 risk/reward)
- Time stop: End of session

## 4. Notes & Risk
- Risk: $0.50 per share
- Position size: 2% of account
- Market conditions: Trending market preferred

## 5. Key Visuals
- ![](assets/frame_0194.jpg) *SPY at VWAP support*
- ![](assets/frame_0312.jpg) *Volume surge confirmation*

## 6. Transcript Quotes
> "My entry signal is when we close above VWAP with volume"
> "I'll place my stop just below this support at 449.50"
```

## Performance Characteristics

- **Token usage**: <2 tokens per second of video
- **Processing time**: ≤45s on M3 Ultra with local models
- **Accuracy**: ≥85% correct indicator/price extraction
- **Completeness**: ≥95% of strategies contain all sections

## Integration Workflows

### Strategy Library Building
```bash
# Process multiple videos into organized library
for video in trading_courses/*.mp4; do
  name=$(basename "$video" .mp4)
  scribe analyze "$video" | fabric -p extract_trading_strategy > "strategies/${name}_strategy.md"
done
```

### Live Trading Reference
```bash
# Create quick reference during market hours
scribe analyze recent_setup.mp4 | fabric -p extract_trading_strategy | grep -A5 "Entry Criteria"
```

### Team Knowledge Sharing
```bash
# Convert team training videos
scribe analyze team_training.mp4 | \
  fabric -p extract_trading_strategy | \
  fabric -p create_trading_checklist > team_checklist.md
```

## Visual Analysis Features

When used with the `captions` workflow, this pattern can:

### Chart Pattern Recognition
- Support/resistance levels from OCR text
- Trend lines and chart formations
- Technical indicator values and signals

### Platform Integration
- Trading platform UI elements
- Order entry screens and settings
- Position sizing calculations

### Market Context
- Time and session information
- Market conditions and volatility
- Economic event timing

## Troubleshooting

### Common Issues

**"No asset identified"**
- Ensure video mentions specific symbols (SPY, EUR/USD, BTC)
- Check transcript quality with `scribe transcribe --verbose`

**"Frame selection poor"**
- Use shorter frame intervals: `--frame-interval 15`
- Verify charts are visible: check frame extraction quality

**"Strategy incomplete"**
- Ensure complete trading discussion in video
- Try longer videos (>5 minutes) for complete strategies

### Quality Optimization

**For better accuracy:**
- Use larger Whisper models: `--whisper-model medium`
- Enable rich captions: two-pass vision analysis
- Process shorter video segments (<30 minutes)

**For faster processing:**
- Use `--whisper-model tiny` for previews
- Skip frames for audio-only: `--skip-frames`
- Reduce frame intervals for long videos

## Technical Details

### Frame Selection Algorithm
1. Frames mentioned in transcript (±3s window)
2. High OCR confidence frames (>0.8) with indicators
3. Scene change detection (>30% visual delta)
4. Temporal distribution across video length

### Indicator Normalization
The pattern recognizes common OCR errors:
- "WAP" → "VWAP"
- "MAC-D" → "MACD"
- "R.S.I" → "RSI"
- "B-Bands" → "Bollinger Bands"

### Token Optimization
- Transcript truncation: 10K tokens max
- Caption compression: 120 chars per frame
- Frame sampling: 30s intervals for long videos
- JSON minification for efficiency

## Related Patterns

- `analyze_trading_video` - General trading analysis
- `extract_technical_analysis` - Focus on indicators
- `analyze_market_commentary` - Market outlook extraction

## Contributing

To improve this pattern:
1. Test with diverse trading content
2. Submit evaluation results using eval.md rubric
3. Report edge cases and failure modes
4. Contribute sample input/output pairs