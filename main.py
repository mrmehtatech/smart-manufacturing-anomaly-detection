"""Command-line entry point for the smart manufacturing pipeline."""
import logging
from config import SETTINGS, ensure_directories, LOG_DIR
from src.utils import configure_logging
from src.pipeline import run_pipeline
from src.analysis import calculate_kpis, evaluate_simulated_labels

def main() -> None:
    """Run the analytics pipeline and print a concise summary."""
    ensure_directories()
    configure_logging(LOG_DIR)
    logger = logging.getLogger(__name__)
    try:
        data, recommendations = run_pipeline()
        logger.info("KPI summary: %s", calculate_kpis(data))
        logger.info("Simulated-label evaluation: %s", evaluate_simulated_labels(data))
        logger.info("Recommendations generated: %s", len(recommendations))
        print(f"Pipeline completed. Processed data: {SETTINGS.processed_path}")
    except Exception:
        logger.exception("Pipeline failed.")
        raise

if __name__ == "__main__":
    main()
