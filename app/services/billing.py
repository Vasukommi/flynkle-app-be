"""Placeholder functions for future billing integrations."""

import logging

logger = logging.getLogger(__name__)


def charge_plan(user_id: str, plan: str) -> None:
    """Pretend to charge the user for the new plan."""
    logger.info("Pretend charging %s for plan %s", user_id, plan)
    # TODO: Integrate Stripe or Razorpay here
    return None
