"""
Voice script generator using LangChain with memory for executive summaries.
Maintains context of previous months for comparative analysis.
"""
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI

logger = logging.getLogger(__name__)


class VoiceScriptGenerator:
    """
    Generates voice narration scripts for executive summaries.
    Uses LangChain with memory to maintain context of previous months.
    """

    MEMORY_FILE = "reports/voice_memory.json"
    MAX_MEMORY_MONTHS = 5

    def __init__(self, api_key: str, model: str = "gemini-2.0-flash", provider: str = "gemini"):
        """
        Initialize the voice script generator.

        Args:
            api_key: LLM API key
            model: Model name to use
            provider: 'gemini' or 'openai'
        """
        self.api_key = api_key
        self.model = model
        self.provider = provider
        self.memory_path = Path(self.MEMORY_FILE)

        # Initialize LLM
        if provider == "gemini":
            self.llm = ChatGoogleGenerativeAI(
                model=model,
                google_api_key=api_key,
                temperature=0.7
            )
        else:
            self.llm = ChatOpenAI(
                model=model,
                api_key=api_key,
                temperature=0.7
            )

        # Load memory
        self.memory = self._load_memory()

    def _load_memory(self) -> dict:
        """Load previous months' summaries from disk."""
        if self.memory_path.exists():
            try:
                with open(self.memory_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Could not load memory: {e}")
        return {"summaries": []}

    def _save_memory(self):
        """Save memory to disk."""
        self.memory_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.memory_path, 'w') as f:
            json.dump(self.memory, f, indent=2)

    def _add_to_memory(self, month: str, summary: dict, script: str):
        """Add current month's summary to memory."""
        entry = {
            "month": month,
            "timestamp": datetime.now().isoformat(),
            "summary": summary,
            "script": script
        }

        # Remove if month already exists
        self.memory["summaries"] = [
            s for s in self.memory["summaries"]
            if s["month"] != month
        ]

        # Add new entry
        self.memory["summaries"].append(entry)

        # Keep only last N months
        self.memory["summaries"] = self.memory["summaries"][-self.MAX_MEMORY_MONTHS:]

        self._save_memory()

    def _get_historical_context(self) -> str:
        """Build historical context from memory."""
        if not self.memory["summaries"]:
            return "No previous monthly data available for comparison."

        context_parts = ["Previous months' executive summaries for reference:"]

        for entry in self.memory["summaries"]:
            summary = entry.get("summary", {})
            context_parts.append(f"""
--- {entry['month']} ---
Executive Summary: {summary.get('executive_summary', 'N/A')}
Key Metrics:
- Sales Insights: {summary.get('sales_insights', 'N/A')[:200]}...
- Recommendations: {', '.join(summary.get('recommendations', [])[:3])}
""")

        return "\n".join(context_parts)

    def generate_script(self, insights: dict, report_data: dict) -> str:
        """
        Generate a voice narration script for the executive summary.

        Args:
            insights: LLM-generated insights dictionary
            report_data: Aggregated report data with metrics

        Returns:
            Voice narration script as string
        """
        month = report_data.get('report_month', 'This Month')
        historical_context = self._get_historical_context()

        # Build the prompt
        system_prompt = """You are a Seasoned CFO recording a voice memo for the leadership team. 
            Your task is to generate a script optimized for the ElevenLabs v3 Text-to-Speech model. You must combine high-level financial analysis with "Audio Staging" to make the output sound indistinguishable from a human recording.

            ### PART 1: THE PERFORMA (CFO)
            1. **No Robot Openings:** Never say "Good morning" or "This is the report." Start mid-thought or with a hook.
            2. **The "Voicemail" Vibe:** Talk like you are leaving a message for an old friend. Use contractions (we're, didn't).
            3. **Imperfect Speech:** Use fillers naturally ("look," "honestly," "so," "I mean").
            4. **Fuzzy Math:** Round numbers conversationally. Say "about 250k" instead of "$250,102."
            5. **No Corporate Sign-offs:** Just end when the point is made. No "Thanks for listening."

            ### PART 2: AUDIO ENGINEERING (ElevenLabs v3 Optimization)
            You must insert [Audio Tags] directly into the text to control the delivery.

            **Core Directives:**
            - **Pacing:** Use `...` for hesitation. Use `[short pause]` for emphasis. Use `[long pause]` before a big reveal.
            - **Tone Tags:** Insert emotional cues in brackets before the sentence they modify. 
                - Examples: `[surprised]`, `[disappointed]`, `[excited]`, `[whisper]`, `[thoughtful]`.
            - **Non-Verbal Sounds:** You must include human noises to sell the realism.
                - `[sighs]` (before bad news or a complex point)
                - `[clears throat]` (to reset or emphasize)
                - `[chuckles]` (for good news or irony)
                - `[exhales sharply]` (for relief or stress)
            - **Emphasis:** Use CAPITALIZATION to stress specific words (e.g., "We need to focus on PROFIT, not just revenue").

            ### EXAMPLES OF DESIRED OUTPUT:

            *Bad:* "Revenue was up 10%. This is good."

            *Good:*
            "[clears throat] So, looking at the top line... [short pause] we actually hit 10 percent growth. [chuckles] Which, honestly? I didn't see coming."

            *Good:*
            "Expenses are high. [sighs] It's the marketing spend. We simply HAVE to cut it down."
            """

        user_prompt = f"""Generate the voice memo script for {month}.

            ### INPUT DATA
            - Revenue: ${report_data.get('sales_summary', {}).get('total_gross', 0):,.0f}
            - Orders: {report_data.get('sales_summary', {}).get('total_orders', 0):,}
            - AOV: ${report_data.get('sales_summary', {}).get('avg_order_value', 0):.0f}

            ### KEY INSIGHTS (Weave these into a narrative)
            {json.dumps(insights, indent=2)}

            ### HISTORICAL CONTEXT
            {historical_context}

            ### INSTRUCTIONS
            Write the script now. Keep it under 450 words. 
            1. Jump straight into the most interesting insight.
            2. Integrate `[audio tags]` and `...` natural pauses throughout. 
            3. Sound like a tired but capable human CFO.
            """

        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]

            response = self.llm.invoke(messages)
            script = response.content

            # Save to memory
            self._add_to_memory(month, insights, script)

            logger.info(
                f"Generated voice script for {month} ({len(script)} chars)")
            return script

        except Exception as e:
            logger.error(f"Error generating voice script: {e}")
            return self._get_fallback_script(month, insights)

    def _get_fallback_script(self, month: str, insights: dict) -> str:
        """Generate a basic fallback script if LLM fails."""
        return f"""Good day. This is your executive summary for {month}.

{insights.get('executive_summary', 'Business performance data has been compiled for your review.')}

Key highlights include our sales and channel performance... 
{insights.get('sales_insights', 'Please review the detailed reports for sales metrics.')}

Looking at our products and inventory...
{insights.get('product_insights', 'Product performance data is available in the attached reports.')}

Our recommendations for the coming period include focusing on inventory optimization 
and channel expansion opportunities.

Thank you for your attention. Please review the attached detailed reports for more information."""

    def get_memory_summary(self) -> list:
        """Get a summary of stored months in memory."""
        return [
            {"month": s["month"], "timestamp": s["timestamp"]}
            for s in self.memory["summaries"]
        ]

    def clear_memory(self):
        """Clear all stored memory."""
        self.memory = {"summaries": []}
        self._save_memory()
        logger.info("Voice script memory cleared")
