# TRADING STRATEGY EXTRACTION

You are analyzing a trading video. Extract a structured strategy following this exact format:

# Strategy Summary – [ASSET] ([TIMEFRAME])

## 1. Trade Setup
## 2. Entry Criteria  
## 3. Exit Plan
## 4. Notes & Risk
## 5. Key Visuals
## 6. Transcript Quotes

## TRANSCRIPT
{{transcript}}

## FRAME CAPTIONS
{{captions_json}}

## INSTRUCTIONS

- Extract ASSET and TIMEFRAME from the content
- Use bullet points for sections 1-4
- List specific price levels when mentioned
- For Key Visuals, select frames that show entry/exit points or important chart patterns
- Include 2-3 most relevant transcript quotes as block quotes (use > markdown syntax)
- If information is missing, write "Not specified" or "N/A"
- Focus on actionable trading information
- Prioritize direct quotes over paraphrasing
- Flag uncertain information with [?] markers

## FRAME SELECTION CRITERIA

When selecting Key Visuals, prioritize frames that show:
1. Entry and exit signals on charts
2. Key technical indicators mentioned in transcript
3. Support/resistance levels being discussed
4. Chart patterns or setups being explained
5. Risk management areas (stop losses, targets)

## INDICATOR NORMALIZATION

When processing captions, recognize these common indicator aliases:
- VWAP: "WAP", "VWAP", "V-WAP", "Volume Weighted"
- EMA: "EMA", "Exponential MA", "Exp Moving Avg"  
- RSI: "RSI", "Relative Strength", "R.S.I"
- MACD: "MACD", "MAC-D", "Moving Average Convergence"
- SMA: "SMA", "Simple MA", "Moving Avg"
- Bollinger Bands: "BB", "Bollinger", "B-Bands", "Bollinger Bands"

## OUTPUT REQUIREMENTS

- Maximum 600 words total
- Must include all 6 sections
- Use exact markdown formatting as shown
- Include specific frame filenames in Key Visuals section
- Use block quote format (>) for transcript quotes
- Be concise but comprehensive