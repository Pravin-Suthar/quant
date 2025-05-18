from db.mysql_client import insert_range_backtest, insert_actual_trade
from core.evaluator import evaluate_range
from core.simulator import simulate_trade
from utils.candle_utils import group_by_day
from config import LOOKBACK_DAYS, MAX_RANGE_MINUTES, START_TIME, END_TIME

# load candles from db (or cached CSV for now)
candles = load_candles()  # You implement this
daily_data = group_by_day(candles)

for i in range(LOOKBACK_DAYS, len(daily_data)):
    today = daily_data[i]
    lookback = daily_data[i - LOOKBACK_DAYS:i]

    best = None
    best_pnl = -float("inf")

    for size in range(1, MAX_RANGE_MINUTES + 1):
        for idx in range(0, len(today) - size):
            from_time = today[idx]["time"]
            to_time = today[idx + size - 1]["time"]

            if from_time > END_TIME:
                break

            for direction in ['long', 'short']:
                stats, high, low = evaluate_range(lookback, from_time, to_time, direction)
                insert_range_backtest([(from_time, to_time, direction, stats["total_profit"], stats["total_loss"],
                                        stats["win_count"], stats["loss_count"], stats["total_trades"],
                                        lookback[0][0]["date"], lookback[-1][0]["date"])])

                if stats["total_profit"] > best_pnl:
                    best = (from_time, to_time, direction, high, low)
                    best_pnl = stats["total_profit"]

    if best:
        result = simulate_trade(today, best[:2], best[2], best[3], best[4])
        if result:
            insert_actual_trade(result)
