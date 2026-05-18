import sys
import os
from app.services.pipeline import run_pipeline

ms_path = os.path.abspath("../../data/Modena_LettereAntiche_II.11")

try:
    print(f"Starting extraction for {ms_path} using openai provider...")
    output = run_pipeline(
        manuscript_path=ms_path,
        mode="both",
        granularity="both",
        device="auto",
        provider="openai"
    )
    print("Pipeline finished successfully!")
    print("Outputs:", output)
except Exception as e:
    print(f"Error during extraction: {e}")
    sys.exit(1)
