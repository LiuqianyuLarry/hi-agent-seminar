"""Predefined statistics only: never evaluate model-supplied Python expressions."""
import math
from schemas import StatsArgs,success

def temperature_stats(values_c:list[float],limit_c:float)->dict:
    """Count READINGS strictly above a supplied limit; not the duration above it."""
    args=StatsArgs.model_validate({'values_c':values_c,'limit_c':limit_c})
    # BEGIN_SOLUTION W3.1
    count=len(args.values_c)
    above=sum(v>args.limit_c for v in args.values_c)
    return success({'count':count,'mean_c':math.fsum(args.values_c)/count,
                    'max_c':max(args.values_c),'limit_c':args.limit_c,'above_count':above,
                    'above_fraction':above/count,'comparison':'strictly_greater_than'},
                   source='caller_supplied_values')
    # END_SOLUTION W3.1
