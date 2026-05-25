from __future__ import annotations

"""
Worker Entry Point - DDD Version
Delega para a implementação na camada Infrastructure.
"""

from app.infrastructure.message_queue.redis_worker import run_worker

if __name__ == "__main__":
    run_worker()
