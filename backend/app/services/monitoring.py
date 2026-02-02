"""
Monitoring Service
Handles the scheduling and execution of URL monitoring tasks.
"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlmodel import Session, select
from ..database import engine
from ..models.monitor import Monitor
from ..models.user import User
from .scanner import process_url
from .notifications import send_alert_email
import logging

from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

# Initialize Scheduler
scheduler = AsyncIOScheduler()

async def check_monitors():
    """
    Scheduled job to check all active monitors based on their frequency.
    Runs hourly and checks if enough time has passed since the last check.
    """
    logger.info("🕒 Watchdog: Starting scheduled monitor checks...")
    
    with Session(engine) as session:
        # Calculate thresholds
        now = datetime.utcnow()
        day_ago = now - timedelta(days=1)
        week_ago = now - timedelta(days=7)
        
        # Select active monitors
        statement = select(Monitor).where(Monitor.is_active == True)
        all_monitors = session.exec(statement).all()
        
        monitors_to_check = []
        for monitor in all_monitors:
            # Check if due
            is_due = False
            if not monitor.last_checked_at:
                is_due = True
            elif monitor.frequency == "daily" and monitor.last_checked_at <= day_ago:
                is_due = True
            elif monitor.frequency == "weekly" and monitor.last_checked_at <= week_ago:
                is_due = True
                
            if is_due:
                monitors_to_check.append(monitor)

        logger.info(f"🕒 Watchdog: Found {len(monitors_to_check)} monitors due for check.")
        
        for monitor in monitors_to_check:
            try:
                logger.info(f"🔍 Watchdog: Scanning {monitor.url}...")
                
                # Process URL (Async)
                response = await process_url(monitor.url)
                current_score = int(response.global_score)
                
                # Determine if alert is needed
                alert_needed = False
                old_score = monitor.last_score
                
                # Condition 1: Score Drop
                if old_score is not None and current_score < old_score:
                    logger.warning(f"📉 Watchdog: Score dropped for {monitor.url} ({old_score} -> {current_score})")
                    alert_needed = True
                
                # Condition 2: Below Threshold
                if current_score < monitor.threshold:
                    logger.warning(f"⚠️ Watchdog: Score below threshold for {monitor.url} ({current_score} < {monitor.threshold})")
                    alert_needed = True
                     
                if alert_needed:
                    # Get User email to notify
                    user = session.get(User, monitor.user_id)
                    if user and user.email:
                        await send_alert_email(user.email, monitor.url, old_score if old_score else 0, current_score)
                
                # Update Monitor State
                monitor.last_score = current_score
                monitor.last_checked_at = response.analyzed_at or datetime.utcnow()
                session.add(monitor)
                session.commit()
                session.refresh(monitor)
                
            except Exception as e:
                logger.error(f"❌ Watchdog Error on {monitor.url}: {e}")
                session.rollback()

def start_scheduler():
    """Start the APScheduler"""
    # Run every hour to check for due monitors
    scheduler.add_job(check_monitors, CronTrigger(minute=0)) 
    logger.info("✅ Watchdog: Scheduler started (Runs every hour)")
    scheduler.start()

def shutdown_scheduler():
    """Shutdown the APScheduler"""
    scheduler.shutdown()
    logger.info("🛑 Watchdog: Scheduler stopped")
